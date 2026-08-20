# 仕様概要（Spec Overview）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual in order to
> understand the concepts of AI infrastructure tools hands-on. It is not a commercial
> product and not an official implementation.
> The implementation is entirely original, and is made of an OSS stack:
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

This document organizes the features confirmed as of Cynovela  and the known limitations, so that they can be seen at a glance. For detailed specifications and the reasoning behind the design, see each individual document.

---

## 1. List of confirmed implemented features

### 1.1 RAG (Retrieval-Augmented Generation) pipeline

| Feature | State | Overview |
|---|---|---|
| Vector search | Implemented | 1024-dimension embeddings by BGE-M3 are put into ChromaDB |
| BM25 search | Implemented | Tokenization based on morphological analysis (fugashi/MeCab for Japanese, space-separated for English) |
| Hybrid merge | Implemented | The default is RRF (reciprocal rank fusion); can also be switched to weighted (weighted average) |
| MMR re-selection | Implemented | Balances relevance and diversity |
| Parent-Child chunking | Implemented | Search with child chunks, replace with the parent chunk and pass it to the LLM |
| Multi-Query expansion | Implemented | The LLM expands the query into several variants and merges them with RRF |
| CRAG (self-evaluating re-search) | Implemented | The LLM evaluates the quality of the search results and searches again if needed |
| HyDE (hypothetical document embedding) | Implemented | Generates a hypothetical answer and searches with its embedding |
| Reranker | Implemented (replaceable) | The default is disabled (NoReranker); can be switched to CrossEncoder / FlashRank / Ollama / HTTP and others |
| Adaptive RAG | Implemented | Automatically switches between "basic" and "agentic" by query complexity |
| Citation embedding | Implemented | Embeds citation numbers in the `[1][2]` form into the answer |

### 1.2 Guardrails / security

| Feature | State | Overview |
|---|---|---|
| PII detection (first stage: regular expressions) | Implemented | The 8 types URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4 |
| PII detection (second stage: named entity recognition) | Implemented | presidio + GiNZA fallback |
| Tier1 masking at ingest | Implemented | Generates both raw and masked at publish |
| Tier2 masking at answer time | Implemented | Applies the exit mask per role |
| Fernet encryption | Implemented | Encrypts right before storing the original into SQLite / Chroma |
| Prompt injection countermeasures (3 layers) | Implemented | Input inspection → post-retrieval inspection → output inspection |
| Audit log | Implemented | Records authentication failures, PII detection, prompt injection blocking, and so on |
| Guardrail policy | Implemented | The 4 actions mask / exclude_from_rag / log_only / allow |
| RBAC (role-based authorization) | Implemented | The 3 roles admin / curator / viewer |

### 1.3 Smart Ingestion (ingest and classification)

| Feature | State | Overview |
|---|---|---|
| Automatic classification into 14 categories | Implemented | governance_policy / incident_report / technical_guide and others |
| Lightweight classifier | Implemented | Keyword matching on the file name and the first 500 characters |
| LLM classifier | Implemented | Zero-shot classification with Ollama (llama3 by default) |
| Hybrid classifier | Implemented | Lightweight first, falls back to the LLM when confidence is low |
| Workspace / Collection structure | Implemented | Workspace (unit of administration) and Collection (a group of files) |
| Collection state transitions | Implemented | draft → ingested → ready and so on |
| Automatic polling sync | Implemented (partly) | Difference detection over the set of paths (60 second interval by default). Automatic linkage to Publish is not integrated |
| Raw mode | Implemented | Stores `rag_mode='raw'` per collection |
| Contextual Chunking | Implemented (Phase 2) | Prepends a metadata summary to the beginning of a chunk |

### 1.4 Surrounding features

| Feature | State | Overview |
|---|---|---|
| MCP server | Implemented | Exposes 25 tools that can be called from outside (22 visible by default; 3 admin tools appear only when CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 is set) |
| LM Studio integration | Implemented | Goes through the OpenAI-compatible `/v1` API |
| Circuit breaker | Implemented | Automatic cut-off and recovery when the LLM fails |
| Dashboard | Implemented | Visualizes pipeline health / statistics / polling state and others |
| Audit log viewing API | Implemented | Tampering via the API is prohibited (append only) |
| LAN / Tailscale exposure | Implemented | `--lan` / `--allow-tailscale` / `--allow-subnet` |

