# MCP（Model Context Protocol）連携ガイド

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual in order to
> understand the concepts of AI infrastructure tools hands-on. It is not a commercial
> product and not an official implementation.
> The implementation is entirely original, and is made of an OSS stack:
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela can expose its own features to external LLM clients as an MCP server for MCP (Model Context Protocol, the AI tool integration protocol proposed by Anthropic). This document explains the concept of MCP, the MCP tools that Cynovela exposes, and the connection procedure.

The server (`mcp_server.py`) implements protocol revision **2026-07-28** over stdio: it answers `server/discover` (no handshake and no session id is required — `initialize` from older clients is answered too), declares tool inputs and outputs with JSON Schema 2020-12, and returns results as `structuredContent` in addition to plain text. When the target material does not exist it returns JSON-RPC error `-32602`.

---

## 1. What MCP is

MCP is a standard protocol by which an AI assistant (the client) calls features (tools) of an external system.

- **Client**: the side the user talks to, such as LM Studio or another supported LLM client
- **Server**: the side that provides features (Cynovela is this side)
- **Tool**: an operation the server exposes (search, registration, reference, and so on)

With MCP, when a user says to an LLM client "search our internal documents", the LLM calls Cynovela's search tool and generates an answer based on the result.

---

## 2. MCP tools Cynovela exposes (11 in total)

### 2-1. RAG search tools (4)

#### `search_collection`
- **Arguments (required)**: `query`, `workspace_id`, `collection_id`
- **Arguments (optional)**: `preset`
- **Description**: Performs a RAG search against a single Collection (a group of documents).

#### `search_across_collections`
- **Arguments (required)**: `query`, `workspace_id`, `collection_ids`
- **Arguments (optional)**: `preset`
- **Description**: Performs a RAG search across multiple Collections.

#### `rag_with_role`
- **Arguments (required)**: `query`, `workspace_id`, `collection_id`, `style_role`
- **Arguments (optional)**: `preset`
- **Description**: Performs a RAG search while switching the answer style by role (for administrators / for general users, and so on).

#### `rag_general`
- **Arguments (required)**: `query`, `workspace_id`
- **Description**: Generates an answer using only the LLM's general knowledge, without using RAG. It is for general questions that do not depend on internal documents.

### 2-2. Information retrieval tools (4)

#### `list_workspaces`
- **Arguments**: none
- **Description**: Gets a list of all workspaces and their collections.

#### `get_workspace_info`
- **Arguments (required)**: `workspace_id`
- **Description**: Returns detailed information about the specified workspace (name, guardrail policy, creation time, and so on).

#### `get_collection_info`
- **Arguments (required)**: `workspace_id`, `collection_id`
- **Description**: Returns details of the collection (document count, status, access level).

#### `get_audit_logs`
- **Arguments (required)**: `workspace_id`
- **Arguments (optional)**: `limit` (default 10, maximum 50)
- **Description**: Gets the audit log (chat history, PII detection, errors).

### 2-3. Administration tools (3)

#### `list_sources`
- **Arguments (required)**: `workspace_id`
- **Description**: Returns a list of the data sources under the workspace (file path, status, file count).

#### `publish_collection`
- **Arguments (required)**: `collection_id`
- **Description**: Publishes the specified collection into a state where it can be searched by RAG.

#### `create_workspace`
- **Arguments (required)**: `name`
- **Arguments (optional)**: `description`
- **Description**: Creates a new workspace.

---

## 3. Connecting from LM Studio

LM Studio has MCP client features, and an MCP server can be registered in its configuration file.

### 3-1. Connection flow

```
LM Studio（ユーザー対話）
  ↓ MCP プロトコル（標準入出力経由）
Cynovela MCP サーバー（mcp_server.py）
  ↓ HTTP API
Cynovela 本体（FastAPI サーバー）
```

### 3-2. Configuration example

Register the following in LM Studio's MCP server configuration. For the actual key names, see the client's own documentation.

```json
{
  "mcpServers": {
    "cynovela": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp_server.py"
      ],
      "env": {
        "CYNOVELA_BASE": "http://127.0.0.1:8765",
        "CYNOVELA_TOKEN": "<認証トークン>"
      }
    }
  }
}
```

---

## 4. Which Python runs the MCP server

