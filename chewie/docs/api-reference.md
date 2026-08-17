# API リファレンス（概要）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual to
> understand the concepts of AI infrastructure tools hands-on. It is not a
> commercial product or an official implementation.
> The implementation is entirely original, and consists of an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela is built with FastAPI, and the endpoints are placed across **36 files** under `routers/`. This document is not a specification of the individual endpoints; it is put together so that you can **survey the main categories as a whole map**.

---

## 1. Authentication method

### 1.1 Authentication header

API requests pass the authentication information in the `Authorization` header as a rule.

- In normal mode, you go through a login with a `username` and a `password`, and then use the token that the server side issues.
- Authentication is only the JWT that `POST /api/auth/login` issues. The simple token of the form `Bearer demo-token-{user_id}` that used to exist was abolished on 2026-07-29, and is not accepted even on a `--demo` startup.

### 1.2 Authorization (permission check)

At the top of each endpoint, a role check helper of `core/auth.py` is called.

| Helper | What it checks |
|---|---|
| `_require_admin()` | role == admin |
| `_require_authenticated()` | Authenticated (any role) |
| `_require_role(roles)` | Matches one of the specified roles |
| `_require_admin_or_self()` | admin, or the person themselves |

Calls to the role checks are spread over **about 242 places**.
For details, see `docs/rbac.md`.

---

## 2. List of the main endpoints by category

### 2.1 Authentication and user management

| Router | Main role |
|---|---|
| `auth.py` | Login, logout, user creation / deletion / listing (admin only) |
| `users.py` | User details, information about yourself |
| `sessions.py` | Listing and deletion of chat sessions (some parts admin only) |

### 2.2 Data source and file management

| Router | Main role |
|---|---|
| `sources.py` | Registration and scanning of the ingest source (Source) |
| `files.py` | Upload, listing, and deletion of files (some operations are admin only) |
| `archived.py` | Lookup and restore of archives (admin only) |

### 2.3 Workspaces and collections

| Router | Main role |
|---|---|
| `workspaces.py` | Creation, deletion, and details of workspaces |
| `collections.py` | Creation, editing, and Publish of collections |
| `catalog.py` | Reference of the data catalog |

### 2.4 RAG / Chat

| Router | Main role |
|---|---|
| `chat.py` | Chat responses (normal / comparison / SSE stream) |
| `agent.py` | Agent-related operations |
| `mcp.py` | Management of MCP (Model Context Protocol, externally exposed tools) |
| `messages.py` | Operations per message |

### 2.5 Guardrails and compliance

| Router | Main role |
|---|---|
| `guardrails.py` | Aggregation of the PII detection history (admin only), CRUD of forbidden topics |
| `policies.py` | Listing and editing of guardrail policies |
| `compliance.py` | Compliance-related operations (admin only) |
| `feedback.py` | Retrieval and editing of 👍👎 feedback (admin only) |

### 2.6 Models and LLM connection

| Router | Main role |
|---|---|
| `llm.py` | LLM provider settings (admin only) |
| `lmstudio.py` | Operations specific to LM Studio |
| `models.py` | Model settings (admin only) |
| `mode.py` | Reference of the startup mode (text / lite / lite-en) |
| `pipeline_config.py` | Retrieval of RAG presets |

### 2.7 Monitoring and operations

| Router | Main role |
|---|---|
| `dashboard.py` | Summary for the dashboard |
| `health.py` | Health check (some parts admin only) |
| `stats.py` | Statistics |
| `alerts.py` | Alerts (admin only) |
| `audit_logs.py` | Audit log browsing |
| `jobs.py` | Reference of background jobs |
| `cost.py` | Cost aggregation |
| `reports.py` | Report-related |

### 2.8 Settings and others

| Router | Main role |
|---|---|
| `settings.py` | Reference and update of the various settings (including `/api/settings/pii-mode` for switching the PII detection mode) |
| `features.py` | Reference of the feature toggles |
| `admin.py` | Operations for administrators |
| `demo.py` | Demo data management |
| `pages.py` | Static pages |

---

## 3. Basic format of requests and responses

### 3.1 Common headers

- `Content-Type: application/json`
- `Authorization: Bearer<token>`
- `X-Request-ID:<uuid>` … added to all requests on the server side (the default of `logging.request_id = true`)

### 3.2 Responses

