> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# Cynovela アーキテクチャ

## 1. コンポーネント全体図

```
            +-----------------------------------------------------+
            |              フロントエンド (frontend/)              |
            |  Pages / Workspace UI / Chat UI / Dashboard         |
            +-----------------------------------------------------+
                                  |  HTTP / SSE (Server-Sent Events)
                                  v
+-----------------------------------------------------------------------+
|                       FastAPI アプリ (server.py)                       |
|                                                                       |
|  +----------------+   +----------------+   +----------------------+   |
|  | IP アローリスト |   |  認証ミドル     |   |  RBAC ヘルパー        |   |
|  | (lan/tailscale)|   |  (Bearer Token)|   |  core/auth.py        |   |
|  +----------------+   +----------------+   +----------------------+   |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  ルーター層 (routers/) 36 個                                      |  |
|  |  workspaces / collections / sources / chat / settings /         |  |
|  |  guardrails / policies / mcp / dashboard / files / users ...    |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  サービス・ドメイン層                                              |  |
|  |  rag.py            : RAG パイプライン本体                          |  |
|  |  guardrail.py      : PII マスク / ガードレール                     |  |
|  |  chunker.py        : Contextual Chunking                        |  |
|  |  adaptive_rag.py   : 複雑度判定 / Agentic ループ                   |  |
|  |  services/data_sync.py : ハッシュ差分同期                          |  |
|  |  vault_enc.py      : Fernet 暗号化インターフェース (enc:)                     |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  |  Provider 抽象 (providers/)                                       |  |
|  |  llm_adapter.py (LMStudioAdapter / MockAdapter)                 |  |
|  |  embedding.py (BGE-M3 / MiniLM / TF-IDF / MLX 骨格)              |  |
|  |  reranker.py  (NoReranker / CrossEncoder / FlashRank /          |  |
|  |                Ollama / MLX 骨格)                                 |  |
|  |  classifier.py (RuleBased / API)                                |  |
|  |  vector_store.py (Chroma 実装 / Qdrant 骨格)                      |  |
|  +-----------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
        |                            |                       |
        v                            v                       v
+----------------+         +-------------------+    +-------------------+
| SQLite DB      |         | ChromaDB          |    | LM Studio (LLM)   |
| ~/.cynovela/    |         | ~/.cynovela/       |    | (HTTP /v1)        |
| db/*.db        |         | vector/*/chroma   |    | またはモック       |
| 38 テーブル     |         | __raw / __masked  |    |                   |
+----------------+         +-------------------+    +-------------------+
```

外部接続は MCP（Model Context Protocol：LLM 向け外部ツール接続規格）サーバー経由でも提供されており、`mcp_server.py` が JSON-RPC を受けて FastAPI 側のエンドポイントを叩く構成です。

---

## 2. 各レイヤーの役割

### 2.1 フロントエンド層

`frontend/index.html` を起点とする静的 UI です。ワークスペース一覧・Collection 詳細・Chat・Dashboard などの画面を持ち、FastAPI が同一オリジンで配信します。一部の領域は JavaScript の初期化が終わるまで `display:none` で隠され、初期化後にロールや設定に応じて表示が切り替わります。

### 2.2 ミドルウェア層（IP アローリスト・認証）

- **IP アローリスト**: `--allow-tailscale`（`tailscale ip -4` 検出経由）または `--allow-subnet`（任意の CIDR）を渡したときだけ働きます。**渡さなければ全通過**です。許可を設定した場合、許可外 IP には HTTP 403 を返します。バインドアドレスの既定は `0.0.0.0` で、絞るのは `--local-only` です。
- **認証**: `Authorization: Bearer <token>` 形式で受け取り、`core/auth.py` の `get_user_from_token()` でユーザ情報を解決します。認証は `POST /api/auth/login` が発行する JWT のみです（`--demo` 起動でも同じ）。かつての `Bearer demo-token-{user_id}` は廃止済みで受理しません。

### 2.3 ルーター層（routers/）

