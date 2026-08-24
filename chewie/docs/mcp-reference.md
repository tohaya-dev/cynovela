# MCP reference / MCP リファレンス

<!-- DD-CYN-0151 §10: 実物の mcp_server.py の TOOLS からそのまま起こしている。 -->

## English

Cynovela's MCP server offers **25 tools**. This page lists every one of
them: what you hand it, and what comes back.

### Starting it

It speaks over standard input and output. Point your MCP client at:

```
<the folder you extracted>/.condapack-cynovela/bin/python  <the folder you extracted>/mcp_server.py
(source edition: .venv-cynovela/bin/python instead)
```

and give it two settings in its environment:

| Setting | What it is |
|---|---|
| `CYNOVELA_BASE` | where Cynovela is answering, e.g. `http://127.0.0.1:8765` |
| `CYNOVELA_TOKEN` | the token from sign-in (`cynovela-cli login` writes one to `~/.cynovela_cli.env`) |

The protocol version is `2026-07-28`. If your client asks for an older version,
the server answers with the version it does speak — read that answer, do not
assume yours was accepted.

### Tools that are closed unless you open them

Three tools do not even appear in `tools/list` unless the MCP server's environment
has `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`:

* `delete_item`
* `manage_backups`
* `manage_users`

One more tool appears, but refuses to run unless the environment has
`CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1`:

* `settings_set`

So a plain start offers 22 tools, and one of those
will refuse to write until you open it.

### The tools

#### `search_collection`

Ask a question against one collection and get the answer with the fragments it used.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `query` | string | yes | the question |
| `workspace_id` | string | yes | the workspace id |
| `collection_id` | string | yes | the collection id |
| `preset` | string | no | lite / standard / hq (default: standard) |

**It hands back:** `answer`, `sources`, `source_count`

#### `search_across_collections`

Ask the same question against several collections at once and get one merged answer.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `query` | string | yes | the question |
| `workspace_id` | string | yes | the workspace id |
| `collection_ids` | array of string | yes | the collection ids, more than one allowed |
| `preset` | string | no | lite / standard / hq (default: standard) |

**It hands back:** `answer`, `collections_searched`, `sources`, `source_count`

#### `rag_with_role`

Same as search_collection, but the wording of the answer is aimed at an administrator or at a plain reader.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `query` | string | yes | the question |
| `workspace_id` | string | yes | the workspace id |
| `collection_id` | string | yes | the collection id |
| `style_role` | string | yes | admin / reader |
| `preset` | string | no | lite / standard / hq (default: standard) |

**It hands back:** `answer`, `style_role`, `source_count`

#### `rag_general`

Answer from the model's own knowledge, without looking at any document. Nothing is cited.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `query` | string | yes | the question |
| `workspace_id` | string | yes | the workspace id, recorded in the log only |

**It hands back:** `answer`, `rag_used`

#### `list_workspaces`

List the workspaces, and the collections inside each one.

**You hand it:**

(takes nothing)

**It hands back:** `workspaces`

#### `get_workspace_info`

Details of one workspace.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `workspace_id` | string | yes | the workspace id |

**It hands back:** `id`, `name`, `description`, `created_at`, `updated_at`, `guardrail_policy_id`

#### `get_collection_info`

Details of one collection: how many chunks it holds, whether it is published, who may read it.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `workspace_id` | string | yes | the workspace id |
| `collection_id` | string | yes | the collection id |

**It hands back:** `id`, `name`, `status`, `chunk_count`, `access_level`, `created_at`, `allowed_roles`

#### `get_audit_logs`

Recent audit log entries for a workspace.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `workspace_id` | string | yes | the workspace id |
| `limit` | integer | no | how many to return (default 10, at most 50) |

**It hands back:** `logs`, `count`

#### `list_sources`

The folders registered for a workspace, and how many files each holds.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `workspace_id` | string | yes | the workspace id, used to narrow the list |

**It hands back:** `sources`, `count`

#### `publish_collection`