JSON format is the basis. On an error, it is returned in the following format.

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "action must be 'block' or 'warn'"
  }
}
```

Examples of the main error codes:

| Code | HTTP | Use |
|---|---|---|
| `BAD_REQUEST` | 400 | Input validation error |
| `INVALID_REGEX` | 400 | Failure to compile a regular expression |
| Authorization error | 403 | Insufficient role |
| 410 Gone | 410 | An abolished endpoint (for example: `/chat-popup`) |

### 3.3 SSE (Server-Sent Events)

Streaming responses of the chat are returned in SSE format.

- `event:` and `data:` are sent per event, separated by newlines
- Designed so that the DB can be handled safely with `db.get_db(check_same_thread=False)` even when the connection refers to the DB from an SSE thread

---

## 4. Rate limiting

- A rate limit using SlowAPI is enabled by default.
- Setting the environment variable `CYNOVELA_DISABLE_RATE_LIMIT` to any of `1` / `true` / `yes` disables it (intended for use during tests).

---

## 5. Upload limit

- The default limit for file uploads is **100 MB**.
- It can be changed with the environment variable `CYNOVELA_MAX_UPLOAD_BYTES`.

---

## 6. Pagination

The main listing APIs (list endpoints) support pagination.

| Parameter | Use |
|---|---|
| `limit` | Number of items per page (the default is per endpoint) |
| `offset` | Position to start retrieving from |

The `limit` of audit log retrieval (`get_audit_logs` of MCP) is 10 by default and 50 at most.

---

## 7. Known limitations

- **Deletion and tampering of the audit log through the API are forbidden** (append only).
- Forced authentication works regardless of the startup form. Even on a `--demo` startup the authentication check is not skipped (the fixed token of the form `Bearer demo-token-<user_id>` was abolished on 2026-07-29, and is rejected uniformly with 401).
- The path parameter of `/api/sources` needs validation to prevent access to system paths.
- `llm_endpoint` is validated so that it cannot be changed to a value that points to the internal network.
- When composing the LLM prompt, the design is that the system prompt is placed **after** retrieved_content (because placing it first makes it overwritable by the documents).
- Some endpoints depend on features planned for future implementation (Qdrant, MLX, GraphRAG, and so on), and are currently only a skeleton.

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela は FastAPI で構築されており、`routers/` 配下の **36 ファイル** にエンドポイントが分かれて配置されています。本ドキュメントは個別のエンドポイント仕様ではなく、**全体マップとして主要カテゴリを一望** できるようにまとめたものです。

---

## 1. 認証方式

### 1.1 認証ヘッダー

API リクエストは原則として `Authorization` ヘッダーで認証情報を渡します。

- 通常モードでは `username` と `password` によるログインを経て、サーバー側で発行されたトークンを利用します。
- 認証は `POST /api/auth/login` が発行する JWT のみです。かつて存在した `Bearer demo-token-{user_id}` 形式の簡易トークンは 2026-07-29 に廃止され、`--demo` 起動でも受理しません。
<!-- BACKLOG: JWT 化後のトークン形式は未定 -->

### 1.2 認可（権限チェック）

各エンドポイントの先頭で、`core/auth.py` のロール検査ヘルパーを呼び出します。

| ヘルパー | 検査内容 |
|---|---|
| `_require_admin()` | role == admin |
| `_require_authenticated()` | 認証済み（ロール不問） |
| `_require_role(roles)` | 指定ロールのいずれかに合致 |
| `_require_admin_or_self()` | admin または本人 |

ロール検査の呼び出しは **約 242 箇所** に分散しています。
詳細は `docs/rbac.md` を参照してください。

---

## 2. 主要エンドポイントのカテゴリ別一覧

### 2.1 認証・ユーザー管理

| ルーター | 主な役割 |
|---|---|
| `auth.py` | ログイン、ログアウト、ユーザー作成・削除・一覧（admin 限定） |
| `users.py` | ユーザー詳細、自分自身の情報 |
| `sessions.py` | チャットセッションの一覧・削除（一部 admin 限定） |

### 2.2 データソース・ファイル管理

| ルーター | 主な役割 |
|---|---|
| `sources.py` | 取り込み元（Source）の登録・スキャン |
| `files.py` | ファイルのアップロード・一覧・削除（admin 限定の操作あり） |
| `archived.py` | アーカイブの照会・復元（admin 限定） |

### 2.3 ワークスペース・コレクション

| ルーター | 主な役割 |
|---|---|
| `workspaces.py` | ワークスペースの作成・削除・詳細 |
| `collections.py` | コレクションの作成・編集・Publish |
| `catalog.py` | データカタログの参照 |

### 2.4 RAG / Chat

| ルーター | 主な役割 |
|---|---|
| `chat.py` | チャット応答（通常 / 比較 / SSE ストリーム） |
| `agent.py` | エージェント系の操作 |
| `mcp.py` | MCP（Model Context Protocol、外部公開ツール）の管理 |
| `messages.py` | メッセージ単位の操作 |

### 2.5 ガードレール・コンプライアンス

| ルーター | 主な役割 |
|---|---|
| `guardrails.py` | PII 検出履歴の集計（admin 限定）、禁止トピックの CRUD |
| `policies.py` | ガードレールポリシーの一覧・編集 |
| `compliance.py` | コンプライアンス系の操作（admin 限定） |
| `feedback.py` | 👍👎 フィードバックの取得・編集（admin 限定） |

### 2.6 モデル・LLM 接続

| ルーター | 主な役割 |
|---|---|
| `llm.py` | LLM プロバイダー設定（admin 限定） |
| `lmstudio.py` | LM Studio 固有の操作 |
| `models.py` | モデル設定（admin 限定） |
| `mode.py` | 起動モード（text / lite / lite-en）参照 |
| `pipeline_config.py` | RAG プリセットの取得 |

### 2.7 監視・運用

| ルーター | 主な役割 |
|---|---|
| `dashboard.py` | ダッシュボード用のサマリー |
| `health.py` | 健全性確認（一部 admin 限定） |
| `stats.py` | 統計情報 |
| `alerts.py` | アラート（admin 限定） |
| `audit_logs.py` | 監査ログ閲覧 |
| `jobs.py` | バックグラウンドジョブの参照 |
| `cost.py` | コスト集計 |
| `reports.py` | レポート系 |

### 2.8 設定・その他

| ルーター | 主な役割 |
|---|---|
| `settings.py` | 各種設定の参照・更新（PII 検出モード切替の `/api/settings/pii-mode` を含む） |
| `features.py` | 機能トグルの参照 |
| `admin.py` | 管理者向け操作 |
| `demo.py` | デモデータ管理 |
| `pages.py` | 静的ページ |

---

## 3. リクエスト / レスポンスの基本形式

### 3.1 共通ヘッダー

- `Content-Type: application/json`
- `Authorization: Bearer<token>`
- `X-Request-ID:<uuid>` … サーバー側で全リクエストに付与（`logging.request_id = true` の既定）

### 3.2 レスポンス

JSON 形式が基本です。エラー時は次の形式で返します。

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "action must be 'block' or 'warn'"
  }
}
```