---

## 2. Main categories of API endpoints

The router implementation is split into **36 files** (under `routers/`). The main categories are as follows.

| Category | Router | Main role |
|---|---|---|
| Authentication and users | `auth.py`, `users.py`, `sessions.py` | Login, user list, session management |
| Data management | `sources.py`, `files.py`, `workspaces.py`, `collections.py` | Ingest sources, files, storage units, collections |
| RAG / Chat | `chat.py`, `agent.py`, `mcp.py` | Chat responses, agent, MCP |
| Metadata | `catalog.py`, `pipeline_config.py` | Catalog, presets |
| Guardrails | `guardrails.py`, `policies.py`, `compliance.py` | PII detection, policies, compliance |
| Monitoring and operations | `dashboard.py`, `health.py`, `stats.py`, `alerts.py`, `audit_logs.py`, `jobs.py` | Monitoring, health, statistics, alerts, auditing |
| LLM / models | `llm.py`, `lmstudio.py`, `models.py`, `mode.py` | LLM connection, model management |
| Others | `archived.py`, `cost.py`, `demo.py`, `features.py`, `feedback.py`, `messages.py`, `pages.py`, `reports.py`, `settings.py`, `admin.py` | Archive, cost, demo, feature toggles, feedback, and so on |

For details, see `docs/api-reference.md`.

---

## 3. Known limitations

### 3.1 Features that are only an abstract base or whose implementation stays a skeleton

| Feature | State |
|---|---|
| Qdrant vector store | Skeleton only (returns `NotImplementedError`) |
| MLX Embedding | Skeleton only |
| MLX Reranker | Skeleton only |
| LanceDB backend | Skeleton only |
| GraphRAG strategy | Planned for future implementation |

### 3.2 Removed features

| Feature | How it was removed |
|---|---|
| The `/chat-popup` route | Returns 410 Gone following the removal of the side panel |
| Login with user_id alone | Changed to require username / password |
| Unauthenticated demo access to `/api/auth/users` | Changed to always require admin authentication |

### 3.3 Limitations by design

- The confidence threshold (confidence_threshold = 0.50) is defined as a configuration value, but its exclusion logic in the search pipeline is only **partly integrated**.
- Automatic polling sync works up to difference detection, but automatic linkage to Publish is **not integrated** (planned to be connected in a later phase).
- Hash difference sync works **per path**. Comparison by `content_hash` is not implemented yet.
- Authentication is enforced in all startup forms (it is not skipped even with `--demo`). The fixed token that used to be accepted with `--demo` startup was abolished on 2026-07-29.

### 3.4 Structured answer templates

- A feature that fixes the LLM's answer into a **structured format** such as JSON or an `<answer>` tag is not implemented. A free-form answer is the standard.

---

## 4. Items planned toward Beta GA

The priority topics toward Beta GA, as read from the CHANGELOG, are as follows.

| Item | Overview |
|---|---|
| Fixing HIGH priority bugs | The reversed DB → Chroma order in `import_workspace`, the race condition in `admin_cleanup_chromadb_orphans`, the physical boundary of WS isolation, the WS-A → WS-B cross-boundary check, and others |
| Indirect prompt injection detection | A detection mechanism aimed at attacks that come through ingested documents |
| Implementation of Qdrant / MLX / LanceDB | Advance the currently skeleton-only implementations into real implementations |
| Reranker testing with a real model | Improving RAG quality with CrossEncoder and others |
| Persisting Embedding / Reranker settings to YAML | They are currently held in memory, so they return to the defaults on restart |
| Introducing JWT authentication | Enforcing RBAC in all modes |
| KnowledgeCatalog extension | Metadata search in the Chunks viewer, citation tracking |

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

このドキュメントは、現時点で確認済みの機能と既知制限を一望できるように整理したものです。詳細な仕様や設計の根拠は各個別ドキュメントを参照してください。

---

## 1. 確認済み実装機能の一覧

### 1.1 RAG（検索拡張生成）パイプライン

