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

## 2. MCP tools Cynovela exposes (25 in total)

22 tools are visible by default. The three administration tools in section 2-6 are closed by default: they appear in `tools/list` only when the MCP server's `env` sets `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` (see section 5-5).

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

### 2-2. Information retrieval tools (6)

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

#### `list_sources`
- **Arguments (required)**: `workspace_id`
- **Description**: Returns a list of the data sources under the workspace (file path, status, file count).

#### `server_status`
- **Arguments**: none
- **Description**: Shows whether the server is up and the state of the index (collections and their chunk counts).

### 2-3. Ingestion and progress tools (3)

#### `ingest_source`
- **Arguments (required)**: `path`
- **Arguments (optional)**: `name`, `workspace_id`
- **Description**: Ingests material in one tool: adds the folder as a data source, registers the material, and starts the scan. The scan returns a `job_id` the moment it starts and the call comes back immediately; watch the progress with `get_job_status`.

#### `get_job_status`
- **Arguments (required)**: `job_id`
- **Description**: Shows the progress of a scan or a publish. Pass the `job_id` returned by `ingest_source` or `publish_collection`.

#### `cancel_scan`
- **Arguments (required)**: `source_id`
- **Description**: Requests cancellation of a running scan.

### 2-4. Publishing and creation tools (4)

#### `publish_collection`
- **Arguments (required)**: `collection_id`
- **Description**: Starts publishing the collection and returns a `job_id` immediately — it does not wait for the publish to finish. Watch the progress with `get_job_status`. Once published, the collection can be searched by RAG.

#### `create_collection`
- **Arguments (required)**: `workspace_id`, `name`
- **Arguments (optional)**: `source_id`
- **Description**: Creates a collection inside the workspace. When `source_id` is given, all files of that data source are linked to the new collection.

#### `publish_control`
- **Arguments (required)**: `collection_id`, `action` (`stop` or `recover`)
- **Description**: Stops a running publish, or recovers a collection stuck in the publishing state.

#### `create_workspace`
- **Arguments (required)**: `name`
- **Arguments (optional)**: `description`
- **Description**: Creates a new workspace.

### 2-5. Settings tools (5)

All five require an **admin** token. API keys are write-only: responses carry only the
`api_key_set` boolean (set / not set), never a key value.

#### `settings_show`
- **Arguments (optional)**: `name` — one of `llm` (default), `reranker`, `classifier`, `embedding`, `pii`, `vector-store`, `datasync`
- **Description**: Shows the current settings of the chosen target.

#### `settings_models`
- **Arguments**: none
- **Description**: Lists the models at the configured inference endpoint. Note: this is the *downloaded* list — it does not mean a model is loaded.

#### `settings_test`
- **Arguments (optional)**: `provider`, `base_url`, `model` (when given, these are tested instead of the saved settings)
- **Description**: Tests the LLM connection and answers in words (connected / not connected, with the reason).

#### `settings_set`
- **Arguments (required)**: `values` — an object with only the items to change (e.g. `{"model": "..."}`)
- **Arguments (optional)**: `name` — same choices as `settings_show` (default `llm`)
- **Description**: Changes settings. **Closed by default**: it runs only when the MCP server process was started with the environment variable `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` (see section 5-4). When closed, the call returns an error text explaining exactly that, and nothing is executed.

#### `settings_providers`
- **Arguments**: none
- **Description**: Lists the selectable LLM provider presets.

### 2-6. Administration tools (3) — closed by default

These three appear in `tools/list` only when the MCP server's `env` sets `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` (see section 5-5). This is not a removed feature: it is a guard that stops an AI, swayed by material it has just read, from firing destructive operations on its own.

#### `delete_item`
- **Arguments (required)**: `kind` (`source` / `collection` / `workspace`), `id`
- **Description**: Deletes a data source, a collection, or a workspace.

