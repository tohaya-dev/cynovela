# 変更履歴（Changelog）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool built by an individual to
> understand the concepts of AI platform tools hands-on. It is not a commercial
> product nor an official implementation.
> The implementation is entirely original, built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

This records the main changes to Cynovela in chronological order.

---

## v1.0.6 (2026-08-20)

- **The CLI now covers the same work as the screen.** Added: `sources` / `audit-logs` / `chat` /
  `ingest` (register a folder and start scanning in one line) / `scan start·status·cancel` /
  `publish start·status·stop·recover` / `collections create·link` / `workspaces create·update·archive·unarchive` /
  `delete` / `users` / `backup`. Dangerous operations show what would happen and never run without `--yes`.
- **MCP now has 25 tools (22 visible by default).** Added `server_status`, `ingest_source`,
  `get_job_status`, `cancel_scan`, `create_collection`, `publish_control`; the three admin tools
  (`delete_item` / `manage_users` / `manage_backups`) are closed by default and appear only when
  `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` is set. `publish_collection` now starts the publish and
  returns a `job_id` immediately instead of blocking.
- **Scans run in the background.** New `POST /api/sources/{id}/scan/async` returns a `job_id`
  immediately; progress via `GET /api/jobs/{job_id}` (same shape as publish). The screen's rescan
  uses this, a "Reload sources" button was added above the source list, and the server scans the
  registered sources once at every startup (files that have not changed are not re-read).
- **`launch.sh`**: drops the quarantine marks inside the package by itself at start; warns before
  starting when the folder sits under cloud sync (iCloud Drive / Dropbox / OneDrive / Google Drive);
  and skips the base-selection screen when the bundled `.venv-cynovela` is present and working.
- **`uninstall.sh`** now reports the reason and the next step when the move to the Trash fails.
- Removed the old, unreferenced `cynovela_cli.py` (underscore name). The CLI is `cynovela-cli.py`.
- Documents: added download-and-assembly guidance, updated tool counts and command lists, fixed the
  model overlay destination to `store/models/`, and aligned stale version numbers.

## Public repository and package form (2026-08-12)

- In the public GitHub repository (cynovela), two forms were placed side by side:
  falcon (the form that runs inside a container) and chewie (the form that runs directly on a Mac).
- There are now four package forms: falcon all-in-one, falcon lightweight, chewie all-in-one, and chewie lightweight.
- The all-in-one form (the form that bundles the models) is too large to fit in a single file, so it is
  distributed **split into multiple files**. `HOW-TO-ASSEMBLE.md` and `SHA256SUMS` are placed in the same location as the split files;
  assemble them and verify the SHA256 before use.
- The lightweight form (the form that does not bundle the models) is distributed as **a single file**. At first startup you can choose to
  download the models (no communication starts until you choose).

## The first working milestone (before the public repository)

This is the milestone for "a state in which the core flows work end to end as a personal learning tool". After going through Stage 0 to Stage 6, the main features of guardrails, PII detection, RAG, and MCP integration became operational.

### Stage 0: Startup foundation

- Organizing the CLI argument definitions with argparse
- Introducing the 5 values of `--mode` (full / text / lite / lite-en / minimal)
- Startup preflight (checking that the required models exist, and offering download or an alternative mode when they are not obtained)
- Skipping the dialog during script execution with `CYNOVELA_NONINTERACTIVE=1`
- Centralizing configuration with `cynovela.yaml`, plus environment variable overrides

### Stage 1: Data persistence and FK integrity

- Setting up the SQLite schema (`workspaces`, `collections`, `sources`, `files`, `chunks`, `audit_logs`, etc.)
- Applying `PRAGMA foreign_keys = ON` to all connections
- The `_purge_chunks_for_*()` family of helpers that clean up both SQLite and ChromaDB on deletion
- Introducing `_stable_fid(path)` for `file_id` stability after a rescan
- Thorough use of the audit recording helper `_log_audit(conn, action, target, detail)`

### Stage 2: Guardrails and PII