Publish a collection and wait for it to finish.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `collection_id` | string | yes | the collection id |

**It hands back:** `ok`, `collection_id`, `job_id`, `status`, `message`

#### `create_workspace`

Create a workspace.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `name` | string | yes | the name of the workspace |
| `description` | string | no | a description (optional) |

**It hands back:** `ok`, `id`, `name`, `description`

#### `settings_show`

Show one group of settings. API keys read as set / not set, never as values.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `name` | string | no | which group of settings (default: llm) one of `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` |

**It hands back:** `name`, `settings`

#### `settings_models`

The models the configured inference server can see right now.

**You hand it:**

(takes nothing)

**It hands back:** `models`, `count`

#### `settings_test`

Try the connection to the inference server.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `provider` | string | no | a provider to try instead of the saved one (optional) |
| `base_url` | string | no | an endpoint to try instead of the saved one (optional) |
| `model` | string | no | a model to try instead of the saved one (optional) |

**It hands back:** `connected`, `status`, `endpoint`, `models`, `error`

#### `settings_set` — **refuses to write by default** (`CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1`)

Change settings. Closed by default.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `name` | string | no | which group of settings (default: llm) one of `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` |
| `values` | object | yes | the settings to change, e.g. {"model": "..."} |

**It hands back:** `ok`, `name`, `applied`, `after`

#### `settings_providers`

The ready-made provider choices.

**You hand it:**

(takes nothing)

**It hands back:** `providers`, `count`

#### `server_status`

Is Cynovela up, which version, how many collections and chunks.

**You hand it:**

(takes nothing)

**It hands back:** `up`, `version`, `collections`, `total_chunks`

#### `ingest_source`

Register a folder and start scanning it, in one step.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `path` | string | yes | the full path of the folder to take in |
| `name` | string | no | a name for the source (default: the folder name) |
| `workspace_id` | string | no | a workspace to tie it to (optional) |

**It hands back:** `ok`, `source_id`, `job_id`, `steps`

#### `get_job_status`

How far along a scan or a publish is.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `job_id` | string | yes | the job id |

**It hands back:** `kind`, `status`, `stage`, `progress`, `total`, `message`, `error`

#### `cancel_scan`

Ask a running scan to stop.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `source_id` | string | yes | the source id |

**It hands back:** `ok`, `status`

#### `create_collection`

Create a collection inside a workspace.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `workspace_id` | string | yes | the workspace id |
| `name` | string | yes | the name of the collection |
| `source_id` | string | no | tie every file of this source to the new collection (optional) |

**It hands back:** `ok`, `id`, `name`, `linked_files`

#### `publish_control`

Start, stop, check or recover a publish.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `collection_id` | string | yes | the collection id |
| `action` | string | yes | one of `stop` / `recover` |

**It hands back:** `ok`, `action`, `result`

#### `delete_item` — **closed by default** (`CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`)

Delete a source, a collection or a workspace. Closed by default.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `kind` | string | yes | one of `source` / `collection` / `workspace` |
| `id` | string | yes | the id of the thing to delete |

**It hands back:** `ok`, `kind`, `id`

#### `manage_users` — **closed by default** (`CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`)

List, create, change or remove people. Closed by default.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `action` | string | yes | one of `list` / `create` / `update` / `delete` / `reset_password` |
| `user_id` | string | no | who it applies to, for update / delete / reset_password |
| `username` | string | no | the login name, for create |
| `password` | string | no | the password, for create / reset_password (8 characters or more) |
| `role` | string | no | the role, for create / update (admin / viewer) |
| `display_name` | string | no | the display name, for create / update |
| `is_active` | boolean | no | on or off, for update |
| `purge` | boolean | no | on delete, true removes the row for good (default false = only switch the account off). Audit log entries are kept either way. |

**It hands back:** `ok`, `action`, `users`, `result`

#### `manage_backups` — **closed by default** (`CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`)

List, take, restore or delete backups. Closed by default.