#### `manage_users`
- **Arguments (required)**: `action` (`list` / `create` / `update` / `delete` / `reset_password`)
- **Arguments (optional)**: `user_id`, `username`, `password`, `role`, `display_name`, `is_active`
- **Description**: Manages users (list, create, update, delete, reset a password).

#### `manage_backups`
- **Arguments (required)**: `action` (`list` / `create` / `restore` / `delete`)
- **Arguments (optional)**: `name`, `label`
- **Description**: Handles backups (list, create, restore, delete). `restore` replaces the current data with the contents of the backup; a server restart is required for the restore to take effect.

### 2-7. How to use the long-running operations

Scanning (`ingest_source`) and publishing (`publish_collection`) return a `job_id` the moment they start and come back immediately. Watch the progress by passing that `job_id` to `get_job_status`, repeatedly. To cancel, use `cancel_scan` for a scan and `publish_control` with `stop` for a publish.

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

### 3-2. Where LM Studio's configuration file is

The MCP registration lives in a single JSON file named `mcp.json` inside LM Studio's home
directory. Measured locations on macOS (measured on LM Studio 0.4.x):

- `~/.cache/lm-studio/mcp.json` — the location measured on the development machine
- `~/.lmstudio/mcp.json` — the location when LM Studio's home is the newer default

You do not have to guess which one your machine uses: inside LM Studio, open the
right-hand **Program** panel → **Install** → **Edit mcp.json** — that editor opens the
correct file, and saving it there is the same as editing the file directly.

### 3-3. Getting the token (`CYNOVELA_TOKEN`) — full procedure

