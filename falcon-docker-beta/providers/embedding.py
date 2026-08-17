"""Cynovela — EmbeddingProvider 抽象層。

注意: v11では ChromaDB の get_or_create_collection が内部で sentence-transformers を
呼び出しており、rag.py から直接 sentence-transformers を呼ぶ箇所は無い。
本Providerは将来 ChromaDB 経由を bypass して埋め込みを差し替えるための
インターフェイスを提供する（現状は test_connection / 直接embed の試験経路）。
"""

from __future__ import annotations

import logging
import os
import os.path as _osp
from urllib.parse import urlsplit, urlunsplit

import httpx

_log = logging.getLogger("cynovela.embedding")  # rag.py と同じ handler 系統に載せる

# c10-external-host-20260729: 外の推論サーバ (Mac Accelerator Service) の宛先を
# コンテナ形態でもホスト直起動でも同じ設定のまま成立させる。
# 配る cynovela.yaml の既定は host.containers.internal (podman のホストゲートウェイ) で、
# これはコンテナの外では名前解決できない = ホスト直起動では必ず届かず、毎回ローカルへ
# 退避していた。判定は core/llm.py default_llm_endpoint() と同一 (コンテナマーカーのみ・
# 環境変数を一切参照しない)。
_CONTAINER_GATEWAY_HOSTS = ("host.containers.internal", "host.docker.internal")


def _in_container() -> bool:
    """コンテナ内で動いているか (core/llm.py default_llm_endpoint と同一判定)。"""
    return _osp.exists("/run/.containerenv") or _osp.exists("/.dockerenv")


def resolve_external_base_url(base_url: str) -> str:
    """外の推論サーバの base_url を実行形態に合わせて解決する。

    読み替えるのは「コンテナのホストゲートウェイ名が書かれていて、かつコンテナの外で
    動いている」ときだけで、その 1 通りに限る:
        http://host.containers.internal:18850  →  http://127.0.0.1:18850  (コンテナ外)
    それ以外 (LAN の IP・別ホスト名・localhost など、利用者が明示的に書いた宛先) は
    一切書き換えず素通しする。ホストゲートウェイ名はコンテナの外では定義が無く必ず
    名前解決に失敗するため、この読み替えで失われる指定は無い。
    逆向き (localhost → host.containers.internal) は行わない。コンテナ内の localhost を
    明示指定する使い方 (同じコンテナに口を同居させる) を壊さないため。
    """
    if not base_url:
        return base_url
    try:
        parts = urlsplit(base_url)
        if (parts.hostname or "").lower() not in _CONTAINER_GATEWAY_HOSTS:
            return base_url
        if _in_container():
            return base_url
        netloc = "127.0.0.1" if parts.port is None else f"127.0.0.1:{parts.port}"
        resolved = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return base_url
    _log.info(
        f"[Cynovela] 外の推論サーバの宛先をホスト直起動向けに読み替えました: "
        f"{base_url} → {resolved}"
    )
    return resolved


class EmbeddingProvider:
    """抽象基底クラス。"""

    # BLOCK A-1: optional 属性。サブクラスで上書き可能。
    # 既存サブクラス (Local/MLX/OpenAI互換) はモデルがロードされるまで dim 不明だが、
    # all-MiniLM-L6-v2 / paraphrase-MiniLM-L3-v2 ともに 384 のため既定値とする。
    dimension: int = 384

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    async def embed_query(self, text: str) -> list[float]:
        """単一クエリの埋め込み。デフォルトは embed() への薄いラッパー。"""
        vecs = await self.embed([text])
        return vecs[0] if vecs else []

    async def test_connection(self) -> dict:
        raise NotImplementedError