36 個のルーターが API エンドポイントを担います。ロール検査は `_require_admin` `_require_authenticated` `_require_role` `_require_admin_or_self` の 4 ヘルパーに集約され、合計 242 箇所で利用されています。

### 2.4 サービス・ドメイン層

RAG パイプライン本体は `rag.py`（44 関数）に集約され、PII マスキングは `guardrail.py`、文脈付きチャンキングは `chunker.py`、複雑度判定と Agentic ループは `adaptive_rag.py` が担います。Fernet 暗号化は `vault_enc.py` が薄いラッパーを提供し、raw tier の本文だけを暗号化します。

### 2.5 Provider 抽象（providers/）

LLM・埋め込み・Reranker・分類器・ベクターストアを差し替え可能な抽象として持ちます。実装が完了しているもの（LM Studio / BGE-M3 / Chroma / NoReranker / CrossEncoder / FlashRank / Ollama Reranker / RuleBased Classifier）と、骨格のみで `NotImplementedError` を返すもの（MLX Embedding / MLX Reranker / Qdrant VectorStore / GraphRAG Strategy）が混在しています。

### 2.6 ストレージ層

- **SQLite**: 既定 `~/.cynovela/db/cynovela.db`（demo モード時は `~/.cynovela/db/demo.db`）。`CYNOVELA_DB` 環境変数で上書きできます。
- **ChromaDB**: 既定 `~/.cynovela/vector/default/chroma`。`CYNOVELA_CHROMA` 環境変数で上書きできます。Collection ID ごとに `{cid}__raw` と `{cid}__masked` の 2 つに分かれます。

---

## 3. RAG パイプラインのフロー

ユーザのクエリは `routers/chat.py` を入口とし、最終的に `rag.py` の `rag_retrieve()`（非同期）を経由して LLM 応答に至ります。

```
ユーザ クエリ
   |
   v
[1] 入力検査 (detect_prompt_injection)
   |  --- 注入パターン検出 → 400 + audit_logs(PROMPT_INJECTION_BLOCKED)
   v
[2] クエリ展開 (任意)
   |  Multi-Query RAG : LLM で N-1 個の言い換えを生成
   |  HyDE          : 仮想回答を生成してその埋め込みで検索
   v
[3] ベクター検索 (Chroma / BGE-M3)
   |  fetch_k 件取得 → MMR(Maximal Marginal Relevance) で多様性を確保
   |  ACL: allowed_roles と user_role を照合
   v
[4] BM25 検索 (メモリ内インデックス)
   |  形態素解析 (fugashi/MeCab) で日本語トークン化
   |  ACL チェック
   v
[5] ハイブリッド統合
   |  RRF (Reciprocal Rank Fusion, k=60) または weighted (v0.7 + bm0.3)
   v
[6] Parent-Child 解決
   |  child hit → parent_chunks の長文に差し替え
   v
[7] Reranker (任意)
   |  CrossEncoder / FlashRank / Ollama Reranker などで rerank_score 付与
   v
[8] 取得結果検査 (filter_poisoned_chunks)
   |  注入パターンを含む chunk を context 構築前に除外
   v
[9] LLM 呼び出し (call_llm)
   |  CRAG : 検索結果が質問に十分か LLM が評価
   |  Adaptive: 複雑度スコア >= 2.0 で Agentic ループ (最大 3 反復)
   v
[10] 出力検査 (detect_output_exfiltration)
   |  HACKED / PWNED / SECRET-ALPHA-TOKEN / [SYSTEM OVERRIDE] を検査
   v
[11] 出口マスク (_mask_for_viewer)
   |  tier_for_role(role) == 'raw'(admin) は素通し、それ以外は再マスク
   v
LLM 回答 + Citation([1][2]...)
```

各段の計測値（`vector_elapsed` `llm_elapsed` `total_elapsed` `rerank_latency_ms` `rerank_scores` `bm25_scores`）は `RetrievalResult` データクラスに保持されます。

---

## 4. Workspace 分離の仕組み

Cynovela は「Workspace（ワークスペース：ユーザとガードレールポリシーをまとめる単位）」と「Collection（コレクション：実際のファイル群と検索戦略を持つ単位）」の 2 層で分離します。

