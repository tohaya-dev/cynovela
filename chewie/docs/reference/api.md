# API reference / API リファレンス

## English

This lists **every** HTTP endpoint this server answers. It was produced by reading
the route declarations in `routers/*.py`, so it does not contain an endpoint that
does not exist, and it does not leave one out.

Total: **186 endpoints** across **35 router files**.

### How to call one

```
GET http://127.0.0.1:8765/api/health
Authorization: Bearer <your token>
Content-Type: application/json
```

* The port is 8765 unless you started the server with `--port`.
* The token is the one issued at sign-in. `cynovela-cli login` writes it to
  `~/.cynovela_cli.env` for you; the web screen shows it too.
* A token has no expiry unless the caller asked for one (see `/api/auth/login`).
* Bodies are JSON. Answers are JSON, except the export endpoints (a ZIP), the CSV
  endpoints (text), the stream endpoints (server-sent events) and the page
  endpoints (HTML).

### What the answers look like when something is wrong

| Status | Meaning |
|---|---|
| 400 | The body was not what the endpoint expects. |
| 401 | No token, or a token that is not valid any more. |
| 403 | Signed in, but not allowed to do this. |
| 404 | No such workspace / collection / source / file. |
| 409 | It clashes with something that already exists or is already running. |
| 429 | Too many attempts (sign-in is limited to 5 per minute per address). |
| 500 | The server failed. The reason is in `store/logs/server.log`. |

The body of a failure is `{"detail": "..."}`.

### Endpoints worth spelling out

#### `POST /api/auth/login`

```json
{ "username": "cynovela", "password": "...", "expires_in_hours": 8 }
```

`expires_in_hours` (or `expires_in_seconds`) is optional. **Leave it out and the
token never expires.** Pass it and the token stops working after that long.
A number that is zero or below is rejected with 400.

The answer carries `access_token`, `refresh_token`, `role`,
`must_change_password`, and `expires_in` (the number of seconds, or `null` when
the token does not expire).

#### `POST /api/auth/refresh`

```json
{ "refresh_token": "...", "expires_in_hours": 8 }
```

Same rule: no expiry unless you ask for one.

#### `GET /api/workspaces/{id}/full-export`

Returns a ZIP. Administrator only. Inside:

| Name | What it holds |
|---|---|
| `workspace.json` | the workspace row |
| `collections.json` | the collections, each with the ids of the files it holds |
| `sources.json` | the folders those files came from |
| `files.json` | the file records |
| `links.json` | which sources, users and policies the workspace is tied to |
| `guardrail_policies.json` | the policies |
| `vectors/<collection id>.jsonl` | one line per chunk, with its embedding |
| `_meta.json` | the embedding model name, the count, the time |

#### `POST /api/workspaces/import`

Multipart, field name `file`, the ZIP above. Administrator only. Everything is
inserted under **new** ids, so importing into the same server is safe and can be
done twice. The answer is:

```json
{ "ok": true, "workspace_id": "...", "collections": ["..."],
  "include_vectors": true, "restored_vectors": 64,
  "warnings": [], "collection_files": [{"name": "...", "declared": 7, "linked": 7}] }
```

`ok` is **false** when a collection declared file ids but none could be created —
that is, the ZIP's `files.json` was empty. The collection exists but is hollow, so
do not treat that as a success.

#### `DELETE /api/admin/users/{id}` and `?purge=true`

Without `purge`, the account is only switched off (`is_active = 0`) and the row
stays. With `?purge=true` the row is removed for good, along with its workspace
assignments, refresh tokens and sessions. Audit log entries are kept either way.

#### `POST /api/sources`

Rejects with 409 when the folder is already registered, comparing resolved real
paths — so the same folder cannot be registered twice under two names.

#### `POST /api/sources/{id}/scan` and `/scan/async`

Both answer 409 while a scan of that source is already running.

### Signing in — `routers/auth.py` (9)

Signing in, signing out, the token, and the password.

| Method | Path | Who may call it |
|---|---|---|
| `POST` | `/api/auth/change-password` | any signed-in user |
| `POST` | `/api/auth/login` | anyone (no sign-in) |
| `POST` | `/api/auth/logout` | any signed-in user |
| `GET` | `/api/auth/me` | any signed-in user |
| `POST` | `/api/auth/refresh` | anyone (no sign-in) |
| `GET` | `/api/auth/session-config` | administrator |
| `POST` | `/api/auth/session-config` | administrator |
| `GET` | `/api/auth/users` | administrator |
| `POST` | `/api/auth/verify-password` | any signed-in user |

### Workspaces — `routers/workspaces.py` (18)

Create and list workspaces, export one, and bring one back in.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/workspaces` | any signed-in user |
| `POST` | `/api/workspaces` | administrator |
| `GET` | `/api/workspaces/selectable` | any signed-in user |
| `GET` | `/api/workspaces/{workspace_id}/chunks` | any signed-in user |
| `GET` | `/api/workspaces/{workspace_id}/export` | administrator |
| `GET` | `/api/workspaces/{workspace_id}/lineage` | administrator |
| `POST` | `/api/workspaces/{workspace_id}/lineage/diff` | administrator |
| `GET` | `/api/workspaces/{workspace_id}/publish-history` | any signed-in user; some paths need an administrator |
| `DELETE` | `/api/workspaces/{ws_id}` | administrator |
| `GET` | `/api/workspaces/{ws_id}` | administrator |
| `PATCH` | `/api/workspaces/{ws_id}` | administrator |
| `PUT` | `/api/workspaces/{ws_id}` | administrator |
| `PATCH` | `/api/workspaces/{ws_id}/archive` | administrator |
| `PUT` | `/api/workspaces/{ws_id}/policy` | administrator |
| `POST` | `/api/workspaces/{ws_id}/scan` | administrator |
| `GET` | `/api/workspaces/{ws_id}/sync-config` | administrator |
| `PATCH` | `/api/workspaces/{ws_id}/sync-config` | administrator |
| `PATCH` | `/api/workspaces/{ws_id}/unarchive` | administrator |

### Collections — `routers/collections.py` (19)

Collections inside a workspace, the files they hold, and publishing them.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/collections` | any signed-in user |
| `POST` | `/api/collections` | administrator |
| `DELETE` | `/api/collections/{col_id}` | administrator |
| `GET` | `/api/collections/{col_id}` | administrator |
| `PUT` | `/api/collections/{col_id}` | administrator |
| `PATCH` | `/api/collections/{col_id}/archive` | administrator |
| `POST` | `/api/collections/{col_id}/link-files` | administrator |
| `DELETE` | `/api/collections/{col_id}/lock` | administrator |
| `POST` | `/api/collections/{col_id}/lock` | administrator |
| `POST` | `/api/collections/{col_id}/publish` | administrator |
| `GET` | `/api/collections/{col_id}/publish-diff` | administrator |
| `GET` | `/api/collections/{col_id}/publish-summary` | administrator |
| `POST` | `/api/collections/{col_id}/publish/async` | administrator |
| `POST` | `/api/collections/{col_id}/publish/recover` | administrator |
| `POST` | `/api/collections/{col_id}/publish/stop` | administrator |
| `GET` | `/api/collections/{col_id}/publish/stream` | administrator |
| `PATCH` | `/api/collections/{col_id}/unarchive` | administrator |
| `GET` | `/api/collections/{col_id}/unlinked-files` | administrator |
| `GET` | `/api/collections/{collection_id}/provenance` | administrator |