1. Start Cynovela (`./launch.sh` or `./launch.sh --demo`) and confirm `http://127.0.0.1:8765` answers.
2. Ask the server for a token with your login name and password (the same values you use on the web screen):

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"<your username>","password":"<your password>"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
```

3. The printed string is the token. Put it into the `env` block of `mcp.json` (next step).
4. **The token does not expire unless you ask it to.** Signing in gives a token with no expiry; pass `expires_in_hours` to the login call if you want one that does. If tool calls start failing with an authentication error, issue a new token with the same command and update `mcp.json`.

Note: for the settings tools (and other admin tools) the login must be the **administrator** account; a viewer token is rejected by the server with 403.

### 3-4. Configuration example

Register the following in `mcp.json` (merge into the existing `mcpServers` object if the file already has one):

```json
{
  "mcpServers": {
    "cynovela": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp_server.py",
        "--cynovela-url", "http://127.0.0.1:8765"
      ],
      "env": {
        "CYNOVELA_TOKEN": "<the token from 3-3>"
      }
    }
  }
}
```

- `command`: any Python 3.12+ — the natural choice is the one this package prepared (see section 4).
- To allow `settings_set`, add `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` to the `env` block (see 5-4). Leave it out to keep settings read-only.
- To expose the three administration tools (`delete_item` / `manage_users` / `manage_backups`), add `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` to the `env` block (see 5-5). Leave it out and they do not appear at all.

### 3-5. LM Studio asks a person for permission — this part is yours

Registering the server in `mcp.json` is **not** the last step. LM Studio guards local MCP
tools behind an explicit, human confirmation in its own window:

- **Where**: when the model first tries to call a Cynovela tool in a chat, LM Studio shows a confirmation dialog in the chat window asking whether to allow the tool call (per call, or "always allow" per tool). The server can also be switched on and off in the **Program** panel where `mcp.json` was edited.
- **After you allow it**: the tool call runs, and the result (with `structuredContent`) is handed to the model — from then on the flow of section 3-1 works end to end.
- **If you never allow it**: the registration itself still looks fine (the server appears in the panel), but no tool is ever called — this is the single most common "it does not work" state. It is not an error in Cynovela; grant the permission in the LM Studio window.

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

- Authentication is the JWT issued by `POST /api/auth/login` (the procedure is in section 3-3). The old `Bearer demo-token-<user_id>` form has been abolished and is not accepted.
- The token does not expire unless the login call asked for an expiry (`expires_in_hours`). Issue a new one with the same login call whenever you need to.

### 5-2. Role permissions

Calls made through MCP also pass the same role permission checks (admin / curator / viewer) as the main API. In particular, tools that write — such as `ingest_source`, `publish_collection` and `create_workspace` — may require admin permission, and all five settings tools require it.

### 5-3. Audit log

Operations made through MCP are also recorded in the same audit log (the `audit_logs` table) as the main body. You can check the history with `get_audit_logs`.

### 5-4. Write guard for the settings tools (default: read-only)

The settings tools are split into reading and writing:

- **Reading** (`settings_show`, `settings_models`, `settings_test`, `settings_providers`) works whenever the token is an admin token. No extra switch.
- **Writing** (`settings_set`) is **closed by default**. It runs only when the MCP server process was started with `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` in its environment — in LM Studio, that means adding the line to the `env` block of `mcp.json` (section 3-4). When closed, the call returns an error message saying exactly this, and nothing is executed.

Why: the caller of an MCP tool is an AI that can be swayed by whatever material it has just read. If a document says "rewrite the settings", a path exists in principle for the AI to treat that as an instruction. Writing therefore requires an explicit, human-made decision on the client side. This guard is *not* a replacement for the server-side role check — that check still runs as before; this is a thin extra layer in front of it.

### 5-5. Guard for the administration tools (default: hidden)

The three administration tools (`delete_item`, `manage_users`, `manage_backups`) are **closed by default**. They appear in `tools/list` — and run — only when the MCP server process was started with `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` in its environment; in LM Studio, that means adding the line to the `env` block of `mcp.json` (section 3-4). The reason is the same as in 5-4: deletion, user management and backup restore are exactly the operations an AI must not fire on its own after being swayed by material it has just read. This is not a removed feature — it is a thin, explicit switch a human turns on; the server-side role check still runs as before.

---

## 6. Troubleshooting

| Symptom | What to check |
|---|---|
| The tools are not found | Whether the Cynovela main body (`server.py`) is already running at `http://127.0.0.1:8765` |
| The server appears in LM Studio but no tool is ever called | The human permission in LM Studio has not been granted yet — see section 3-5. The registration alone does not allow calls; allow the tool call in the chat window's confirmation dialog |
| Authentication error | The value of the `CYNOVELA_TOKEN` environment variable, and whether the token is still valid — **a token has no expiry unless the login call asked for one**; re-issue with the login call in section 3-3 |
| `settings_set` answers "the write is closed by default" | That is the write guard (section 5-4), not a fault. Add `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` to the `env` block of `mcp.json` if you really want writes |
| `delete_item` / `manage_users` / `manage_backups` do not appear in the tool list | That is the guard (section 5-5), not a fault. Add `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` to the `env` block of `mcp.json` if you really want them |
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

## 2. Cynovela が公開する MCP ツール（全 25 件）