### 4.1 テーブル構造

```
workspaces  ──┬── workspace_users    (user の所属)
              ├── workspace_policies (ガードレールポリシー紐付け)
              └── workspace_sources  (Source の紐付け)
                       |
                       v
                  collections (workspace_id を FK で持つ、ON DELETE CASCADE)
                       |
                       └── collection_files (file_id 紐付け)
                       └── collection_locks (publish 中のロック)
```

### 4.2 Collection の状態遷移

```
draft ──> ingested ──> ready
  │           │
  │           └──> publishing ──> ready
  │                       └────> failed ──> draft
  │                       └────> stopped
  ready ──> draft (再公開のため)
```

### 4.3 ChromaDB 上の分離

Collection ID ごとに `{cid}__raw` と `{cid}__masked` の 2 つの Chroma コレクションが作られ、ロール別に引き先を変えます。`tier_for_role(role)` が admin に対しては `raw`、それ以外には `masked` を返すため、viewer（`curator` 等は viewer に正規化）は構造的に生本文に届きません。SQLite の `chunks` テーブルにも `tier='raw'` と `tier='masked'` の 2 行を保持します。

### 4.4 Workspace 単位の追加分離

BM25 インデックスは `(workspace_id, tier)` をキーとした辞書で持つため、ワークスペースをまたぐ検索が起こらないようキー設計でも分離されています（`rag.py:101-107`）。

<!-- BACKLOG: ChromaDB レベルでの workspace 物理境界は Phase 3 引き継ぎの HIGH 優先度バグとして A-6 に挙がっており、現状は collection_id 単位での分離 -->

---

## 5. 起動モードによるコンポーネント変化

`--mode` フラグで読み込むモデルと Provider が切り替わります（`server.py:2725-2740` の `_MODE_MODELS` と `server.py:2854-2895` の `_wire_providers_for_mode`）。

| mode | 主用途 | Embedding | Reranker | 想定環境 |
|------|--------|-----------|----------|----------|
| `text`（既定） | テキスト RAG 全機能 | BAAI/bge-m3 | yaml で選択可 | GPU 不要・汎用 |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — | — |

以前は `--mock` フラグが最優先で適用され、`Embedding` を `TFIDFEmbedding`、`Reranker` を `NoReranker` に固定していました。この指定は撤去済みで、いま指定するとエラーで止まります。

### 5.1 起動フロー

```
main() 呼び出し
   ↓
argparse で CLI 引数パース
   ↓
_preflight_model_check()
  ├─ 必要モデルが ~/.cynovela/models/ に存在するか確認
  └─ 不足時はユーザに DL / 代替モード / キャンセルを提示
       （CYNOVELA_NONINTERACTIVE=1 なら即 exit）
   ↓
get_llm_adapter()  : cynovela.yaml の llm 設定に従う
   ↓
load_yaml_config() : cynovela.yaml を読み、CYNOVELA_* で上書き
   ↓
_wire_providers_for_mode()
  ├─ Reranker (yaml.reranker.provider)
  ├─ 例外 → NoReranker フォールバック
   ↓
set_pii_detection_mode(lite / standard / quality)
   ↓
init_db(demo=args.demo)
   ↓
uvicorn.run() で FastAPI 起動
```

### 5.2 設定上書きの優先順

1. CLI 引数（`--port` `--host` `--lan` など）が最優先
2. 環境変数 `CYNOVELA_*`（`config.py` の `_ENV_OVERRIDES` で yaml に上書き）
3. `cynovela.yaml`
4. ハードコードされた既定値

### 5.3 features フラグ

`cynovela.yaml` の `features` セクションで `metadata_engine` `data_guardrails` `data_sync` `audit_log` `acl_filter` `pipeline_visualization` `session_history` `feedback` を個別に on/off できます。たとえば `features.acl_filter=false` にすると、ベクター・BM25 両経路の ACL チェックがスキップされます。

---

最終更新: 2026-05-26 / Alpha GA 対応版
