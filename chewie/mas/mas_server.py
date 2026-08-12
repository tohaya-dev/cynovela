"""Mac Accelerator Service (MAS) — 外の口。

同一 Mac のホスト側ネイティブで動く推論の口。コンテナ (falcon / hansolo worker) や
ホスト直アプリ (chewie) から HTTP で呼ばれ、Apple GPU (Metal / MPS) に届かせる。
信頼境界は Mac の中から出ない設計だが、口自体は「同一マシン内にいること」を
作り込まない (呼び先は呼ぶ側の設定で決まる)。複数 Mac にまたがる配置は外部送出に
なるため、渡すものが原文か伏字済みかを常に明示的に受け取る (content_class)。

提供する口 (ga-finish-20260727):
  GET  /health          — 生存とデバイス・モデル常駐状態
  GET  /capabilities    — 相手の能力の問い合わせ (embeddings / rerank / images)
  GET  /metrics         — 工程別の基本計測
  POST /v1/embeddings   — OpenAI 互換 + content_class 必須。バッチ可
  POST /v1/rerank       — 再ランク (content_class 必須・埋め込みの窓と同じ作り)
  POST /v1/images/embeddings — 将来の口 (未実装を明示して返す)

設定は mas.yaml のみ (環境変数は使わない・増やさない)。
モデルは本流と同じ置き場 (store/models) を読み取り専用で参照し、新規ダウンロードは
行わない。モデルは常駐させ、同じモデルを二度読まない。
起動: python mas/mas_server.py [--config mas/mas.yaml]
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

MAS_VERSION = "0.2.0-ga-finish-20260727"
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_APP_DIR)

_DEFAULT_CONFIG = {
    "server": {"host": "127.0.0.1", "port": 18850},
    # models.*.path が '' のときは store/models (本流と同じ置き場) の HF キャッシュ形式から解決する。
    "models": {
        "embedding": {"name": "BAAI/bge-m3", "path": ""},
        "reranker": {"name": "BAAI/bge-reranker-v2-m3", "path": ""},
    },
    # device: auto / cpu / mps  (auto = MPS が使えれば MPS)
    "device": "auto",
    "batch": {"max_texts": 512},
    # ANE (Core ML) 経路はベータ。既定オフで並べるところまで (正式統合は hansolo 側)。
    "ane": {"enabled": False, "rerank_mlpackage": ""},
    # 同一 Mac 内では raw も受けられるが、複数 Mac にまたがる配置 (=外部送出) では
    # 伏字済みのみ受ける不変条件に合わせて false にすること。
    "policy": {"allow_raw_content": True},
}


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | None) -> dict:
    cfg = dict(_DEFAULT_CONFIG)
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            user = yaml.safe_load(f) or {}
        cfg = _merge(cfg, user)
    return cfg


def _resolve_model_dir(name: str, explicit_path: str) -> str | None:
    """モデル実体のローカルディレクトリを解決する。新規ダウンロードはしない。"""
    if explicit_path and os.path.isdir(explicit_path):
        return explicit_path
    store_models = os.path.join(_REPO_ROOT, "store", "models")
    direct = os.path.join(store_models, name.replace("/", os.sep))
    if os.path.isdir(direct):
        return direct
    hf_dir = os.path.join(store_models, "models--" + name.replace("/", "--"))
    snap_dir = os.path.join(hf_dir, "snapshots")
    if os.path.isdir(snap_dir):
        snaps = sorted(os.listdir(snap_dir))
        if snaps:
            return os.path.join(snap_dir, snaps[-1])
    return None


class MasState:
    """常駐モデルと計測値。モデルは一度だけ読む。"""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.started_at = time.time()
        self.lock = threading.Lock()
        self.model = None
        self.model_dir = None
        self.device = "cpu"
        self.load_seconds = 0.0
        # ga-finish-20260727: 再ランクモデルの常駐 (埋め込みと同じ「一度だけ読む」作り)
        self.rr_model = None
        self.rr_model_dir = None
        self.rr_device = "cpu"
        self.rr_load_seconds = 0.0
        self.rr_lock = threading.Lock()
        self.metrics = {
            "embeddings_requests": 0,
            "embeddings_texts": 0,
            "embeddings_seconds_total": 0.0,
            "embeddings_last_batch_size": 0,
            "embeddings_last_seconds": 0.0,
            "embeddings_last_texts_per_second": 0.0,
            # ga-finish-20260727: 再ランクの実測。rejected は不正リクエスト却下数として残す。
            "rerank_requests": 0,
            "rerank_pairs": 0,
            "rerank_seconds_total": 0.0,
            "rerank_last_pairs": 0,
            "rerank_last_seconds": 0.0,
            "rerank_requests_rejected": 0,
            "images_requests_rejected": 0,
            "content_class_counts": {"masked": 0, "raw": 0},
        }

    def resolve_device(self) -> str:
        want = (self.cfg.get("device") or "auto").lower()
        if want == "cpu":
            return "cpu"
        try:
            import torch

            has_mps = torch.backends.mps.is_available()
        except Exception:
            has_mps = False
        if want == "mps":
            if not has_mps:
                raise RuntimeError("device=mps 指定だが MPS が使えない環境")
            return "mps"
        return "mps" if has_mps else "cpu"

    def ensure_embedding_model(self):
        if self.model is not None:
            return self.model
        with self.lock:
            if self.model is not None:
                return self.model
            emb_cfg = (self.cfg.get("models") or {}).get("embedding") or {}
            name = emb_cfg.get("name") or "BAAI/bge-m3"
            model_dir = _resolve_model_dir(name, emb_cfg.get("path") or "")
            if not model_dir:
                raise RuntimeError(
                    f"埋め込みモデル {name} のローカル実体が見つからない (store/models 配下・"
                    "新規ダウンロードは行わない方針)。mas.yaml の models.embedding.path を確認。"
                )
            self.device = self.resolve_device()
            t0 = time.perf_counter()
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_dir, device=self.device)
            self.load_seconds = time.perf_counter() - t0
            self.model_dir = model_dir
            return self.model

    def ensure_reranker_model(self):
        """ga-finish-20260727: 再ランクモデルの常駐。埋め込み (ensure_embedding_model) と同じ作り。
        共有置き場 (store/models) の既存重みのみ使い、新規ダウンロードは行わない。装置は MPS
        (resolve_device の auto = MPS が使えれば MPS)。"""
        if self.rr_model is not None:
            return self.rr_model
        with self.rr_lock:
            if self.rr_model is not None:
                return self.rr_model
            rr_cfg = (self.cfg.get("models") or {}).get("reranker") or {}
            name = rr_cfg.get("name") or "BAAI/bge-reranker-v2-m3"
            model_dir = _resolve_model_dir(name, rr_cfg.get("path") or "")
            if not model_dir:
                raise RuntimeError(
                    f"再ランクモデル {name} のローカル実体が見つからない (store/models 配下・"
                    "新規ダウンロードは行わない方針)。mas.yaml の models.reranker.path を確認。"
                )
            self.rr_device = self.resolve_device()
            t0 = time.perf_counter()
            from sentence_transformers import CrossEncoder

            self.rr_model = CrossEncoder(model_dir, max_length=512, device=self.rr_device)
            self.rr_load_seconds = time.perf_counter() - t0
            self.rr_model_dir = model_dir
            return self.rr_model


def create_app(cfg: dict) -> FastAPI:
    app = FastAPI(title="Mac Accelerator Service", version=MAS_VERSION)
    state = MasState(cfg)
    app.state.mas = state

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "service": "mac-accelerator-service",
            "version": MAS_VERSION,
            "device": state.device if state.model is not None else None,
            "model_loaded": state.model is not None,
            "reranker_device": state.rr_device if state.rr_model is not None else None,
            "reranker_loaded": state.rr_model is not None,
            "uptime_seconds": round(time.time() - state.started_at, 3),
        }

    @app.get("/capabilities")
    def capabilities():
        emb_cfg = (cfg.get("models") or {}).get("embedding") or {}
        ane_cfg = cfg.get("ane") or {}
        # §9-4: 埋め込みの識別 (名前+版) を返し、呼び側の索引整合チェックに使わせる。
        # 版 = HF キャッシュの snapshot ディレクトリ名 (実体の commit hash)。
        _emb_name = emb_cfg.get("name") or "BAAI/bge-m3"
        _emb_dir = _resolve_model_dir(_emb_name, emb_cfg.get("path") or "")
        _emb_rev = "unknown"
        if _emb_dir and os.path.basename(os.path.dirname(_emb_dir)) == "snapshots":
            _emb_rev = os.path.basename(_emb_dir)
        return {
            "service": "mac-accelerator-service",
            "version": MAS_VERSION,
            "embeddings": {
                "available": True,
                "models": [_emb_name],
                "revision": _emb_rev,
                "device": state.device if state.model is not None else (cfg.get("device") or "auto"),
                "batch_max_texts": int((cfg.get("batch") or {}).get("max_texts") or 512),
                "content_class_required": True,
            },
            "rerank": {
                "available": True,
                "models": [((cfg.get("models") or {}).get("reranker") or {}).get("name") or "BAAI/bge-reranker-v2-m3"],
                "device": state.rr_device if state.rr_model is not None else (cfg.get("device") or "auto"),
                "batch_max_texts": int((cfg.get("batch") or {}).get("max_texts") or 512),
                "content_class_required": True,
                "ane": {"present": bool(ane_cfg.get("rerank_mlpackage")), "enabled": bool(ane_cfg.get("enabled"))},
            },
            "images": {"available": False, "reason": "not_implemented (将来の口)"},
        }

    @app.get("/metrics")
    def metrics():
        m = dict(state.metrics)
        m["content_class_counts"] = dict(state.metrics["content_class_counts"])
        m["model_load_seconds"] = round(state.load_seconds, 3)
        m["reranker_load_seconds"] = round(state.rr_load_seconds, 3)
        m["uptime_seconds"] = round(time.time() - state.started_at, 3)
        m["device"] = state.device if state.model is not None else None
        m["reranker_device"] = state.rr_device if state.rr_model is not None else None
        return m

    @app.post("/v1/embeddings")
    async def embeddings(request: Request):
        body = await request.json()
        texts = body.get("input")
        if isinstance(texts, str):
            texts = [texts]
        if not isinstance(texts, list) or not texts or not all(isinstance(t, str) for t in texts):
            raise HTTPException(400, "input は文字列または文字列の配列")
        max_texts = int((cfg.get("batch") or {}).get("max_texts") or 512)
        if len(texts) > max_texts:
            raise HTTPException(413, f"バッチ上限 {max_texts} 件を超過 ({len(texts)} 件)")
        # 信頼境界: 渡された本文が原文か伏字済みかを明示的に受け取る。
        content_class = body.get("content_class")
        if content_class not in ("masked", "raw"):
            raise HTTPException(
                400,
                "content_class は必須 ('masked' | 'raw')。渡す本文が伏字済みか原文かを明示すること。",
            )
        if content_class == "raw" and not (cfg.get("policy") or {}).get("allow_raw_content", True):
            raise HTTPException(403, "この口は raw (原文) を受けない設定 (伏字済みのみ)")
        try:
            model = state.ensure_embedding_model()
        except Exception as e:
            raise HTTPException(503, f"モデル未ロード: {e}")
        t0 = time.perf_counter()
        import asyncio

        vecs = await asyncio.to_thread(model.encode, texts)
        dt = time.perf_counter() - t0
        m = state.metrics
        m["embeddings_requests"] += 1
        m["embeddings_texts"] += len(texts)
        m["embeddings_seconds_total"] += dt
        m["embeddings_last_batch_size"] = len(texts)
        m["embeddings_last_seconds"] = round(dt, 6)
        m["embeddings_last_texts_per_second"] = round(len(texts) / dt, 3) if dt > 0 else 0.0
        m["content_class_counts"][content_class] += 1
        data = [
            {"object": "embedding", "index": i, "embedding": [float(x) for x in v]}
            for i, v in enumerate(vecs)
        ]
        return {
            "object": "list",
            "data": data,
            "model": body.get("model") or ((cfg.get("models") or {}).get("embedding") or {}).get("name"),
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
            "mas": {"device": state.device, "seconds": round(dt, 6), "content_class": content_class},
        }

    @app.post("/v1/rerank")
    async def rerank(request: Request):
        # ga-finish-20260727: 再ランクの実装。埋め込みの窓 (/v1/embeddings) と同じ作りに揃える:
        #   - content_class 必須 (信頼境界: 渡す本文が伏字済みか原文かを常に明示)
        #   - バッチ上限は batch.max_texts を documents 件数に適用
        #   - モデルは store/models の既存重みを一度だけ読み常駐 (新規ダウンロードなし)
        # 応答形は呼び側 (providers/reranker.py の results=[{index, relevance_score}] 解釈) に合わせる。
        body = await request.json()
        query = body.get("query")
        documents = body.get("documents")
        if not isinstance(query, str) or not query:
            state.metrics["rerank_requests_rejected"] += 1
            raise HTTPException(400, "query は必須 (文字列)")
        if not isinstance(documents, list) or not documents or not all(isinstance(d, str) for d in documents):
            state.metrics["rerank_requests_rejected"] += 1
            raise HTTPException(400, "documents は文字列の配列 (1件以上)")
        max_texts = int((cfg.get("batch") or {}).get("max_texts") or 512)
        if len(documents) > max_texts:
            state.metrics["rerank_requests_rejected"] += 1
            raise HTTPException(413, f"バッチ上限 {max_texts} 件を超過 ({len(documents)} 件)")
        try:
            top_n = int(body.get("top_n") or len(documents))
        except (TypeError, ValueError):
            top_n = len(documents)
        top_n = max(1, min(top_n, len(documents)))
        content_class = body.get("content_class")
        if content_class not in ("masked", "raw"):
            state.metrics["rerank_requests_rejected"] += 1
            raise HTTPException(
                400,
                "content_class は必須 ('masked' | 'raw')。渡す本文が伏字済みか原文かを明示すること。",
            )
        if content_class == "raw" and not (cfg.get("policy") or {}).get("allow_raw_content", True):
            state.metrics["rerank_requests_rejected"] += 1
            raise HTTPException(403, "この口は raw (原文) を受けない設定 (伏字済みのみ)")
        try:
            model = state.ensure_reranker_model()
        except Exception as e:
            raise HTTPException(503, f"モデル未ロード: {e}")
        t0 = time.perf_counter()
        import asyncio

        pairs = [(query, d) for d in documents]
        scores = await asyncio.to_thread(model.predict, pairs)
        dt = time.perf_counter() - t0
        m = state.metrics
        m["rerank_requests"] += 1
        m["rerank_pairs"] += len(pairs)
        m["rerank_seconds_total"] += dt
        m["rerank_last_pairs"] = len(pairs)
        m["rerank_last_seconds"] = round(dt, 6)
        m["content_class_counts"][content_class] += 1
        ranked = sorted(
            ((i, float(scores[i])) for i in range(len(documents))),
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]
        return {
            "results": [{"index": i, "relevance_score": s} for i, s in ranked],
            "model": body.get("model") or ((cfg.get("models") or {}).get("reranker") or {}).get("name"),
            "mas": {"device": state.rr_device, "seconds": round(dt, 6), "content_class": content_class},
        }

    @app.post("/v1/images/embeddings")
    async def images_embeddings(request: Request):
        # 画像の将来の口。今は作らない (塞がない形だけ確保)。
        state.metrics["images_requests_rejected"] += 1
        return JSONResponse(
            status_code=501,
            content={"error": "not_implemented", "message": "画像埋め込みは未実装 (将来の口・入口のみ)"},
        )

    return app


def main():
    ap = argparse.ArgumentParser(description="Mac Accelerator Service (外の口)")
    ap.add_argument("--config", default=os.path.join(_APP_DIR, "mas.yaml"))
    ap.add_argument("--port", type=int, default=None, help="mas.yaml の server.port を上書き")
    ap.add_argument("--host", default=None, help="mas.yaml の server.host を上書き")
    ap.add_argument("--preload", action="store_true", help="起動時にモデルを常駐ロードする (既定: 初回要求時)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    host = args.host or (cfg.get("server") or {}).get("host") or "127.0.0.1"
    port = int(args.port or (cfg.get("server") or {}).get("port") or 18850)

    app = create_app(cfg)
    if args.preload:
        t0 = time.perf_counter()
        app.state.mas.ensure_embedding_model()
        print(
            f"[MAS] model preloaded: dir={app.state.mas.model_dir} device={app.state.mas.device} "
            f"load={time.perf_counter() - t0:.2f}s",
            flush=True,
        )

    import uvicorn

    print(f"[MAS] Mac Accelerator Service {MAS_VERSION} listening on {host}:{port}", flush=True)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    sys.exit(main())