### Sources and folders — `routers/sources.py` (13)

Registered folders, the scan of a folder, and the list of files it found.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/ingest-roots` | administrator |
| `POST` | `/api/ingest-roots` | administrator |
| `GET` | `/api/ingest-roots/browse` | administrator |
| `DELETE` | `/api/ingest-roots/{name}` | administrator |
| `GET` | `/api/sources` | any signed-in user |
| `POST` | `/api/sources` | administrator |
| `DELETE` | `/api/sources/{source_id}` | administrator |
| `GET` | `/api/sources/{source_id}` | administrator |
| `GET` | `/api/sources/{source_id}/files` | administrator |
| `GET` | `/api/sources/{source_id}/open-in-finder` | administrator |
| `POST` | `/api/sources/{source_id}/scan` | administrator |
| `POST` | `/api/sources/{source_id}/scan/async` | administrator |
| `POST` | `/api/sources/{source_id}/scan/cancel` | administrator |

### Files — `routers/files.py` (4)

Looking at one file and at what was learned about it.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/browse` | administrator |
| `PATCH` | `/api/documents/{document_id}/metadata` | any signed-in user |
| `GET` | `/api/files/{file_id}/preview` | anyone (no sign-in) |
| `POST` | `/api/folder-scan-preview` | administrator |

### Asking questions — `routers/chat.py` (9)

Asking a question and getting an answer with its sources.

| Method | Path | Who may call it |
|---|---|---|
| `POST` | `/api/chat` | any signed-in user; some paths need an administrator |
| `POST` | `/api/chat/compare` | administrator |
| `POST` | `/api/chat/compare-collections` | any signed-in user; some paths need an administrator |
| `POST` | `/api/chat/followups` | any signed-in user; some paths need an administrator |
| `POST` | `/api/chat/summarize` | any signed-in user |
| `POST` | `/api/rag/query` | administrator |
| `POST` | `/api/workspaces/import` | administrator |
| `POST` | `/api/workspaces/{workspace_id}/chat/stream` | any signed-in user |
| `GET` | `/api/workspaces/{workspace_id}/full-export` | administrator |

### Agent — `routers/agent.py` (1)

The multi-step answering mode.

| Method | Path | Who may call it |
|---|---|---|
| `POST` | `/api/agent/chat` | administrator |

### Messages — `routers/messages.py` (2)

One message of a conversation, and the thumbs up / down on it.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/messages/{message_id}` | anyone (no sign-in) |
| `POST` | `/api/messages/{message_id}/feedback` | anyone (no sign-in) |

### Conversations — `routers/sessions.py` (5)

The list of conversations and the messages inside one.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/sessions` | any signed-in user |
| `POST` | `/api/sessions` | any signed-in user |
| `DELETE` | `/api/sessions/{session_id}` | any signed-in user |
| `GET` | `/api/sessions/{session_id}` | any signed-in user |
| `GET` | `/api/sessions/{session_id}/messages` | any signed-in user |

### Feedback — `routers/feedback.py` (3)

What people marked as wrong, and the totals.

| Method | Path | Who may call it |
|---|---|---|
| `POST` | `/api/feedback` | administrator |
| `GET` | `/api/feedback/negatives` | administrator |
| `GET` | `/api/feedback/stats` | administrator |

### Settings — `routers/settings.py` (23)

Every setting the server keeps: the LLM, the embedding, masking, the vector store.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/settings` | administrator |
| `PUT` | `/api/settings` | administrator |
| `GET` | `/api/settings/classifier` | administrator |
| `POST` | `/api/settings/classifier` | administrator |
| `GET` | `/api/settings/datasync` | administrator |
| `POST` | `/api/settings/datasync` | administrator |
| `GET` | `/api/settings/embedding` | administrator |
| `POST` | `/api/settings/embedding` | administrator |
| `GET` | `/api/settings/llm` | administrator |
| `POST` | `/api/settings/llm` | administrator |
| `GET` | `/api/settings/models` | administrator |
| `GET` | `/api/settings/pii-mode` | administrator |
| `PUT` | `/api/settings/pii-mode` | administrator |
| `GET` | `/api/settings/presets` | administrator |
| `GET` | `/api/settings/remote-access` | administrator |
| `GET` | `/api/settings/reranker` | administrator |
| `POST` | `/api/settings/reranker` | administrator |
| `POST` | `/api/settings/reranker/test` | administrator |
| `GET` | `/api/settings/system-prompt` | administrator |
| `POST` | `/api/settings/system-prompt` | administrator |
| `POST` | `/api/settings/test-connection` | administrator |
| `GET` | `/api/settings/vector-store` | administrator |
| `POST` | `/api/settings/vector-store` | administrator |

### LLM connection — `routers/llm.py` (4)

The endpoint, the presets, and the list of models it can see.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/llm/context-length` | administrator |
| `POST` | `/api/llm/list-models` | any signed-in user |
| `GET` | `/api/llm/presets` | administrator |
| `PUT` | `/api/llm/providers` | administrator |