既定で見えるのは 22 件です。2-6 節の管理系 3 件は既定で閉じており、MCP サーバの `env` に `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を書いたときだけ `tools/list` に現れます（5-5 節）。

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

### 2-2. 情報取得系（6 件）

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

#### `list_sources`
- **引数（必須）**: `workspace_id`
- **説明**: ワークスペース配下のデータソース一覧（ファイルパス、ステータス、ファイル数）を返します。

#### `server_status`
- **引数**: なし
- **説明**: サーバの稼働と索引の状態（まとまりごとの塊の数）を見ます。

### 2-3. 資料を入れる・進み具合（3 件）

#### `ingest_source`
- **引数（必須）**: `path`
- **引数（任意）**: `name`, `workspace_id`
- **説明**: 資料を入れます。取り込み元を足す→資料として登録する→走査を始める、を 1 道具で行います。走査は始めた時点で `job_id` を返してすぐ戻ります。進み具合は `get_job_status` で見ます。

#### `get_job_status`
- **引数（必須）**: `job_id`
- **説明**: 走査と公開の進み具合を見ます。`ingest_source` / `publish_collection` が返した `job_id` を渡します。

#### `cancel_scan`
- **引数（必須）**: `source_id`
- **説明**: 走行中の走査に中止を要求します。

### 2-4. 公開と作成系（4 件）

#### `publish_collection`
- **引数（必須）**: `collection_id`
- **説明**: 指定コレクションの公開を始め、`job_id` を即座に返します — 終わるまで待ちません。進み具合は `get_job_status` で見ます。公開後は RAG 検索が可能になります。

#### `create_collection`
- **引数（必須）**: `workspace_id`, `name`
- **引数（任意）**: `source_id`
- **説明**: 作業場所の中にまとまり（コレクション）を作ります。`source_id` を渡すと、その資料の全ファイルを結び付けます。

#### `publish_control`
- **引数（必須）**: `collection_id`, `action`（`stop` / `recover`）
- **説明**: 走行中の公開を止める、または固着した公開から復旧します。

#### `create_workspace`
- **引数（必須）**: `name`
- **引数（任意）**: `description`
- **説明**: 新規ワークスペースを作成します。

### 2-5. 設定系（5 件）

5 件とも**管理者**のトークンが必要です。API キーは書き込み専用で、応答には
設定あり / なし の bool（`api_key_set`）だけが載り、値は決して返しません。

#### `settings_show`
- **引数（任意）**: `name` — `llm`（既定）/ `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` のいずれか
- **説明**: 選んだ対象のいまの設定を見ます。

#### `settings_models`
- **引数**: なし
- **説明**: 設定された推論サーバの接続先にあるモデルの一覧を出します。注意: これは*ダウンロード済み*の一覧で、読み込み済みを意味しません。

#### `settings_test`
- **引数（任意）**: `provider`, `base_url`, `model`（渡すと保存済み設定の代わりにその値で試します）
- **説明**: LLM への接続を確かめ、通ったか通らなかったかを理由つきの言葉で返します。

#### `settings_set`
- **引数（必須）**: `values` — 変える項目だけを入れた object（例: `{"model": "..."}`）
- **引数（任意）**: `name` — `settings_show` と同じ選択肢（既定 `llm`）
- **説明**: 設定を変えます。**既定で閉じています**: MCP サーバのプロセスが環境変数 `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` 付きで起動されたときだけ実行されます（5-4 節）。閉じているときに呼ぶと、その旨を説明するエラー文が返り、何も実行されません。

#### `settings_providers`
- **引数**: なし
- **説明**: 選べる LLM プロバイダーのプリセット一覧を出します。

### 2-6. 管理系（3 件）— 既定で閉

この 3 件は、MCP サーバの `env` に `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を書いたときだけ `tools/list` に現れます（5-5 節）。これは機能を削っているのではなく、直前に読んだ資料に引きずられた AI の暴発を止める仕掛けです。

#### `delete_item`
- **引数（必須）**: `kind`（`source` / `collection` / `workspace`）, `id`
- **説明**: 資料・まとまり・作業場所を消します。

#### `manage_users`
- **引数（必須）**: `action`（`list` / `create` / `update` / `delete` / `reset_password`）
- **引数（任意）**: `user_id`, `username`, `password`, `role`, `display_name`, `is_active`
- **説明**: 利用者を管理します（一覧・作成・変更・削除・パスワード再設定）。

#### `manage_backups`
- **引数（必須）**: `action`（`list` / `create` / `restore` / `delete`）
- **引数（任意）**: `name`, `label`
- **説明**: 控えを扱います（一覧・作成・復元・削除）。`restore` はいまのデータを控えの中身に置き換えます。反映にはサーバの再起動が要ります。

### 2-7. 時間のかかる処理の使い方