`mcp_server.py` uses the standard library only — it has no external dependencies, so **any Python 3.12 or later can run it**; no environment needs to be activated. The natural choice is the Python this package prepared (package edition: `.venv-cynovela/bin/python3`; source edition choice 1: the `cynovela-dist` conda environment).

### 4-1. Specifying the Python path

The environment variable `CYNOVELA_MCP_PYTHON` can specify the absolute path of the Python that the `/api/mcp/config` snippet points clients at.

```bash
export CYNOVELA_MCP_PYTHON=/path/to/.venv-cynovela/bin/python3
```

---

## 5. Notes on authentication

### 5-1. Bearer token

The MCP server authenticates to the main Cynovela API with the `Authorization: Bearer<token>` header. The token is passed through an environment variable on the client side.

- Authentication is the JWT issued by `POST /api/auth/login`. The old `Bearer demo-token-<user_id>` form has been abolished and is not accepted.
- For production operation, introducing JWT authentication is required (it is not implemented at present).

### 5-2. Role permissions

Calls made through MCP also pass the same role permission checks (admin / curator / viewer) as the main API. In particular, administration tools such as `create_workspace` and `publish_collection` may require admin permission.

### 5-3. Audit log

Operations made through MCP are also recorded in the same audit log (the `audit_logs` table) as the main body. You can check the history with `get_audit_logs`.

---

## 6. Troubleshooting

| Symptom | What to check |
|---|---|
| The tools are not found | Whether the Cynovela main body (`server.py`) is already running at `http://127.0.0.1:8765` |
| Authentication error | The value of the `CYNOVELA_TOKEN` environment variable, and whether the token is still valid |
| ImportError appears | Whether the Python is 3.12 or later (`mcp_server.py` itself has no external dependencies) |
| The result is empty | Whether the target Collection has reached the `ready` status |

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela は MCP（Model Context Protocol、Anthropic が提唱する AI ツール連携プロトコル）の MCP サーバーとして自身の機能を外部の LLM クライアントへ公開できます。本ドキュメントでは MCP の概念と Cynovela が公開している MCP ツール、接続手順を説明します。

サーバー（`mcp_server.py`）はプロトコル版 **2026-07-28** を stdio で実装しています: `server/discover` に応え（握手もセッション ID も要求しません — 旧世代クライアントの `initialize` にも応えます）、道具の入出力を JSON Schema 2020-12 で宣言し、結果を平文に加えて `structuredContent` で構造化して返します。対象の資料が無いときは JSON-RPC エラー `-32602` を返します。

---

## 1. MCP とは

MCP は、AI アシスタント（クライアント）が外部システムの機能（ツール）を呼び出すための標準プロトコルです。

- **クライアント**: LM Studio や対応する LLM クライアントなど、ユーザーが対話する側
- **サーバー**: 機能を提供する側（Cynovela がここに該当）
- **ツール**: サーバーが公開する操作（検索、登録、参照など）

MCP を使うと、ユーザーが LLM クライアントに「うちの社内文書を検索して」と話しかけたときに、LLM が Cynovela の検索ツールを呼び出し、結果を踏まえて回答を生成する、という連携が成立します。

---

## 2. Cynovela が公開する MCP ツール（全 11 件）

### 2-1. RAG 検索系（4 件）

#### `search_collection`
- **引数（必須）**: `query`, `workspace_id`, `collection_id`
- **引数（任意）**: `preset`
- **説明**: 単一の Collection（コレクション、文書群）に対して RAG 検索を行います。

#### `search_across_collections`
- **引数（必須）**: `query`, `workspace_id`, `collection_ids`
- **引数（任意）**: `preset`
- **説明**: 複数の Collection を横断して RAG 検索を行います。

#### `rag_with_role`
- **引数（必須）**: `query`, `workspace_id`, `collection_id`, `style_role`
- **引数（任意)**: `preset`
- **説明**: ロール別の回答スタイル（管理者向け / 一般ユーザー向けなど）を切り替えて RAG 検索します。

#### `rag_general`
- **引数（必須）**: `query`, `workspace_id`
- **説明**: RAG を使わず、LLM の一般知識のみで回答を生成します。社内文書に依存しない一般的な質問用です。