### LM Studio — `routers/lmstudio.py` (2)

Talking to LM Studio directly.

| Method | Path | Who may call it |
|---|---|---|
| `POST` | `/api/lmstudio/load` | administrator |
| `GET` | `/api/lmstudio/models` | administrator |

### Models — `routers/models.py` (1)

The models this server itself loads.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/models` | administrator |

### How answers are built — `routers/pipeline_config.py` (7)

Chunk sizes, execution options and the saved presets.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/chunking-config` | administrator |
| `PATCH` | `/api/chunking-config` | administrator |
| `GET` | `/api/execution-config` | administrator |
| `PATCH` | `/api/execution-config` | administrator |
| `GET` | `/api/pipeline-presets` | administrator |
| `POST` | `/api/pipeline-presets` | administrator |
| `DELETE` | `/api/pipeline-presets/{preset_id}` | administrator |

### Guardrails — `routers/guardrails.py` (5)

Blocked topics and what personal data was detected.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/guardrails/blocked-topics` | any signed-in user |
| `POST` | `/api/guardrails/blocked-topics` | administrator |
| `DELETE` | `/api/guardrails/blocked-topics/{topic_id}` | administrator |
| `GET` | `/api/guardrails/pii-detections` | administrator |
| `GET` | `/api/pii-detections` | administrator |

### Policies — `routers/policies.py` (8)

The rules, and the matrix that states who may see what.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/compliance-report.csv` | administrator |
| `GET` | `/api/guardrails/policies` | anyone (no sign-in) |
| `GET` | `/api/policies` | administrator |
| `POST` | `/api/policies` | administrator |
| `DELETE` | `/api/policies/{policy_id}` | administrator |
| `PUT` | `/api/policies/{policy_id}` | administrator |
| `GET` | `/api/policy-matrix` | administrator |
| `PUT` | `/api/policy-matrix` | administrator |

### Compliance — `routers/compliance.py` (3)

The checklist and its report.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/classification/categories` | administrator |
| `GET` | `/api/compliance/checklist` | administrator |
| `GET` | `/api/compliance/report` | administrator |

### Catalogue — `routers/catalog.py` (3)

A flat list of everything registered.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/catalog` | any signed-in user |
| `GET` | `/api/data-catalog` | any signed-in user |
| `GET` | `/api/data-catalog/export` | administrator |

### Administration — `routers/admin.py` (16)

People, backups, exports and housekeeping.

| Method | Path | Who may call it |
|---|---|---|
| `POST` | `/api/admin/backup` | administrator |
| `GET` | `/api/admin/backups` | administrator |
| `DELETE` | `/api/admin/backups/{name}` | administrator |
| `POST` | `/api/admin/backups/{name}/restore` | administrator |
| `GET` | `/api/admin/change-log` | administrator |
| `POST` | `/api/admin/cleanup/chromadb-orphans` | administrator |
| `POST` | `/api/admin/export` | administrator |
| `GET` | `/api/admin/export/csv` | administrator |
| `POST` | `/api/admin/maintenance/vacuum` | administrator |
| `GET` | `/api/admin/processing-logs` | administrator |
| `GET` | `/api/admin/storage-info` | administrator |
| `GET` | `/api/admin/users` | administrator |
| `POST` | `/api/admin/users` | administrator |
| `DELETE` | `/api/admin/users/{user_id}` | administrator |
| `PATCH` | `/api/admin/users/{user_id}` | administrator |
| `POST` | `/api/admin/users/{user_id}/reset-password` | administrator |

### One user — `routers/users.py` (1)

Changing one user.

| Method | Path | Who may call it |
|---|---|---|
| `PATCH` | `/api/users/{user_id}` | anyone (no sign-in) |

### Audit log — `routers/audit_logs.py` (2)

Who did what, and a CSV of it.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/audit-logs` | administrator |
| `GET` | `/api/audit-logs/export` | administrator |

### Archive — `routers/archived.py` (4)

Putting something aside and bringing it back.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/archived` | administrator |
| `DELETE` | `/api/archived/{kind}/{item_id}` | administrator |
| `POST` | `/api/archived/{kind}/{item_id}/archive` | administrator |
| `POST` | `/api/archived/{kind}/{item_id}/restore` | administrator |

### Jobs — `routers/jobs.py` (1)

The progress of a scan or a publish.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/jobs/{job_id}` | administrator |

### Health — `routers/health.py` (6)

Is the server up, is the database there, is the index there.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/health` | anyone (no sign-in) |
| `GET` | `/api/health/db` | anyone (no sign-in) |
| `GET` | `/api/health/detailed` | administrator |
| `GET` | `/api/health/guardrails` | anyone (no sign-in) |
| `GET` | `/api/health/vector` | anyone (no sign-in) |
| `GET` | `/api/ready` | anyone (no sign-in) |

### Numbers — `routers/stats.py` (3)

Speed, model use and answer quality.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/stats/model` | administrator |
| `GET` | `/api/stats/performance` | administrator |
| `GET` | `/api/stats/rag-quality` | administrator |

### Dashboard — `routers/dashboard.py` (1)

The summary the first screen shows.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/dashboard/summary` | any signed-in user |

### Reports — `routers/reports.py` (3)

Generated reports.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/reports` | anyone (no sign-in) |
| `POST` | `/api/reports/generate` | anyone (no sign-in) |
| `GET` | `/api/reports/{report_id}` | anyone (no sign-in) |

### Cost — `routers/cost.py` (1)

An estimate of what a question costs.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/cost/estimate` | any signed-in user |

### Alerts — `routers/alerts.py` (1)

Things the server wants to tell you about.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/alerts` | administrator |

### Features — `routers/features.py` (2)

Which optional parts are switched on.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/features` | administrator |
| `PATCH` | `/api/features` | administrator |

### Mode — `routers/mode.py` (1)

Production or demo.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/mode` | any signed-in user |

### MCP — `routers/mcp.py` (2)

The MCP configuration and a connection test.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/mcp/config` | administrator |
| `GET` | `/api/mcp/test-connection` | administrator |

### Demo — `routers/demo.py` (1)