- 4 guardrail actions (`mask` / `exclude_from_rag` / `log_only` / `allow`)
- Detection of 8 kinds of PII patterns (URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4)
- Generation of dual-tier storage (raw / masked) at publish time
- Protection of the raw body text by Fernet encryption (`vault_enc.py`)
- 3-layer prompt injection countermeasures (input inspection, post-retrieval inspection, output inspection)

### Stage 3: RAG pipeline

- Hybrid fusion of BM25 and vector search (default: RRF, k=60)
- BAAI/bge-m3 vector embeddings
- Replaceable Reranker (CrossEncoder, FlashRank, Ollama, HTTP)
- Advanced search features (MMR, Parent-Child chunking, Multi-Query, CRAG, HyDE, Adaptive RAG)
- Adoption of a confidence threshold (cosine similarity 0.50)

### Stage 4: Smart Ingestion

- Automatic classification into 14 document categories
- 3 kinds of classification engines (lightweight, LLM, hybrid)
- Hash-based differential sync per path by DataSyncService (default interval 60 seconds)
- Contextual Chunking (prepending metadata to the beginning of a chunk)

### Stage 5: RBAC and auditing

- Applying a SQL CHECK constraint for the 3 roles (admin / curator / viewer)
- Setting up the 4 RBAC helper functions (`_require_admin`, `_require_authenticated`, `_require_role`, `_require_admin_or_self`)
- Applying RBAC checks to 33 routers (242 places)
- Prohibiting modification and deletion of audit_logs via the API

### Stage 6: External integration

- Publishing an MCP server (11 tools at that time; 25 as of v1.0.6)
- LM Studio / Ollama / OpenAI-compatible API connections
- Setting up the flags for LAN sharing and Tailscale sharing (`--lan` / `--allow-tailscale` / `--allow-subnet`)
- IP allowlist middleware

---

## History of main fixes

### Security hardening

- **Complete removal of user_id-only login**: The legacy path was deleted and username/password became mandatory.
- **Making `/api/auth/users` admin-only**: The unauthenticated allowance in demo mode was abolished.
- **Restricting the PII detection history to admin**: `/api/guardrails/pii-detections` was changed to admin only.
- **Abolishing the chat popup route**: `/chat-popup` was changed to 410 Gone.

### Bug fixes

- **Strengthening path validation of `/api/sources`**: Prevents references to system paths.
- **Validation of `llm_endpoint`**: Restricts changes that reference the internal network.
- **Fixing the placement order of the system prompt**: Placed after retrieved_content (preventing overwriting by documents).
- **Eliminating `INSERT OR REPLACE`**: Unified to `ON CONFLICT DO UPDATE` to prevent FK CASCADE from firing by mistake.
- **Testability of `_publish_semaphore`**: Changed from module scope to dependency injection (carried over from Stage-3).

### Quality improvements

- Reduced pyright errors from 16 to 0
- Protecting all contracts of the dependency constraints with import-linter
- Expanded the pytest suite to 14 PHASEs / more than 405 assertions
- Maintained 0 console errors

---

## Planned items toward Beta GA

Beta GA is a milestone under consideration whose goal is "a state that can withstand simple shared use in addition to personal learning".

### Authentication and authorization

- Full introduction of JWT authentication (enforcing RBAC in all modes)
- Issuing API keys per user

### RAG quality

- Reranker substance testing (quality verification of CrossEncoder, etc.)
- Adjusting the chunking strategy (considering making Contextual Chunking the default)
- Considering the introduction of structured answer templates

### Stability

- YAML persistence of the Embedding / Reranker settings (currently memory only)
- Hardening the error recovery paths
- Integrating DataSyncService with publish (currently a noop)

### Integration expansion

- Expanding the tools published by the MCP server
- Expanding the Chunks viewer of KnowledgeCatalog (metadata search, citation tracking)

### Backend diversification

- Vector store support for Qdrant / LanceDB (currently a skeleton only)
- Implementing MLX Embedding / Reranker (Apple Silicon optimization)

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela の主要な変更内容を時系列で記録します。

---

## v1.0.6（2026-08-20）