### 2-2. 情報取得系（4 件）

#### `list_workspaces`
- **引数**: なし
- **説明**: 全ワークスペースとそのコレクション一覧を取得します。

#### `get_workspace_info`
- **引数（必須）**: `workspace_id`
- **説明**: 指定ワークスペースの詳細情報（名前、ガードレールポリシー、作成日時など）を返します。

#### `get_collection_info`
- **引数（必須）**: `workspace_id`, `collection_id`
- **説明**: コレクションの詳細（ドキュメント数、ステータス、アクセスレベル）を返します。

#### `get_audit_logs`
- **引数（必須）**: `workspace_id`
- **引数（任意）**: `limit`（既定 10、上限 50）
- **説明**: 監査ログ（チャット履歴、PII 検出、エラー）を取得します。

### 2-3. 管理系（3 件）

#### `list_sources`
- **引数（必須）**: `workspace_id`
- **説明**: ワークスペース配下のデータソース一覧（ファイルパス、ステータス、ファイル数）を返します。

#### `publish_collection`
- **引数（必須）**: `collection_id`
- **説明**: 指定コレクションを RAG 検索可能な状態に公開します。

#### `create_workspace`
- **引数（必須）**: `name`
- **引数（任意）**: `description`
- **説明**: 新規ワークスペースを作成します。

---

## 3. LM Studio からの接続

LM Studio は MCP クライアント機能を備えており、設定ファイルで MCP サーバーを登録できます。

### 3-1. 接続フロー

```
LM Studio（ユーザー対話）
  ↓ MCP プロトコル（標準入出力経由）
Cynovela MCP サーバー（mcp_server.py）
  ↓ HTTP API
Cynovela 本体（FastAPI サーバー）
```

### 3-2. 設定例

LM Studio の MCP サーバー設定に以下を登録します。実際のキー名はクライアント側のドキュメントを参照してください。

```json
{
  "mcpServers": {
    "cynovela": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp_server.py"
      ],
      "env": {
        "CYNOVELA_BASE": "http://127.0.0.1:8765",
        "CYNOVELA_TOKEN": "<認証トークン>"
      }
    }
  }
}
```

---

## 4. MCP サーバーを動かす Python

`mcp_server.py` は標準ライブラリのみで動きます — 外部依存が無いため、**Python 3.12 以上ならどれでも動きます**。環境のアクティブ化も要りません。自然な選択は、この配布物が用意した Python です（パッケージ版: `.venv-cynovela/bin/python3`、ソース版の選択肢1: conda 環境 `cynovela-dist`）。

### 4-1. Python パスの指定

環境変数 `CYNOVELA_MCP_PYTHON` で、`/api/mcp/config` のスニペットがクライアントへ示す Python の絶対パスを指定できます。

```bash
export CYNOVELA_MCP_PYTHON=/path/to/.venv-cynovela/bin/python3
```

---

## 5. 認証の注意

### 5-1. ベアラートークン

MCP サーバーは Cynovela 本体 API に対して `Authorization: Bearer<token>` ヘッダーで認証します。トークンはクライアント側の環境変数で渡します。

- 認証は `POST /api/auth/login` が発行する JWT です。旧 `Bearer demo-token-<user_id>` 形式は廃止済みで受理しません。
- 本番運用では JWT 認証導入が必要です（現時点では未実装）。

### 5-2. ロール権限

MCP 経由の呼び出しも本体 API と同じロール（admin / curator / viewer）の権限チェックを通過します。特に `create_workspace` や `publish_collection` などの管理系ツールは admin 権限を要する場合があります。

### 5-3. 監査ログ

MCP 経由の操作も本体と同じ監査ログ（`audit_logs` テーブル）に記録されます。`get_audit_logs` で履歴を確認できます。

---

## 6. トラブルシューティング

| 症状 | 確認ポイント |
|---|---|
| ツールが見つからない | Cynovela 本体（`server.py`）が `http://127.0.0.1:8765` で起動済みか |
| 認証エラー | `CYNOVELA_TOKEN` 環境変数の値、トークンの有効性 |
| ImportError が出る | Python が 3.12 以上か（`mcp_server.py` 自体に外部依存はありません） |
| 結果が空 | 対象 Collection が `ready` ステータスに到達済みか |

---