The demo-only role switch.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/api/demo/role-switch` | any signed-in user |

### Web pages — `routers/pages.py` (2)

The HTML the browser loads.

| Method | Path | Who may call it |
|---|---|---|
| `GET` | `/` | anyone (no sign-in) |
| `GET` | `/chat-popup` | anyone (no sign-in) |

---

## 日本語

このサーバが答える口を**全部**並べたものです。`routers/*.py` の宣言をそのまま読み取って
作っているので、実在しない口は入っていませんし、抜けもありません。

合計 **186件**（`routers/*.py` は **35ファイル**）。

### 叩き方

```
GET http://127.0.0.1:8765/api/health
Authorization: Bearer <あなたのトークン>
Content-Type: application/json
```

* 番号は 8765 です（起動のときに `--port` を付けたなら、その番号）。
* トークンはログインで発行された値です。`cynovela-cli login` が
  `~/.cynovela_cli.env` に書きます。画面のログインでも出ます。
* トークンには期限がありません（呼ぶ側が期間を渡したときだけ切れます。`/api/auth/login` を参照）。
* 本文は JSON です。返るものも JSON です。ただし書き出しの口は ZIP、CSV の口は文字、
  流し込みの口は server-sent events、画面の口は HTML を返します。

### うまくいかなかったときに返るもの

| 番号 | 意味 |
|---|---|
| 400 | 本文がその口の求める形ではありません。 |
| 401 | トークンが無いか、もう使えません。 |
| 403 | ログインはしているが、その操作は許されていません。 |
| 404 | その作業場所・まとまり・取り込み元・資料がありません。 |
| 409 | 既に在るもの、または既に走っているものとぶつかります。 |
| 429 | 試しすぎです（ログインは 1分あたり 5回まで・接続元ごと）。 |
| 500 | サーバ側で失敗しました。理由は `store/logs/server.log` にあります。 |

失敗の本文は `{"detail": "…"}` の形です。

### 細かく書いておく口

#### `POST /api/auth/login`

```json
{ "username": "cynovela", "password": "…", "expires_in_hours": 8 }
```

`expires_in_hours`（または `expires_in_seconds`）は省けます。**省くとトークンに期限はつきません。**
渡すと、その長さで使えなくなります。0 以下の数は 400 で拒否されます。

返るものは `access_token`・`refresh_token`・`role`・`must_change_password`、そして
`expires_in`（秒数。期限が無いときは `null`）です。

#### `POST /api/auth/refresh`

```json
{ "refresh_token": "…", "expires_in_hours": 8 }
```

同じ決まりです。渡さなければ期限はつきません。

#### `GET /api/workspaces/{id}/full-export`

ZIP が返ります。管理者だけです。中身は次のとおりです。

| 名前 | 中身 |
|---|---|
| `workspace.json` | 作業場所の1行 |
| `collections.json` | まとまりと、それが持つ資料の番号 |
| `sources.json` | その資料の出どころのフォルダ |
| `files.json` | 資料の記述 |
| `links.json` | 作業場所に結ばれた取り込み元・利用者・決まりごと |
| `guardrail_policies.json` | 決まりごとの中身 |
| `vectors/<まとまりの番号>.jsonl` | 塊1つに1行。埋め込みの数値つき |
| `_meta.json` | 埋め込みモデルの名前・件数・書き出した時刻 |

#### `POST /api/workspaces/import`

multipart で、欄の名前は `file`、中身は上の ZIP です。管理者だけです。
持ち込むものには**すべて新しい番号**を振り直すので、同じサーバへ取り込んでも
ぶつかりませんし、2回続けて取り込んでも失敗しません。返るものは次のとおりです。

```json
{ "ok": true, "workspace_id": "…", "collections": ["…"],
  "include_vectors": true, "restored_vectors": 64,
  "warnings": [], "collection_files": [{"name": "…", "declared": 7, "linked": 7}] }
```

まとまりが資料の番号を持っているのに、資料が1つも作れなかったときは `ok` が **false** になります。
書き出し物の `files.json` が空だった、ということです。まとまりは出来ていても中身が空なので、
成功として扱わないでください。

#### `DELETE /api/admin/users/{id}` と `?purge=true`

`purge` を付けないと、使えなくするだけ（`is_active = 0`）で行は残ります。
`?purge=true` を付けると行そのものを消し、作業場所の割り当て・リフレッシュトークン・
入室の記録も一緒に消えます。監査の記録はどちらの場合も残ります。

#### `POST /api/sources`

同じフォルダが既に登録されているときは 409 で拒否されます。見分けは実体のパスで行うので、
名前を変えて同じフォルダを二重に登録することはできません。

#### `POST /api/sources/{id}/scan` と `/scan/async`

その取り込み元の走査が既に走っている間は、どちらも 409 を返します。

### サインイン — `routers/auth.py`（9件）

ログイン・ログアウト・トークン・パスワード。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `POST` | `/api/auth/change-password` | 利用者（管理者・閲覧者のいずれか） | Batch-B S1-1: ログイン済みユーザーが自分のパスワードを変更する。current_password 検証必須。 |
| `POST` | `/api/auth/login` | 認証なしで通る | ログイン: username + password で password_hash 検証し新規セッション発行。 |
| `POST` | `/api/auth/logout` | 利用者（管理者・閲覧者のいずれか） | 認証必須化 (未認証 logout は意味なし、401 で reject). |
| `GET` | `/api/auth/me` | 利用者（管理者・閲覧者のいずれか） |  |
| `POST` | `/api/auth/refresh` | 認証なしで通る | Batch-B S1-3: リフレッシュトークンで新しいアクセストークンを発行する。 |
| `GET` | `/api/auth/session-config` | 管理者 | PHASE AUTH-1: セッション持続時間設定を返す。 |
| `POST` | `/api/auth/session-config` | 管理者 | PHASE AUTH-1: セッション持続時間設定を更新する。 |
| `GET` | `/api/auth/users` | 管理者 |  |
| `POST` | `/api/auth/verify-password` | 利用者（管理者・閲覧者のいずれか） | Batch-B S1-3: パスワードを検証する（ロック画面解除用）。トークンは発行しない。 |

### 作業場所 — `routers/workspaces.py`（18件）

作業場所を作る・並べる・書き出す・取り込む。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/workspaces` | 利用者（管理者・閲覧者のいずれか） | List workspaces. |
| `POST` | `/api/workspaces` | 管理者 |  |
| `GET` | `/api/workspaces/selectable` | 利用者（管理者・閲覧者のいずれか） | RAGChat WS選択用軽量エンドポイント。 |
| `GET` | `/api/workspaces/{workspace_id}/chunks` | 利用者（管理者・閲覧者のいずれか） | Workspace内のチャンク一覧をメタデータ付きで返す。 |
| `GET` | `/api/workspaces/{workspace_id}/export` | 管理者 | Workspace 配下の Collection / Guardrail / Source 設定を ZIP で返す。 |
| `GET` | `/api/workspaces/{workspace_id}/lineage` | 管理者 | Workspace 配下の document_lineage 一覧を返す (updated_at DESC)。 |
| `POST` | `/api/workspaces/{workspace_id}/lineage/diff` | 管理者 | body.file_hashes ({path: sha256}) を受け取り new/changed/unchanged を返す。 |
| `GET` | `/api/workspaces/{workspace_id}/publish-history` | 利用者（管理者・閲覧者のいずれか）・管理者 | Workspace のPublish履歴を新しい順で返す。 |
| `DELETE` | `/api/workspaces/{ws_id}` | 管理者 |  |
| `GET` | `/api/workspaces/{ws_id}` | 管理者 | PHASE 0-C: Workspace 単体取得 |
| `PATCH` | `/api/workspaces/{ws_id}` | 管理者 | workspace の name / description / sync_config を更新する。 |
| `PUT` | `/api/workspaces/{ws_id}` | 管理者 |  |
| `PATCH` | `/api/workspaces/{ws_id}/archive` | 管理者 |  |
| `PUT` | `/api/workspaces/{ws_id}/policy` | 管理者 |  |
| `POST` | `/api/workspaces/{ws_id}/scan` | 管理者 | workspace に紐づく全 source をまとめて scan する。 |
| `GET` | `/api/workspaces/{ws_id}/sync-config` | 管理者 | workspace のポーリング設定を返す。 |
| `PATCH` | `/api/workspaces/{ws_id}/sync-config` | 管理者 | workspace のポーリング設定だけを更新する。 |
| `PATCH` | `/api/workspaces/{ws_id}/unarchive` | 管理者 |  |

### まとまり — `routers/collections.py`（19件）

作業場所の中のまとまり、それが持つ資料、そして公開。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/collections` | 利用者（管理者・閲覧者のいずれか） | UX-4: include_archived=true でアーカイブ済み Collection も返す. |
| `POST` | `/api/collections` | 管理者 |  |
| `DELETE` | `/api/collections/{col_id}` | 管理者 |  |
| `GET` | `/api/collections/{col_id}` | 管理者 | PHASE 0-C: Collection 単体取得 |
| `PUT` | `/api/collections/{col_id}` | 管理者 |  |
| `PATCH` | `/api/collections/{col_id}/archive` | 管理者 |  |
| `POST` | `/api/collections/{col_id}/link-files` | 管理者 |  |
| `DELETE` | `/api/collections/{col_id}/lock` | 管理者 | PHASE UX-3: コレクションロック解放。 |
| `POST` | `/api/collections/{col_id}/lock` | 管理者 | PHASE UX-3: Publish 同時実行防止のためのコレクションロック取得。 |
| `POST` | `/api/collections/{col_id}/publish` | 管理者 |  |
| `GET` | `/api/collections/{col_id}/publish-diff` | 管理者 | PORTABILITY FIX 20260527 Stage2 D-1: 再 Publish 前の差分チェック。 |
| `GET` | `/api/collections/{col_id}/publish-summary` | 管理者 | v3.5.0 Phase2 (完了ログ用): masked tier の chunks.pii_summary を集計して |
| `POST` | `/api/collections/{col_id}/publish/async` | 管理者 | 非同期 Publish: job_id を発行して即座に返す。 |
| `POST` | `/api/collections/{col_id}/publish/recover` | 管理者 | Phase 0c B-2(i): "publishing" で固着した Collection を draft に戻す。 |
| `POST` | `/api/collections/{col_id}/publish/stop` | 管理者 | P2-C: 進行中のPublishに停止フラグを立てる。 |
| `GET` | `/api/collections/{col_id}/publish/stream` | 管理者 | SSEでPublish進捗をリアルタイム配信する。 |
| `PATCH` | `/api/collections/{col_id}/unarchive` | 管理者 |  |
| `GET` | `/api/collections/{col_id}/unlinked-files` | 管理者 |  |
| `GET` | `/api/collections/{collection_id}/provenance` | 管理者 | Collection の Provenance 履歴を返す (filename, version 降順). |

### 取り込み元とフォルダ — `routers/sources.py`（13件）

登録したフォルダ、その走査、見つかった資料の一覧。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/ingest-roots` | 管理者 | いま足してある取り込み元の一覧 (管理者のみ)。 |
| `POST` | `/api/ingest-roots` | 管理者 | 取り込み元を1件足す (管理者のみ・1回に1件だけ)。 |
| `GET` | `/api/ingest-roots/browse` | 管理者 | 新しいルートを選ぶためのフォルダ辿り (管理者のみ・フォルダ名だけを返す)。 |
| `DELETE` | `/api/ingest-roots/{name}` | 管理者 | 取り込み元を1件外す (管理者のみ)。原本には触らない。 |
| `GET` | `/api/sources` | 利用者（管理者・閲覧者のいずれか） | archived_at IS NULL のもののみ返す。 |
| `POST` | `/api/sources` | 管理者 |  |
| `DELETE` | `/api/sources/{source_id}` | 管理者 | source 削除: DB 行とチャンクを削除する。 |
| `GET` | `/api/sources/{source_id}` | 管理者 |  |
| `GET` | `/api/sources/{source_id}/files` | 管理者 |  |
| `GET` | `/api/sources/{source_id}/open-in-finder` | 管理者 | Open the source path in OS file manager (macOS Finder / Windows Explorer / Linux xdg-open). |
| `POST` | `/api/sources/{source_id}/scan` | 管理者 |  |
| `POST` | `/api/sources/{source_id}/scan/async` | 管理者 | scan を「開始だけを返す口」で始める (publish/async と同じ形)。 |
| `POST` | `/api/sources/{source_id}/scan/cancel` | 管理者 | 進行中のスキャンに停止フラグをセットする。 |

### 資料 — `routers/files.py`（4件）

1つの資料と、その資料について分かったことを見る。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/browse` | 管理者 | Task 5: フォルダブラウザ。指定パス配下のサブフォルダ一覧を返す。 |
| `PATCH` | `/api/documents/{document_id}/metadata` | 利用者（管理者・閲覧者のいずれか） | ビジネスメタデータ + 自動分類を更新. |
| `GET` | `/api/files/{file_id}/preview` | 認証なしで通る | ファイルプレビュー（先頭2000文字） |
| `POST` | `/api/folder-scan-preview` | 管理者 | PHASE M-3: 指定フォルダを再帰スキャンし、拡張子別件数と推定処理時間を返す。 |

### 質問する — `routers/chat.py`（9件）

質問して、答えと出典を受け取る。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `POST` | `/api/chat` | 利用者（管理者・閲覧者のいずれか）・管理者 |  |
| `POST` | `/api/chat/compare` | 管理者 | P6-E: 同じ質問・同じチャンクを2モデルに並列送信し、両方の回答を返す. |
| `POST` | `/api/chat/compare-collections` | 利用者（管理者・閲覧者のいずれか）・管理者 | 2 つの Collection に同じ質問を並列投入 → 左右に並べて返す. |
| `POST` | `/api/chat/followups` | 利用者（管理者・閲覧者のいずれか）・管理者 | 直前の回答からフォローアップ質問を3件生成して返す (LLM生成、JSON抽出)。 |
| `POST` | `/api/chat/summarize` | 利用者（管理者・閲覧者のいずれか） | chat 履歴のサマリーを LLM で生成 (引き継ぎ用). |
| `POST` | `/api/rag/query` | 管理者 | fix061 A1: 軽量 RAG クエリ EP。query + workspace_id 必須。 |
| `POST` | `/api/workspaces/import` | 管理者 | ZIP をインポートして Workspace / Collection / 関連設定を復元する。 |
| `POST` | `/api/workspaces/{workspace_id}/chat/stream` | 利用者（管理者・閲覧者のいずれか） |  |
| `GET` | `/api/workspaces/{workspace_id}/full-export` | 管理者 | ベクター込みのフルエクスポート。 |

### エージェント — `routers/agent.py`（1件）

段を踏んで答える形。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `POST` | `/api/agent/chat` | 管理者 | Agentic RAG エンドポイント。 |

### やりとり — `routers/messages.py`（2件）

会話の1件と、その良し悪しの評価。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/messages/{message_id}` | 認証なしで通る | メッセージとそのRAG参照を取得する。 |
| `POST` | `/api/messages/{message_id}/feedback` | 認証なしで通る | RAG Chat の回答に 👍 / 👎 のフィードバックを保存する。 |

### 会話 — `routers/sessions.py`（5件）

会話の一覧と、その中のやりとり。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/sessions` | 利用者（管理者・閲覧者のいずれか） | セッション一覧。workspace_id 指定で絞り込み。 |
| `POST` | `/api/sessions` | 利用者（管理者・閲覧者のいずれか） | 新規セッションを作成する。session_id を返す。 |
| `DELETE` | `/api/sessions/{session_id}` | 利用者（管理者・閲覧者のいずれか） | セッション + 関連メッセージ + RAG参照 を削除する。 |
| `GET` | `/api/sessions/{session_id}` | 利用者（管理者・閲覧者のいずれか） | セッションのメッセージ一覧を返す。 |
| `GET` | `/api/sessions/{session_id}/messages` | 利用者（管理者・閲覧者のいずれか） | セッション内のメッセージ一覧 (created_at 昇順)。 |

### 良し悪しの評価 — `routers/feedback.py`（3件）

誤りとして評価が付いたものと、その集計。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `POST` | `/api/feedback` | 管理者 | PHASE F-1: 👍/👎 フィードバックを記録する。 |
| `GET` | `/api/feedback/negatives` | 管理者 | PHASE F-2: 👎 (rating=-1) のフィードバック一覧をページネーションで返す。 |
| `GET` | `/api/feedback/stats` | 管理者 | PHASE F-1/F-2: フィードバック集計を返す。 |

### 設定 — `routers/settings.py`（23件）

サーバが持つ設定の全部: LLM・埋め込み・伏字・ベクターの置き場。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/settings` | 管理者 |  |
| `PUT` | `/api/settings` | 管理者 |  |
| `GET` | `/api/settings/classifier` | 管理者 | admin 限定. |
| `POST` | `/api/settings/classifier` | 管理者 |  |
| `GET` | `/api/settings/datasync` | 管理者 |  |
| `POST` | `/api/settings/datasync` | 管理者 |  |
| `GET` | `/api/settings/embedding` | 管理者 | 現在のEmbedding Provider設定を返す。 |
| `POST` | `/api/settings/embedding` | 管理者 |  |
| `GET` | `/api/settings/llm` | 管理者 | 現在のLLM設定を返す。api_key は値ではなく is_set フラグのみ。 |
| `POST` | `/api/settings/llm` | 管理者 | LLM設定を動的更新。api_key はフォーム入力のみ (このセッションのRAM上の adapter に保持し、 |
| `GET` | `/api/settings/models` | 管理者 |  |
| `GET` | `/api/settings/pii-mode` | 管理者 | admin 限定. |
| `PUT` | `/api/settings/pii-mode` | 管理者 |  |
| `GET` | `/api/settings/presets` | 管理者 | PHASE S-1: 推奨プリセット定義を返す (フロントエンド ドロップダウン用)。 |
| `GET` | `/api/settings/remote-access` | 管理者 | PHASE B-1: 現在のバインドアドレス・ポート・TailScale IP・許可サブネットを返す。 |
| `GET` | `/api/settings/reranker` | 管理者 |  |
| `POST` | `/api/settings/reranker` | 管理者 |  |
| `POST` | `/api/settings/reranker/test` | 管理者 | admin 限定. |
| `GET` | `/api/settings/system-prompt` | 管理者 |  |
| `POST` | `/api/settings/system-prompt` | 管理者 |  |
| `POST` | `/api/settings/test-connection` | 管理者 |  |
| `GET` | `/api/settings/vector-store` | 管理者 |  |
| `POST` | `/api/settings/vector-store` | 管理者 |  |

### LLM への接続 — `routers/llm.py`（4件）

宛先・ひな型・向こうに見えているモデルの一覧。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/llm/context-length` | 管理者 | #09 Step B/E: 現在の LLM のコンテキスト長を返す。 |
| `POST` | `/api/llm/list-models` | 利用者（管理者・閲覧者のいずれか） | #06: 許可済みローカルエンドポイントからモデル一覧を取得する。 |
| `GET` | `/api/llm/presets` | 管理者 | P6-E: 比較・切替用のLLMプリセット一覧を返す。 |
| `PUT` | `/api/llm/providers` | 管理者 | ユーザー登録のLLMプロバイダー一覧をDB settings.llm.providers に保存する。 |

### LM Studio — `routers/lmstudio.py`（2件）

LM Studio に直接ものを聞く口。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `POST` | `/api/lmstudio/load` | 管理者 | 指定したモデルを LM Studio にロードする。 |
| `GET` | `/api/lmstudio/models` | 管理者 | LM Studio から利用可能 (ロード済み) モデル一覧を取得する。 |

### モデル — `routers/models.py`（1件）

このサーバ自身が読み込むモデル。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/models` | 管理者 | PHASE X-4: 全 LLM プロバイダーのモデル一覧をマージして返す。 |

### 答えの組み立て方 — `routers/pipeline_config.py`（7件）

塊の大きさ・走らせ方・保存したひな型。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/chunking-config` | 管理者 | フェーズ2: Contextual Chunking 設定の取得。 |
| `PATCH` | `/api/chunking-config` | 管理者 | フェーズ2: Contextual Chunking ON/OFF をDBに保存し、ランタイムに即反映する。 |
| `GET` | `/api/execution-config` | 管理者 | 実行モード設定を返す。APIキー類はマスクする。 |
| `PATCH` | `/api/execution-config` | 管理者 | 実行モード設定を更新する。 |
| `GET` | `/api/pipeline-presets` | 管理者 | PHASE UX-1: パイプラインプリセット一覧 (組み込み + ユーザー定義)。 |
| `POST` | `/api/pipeline-presets` | 管理者 | PHASE UX-1: ユーザープリセットを保存する。 |
| `DELETE` | `/api/pipeline-presets/{preset_id}` | 管理者 | PHASE UX-1: ユーザープリセット削除 (組み込みは削除不可)。 |

### ガードレール — `routers/guardrails.py`（5件）

止める話題と、見つかった個人情報。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/guardrails/blocked-topics` | 利用者（管理者・閲覧者のいずれか） | 登録済み禁止トピック一覧. |
| `POST` | `/api/guardrails/blocked-topics` | 管理者 | 禁止トピックを追加 (admin のみ). |
| `DELETE` | `/api/guardrails/blocked-topics/{topic_id}` | 管理者 |  |
| `GET` | `/api/guardrails/pii-detections` | 管理者 | audit_logs から PII 検出ログを集計して返す. |
| `GET` | `/api/pii-detections` | 管理者 | PII検出済みチャンクをドキュメント単位で集計して返す。 |

### 決まりごと — `routers/policies.py`（8件）

規則と、誰が何を見てよいかの表。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/compliance-report.csv` | 管理者 | P5-C: コンプライアンスレポートCSVエクスポート。 |
| `GET` | `/api/guardrails/policies` | 認証なしで通る | fix061 A6: /api/policies の alias ( E2E 経路維持)。 |
| `GET` | `/api/policies` | 管理者 | BETA-pagination: limit/offset/q でページネーション・検索を有効化。 |
| `POST` | `/api/policies` | 管理者 |  |
| `DELETE` | `/api/policies/{policy_id}` | 管理者 |  |
| `PUT` | `/api/policies/{policy_id}` | 管理者 |  |
| `GET` | `/api/policy-matrix` | 管理者 | P5-C: ロール × PII種別 → action のマトリクスを返す。 |
| `PUT` | `/api/policy-matrix` | 管理者 | P5-C: マトリクス全体を保存する。 |

### 点検 — `routers/compliance.py`（3件）

点検の項目と、その報告。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/classification/categories` | 管理者 | S-4 (Smart Ingestion): 利用可能な 14 カテゴリ一覧を返す。 |
| `GET` | `/api/compliance/checklist` | 管理者 | Return runtime compliance status checks. |
| `GET` | `/api/compliance/report` | 管理者 | コンプライアンスレポートをHTML形式で返す。ブラウザで window.print() → PDF保存。 |

### 目録 — `routers/catalog.py`（3件）

登録されているものを平らに並べた一覧。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/catalog` | 利用者（管理者・閲覧者のいずれか） | 全データアセット横断ビュー。 |
| `GET` | `/api/data-catalog` | 利用者（管理者・閲覧者のいずれか） | P5-B: 全ドキュメント横断のデータカタログ。 |
| `GET` | `/api/data-catalog/export` | 管理者 |  |

### 管理 — `routers/admin.py`（16件）

利用者・控え・書き出し・後片づけ。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `POST` | `/api/admin/backup` | 管理者 |  |
| `GET` | `/api/admin/backups` | 管理者 | BETA-pagination: limit/offset でページネーション。 |
| `DELETE` | `/api/admin/backups/{name}` | 管理者 |  |
| `POST` | `/api/admin/backups/{name}/restore` | 管理者 |  |
| `GET` | `/api/admin/change-log` | 管理者 | 管理変更ログ一覧 (admin のみ). |
| `POST` | `/api/admin/cleanup/chromadb-orphans` | 管理者 | PHASE X-5-2: ChromaDB の孤立エントリを削除（Stage-2G-2 HIGH-2 で二重チェック化）。 |
| `POST` | `/api/admin/export` | 管理者 | PHASE X-1: 完全バックアップ tar.gz を生成して返す。 |
| `GET` | `/api/admin/export/csv` | 管理者 | PHASE X-1 追記: 個別データを CSV/JSON でダウンロード。 |
| `POST` | `/api/admin/maintenance/vacuum` | 管理者 | PHASE X-5-3: SQLite VACUUM を実行してファイル最適化する。 |
| `GET` | `/api/admin/processing-logs` | 管理者 | PHASE B-4: 直近 N 件の処理ログを返す (管理者向け)。 |
| `GET` | `/api/admin/storage-info` | 管理者 | PHASE X-5-1 / PHASE 0-B: ストレージ使用量を返す。 |
| `GET` | `/api/admin/users` | 管理者 |  |
| `POST` | `/api/admin/users` | 管理者 |  |
| `DELETE` | `/api/admin/users/{user_id}` | 管理者 | 既定は論理削除（is_active=0）。`?purge=true` を付けたときだけ完全に消す。 |
| `PATCH` | `/api/admin/users/{user_id}` | 管理者 |  |
| `POST` | `/api/admin/users/{user_id}/reset-password` | 管理者 |  |

### 利用者1件 — `routers/users.py`（1件）

利用者を1件変える。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `PATCH` | `/api/users/{user_id}` | 認証なしで通る |  |

### 監査の記録 — `routers/audit_logs.py`（2件）

誰が何をしたか、とその CSV。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/audit-logs` | 管理者 | BETA-pagination: q (キーワード), category, workspace_id, offset を追加。 |
| `GET` | `/api/audit-logs/export` | 管理者 | Export entire audit_logs as CSV. Admin role required. |

### 保管 — `routers/archived.py`（4件）

脇へ置く・戻す。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/archived` | 管理者 | アーカイブ済みアイテムをまとめて返す。 |
| `DELETE` | `/api/archived/{kind}/{item_id}` | 管理者 | アーカイブ済みアイテムを完全削除する。既存DELETE経路に委譲して chunk/Chroma も掃除。 |
| `POST` | `/api/archived/{kind}/{item_id}/archive` | 管理者 | 指定アイテムを論理削除（archived_at にタイムスタンプを書き込む）。 |
| `POST` | `/api/archived/{kind}/{item_id}/restore` | 管理者 | アーカイブ済みアイテムを復元する。 |

### 仕事の進み具合 — `routers/jobs.py`（1件）

走査や公開の進み具合。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/jobs/{job_id}` | 管理者 | publish_jobs → scan_jobs の順に job の現在状態を返す。見つからなければ 404。 |

### 生死と体調 — `routers/health.py`（6件）

サーバが起きているか・データベースが在るか・索引が在るか。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/health` | 認証なしで通る |  |
| `GET` | `/api/health/db` | 認証なしで通る |  |
| `GET` | `/api/health/detailed` | 管理者 | 全Providerの状態 + システム（DB/Chroma/Stale）を一括返却。 |
| `GET` | `/api/health/guardrails` | 認証なしで通る | Guardrail Policy が active で 1 件以上あるかをチェック。 |
| `GET` | `/api/health/vector` | 認証なしで通る | ChromaDB 疎通確認。heartbeat() がなければ list_collections() でフォールバック。 |
| `GET` | `/api/ready` | 認証なしで通る | K8S Readiness Probe: DB と Vector Store が応答可能かを確認する。 |

### 数字 — `routers/stats.py`（3件）

速さ・モデルの使われ方・答えの質。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/stats/model` | 管理者 | モデル別クエリ数・平均応答時間 (audit_logs.detail JSON 経由). |
| `GET` | `/api/stats/performance` | 管理者 | 応答時間・ディスク使用量・モデル変更イベント. |
| `GET` | `/api/stats/rag-quality` | 管理者 | RAG 品質スコア推移・ゼロヒット率・Guardrail 内訳. |

### ダッシュボード — `routers/dashboard.py`（1件）

最初の画面が出す要約。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/dashboard/summary` | 利用者（管理者・閲覧者のいずれか） | Overview画面用のダッシュボード集計データを返す。 |

### 報告書 — `routers/reports.py`（3件）

作った報告書。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/reports` | 認証なしで通る | admin 限定. |
| `POST` | `/api/reports/generate` | 認証なしで通る | LLM で運用サマリーレポートを生成して reports テーブルに保存. |
| `GET` | `/api/reports/{report_id}` | 認証なしで通る | admin 限定. |

### 費用 — `routers/cost.py`（1件）

1回の質問にかかる見積り。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/cost/estimate` | 利用者（管理者・閲覧者のいずれか） | Local LLM vs Cloud API のコスト試算 (estimate only). 認証必須. |

### 警告 — `routers/alerts.py`（1件）

サーバが伝えたいこと。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/alerts` | 管理者 | 全アラートチェック結果を返す. |

### 機能の入切 — `routers/features.py`（2件）

任意の部分の入切。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/features` | 管理者 | 全featuresフラグの現在値を返す。 |
| `PATCH` | `/api/features` | 管理者 | featuresフラグを更新する。DB settings に永続化する。 |

### 起動の形 — `routers/mode.py`（1件）

本番かデモか。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/mode` | 利用者（管理者・閲覧者のいずれか） | 実行モードを返す。フロントがバナー表示判定に使う。 |

### MCP — `routers/mcp.py`（2件）

MCP の設定と、つながるかの確認。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/mcp/config` | 管理者 | P6-A: claude_desktop_config.json 用のスニペットを生成する。 |
| `GET` | `/api/mcp/test-connection` | 管理者 | P6-A: ローカルMCPの基本疎通テスト。 |

### デモ — `routers/demo.py`（1件）

デモのときだけ在る役割の切り替え。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/api/demo/role-switch` | 利用者（管理者・閲覧者のいずれか） | ロール切替デモの workspace_id と利用可能ロールを返す。 |

### 画面 — `routers/pages.py`（2件）

ブラウザが読み込む HTML。

| 動作 | 口 | 誰が叩けるか | 何をするか |
|---|---|---|---|
| `GET` | `/` | 認証なしで通る |  |
| `GET` | `/chat-popup` | 認証なしで通る |  |

---

## この一覧の作り方 / How this list was made

`routers/*.py` の `@router.get(...)` などの宣言を構文木で読み、口の並びと、
その関数の中で `_require_admin` / `_require_authenticated` のどちらを呼んでいるかを
そのまま写しています。文章を書き足していません。

The list is read out of the `@router.<method>(...)` declarations in `routers/*.py`,
together with which of `_require_admin` / `_require_authenticated` the handler calls.
Nothing here was written by hand from memory.