class LocalSentenceTransformerProvider(EmbeddingProvider):
    """ローカルの sentence-transformers を使用する Provider。"""

    _MODEL_DIMS = {
        "all-MiniLM-L6-v2": 384,
        "paraphrase-MiniLM-L3-v2": 384,
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
        "BAAI/bge-m3": 1024,
        "intfloat/multilingual-e5-large": 1024,
    }

    def __init__(self, model: str = "BAAI/bge-m3", device: str | None = None):
        self.model_name = model
        # mas-device-20260725: None=自動 (sentence-transformers 既定)。"cpu"/"mps" で明示。
        self.device = device
        self._model = None
        if model in self._MODEL_DIMS:
            self.dimension = self._MODEL_DIMS[model]

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            # 状態は store/ 配下に集約 (ホームに状態を置かない)。DLフォールバック先も
            # store/models にする (同梱モデルは下の PORTABILITY FIX で store から直ロード)。
            _models_base = os.environ.get("CYNOVELA_DATA_DIR") or os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "store"
            )
            cache_dir = os.path.join(_models_base, "models")
            os.makedirs(cache_dir, exist_ok=True)
            # Phase 0c: モデルパス自動解決 (cynovela.yaml.models.embedding.path > 配布同梱 > HFキャッシュ)
            try:
                from core.model_paths import resolve_model_path, get_configured_model

                _name, _path = get_configured_model("embedding")
                resolved = resolve_model_path(_name or self.model_name, _path)
            except Exception:
                resolved = self.model_name
            # --- PORTABILITY FIX: TAR 配布同梱 store/models/ をローカルパス候補に追加 ---
            # reranker.py の portability fix と同等。resolve_model_path() で見つからなかった
            # 場合に {repo_root}/store/models/ 配下を 2 形式 (直接 / HF キャッシュ形式) で探索。
            # TAR 展開直後で ~/.cynovela/models/ が空の新環境でも動くようにする目的。
            try:
                import pathlib as _pl_pf
                if not _pl_pf.Path(str(resolved)).is_dir():
                    _app_dir = _pl_pf.Path(__file__).resolve().parent.parent
                    _store_models = _app_dir / "store" / "models"
                    _direct = _store_models / self.model_name.replace("/", os.sep)
                    _hf_dir = _store_models / ("models--" + self.model_name.replace("/", "--"))
                    if _direct.is_dir():
                        resolved = str(_direct)
                    elif _hf_dir.is_dir():
                        _snapshots = sorted((_hf_dir / "snapshots").glob("*"))
                        if _snapshots:
                            resolved = str(_snapshots[-1])
            except Exception:
                pass
            # --- END PORTABILITY FIX ---
            # resolved がローカルディレクトリなら直接ロード（local_files_only 不要）。
            # それ以外（HF model ID）なら local_files_only=True で意図しないネットワーク
            # 取得を防ぐ（事前に preflight でダウンロード済みである前提）。
            import pathlib as _pl

            _is_local_path = _pl.Path(str(resolved)).is_dir()
            if _is_local_path:
                self._model = SentenceTransformer(str(resolved), device=self.device)
            else:
                self._model = SentenceTransformer(
                    str(resolved),
                    cache_folder=cache_dir,
                    local_files_only=True,
                    device=self.device,
                )
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        m = self._ensure_model()
        # SentenceTransformer は同期だが asyncio との親和を保つため to_thread で実行
        import asyncio

        vecs = await asyncio.to_thread(m.encode, texts)
        return [list(map(float, v)) for v in vecs]

    async def test_connection(self) -> dict:
        try:
            self._ensure_model()
            return {"status": "connected", "provider": "local", "model": self.model_name}
        except Exception as e:
            return {"status": "error", "provider": "local", "error": str(e)}


class MLXEmbeddingProvider(EmbeddingProvider):
    """MLX 用 Provider（骨格のみ）。mlx-embeddings の安定性確認後に実装予定。"""

    def __init__(self, model: str = "mlx-community/all-MiniLM-L6-v2-4bit"):
        self.model_name = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("MLX embedding は将来実装予定")

    async def test_connection(self) -> dict:
        return {
            "status": "not_implemented",
            "provider": "mlx",
            "model": self.model_name,
            "message": "MLX embedding は将来実装予定",
        }


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """OpenAI互換 /v1/embeddings エンドポイントを使用する Provider。"""

    def __init__(self, base_url: str, model: str = "text-embedding-ada-002", api_key: str = "", content_class: str = "masked"):
        # c10-external-host-20260729: 生成経路が複数 (get_embedding_provider / 設定画面の
        # 接続テスト / rag.py) あるため、読み替えは入口ではなくここ 1 箇所で行う。
        self.base_url = resolve_external_base_url((base_url or "").rstrip("/"))
        if self.base_url.endswith("/v1"):
            self.base_url = self.base_url[: -len("/v1")]
        self.model = model
        self.api_key = api_key or ""  # DD-CYN-0067 G-2: 鍵は設定/画面からのみ (env 読みを撤去)
        # mas-trust-boundary-20260725: 口へ渡す本文が原文かマスキング済みかを常に明示する。
        # Cynovela のインデックス/検索経路が外へ出すのはマスキング済みのみ (masked-only 不可侵)。
        self.content_class = content_class or "masked"

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{self.base_url}/v1/embeddings",
                headers=self._headers(),
                json={"model": self.model, "input": texts, "content_class": self.content_class},
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            # OpenAI互換: data は [{embedding: [...], index: int}, ...]
            return [item.get("embedding", []) for item in data]

    async def test_connection(self) -> dict:
        if not self.api_key:
            return {
                "status": "warning",
                "provider": "openai_compat",
                "endpoint": f"{self.base_url}/v1/embeddings",
                "error": "API key 未設定（環境変数 CYNOVELA_EMBEDDING_API_KEY または設定UI から）",
            }
        try:
            vecs = await self.embed(["healthcheck"])
            return {
                "status": "connected",
                "provider": "openai_compat",
                "endpoint": f"{self.base_url}/v1/embeddings",
                "dim": len(vecs[0]) if vecs and vecs[0] else 0,
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "provider": "openai_compat",
                "endpoint": f"{self.base_url}/v1/embeddings",
                "error": str(e),
            }