**You hand it:**

| Name | Type | Required | What it is |
|---|---|---|---|
| `action` | string | yes | one of `list` / `create` / `restore` / `delete` |
| `name` | string | no | the name of the backup, for restore / delete |
| `label` | string | no | a short label, for create (optional) |

**It hands back:** `ok`, `action`, `backups`, `result`

---

## 日本語

Cynovela の MCP サーバが持つ道具は **25件** です。ここに全部書いてあります。
何を渡すと、何が返るか、という形です。

### 立ち上げ方

標準入力と標準出力でやりとりします。お使いの MCP クライアントに、次を実行させてください。

```
<展開したフォルダ>/.condapack-cynovela/bin/python  <展開したフォルダ>/mcp_server.py
（ソース版の場合: .venv-cynovela/bin/python）
```

そのうえで、環境に次の2つを入れてください。

| 名前 | 何か |
|---|---|
| `CYNOVELA_BASE` | Cynovela が答えている場所。例: `http://127.0.0.1:8765` |
| `CYNOVELA_TOKEN` | ログインで発行されたトークン（`cynovela-cli login` が `~/.cynovela_cli.env` に書きます） |

取り決めの版は `2026-07-28` です。クライアントが古い版を頼んできたときは、
サーバは自分が話せる版を返します。**返ってきた版を読んでください。**
頼んだ版がそのまま通ったものとして進めないでください。

### 既定で閉じている道具