- **CLI が画面と同じ作業を覆うようになった。** 追加: `sources` / `audit-logs` / `chat` /
  `ingest`（フォルダの登録と走査の開始を1行で）/ `scan start·status·cancel` /
  `publish start·status·stop·recover` / `collections create·link` / `workspaces create·update·archive·unarchive` /
  `delete` / `users` / `backup`。危険な操作は「何が起きるか」を見せ、`--yes` なしには実行しない。
- **MCP の道具が 25 個になった（既定で見えるのは 22 個）。** `server_status`・`ingest_source`・
  `get_job_status`・`cancel_scan`・`create_collection`・`publish_control` を追加。管理系の 3 個
  （`delete_item` / `manage_users` / `manage_backups`）は既定で閉じており、
  `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を設定したときだけ現れる。`publish_collection` は
  公開を始めて `job_id` を即返す形になった（終わるまで待たない）。
- **走査が背景で走るようになった。** `POST /api/sources/{id}/scan/async` が `job_id` を即返し、
  進み具合は `GET /api/jobs/{job_id}`（公開と同じ形）。画面の再スキャンはこの形を使い、
  資料一覧の上に「すべて読み込み直す」を新設。サーバは起動のたびに登録済みの取り込み元を
  1回走査する（変わっていないファイルは読み直さない）。
- **`launch.sh`**: 起動の最初に配布物の中の印（quarantine を含む拡張属性）を自分で全部落とす。
  クラウド同期（iCloud Drive / Dropbox / OneDrive / Google Drive）の下に置かれているときは
  起動前に注意を出す。同梱の `.venv-cynovela` が在って動くときは土台の選択画面を出さない。
- **`uninstall.sh`** は、ゴミ箱へ入れられなかったときに理由と次の一手を出すようになった。
- 参照されていなかった旧 `cynovela_cli.py`（下線の名前）を撤去した。CLI は `cynovela-cli.py`。
- 文書: 落とし方と結合の案内を追加。道具の数と命令の一覧を実体へ更新。モデルを重ねる宛先を
  `store/models/` に統一。古い版番号の表記を揃えた。

## 公開のリポジトリと配る形（2026-08-12）

- 公開の GitHub リポジトリ（cynovela）に、falcon（コンテナの中で動く形）と
  chewie（Mac の上で直に動く形）の2つの形を並べた。
- 配る形は4つになった。falcon 全部入り・falcon 軽量版・chewie 全部入り・chewie 軽量版。
- 全部入り（モデルを同梱する形）は、1つのファイルに収まらない大きさのため、
  **分割ファイルに分けて**配る。分割ファイルと同じ場所に `HOW-TO-ASSEMBLE.md` と `SHA256SUMS` を置き、
  組み立てと SHA256 の確認をしてから使う。
- 軽量版（モデルを同梱しない形）は **1つのファイル**で配る。初回の起動でモデルの
  ダウンロードを選べる（選ぶまで通信は始まらない）。

## 最初に一通り動いた節目（公開リポジトリより前）

これは「個人学習用ツールとして一通りのコアフローが動く状態」のマイルストーンです。Stage 0 〜 Stage 6 を経て、ガードレール・PII 検出・RAG・MCP 連携の主要機能が稼働するに至りました。

### Stage 0: 起動基盤

- argparse による CLI 引数定義の整理
- `--mode`（full / text / lite / lite-en / minimal）の 5 種を導入
- 起動時 preflight（必要モデルの存在確認、未取得時のダウンロード or 代替モード提案）
- `CYNOVELA_NONINTERACTIVE=1` でスクリプト実行時の対話スキップ
- `cynovela.yaml` による設定の一元化と環境変数オーバーライド

### Stage 1: データ永続化と FK 整合性

- SQLite スキーマの整備（`workspaces`、`collections`、`sources`、`files`、`chunks`、`audit_logs` 等）
- `PRAGMA foreign_keys = ON` の全接続適用
- 削除時に SQLite と ChromaDB の両方をクリーンアップする `_purge_chunks_for_*()` 系ヘルパー
- 再スキャン後の `file_id` 安定性のための `_stable_fid(path)` 導入
- 監査記録ヘルパー `_log_audit(conn, action, target, detail)` の徹底

### Stage 2: ガードレール・PII

- 4 種のガードレールアクション（`mask` / `exclude_from_rag` / `log_only` / `allow`）
- 8 種類の PII パターン検出（URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4）
- Dual-tier 保管（raw / masked）の Publish 時生成
- Fernet 暗号化による raw 本文保護（`vault_enc.py`）
- 3 層プロンプトインジェクション対策（入力検査・retrieval 後検査・出力検査）

### Stage 3: RAG パイプライン

- BM25 + ベクター検索のハイブリッド統合（既定: RRF、k=60）
- BAAI/bge-m3 ベクター埋め込み
- Reranker の差し替え（CrossEncoder、FlashRank、Ollama、HTTP）
- 高度な検索機能（MMR、Parent-Child チャンキング、Multi-Query、CRAG、HyDE、Adaptive RAG）
- 信頼度閾値（cosine similarity 0.50）を採用

### Stage 4: Smart Ingestion

- 14 種類のドキュメントカテゴリ自動分類
- 3 種類の分類エンジン（軽量、LLM、ハイブリッド）
- DataSyncService によるパス単位のハッシュ差分同期（既定 60 秒間隔）
- Contextual Chunking（メタデータをチャンク冒頭に付加）

### Stage 5: RBAC・監査

- 3 ロール（admin / curator / viewer）の SQL CHECK 制約適用
- RBAC ヘルパー関数 4 種の整備（`_require_admin`、`_require_authenticated`、`_require_role`、`_require_admin_or_self`）
- 33 ルーター（242 箇所）への RBAC チェック適用
- audit_logs の API 経由変更・削除を禁止

### Stage 6: 外部連携

- MCP サーバー（当時 11 ツール。v1.0.6 時点では 25 ツール）の公開
- LM Studio / Ollama / OpenAI 互換 API 接続
- LAN 共有・Tailscale 共有のフラグ整備（`--lan` / `--allow-tailscale` / `--allow-subnet`）
- IP アローリストミドルウェア

---

## 主要修正履歴

### セキュリティ強化

- **user_id 単独ログインの完全撤去**: レガシーパスを削除し、username/password 必須化。
- **`/api/auth/users` の admin 必須化**: デモモードでの未認証許可を撤廃。
- **PII 検出履歴の admin 限定化**: `/api/guardrails/pii-detections` を admin 専用に変更。
- **Chat popup ルートの廃止**: `/chat-popup` を 410 Gone に変更。

### バグ修正

- **`/api/sources` の path バリデーション強化**: システムパスへの参照を防止。
- **`llm_endpoint` のバリデーション**: 内部ネットワーク参照変更の制限。
- **システムプロンプト配置順序の修正**: retrieved_content の後に配置（文書による上書き防止）。
- **`INSERT OR REPLACE` の排除**: FK CASCADE 誤発火を防ぐため `ON CONFLICT DO UPDATE` に統一。
- **`_publish_semaphore` のテスト容易性**: モジュールスコープから依存注入化（Stage-3 引き継ぎ）。

### 品質改善

- pyright エラーを 16 件から 0 件に削減
- import-linter による依存関係制約の全 contracts 保護
- pytest スイートを 14 PHASE / 405 アサーション以上に拡充
- console エラー 0 件を維持

---

## Beta GA に向けた予定事項

Beta GA は「個人学習に加えて簡易な共同利用にも耐えうる状態」をゴールとして検討中の節目です。

### 認証・認可

- JWT 認証の本格導入（全モードでの RBAC 強制）
- ユーザー単位の API キー発行

### RAG 品質

- Reranker 実体テスト（CrossEncoder 等の品質検証）
- チャンク戦略の調整（Contextual Chunking のデフォルト化検討）
- 構造化回答テンプレートの導入検討

### 安定性

- Embedding / Reranker 設定の YAML 永続化（現状はメモリのみ）
- エラー回復経路の堅牢化
- DataSyncService の publish 連携統合（現状は noop）

### 連携拡張

- MCP サーバーの公開ツール拡充
- KnowledgeCatalog の Chunks ビューア拡張（メタデータ検索、出典追跡）

### バックエンド多様化

- Qdrant / LanceDB のベクターストア対応（現状は骨格のみ）
- MLX Embedding / Reranker の実装（Apple Silicon 最適化）

---