def get_embedding_provider(config: dict) -> EmbeddingProvider:
    """`config["embedding"]` を見て適切な Provider を返す。

    mas-device-20260725: embedding.device で実行先を選ぶ。
      本体(ホスト直)側の指定値: auto / cpu / mps / external
      コンテナ側の指定値:       local_cpu / local_mps / external_accelerator
    external* は base_url (外部の推論サーバ = Mac Accelerator Service) を指す openai_compat。
    auto/未指定は従来どおり provider キーの解釈 (完全無回帰)。
    """
    e = (config or {}).get("embedding", {}) or {}
    provider = (e.get("provider") or "local").lower()
    model = e.get("model") or "BAAI/bge-m3"
    base_url = e.get("base_url") or ""
    api_key = e.get("api_key") or ""
    device = (e.get("device") or "").lower()
    if device in ("external", "external_accelerator"):
        return OpenAICompatibleEmbeddingProvider(base_url=base_url, model=model, api_key=api_key)
    if device in ("cpu", "local_cpu"):
        return LocalSentenceTransformerProvider(model=model, device="cpu")
    if device in ("mps", "local_mps"):
        return LocalSentenceTransformerProvider(model=model, device="mps")
    if provider == "mlx":
        return MLXEmbeddingProvider(model=model)
    if provider == "openai_compat":
        return OpenAICompatibleEmbeddingProvider(base_url=base_url, model=model, api_key=api_key)
    return LocalSentenceTransformerProvider(model=model)


# ─── BLOCK A-1: TF-IDF Embedding (minimal mode, PyTorch不要) ───


class TFIDFEmbedding(EmbeddingProvider):
    """minimalモード用 Embedding。sklearn のみで動作（PyTorch不要）。
    最初の N サンプルが集まるまでは fit できないためゼロベクトルを返す。
    fit 後は TruncatedSVD で固定次元 (DIM=512) に射影し L2 正規化する。

    注意: rag.py の publish 経路への統合は A-2 で行う。A-1 では骨格のみ提供する。
    """

    DIM = 512
    dimension = 512

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        self._TfidfVectorizer = TfidfVectorizer
        self._TruncatedSVD = TruncatedSVD
        self._vectorizer = TfidfVectorizer(max_features=10000)
        self._svd = TruncatedSVD(n_components=self.DIM)
        self._fitted = False
        self._corpus: list[str] = []

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        import numpy as np

        # 学習コーパスに追加（直近 10000 件で再 fit）
        self._corpus.extend(texts)
        all_texts = self._corpus[-10000:]
        try:
            tfidf = self._vectorizer.fit_transform(all_texts)
            if tfidf.shape[0] >= self.DIM and tfidf.shape[1] >= self.DIM:
                self._svd.fit(tfidf)
                self._fitted = True
        except Exception:
            self._fitted = False

        if not self._fitted:
            return [[0.0] * self.DIM for _ in texts]

        try:
            tfidf_q = self._vectorizer.transform(texts)
            vec = self._svd.transform(tfidf_q)
            norms = np.linalg.norm(vec, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            return (vec / norms).tolist()
        except Exception:
            return [[0.0] * self.DIM for _ in texts]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        return await asyncio.to_thread(self._embed_sync, texts)

    async def test_connection(self) -> dict:
        return {
            "status": "ok",
            "provider": "tfidf",
            "dim": self.DIM,
            "fitted": self._fitted,
            "corpus_size": len(self._corpus),
        }


def create_embedding_provider(app_cfg) -> EmbeddingProvider:
    """BLOCK A-1: AppConfig (mode/demo/mock) に基づいて Provider を返す。

    既存の `get_embedding_provider(config: dict)` (cynovela.yaml ベース) は
    そのまま残す。本関数は AppConfig からの新経路。
    """
    if getattr(app_cfg, "use_tfidf", False):
        return TFIDFEmbedding()
    model_name = getattr(app_cfg, "embedding_model_name", "all-MiniLM-L6-v2")
    return LocalSentenceTransformerProvider(model=model_name)