| 機能 | 状態 | 概要 |
|---|---|---|
| ベクター検索 | 実装済み | ChromaDB に BGE-M3 で 1024 次元 Embedding を投入 |
| BM25 検索 | 実装済み | 形態素解析ベースのトークン化（日本語は fugashi/MeCab、英語はスペース区切り） |
| ハイブリッド統合 | 実装済み | 既定は RRF（順位の逆数和）、weighted（加重平均）にも切替可能 |
| MMR 再選別 | 実装済み | 関連性と多様性のバランス調整 |
| Parent-Child チャンキング | 実装済み | 子チャンクで検索、親チャンクに置換して LLM に渡す |
| Multi-Query 展開 | 実装済み | LLM でクエリを複数バリアントに展開して RRF 統合 |
| CRAG（自己評価式再検索） | 実装済み | 検索結果の質を LLM が評価し、必要なら追加検索 |
| HyDE（仮想文書埋め込み） | 実装済み | 仮想回答を生成して、その埋め込みで検索 |
| Reranker | 実装済み（差替可能） | 既定は無効（NoReranker）、CrossEncoder / FlashRank / Ollama / HTTP などに切替可能 |
| Adaptive RAG | 実装済み | クエリ複雑度で「basic」「agentic」を自動切替 |
| 引用埋め込み | 実装済み | 回答中に `[1][2]` 形式の引用番号を埋め込み |

### 1.2 ガードレール / セキュリティ

| 機能 | 状態 | 概要 |
|---|---|---|
| PII 検出（一次：正規表現） | 実装済み | URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4 の 8 種 |
| PII 検出（二次：固有表現抽出） | 実装済み | presidio + GiNZA フォールバック |
| Tier1 取込時マスキング | 実装済み | Publish 時に raw / masked の両方を生成 |
| Tier2 回答時マスキング | 実装済み | ロール別に出口マスクを適用 |
| Fernet 暗号化 | 実装済み | 原本を SQLite / Chroma に保存する直前で暗号化 |
| プロンプトインジェクション対策（3 層） | 実装済み | 入力検査 → retrieval 後検査 → 出力検査 |
| 監査ログ | 実装済み | 認証失敗、PII 検出、プロンプトインジェクション遮断などを記録 |
| ガードレールポリシー | 実装済み | mask / exclude_from_rag / log_only / allow の 4 アクション |
| RBAC（ロールベース認可） | 実装済み | admin / curator / viewer の 3 ロール |

### 1.3 Smart Ingestion（取り込み・分類）

| 機能 | 状態 | 概要 |
|---|---|---|
| 14 カテゴリ自動分類 | 実装済み | governance_policy / incident_report / technical_guide ほか |
| Lightweight 分類器 | 実装済み | ファイル名と先頭 500 文字のキーワードマッチ |
| LLM 分類器 | 実装済み | Ollama（既定 llama3）でゼロショット分類 |
| Hybrid 分類器 | 実装済み | Lightweight 優先、信頼度が低ければ LLM にフォールバック |
| Workspace / Collection 構造 | 実装済み | Workspace（管理単位）と Collection（ファイル群） |
| Collection 状態遷移 | 実装済み | draft → ingested → ready など |
| 自動ポーリング同期 | 実装済み（一部） | パス集合の差分検出（既定 60 秒間隔）。Publish 自動連携は未統合 |
| Raw モード | 実装済み | コレクション単位で `rag_mode='raw'` を保存 |
| Contextual Chunking | 実装済み（Phase 2） | チャンク冒頭にメタデータ要約を付加 |

### 1.4 周辺機能

| 機能 | 状態 | 概要 |
|---|---|---|
| MCP サーバー | 実装済み | 外部から呼べる 25 個の道具を公開（既定で見えるのは 22 個。管理系の 3 個は CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を設定したときだけ現れます） |
| LM Studio 連携 | 実装済み | OpenAI 互換 `/v1` API を経由 |
| サーキットブレーカー | 実装済み | LLM 障害時の自動遮断と回復 |
| ダッシュボード | 実装済み | パイプライン健全性 / 統計 / ポーリング状態などを可視化 |
| 監査ログ閲覧 API | 実装済み | API 経由での改ざんは禁止（追加のみ） |
| LAN / Tailscale 公開 | 実装済み | `--lan` / `--allow-tailscale` / `--allow-subnet` |

---

## 2. API エンドポイントの主要カテゴリ