主なエラーコード例:

| コード | HTTP | 用途 |
|---|---|---|
| `BAD_REQUEST` | 400 | 入力検証エラー |
| `INVALID_REGEX` | 400 | 正規表現のコンパイル失敗 |
| 認可エラー | 403 | ロール不足 |
| 410 Gone | 410 | 廃止されたエンドポイント（例: `/chat-popup`） |

### 3.3 SSE（Server-Sent Events）

チャットのストリーミング応答は SSE 形式で返します。

- イベント単位で `event:` と `data:` を改行区切りで送出
- 接続が SSE スレッドから DB を参照する場合も `db.get_db(check_same_thread=False)` で安全に扱える設計

---

## 4. レート制限

- 既定で SlowAPI を用いたレートリミットが有効です。
- 環境変数 `CYNOVELA_DISABLE_RATE_LIMIT` を `1` / `true` / `yes` のいずれかに設定すると無効化できます（テスト時の利用を想定）。

---

## 5. アップロード上限

- ファイルアップロードの既定上限は **100 MB** です。
- 環境変数 `CYNOVELA_MAX_UPLOAD_BYTES` で変更できます。

---

## 6. ページネーション

主要な一覧 API（list 系エンドポイント）はページネーションに対応しています。

| パラメータ | 用途 |
|---|---|
| `limit` | 1 ページの件数（既定はエンドポイントごと） |
| `offset` | 取得開始位置 |

監査ログ取得（MCP の `get_audit_logs`）の `limit` は既定 10 / 最大 50 です。

---

## 7. 既知制限

- API 経由での **監査ログの削除・改ざんは禁止** されています（追加のみ）。
- 認証強制は起動形態によらず動作します。`--demo` 起動でも認証チェックは省かれません（`Bearer demo-token-<user_id>` 形式の固定トークンは 2026-07-29 に廃止し、一律 401 で拒否します）。
- `/api/sources` の path パラメータは、システムパスへのアクセスを防ぐためのバリデーションが必要です。
- `llm_endpoint` は内部ネットワークを指す値に変更できないようにバリデーションされます。
- LLM プロンプトを構成する際、システムプロンプトは retrieved_content の **後** に配置する設計です（前置きするとドキュメントで上書き可能になるため）。
- 一部のエンドポイントは将来実装予定の機能（Qdrant、MLX、GraphRAG など）に依存しており、現状は骨格のみです。
<!-- BACKLOG: 各エンドポイントの個別仕様（パス、メソッド、入出力スキーマ）の網羅はまだ整理途中 -->

---