走査（`ingest_source`）と公開（`publish_collection`）は、開始した時点で `job_id` を返してすぐ戻ります。進み具合は `get_job_status` に `job_id` を渡して繰り返し見ます。中止は、走査なら `cancel_scan`、公開なら `publish_control` の `stop` です。

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

### 3-2. LM Studio の設定ファイルの場所

MCP の登録は、LM Studio のホームディレクトリにある `mcp.json` という 1 つの JSON
ファイルに書きます。macOS での位置（LM Studio 0.4.x での実測）:

- `~/.cache/lm-studio/mcp.json` — 開発機で実測した位置
- `~/.lmstudio/mcp.json` — LM Studio のホームが新しい既定のときの位置

どちらか迷う必要はありません: LM Studio の画面で右側の **Program** パネル →
**Install** → **Edit mcp.json** を開くと正しいファイルが開き、そこで保存すれば
ファイルを直接書いたのと同じになります。

### 3-3. トークン（`CYNOVELA_TOKEN`）の取り出し方 — 最初から最後まで

1. Cynovela を起動し（`./launch.sh` または `./launch.sh --demo`）、`http://127.0.0.1:8765` が応答することを確かめます。
2. 画面のログインと同じ利用者名とパスワードで、サーバへトークンを頼みます:

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"<利用者名>","password":"<パスワード>"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
```

3. 出力された文字列がトークンです。次の手順の `mcp.json` の `env` に貼ります。
4. **トークンは、頼まないかぎり切れません。** ログインすると期限の無いトークンが渡されます。切れる形が欲しいときは、ログインの呼び出しに `expires_in_hours` を渡してください。道具の呼び出しが認証エラーで失敗しはじめたら、同じコマンドで新しいトークンを発行して `mcp.json` を書き替えてください。

注意: 設定系の道具（と他の管理系の道具）を使うには、ログインは**管理者**のアカウントで行います。閲覧者のトークンはサーバ側が 403 で拒否します。

### 3-4. 設定例

`mcp.json` に以下を登録します（既に `mcpServers` がある場合は、その中へ合流させます）:

```json
{
  "mcpServers": {
    "cynovela": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp_server.py",
        "--cynovela-url", "http://127.0.0.1:8765"
      ],
      "env": {
        "CYNOVELA_TOKEN": "<3-3 で取り出したトークン>"
      }
    }
  }
}
```

- `command`: Python 3.12 以上ならどれでも動きます。自然な選択は、この配布物が用意した Python です（4 節）。
- `settings_set` を許すときだけ、`env` に `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` を足します（5-4 節）。書かなければ設定は読み取り専用のままです。
- 管理系の 3 件（`delete_item` / `manage_users` / `manage_backups`）を出すときだけ、`env` に `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` を足します（5-5 節）。書かなければ 3 件はそもそも現れません。

### 3-5. LM Studio が画面で許可を求めます — ここからは人の操作です

`mcp.json` への登録は最後の手順では**ありません**。LM Studio は手元の MCP の道具を、
自分の画面での明示的な人の同意の内側に置いています:

- **どこで**: チャットの中でモデルが Cynovela の道具をはじめて呼ぼうとしたとき、LM Studio がチャット画面に「この道具の呼び出しを許可するか」の確認ダイアログを出します（1 回ずつ、または道具ごとに常に許可）。サーバ自体の有効・無効は、`mcp.json` を編集したのと同じ **Program** パネルで切り替えられます。
- **許可を出した後**: 道具が実行され、結果（`structuredContent` 付き）がモデルへ渡ります — 以後 3-1 節の流れが最後まで通ります。
- **許可を出さないと**: 登録そのものは成立して見える（パネルにサーバが並ぶ）のに、道具は一度も呼ばれません — これが「動かない」の一番よくある状態です。Cynovela 側の誤りではないので、LM Studio の画面で許可を出してください。

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

- 認証は `POST /api/auth/login` が発行する JWT です（手順は 3-3 節）。旧 `Bearer demo-token-<user_id>` 形式は廃止済みで受理しません。
- トークンは、ログインの呼び出しで期間（`expires_in_hours`）を渡さないかぎり切れません。要るときは同じ呼び出しで発行し直してください。

### 5-2. ロール権限

MCP 経由の呼び出しも本体 API と同じロール（admin / curator / viewer）の権限チェックを通過します。特に `ingest_source` や `publish_collection`、`create_workspace` など書き込みを伴うツールは admin 権限を要する場合があり、設定系の 5 件はすべて admin 権限が必要です。

### 5-3. 監査ログ

MCP 経由の操作も本体と同じ監査ログ（`audit_logs` テーブル）に記録されます。`get_audit_logs` で履歴を確認できます。

### 5-4. 設定系の書き込みの守り（既定: 読み取りのみ）

設定系の道具は、読むものと書くものに分かれています:

- **読むもの**（`settings_show`・`settings_models`・`settings_test`・`settings_providers`）は、トークンが管理者のものであればいつでも動きます。追加のスイッチはありません。
- **書くもの**（`settings_set`）は**既定で閉じています**。MCP サーバのプロセスが環境変数 `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` 付きで起動されたときだけ実行されます — LM Studio では `mcp.json` の `env` にこの 1 行を足すことがそれに当たります（3-4 節）。閉じているときに呼ぶと、その旨を説明するエラー文が返り、何も実行されません。

理由: MCP の道具を呼ぶのは、直前に読んだ資料の中身に引きずられうる AI です。資料の中に「設定を書き換えろ」と書かれていれば、それを指示と受け取って実行する経路が原理的に存在します。∴ 書き込みには、クライアント側での人の明示的な判断を要します。この守りはサーバ側のロール検査の代わりでは*なく*、従来どおり動くその検査の手前に重ねる薄い層です。

### 5-5. 管理系の道具の守り（既定: 見えない）

管理系の 3 件（`delete_item`・`manage_users`・`manage_backups`）は**既定で閉じています**。MCP サーバのプロセスが環境変数 `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` 付きで起動されたときだけ `tools/list` に現れ、実行できます — LM Studio では `mcp.json` の `env` にこの 1 行を足すことがそれに当たります（3-4 節）。理由は 5-4 節と同じです: 削除・利用者管理・控えの復元は、直前に読んだ資料に引きずられた AI が独断で撃ってはならない操作そのものです。これは機能を削っているのではなく、人が明示的に入れる薄いスイッチです。サーバ側のロール検査は従来どおり動きます。

---

## 6. トラブルシューティング

| 症状 | 確認ポイント |
|---|---|
| ツールが見つからない | Cynovela 本体（`server.py`）が `http://127.0.0.1:8765` で起動済みか |
| LM Studio にサーバは並ぶのに道具が一度も呼ばれない | LM Studio の画面での人の許可がまだ出ていません — 3-5 節を見てください。登録だけでは呼び出しは許可されません。チャット画面の確認ダイアログで許可を出します |
| 認証エラー | `CYNOVELA_TOKEN` 環境変数の値、トークンの有効性 — **トークンは、ログインで期間を渡さないかぎり切れません**。3-3 節のログインの呼び出しで発行し直してください |
| `settings_set` が「書き込みは既定で閉じています」と答える | それは守り（5-4 節）であって故障ではありません。本当に書き込みたいときだけ `mcp.json` の `env` に `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` を足します |
| `delete_item` / `manage_users` / `manage_backups` が一覧に出ない | それは守り（5-5 節）であって故障ではありません。本当に使いたいときだけ `mcp.json` の `env` に `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` を足します |
| ImportError が出る | Python が 3.12 以上か（`mcp_server.py` 自体に外部依存はありません） |
| 結果が空 | 対象 Collection が `ready` ステータスに到達済みか |

---