ルーター実装は **36 ファイル**（`routers/` 配下）に分かれています。主なカテゴリは次のとおりです。

| カテゴリ | ルーター | 主な役割 |
|---|---|---|
| 認証・ユーザー | `auth.py`, `users.py`, `sessions.py` | ログイン、ユーザー一覧、セッション管理 |
| データ管理 | `sources.py`, `files.py`, `workspaces.py`, `collections.py` | 取り込み元、ファイル、保管単位、コレクション |
| RAG / Chat | `chat.py`, `agent.py`, `mcp.py` | チャット応答、エージェント、MCP |
| メタデータ | `catalog.py`, `pipeline_config.py` | カタログ、プリセット |
| ガードレール | `guardrails.py`, `policies.py`, `compliance.py` | PII 検出、ポリシー、コンプライアンス |
| 監視・運用 | `dashboard.py`, `health.py`, `stats.py`, `alerts.py`, `audit_logs.py`, `jobs.py` | 監視、健全性、統計、アラート、監査 |
| LLM / モデル | `llm.py`, `lmstudio.py`, `models.py`, `mode.py` | LLM 接続、モデル管理 |
| その他 | `archived.py`, `cost.py`, `demo.py`, `features.py`, `feedback.py`, `messages.py`, `pages.py`, `reports.py`, `settings.py`, `admin.py` | アーカイブ、コスト、デモ、機能トグル、フィードバック、など |

詳細は `docs/api-reference.md` を参照してください。

---

## 3. 既知の制限

### 3.1 抽象基底のみ・実装が骨格に留まる機能

| 機能 | 状態 |
|---|---|
| Qdrant ベクターストア | 骨格のみ（`NotImplementedError` を返す） |
| MLX Embedding | 骨格のみ |
| MLX Reranker | 骨格のみ |
| LanceDB バックエンド | 骨格のみ |
| GraphRAG 戦略 | 将来実装予定 |

### 3.2 廃止された機能

| 機能 | 廃止経緯 |
|---|---|
| `/chat-popup` ルート | サイドパネル廃止に伴い 410 Gone を返却 |
| user_id 単独ログイン | username / password 必須に変更 |
| `/api/auth/users` のデモ未認証許可 | 常時 admin 認証必須に変更 |

### 3.3 設計上の制限

- 信頼度閾値（confidence_threshold = 0.50）は設定値としては定義済みですが、検索パイプラインからの除外ロジックには **部分統合** に留まります。
- 自動ポーリング同期は差分検出までは動作しますが、Publish への自動連携は **未統合** です（後続フェーズで接続予定）。
- ハッシュ差分同期は **パス単位** で動作します。`content_hash` 比較はまだ実装されていません。
<!-- BACKLOG: content_hash 比較の差分検出は仕様未確定 -->
- 認証強制はすべての起動形態で動作します（`--demo` 起動でも省かれません）。かつて `--demo` 起動で受理していた固定トークンは 2026-07-29 に廃止しました。

### 3.4 構造化回答テンプレート

- LLM の回答を JSON や `<answer>` タグなどの **構造化フォーマット** で固定する機能は実装されていません。自由形式の回答が標準です。
<!-- BACKLOG: 構造化回答テンプレートの導入可否は未定 -->

---

## 4. Beta GA に向けて予定している事項

CHANGELOG から読み取れる、Beta GA に向けた重点課題は次のとおりです。

| 項目 | 概要 |
|---|---|
| HIGH 優先度バグの修正 | `import_workspace` の DB → Chroma 順序逆転、`admin_cleanup_chromadb_orphans` の競合状態、WS 分離の物理境界、WS-A → WS-B 越境チェックなど |
| 間接プロンプトインジェクション検出 | 取り込んだドキュメント経由の攻撃を対象とした検出機構 |
| Qdrant / MLX / LanceDB の実装 | 現在骨格のみの実装を本実装に進める |
| Reranker 実体テスト | CrossEncoder などでの RAG 品質向上 |
| Embedding / Reranker 設定の YAML 永続化 | 現在はメモリ保持のため再起動でデフォルトに戻る |
| JWT 認証の導入 | 全モードでの RBAC 強制 |
| KnowledgeCatalog 拡張 | Chunks ビューアのメタデータ検索、出典追跡 |

---