次の3つは、MCP サーバの環境に `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を入れないかぎり、
`tools/list` にも出てきません。

* `delete_item`
* `manage_backups`
* `manage_users`

次の1つは一覧には出ますが、環境に `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` が無いと、
実行そのものを断ります。

* `settings_set`

∴ そのまま立ち上げると使えるのは 22件 で、
そのうち1件は開けるまで書き込みを断ります。

### 道具の一覧

#### `search_collection`

CynovelaのRAGコレクションに対してクエリを実行します。workspace_idとcollection_idはlist_workspacesで取得してください。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `query` | string | 要る | 検索クエリ |
| `workspace_id` | string | 要る | ワークスペースID |
| `collection_id` | string | 要る | コレクションID |
| `preset` | string | 省ける | lite / standard / hq（デフォルト: standard） |

**返るもの:** `answer`、`sources`、`source_count`

#### `search_across_collections`

複数のRAGコレクションを横断してクエリを実行します。collection_idsに複数のIDを渡すと全て検索して統合した結果を返します。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `query` | string | 要る | 検索クエリ |
| `workspace_id` | string | 要る | ワークスペースID |
| `collection_ids` | string の並び | 要る | コレクションIDのリスト（複数指定可） |
| `preset` | string | 省ける | lite / standard / hq（デフォルト: standard） |

**返るもの:** `answer`、`collections_searched`、`sources`、`source_count`

#### `rag_with_role`

ユーザーのロールに応じて回答スタイルを変えてRAG検索を実行します。admin=技術詳細・reader=平易な説明。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `query` | string | 要る | 検索クエリ |
| `workspace_id` | string | 要る | ワークスペースID |
| `collection_id` | string | 要る | コレクションID |
| `style_role` | string | 要る | admin / reader |
| `preset` | string | 省ける | lite / standard / hq（デフォルト: standard） |

**返るもの:** `answer`、`style_role`、`source_count`

#### `rag_general`

RAGを使わずLLMの学習データで直接回答します（一般知識モード）。ワークスペース内のドキュメントを参照しないため、sourcesは空になります。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `query` | string | 要る | 質問 |
| `workspace_id` | string | 要る | ワークスペースID（ログ記録用） |

**返るもの:** `answer`、`rag_used`

#### `list_workspaces`

利用可能なワークスペースとコレクション一覧を返します。search_collectionを呼ぶ前にこのツールでIDを確認してください。

**渡すもの:**

（渡すものはありません）

**返るもの:** `workspaces`

#### `get_workspace_info`

指定ワークスペースの詳細情報（名前・ガードレール設定・作成日時等）を返します。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `workspace_id` | string | 要る | ワークスペースID |

**返るもの:** `id`、`name`、`description`、`created_at`、`updated_at`、`guardrail_policy_id`

#### `get_collection_info`

指定コレクションの詳細情報（ドキュメント数・ステータス・アクセスレベル等）を返します。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `workspace_id` | string | 要る | ワークスペースID |
| `collection_id` | string | 要る | コレクションID |

**返るもの:** `id`、`name`、`status`、`chunk_count`、`access_level`、`created_at`、`allowed_roles`

#### `get_audit_logs`

ワークスペースの直近の監査ログを返します（RAG Chat履歴・PII検出・エラー等）。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `workspace_id` | string | 要る | ワークスペースID |
| `limit` | integer | 省ける | 取得件数（デフォルト10・最大50） |

**返るもの:** `logs`、`count`

#### `list_sources`

登録済みデータソースの一覧を返します（ファイルパス・ステータス・ファイル数等）。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `workspace_id` | string | 要る | ワークスペースID（フィルタ） |

**返るもの:** `sources`、`count`

#### `publish_collection`

指定コレクションのPublish（公開）を始めます。開始した時点で job_id を返してすぐ戻ります (待ちません)。進み具合は get_job_status で job_id を渡して見ます。Publish後はRAG Chatで検索可能になります。既にready状態でも再Publishが可能です。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `collection_id` | string | 要る | コレクションID |

**返るもの:** `ok`、`collection_id`、`job_id`、`status`、`message`

#### `create_workspace`

新しいワークスペースを作成します。作成後にデータソース登録・コレクション作成が必要です。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `name` | string | 要る | ワークスペース名 |
| `description` | string | 省ける | 説明（任意） |

**返るもの:** `ok`、`id`、`name`、`description`

#### `settings_show`

サーバの設定を見ます (管理者のみ)。name で対象を選びます (既定: llm)。APIキーの値は返さず、設定あり/なし (api_key_set) だけを返します。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `name` | string | 省ける | 対象 (既定: llm) `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` のどれか |

**返るもの:** `name`、`settings`

#### `settings_models`

接続先の推論サーバにあるモデルの一覧を出します (管理者のみ)。注意: ダウンロード済み全件であり、読み込み済みを意味しません。

**渡すもの:**

（渡すものはありません）

**返るもの:** `models`、`count`

#### `settings_test`

LLM への接続を確かめ、通ったか通らなかったかを言葉で返します (管理者のみ)。引数を渡すと保存済み設定の代わりにその値で試します。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `provider` | string | 省ける | 試すプロバイダー (任意) |
| `base_url` | string | 省ける | 試す接続先 (任意) |
| `model` | string | 省ける | 試すモデル (任意) |

**返るもの:** `connected`、`status`、`endpoint`、`models`、`error`

#### `settings_set` — **既定では書き込みを断る**（`CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1`）

サーバの設定を変えます (管理者のみ)。この道具は既定で閉じており、MCP サーバの環境変数 CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1 を設定したときだけ実行できます。name で対象を選び (既定: llm)、values に変える項目だけを入れます。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `name` | string | 省ける | 対象 (既定: llm) `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` のどれか |
| `values` | object | 要る | 変える項目と値 (例: {"model": "..."}) |

**返るもの:** `ok`、`name`、`applied`、`after`

#### `settings_providers`

選べる LLM プロバイダーのプリセット一覧を出します (管理者のみ)。

**渡すもの:**

（渡すものはありません）

**返るもの:** `providers`、`count`

#### `server_status`

サーバの稼働と索引の状態を見ます (GET /api/health と、まとまりごとの塊の数)。

**渡すもの:**

（渡すものはありません）

**返るもの:** `up`、`version`、`collections`、`total_chunks`

#### `ingest_source`

資料を入れます: 取り込み元を足し、資料として登録し、走査を始める、を1道具で行います。走査は始めた時点で job_id を返してすぐ戻ります。進み具合は get_job_status で見ます。workspace_id を渡すと、その作業場所へも結び付けます。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `path` | string | 要る | 取り込むフォルダの絶対パス |
| `name` | string | 省ける | 資料の名前 (省略時: フォルダ名) |
| `workspace_id` | string | 省ける | 結び付ける作業場所 (任意) |

**返るもの:** `ok`、`source_id`、`job_id`、`steps`

#### `get_job_status`

走査 (scan) と公開 (publish) の進み具合を見ます。job_id は ingest_source / publish_collection が返した値です。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `job_id` | string | 要る | ジョブID |

**返るもの:** `kind`、`status`、`stage`、`progress`、`total`、`message`、`error`

#### `cancel_scan`

走行中の走査に中止を要求します。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `source_id` | string | 要る | 取り込み元 (source) のID |

**返るもの:** `ok`、`status`

#### `create_collection`

作業場所の中にまとまり (collection) を作ります。source_id を渡すと、その資料の全ファイルを結び付けます (公開は publish_collection で別に始めます)。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `workspace_id` | string | 要る | 作業場所のID |
| `name` | string | 要る | まとまりの名前 |
| `source_id` | string | 省ける | この資料の全ファイルを結び付ける (任意) |

**返るもの:** `ok`、`id`、`name`、`linked_files`

#### `publish_control`

公開 (publish) を止める・固着から復旧する。action に stop か recover を渡します。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `collection_id` | string | 要る | コレクションID |
| `action` | string | 要る | `stop` / `recover` のどれか |

**返るもの:** `ok`、`action`、`result`

#### `delete_item` — **既定で閉**（`CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`）

資料 (source)・まとまり (collection)・作業場所 (workspace) を消します。既定で閉じています: MCP サーバの env に CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を書いたときだけ使えます。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `kind` | string | 要る | `source` / `collection` / `workspace` のどれか |
| `id` | string | 要る | 消す対象のID |

**返るもの:** `ok`、`kind`、`id`

#### `manage_users` — **既定で閉**（`CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`）

利用者を管理します (list / create / update / delete / reset_password)。delete は既定では使えなくするだけです。purge=true で行そのものを消します。既定で閉じています: MCP サーバの env に CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を書いたときだけ使えます。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `action` | string | 要る | `list` / `create` / `update` / `delete` / `reset_password` のどれか |
| `user_id` | string | 省ける | update / delete / reset_password の対象 |
| `username` | string | 省ける | create のログイン名 |
| `password` | string | 省ける | create / reset_password の合言葉 (8文字以上) |
| `role` | string | 省ける | create / update の役割 (admin / viewer) |
| `display_name` | string | 省ける | create / update の表示名 |
| `is_active` | boolean | 省ける | update の有効/無効 |
| `purge` | boolean | 省ける | delete のとき true にすると、行そのものを消します (既定は false = 使えなくするだけ)。監査の記録は残ります。 |

**返るもの:** `ok`、`action`、`users`、`result`

#### `manage_backups` — **既定で閉**（`CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`）

控えを扱います (list / create / restore / delete)。restore はいまのデータを控えの中身に置き換えます。既定で閉じています: MCP サーバの env に CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を書いたときだけ使えます。

**渡すもの:**

| 名前 | 型 | 要る？ | 何か |
|---|---|---|---|
| `action` | string | 要る | `list` / `create` / `restore` / `delete` のどれか |
| `name` | string | 省ける | restore / delete の控えの名前 |
| `label` | string | 省ける | create の短い札 (任意) |

**返るもの:** `ok`、`action`、`backups`、`result`

---

## この一覧の作り方 / How this list was made

`mcp_server.py` の `TOOLS` と `_ADMIN_WRITE_TOOLS` をそのまま読み取って作っています。
The list is read straight out of `TOOLS` and `_ADMIN_WRITE_TOOLS` in `mcp_server.py`.
