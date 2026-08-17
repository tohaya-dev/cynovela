# 運用ガイド

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool built by an individual to
> understand the concepts of AI infrastructure tools by working on them by hand.
> It is not a commercial product or an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

This document collects the procedures for starting and stopping, backup, logs, and user management needed to operate Cynovela day to day.

---

## 1. Normal Startup and Shutdown

### Startup

```bash
conda activate cynovela
python server.py --demo
```

For details of the options, see the deployment guide.

### Shutdown

Send `Ctrl + C` once in the terminal. The FastAPI / Uvicorn shutdown hook runs, and a stop request is propagated to any Publish job in progress (the SSE path).

### Background Startup

You can also keep it resident with `nohup`, or with a terminal multiplexer such as `tmux` / `screen`.

```bash
nohup python server.py --demo > ~/cynovela.out 2>&1 &
```

---

## 2. Backing Up the Database and ChromaDB

### Default Storage Locations

Cynovela's data is stored under `~/.cynovela/`.

| Use | Path | Environment variable for override |
|------|------|------------|
| SQLite DB (normal) | `~/.cynovela/db/cynovela.db` | `CYNOVELA_DB` |
| SQLite DB (demo) | `~/.cynovela/db/demo.db` | `CYNOVELA_DB` |
| ChromaDB (normal) | `~/.cynovela/vector/default/chroma` | `CYNOVELA_CHROMA` |
| ChromaDB (demo) | `~/.cynovela/vector/demo/chroma` | `CYNOVELA_CHROMA` |
| Backups | `~/.cynovela/backups` | `CYNOVELA_BACKUP_DIR` |
| Models | `~/.cynovela/models` | (can be specified individually with `cynovela.yaml.models.*.path`) |
| Logs | `~/.cynovela` | `CYNOVELA_LOG_DIR` |

> The above are the storage locations of the host (conda) edition. The actual location for the host edition is `store/` under the folder where the package was extracted. In the container edition, the DB and vector data are stored in named volumes, and the ingest entry point bind-mounts the ingest sources passed at startup (multiple allowed) read-only at `/app/ingest/<inner name>`. The former default ingest folder `~/Cynovela` has been abolished.

### Manual Backup

With the server stopped, copy the directories above.

```bash
# サーバー停止後に実行
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/cynovela-backups/$TS
cp -R ~/.cynovela/db ~/cynovela-backups/$TS/db
cp -R ~/.cynovela/vector ~/cynovela-backups/$TS/vector
```

### Restore

```bash
# サーバー停止後に実行
cp -R ~/cynovela-backups/20260526-093000/db ~/.cynovela/db
cp -R ~/cynovela-backups/20260526-093000/vector ~/.cynovela/vector
```

### Points to Note

- **Always back up and restore SQLite and ChromaDB together.** If you restore only one of them, the consistency between the `chunks` table and the vector IDs breaks.
- Deleting a source / workspace / collection is implemented so that both SQLite and ChromaDB are cleaned up. Keep this principle of "both from the same snapshot" in backup operations as well.
- Starting with `--demo` uses `db/demo.db` and `vector/demo/chroma`; starting without it, for production, uses `db/cynovela.db` and `vector/default/chroma`. Neither one is wiped on every startup — what you write stays as it is. Do not mix them up with production operation.

---

## 3. Log Files

### Log Level

Controlled by `logging.level` (or `server.log_level`) in `cynovela.yaml`. The default is `INFO`.

```yaml
logging:
  level: INFO
  request_id: true   # 全リクエストに X-Request-ID を付与
```

### Request ID

When you enable `request_id: true`, an `X-Request-ID` header is added to all API responses. It can be used during troubleshooting to link requests on the client side with logs on the server side.

### Preflight Log

The preflight check at startup outputs logs such as the following.

```
[Cynovela] PII detection mode: standard (from cynovela.yaml)
```

---

## 4. Exporting the Audit Log

### What the Audit Log Is

Cynovela records important operations in the `audit_logs` table in SQLite.

Main recorded targets:

- Creation and deletion of workspaces, collections, and sources
- Execution and completion of Publish
- Chat (questions and answers)
- PII detection (`PII_DETECTED` / `pii_detected`)
- Prompt injection detection (`PROMPT_INJECTION_BLOCKED`)
- Authentication failures

### Tamper Prevention

`audit_logs` cannot be deleted or modified through the API. Keep this principle in your operating policy as well.

### Viewing from the GUI

After logging in with the `admin` role, you can view them with filters on the "監査ログ" (audit log) screen.

### Via the API

- `GET /api/guardrails/pii-detections` — aggregates PII detections from `audit_logs` (administrator required)
- `GET /api/pii-detections` — aggregates from the `chunks` table (administrator required)
- `GET /api/audit-logs` — retrieves the audit log (administrator required)

### Extracting Directly from SQLite

If you want to export to CSV or similar, SELECT directly from a SQLite client.

```bash
sqlite3 ~/.cynovela/db/cynovela.db \
  "SELECT timestamp, action, target, detail FROM audit_logs ORDER BY timestamp DESC LIMIT 100;"
```

---

## 5. User Management

### Roles

Cynovela has 3 kinds of roles.

| Role | Permissions |
|--------|------|
| `admin` | All features (user management, system settings, viewing the PII detection history, and so on) |
| `viewer` | Viewing only |

> Names such as `curator` / `data-scientist` are accepted as backward-compatible values, but in the current implementation they are normalized to `viewer` and have no specific permissions. The roles held by the DB are the 2 values `admin` / `viewer`.

### The Initial Administrator

An administrator user is created at first startup. The user name and password can be overridden with environment variables.

| Environment variable | Use | Default |
|---------|------|------|
| `CYNOVELA_ADMIN_USERNAME` | User name of the first administrator | `cynovela` |
| `CYNOVELA_ADMIN_INITIAL_PASSWORD` | Password of the first administrator | (If neither the env var nor `auth.admin_initial_password` in `cynovela.yaml` is set, a password change is forced at first login. No known fixed password is distributed. Set a value only if you want to fix it.) |

### Login Information of the Shipped demo.db

The `demo.db` distributed with `--demo` already has the following accounts loaded.

| User name | Role | Password |
|-----------|--------|-----------|
| `cynovela` | admin | A change is forced at first login (no fixed password is distributed) |
| `demo` | viewer | See `viewer_password` in the bundled credential file (`*.admin-password.txt`, received separately from the package tar). No fixed password is distributed |

### Adding and Deleting Users, and Changing Passwords

After logging in with the administrator role, you can do this from the "ユーザー管理" (user management) screen. Operation via the API is also possible, but the user management endpoints are protected by `_require_admin` or `_require_admin_or_self` (the person themselves or an administrator only).

### Vault Access and Masking by Role

- `admin` → searches the raw (original text) vault. No exit masking in the answer display.
- `viewer` (`curator` and so on are normalized to viewer) → searches the masked vault. Exit masking is applied.

> However, when an external (non-local) LLM is used, crag-egress-guard prevents the raw preview (context_preview) from being sent outside even for an administrator (CRAG is skipped). Note that it is not the case that "administrator = raw text is always passed to the external LLM."

For details, see "admin / viewer の見え方の違い" in the hands-on guide (advanced edition).

### Authentication

API authentication is done with the HTTP `Authorization` header. The token is a JWT issued by `POST /api/auth/login`. The old `Bearer demo-token-{user_id}` form has been abolished and is not accepted.

> **Note**: Production authentication with JWT is unimplemented as of alpha GA. For details, see "既知の制限" (known limitations).

### IP Access Control

By default the access source is not restricted (the allowlist works only when you pass `--allow-tailscale` / `--allow-subnet`). To close it to the inside of your own machine only, add `--local-only`.

---

## 6. Health Checks and Monitoring

### Main Health Endpoints

`/api/health` and other monitoring endpoints for administrators are provided (protected by `_require_admin`).

### Publish History

The Publish result of each collection is recorded in the `publish_history` table.

Recorded items:

- `workspace_id`
- `timestamp`
- `doc_count`
- `chunk_count`
- `pii_count`
- `excluded_count`
- `avg_chunk_chars`
- `elapsed_seconds`

They can be viewed from the "履歴タブ" (history tab) of the Workspace detail screen in the GUI.

### Circuit Breaker

When failures of LLM or external API calls exceed a certain number, the circuit breaker OPENs and calls are stopped temporarily. The behavior can be adjusted in the `circuit_breaker` section of `cynovela.yaml`.

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 3
  recovery_timeout_seconds: 30
```

---

## 7. Notifications (Email)

Email notification via SMTP is supported (disabled by default).

```yaml
notifications:
  smtp:
    enabled: false
    host: smtp.gmail.com
    port: 587
    username: ""
    password: ""              # 環境変数 CYNOVELA_SMTP_PASSWORD 推奨
    from_address: ""
    to_addresses: []
    notify_on:
      - scan_completed
      - scan_error
      - circuit_breaker_opened
```

---

## 8. Operational Notes

- The `--demo` mode is for verification. The demo DB (`db/demo.db`) is not wiped on every startup — what you write keeps accumulating, so do not put production data in it.
- The `--mock` mode that used to exist has been removed. If you specify it now, it stops with an error.
- Take backup snapshots of "SQLite and ChromaDB at the same time." Restoring only one of them breaks consistency.
- `audit_logs` needs tamper prevention. Avoid careless writes to the SQLite file itself.

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

このドキュメントは、Cynovela を日々運用するための起動・停止・バックアップ・ログ・ユーザー管理の手順をまとめたものです。

---

## 1. 通常起動と停止

### 起動

```bash
conda activate cynovela
python server.py --demo
```

オプションの詳細はデプロイメントガイドを参照してください。

### 停止

ターミナル上で `Ctrl + C` を 1 回送信します。FastAPI / Uvicorn のシャットダウンフックが走り、進行中の Publish ジョブ（SSE 経路）には停止リクエストが伝達されます。

### バックグラウンド起動

`nohup` や `tmux` / `screen` などのターミナル多重化ツールで常駐させることもできます。

```bash
nohup python server.py --demo > ~/cynovela.out 2>&1 &
```

---

## 2. データベースと ChromaDB のバックアップ

### 既定の保存場所

Cynovela のデータは `~/.cynovela/` 配下に格納されます。

| 用途 | パス | 上書き用環境変数 |
|------|------|------------|
| SQLite DB（通常） | `~/.cynovela/db/cynovela.db` | `CYNOVELA_DB` |
| SQLite DB（demo） | `~/.cynovela/db/demo.db` | `CYNOVELA_DB` |
| ChromaDB（通常） | `~/.cynovela/vector/default/chroma` | `CYNOVELA_CHROMA` |
| ChromaDB（demo） | `~/.cynovela/vector/demo/chroma` | `CYNOVELA_CHROMA` |
| バックアップ | `~/.cynovela/backups` | `CYNOVELA_BACKUP_DIR` |
| モデル | `~/.cynovela/models` | （`cynovela.yaml.models.*.path` で個別指定可） |
| ログ | `~/.cynovela` | `CYNOVELA_LOG_DIR` |

> 上記はホスト（conda）版の保存場所です。ホスト版の実体は配布物を展開したフォルダ配下の `store/` です。コンテナ版では DB／ベクターは名前付きボリュームに格納され、取り込みの入口は起動時に渡した取り込み元（複数可）を `/app/ingest/<中の名前>` へ読み取り専用で bind します。既定の取り込みフォルダ `~/Cynovela` は廃止しました。

### 手動バックアップ

サーバーを停止した状態で、上記ディレクトリをコピーします。

```bash
# サーバー停止後に実行
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/cynovela-backups/$TS
cp -R ~/.cynovela/db ~/cynovela-backups/$TS/db
cp -R ~/.cynovela/vector ~/cynovela-backups/$TS/vector
```

### 復元

```bash
# サーバー停止後に実行
cp -R ~/cynovela-backups/20260526-093000/db ~/.cynovela/db
cp -R ~/cynovela-backups/20260526-093000/vector ~/.cynovela/vector
```

### 注意点

- SQLite と ChromaDB は **必ず一緒にバックアップ・復元**してください。片方だけ復元すると `chunks` テーブルとベクター ID の整合性が崩れます。
- ソース／ワークスペース／コレクション削除では SQLite と ChromaDB の両方をクリーンアップする実装になっています。バックアップ運用でもこの「両方を同じスナップショット」原則を守ってください。
- `--demo` 起動は `db/demo.db` と `vector/demo/chroma` を、付けない本番起動は `db/cynovela.db` と `vector/default/chroma` を使います。どちらも起動のたびに消えることはなく、書いたものはそのまま残ります。取り違えないよう本運用と混ぜないでください。

---

## 3. ログファイル

### ログレベル

`cynovela.yaml` の `logging.level`（または `server.log_level`）で制御します。既定は `INFO` です。

```yaml
logging:
  level: INFO
  request_id: true   # 全リクエストに X-Request-ID を付与
```

### Request ID

`request_id: true` を有効にすると、全 API レスポンスに `X-Request-ID` ヘッダーが付与されます。トラブルシュート時にクライアント側のリクエストとサーバー側ログを紐付けるのに使えます。

### Preflight ログ

起動時の Preflight チェックでは、次のようなログが出力されます。

```
[Cynovela] PII detection mode: standard (from cynovela.yaml)
```

---

## 4. 監査ログのエクスポート

### 監査ログとは

Cynovela は重要操作を SQLite の `audit_logs` テーブルに記録します。

主な記録対象:

- ワークスペース・コレクション・ソースの作成と削除
- Publish の実行と完了
- チャット（質問・回答）
- PII 検出（`PII_DETECTED` / `pii_detected`）
- プロンプトインジェクション検出（`PROMPT_INJECTION_BLOCKED`）
- 認証失敗

### 改ざん防止

`audit_logs` は API 経由での削除・変更ができません。運用ポリシー上もこの原則を守ってください。

### GUI からの参照

`admin` ロールでログイン後、「監査ログ」画面でフィルタしながら参照できます。

### API 経由

- `GET /api/guardrails/pii-detections` — `audit_logs` から PII 検出を集計（admin 必須）
- `GET /api/pii-detections` — `chunks` テーブルから集計（admin 必須）
- `GET /api/audit-logs` — 監査ログ取得（admin 必須）

### SQLite から直接抽出

CSV 等にエクスポートしたい場合は、SQLite クライアントから直接 SELECT します。

```bash
sqlite3 ~/.cynovela/db/cynovela.db \
  "SELECT timestamp, action, target, detail FROM audit_logs ORDER BY timestamp DESC LIMIT 100;"
```

---

## 5. ユーザー管理

### ロール

Cynovela には 3 種類のロールがあります。

| ロール | 権限 |
|--------|------|
| `admin` | 全機能（ユーザー管理、システム設定、PII 検出履歴閲覧など） |
| `viewer` | 閲覧のみ |

> `curator` / `data-scientist` 等の名称は後方互換の値として受理されますが、現行実装では `viewer` に正規化され、固有権限はありません。DB が保持するロールは `admin` / `viewer` の 2 値です。

### 初期 admin

初回起動時に admin ユーザーが作成されます。ユーザー名とパスワードは環境変数で上書きできます。

| 環境変数 | 用途 | 既定値 |
|---------|------|------|
| `CYNOVELA_ADMIN_USERNAME` | 初回 admin ユーザー名 | `cynovela` |
| `CYNOVELA_ADMIN_INITIAL_PASSWORD` | 初回 admin パスワード | （env・`cynovela.yaml` の `auth.admin_initial_password` いずれも未設定なら、初回ログインでパスワード変更を強制します。既知の固定 PW は配布しません。固定したい場合のみ値を設定） |

### 出荷 demo.db のログイン情報

`--demo` で配布される `demo.db` には次のアカウントが投入済みです。

| ユーザー名 | ロール | パスワード |
|-----------|--------|-----------|
| `cynovela` | admin | 初回ログイン時に変更を強制（固定 PW は配布しません） |
| `demo` | viewer | 同梱の資格情報ファイル（配布物の tar とは別便で受け取る `*.admin-password.txt`）の `viewer_password` を参照。固定 PW は配布しません |

### ユーザー追加・削除・パスワード変更

admin ロールでログイン後、「ユーザー管理」画面から実行できます。API での操作も可能ですが、ユーザー管理系エンドポイントは `_require_admin` または `_require_admin_or_self`（本人か admin のみ）で保護されています。

### ロール別の保管庫アクセスとマスキング

- `admin` → raw（生本文）保管庫を検索。回答表示では出口マスクなし。
- `viewer`（`curator` 等は viewer に正規化）→ masked（マスク済み）保管庫を検索。出口マスクあり。

> ただし外部（非ローカル）LLM を使う場合は、crag-egress-guard により admin でも raw の下読み（context_preview）が外部へ送出されません（CRAG スキップ）。「admin＝常に生本文が外部 LLM へ渡る」ではない点に注意してください。

詳しくはハンズオン（応用編）「admin / viewer の見え方の違い」を参照してください。

### 認証

API 認証は HTTP `Authorization` ヘッダーで行います。トークンは `POST /api/auth/login` が発行する JWT です。旧 `Bearer demo-token-{user_id}` 形式は廃止済みで受理しません。

> **注意**: JWT による本番認証は alpha GA 時点で未実装です。詳しくは「既知の制限」を参照してください。

### IP アクセス制御

既定ではアクセス元を制限しません（アローリストは `--allow-tailscale` / `--allow-subnet` を渡したときだけ働きます）。自分のマシンの中だけに閉じるには `--local-only` を付けます。

---

## 6. ヘルスチェックと監視

### 主要なヘルスエンドポイント

`/api/health` ほか admin 向けの監視系エンドポイントが用意されています（`_require_admin` で保護）。

### Publish 履歴

各コレクションの Publish 結果は `publish_history` テーブルに記録されます。

記録項目:

- `workspace_id`
- `timestamp`
- `doc_count`
- `chunk_count`
- `pii_count`
- `excluded_count`
- `avg_chunk_chars`
- `elapsed_seconds`

GUI 上の Workspace 詳細画面「履歴タブ」から参照できます。

### サーキットブレーカー

LLM や外部 API 呼び出しの失敗が一定数を超えると、サーキットブレーカーが OPEN し、一時的に呼び出しを停止します。`cynovela.yaml` の `circuit_breaker` セクションで挙動を調整できます。

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 3
  recovery_timeout_seconds: 30
```

---

## 7. 通知（メール）

SMTP 経由でのメール通知に対応しています（既定は無効）。

```yaml
notifications:
  smtp:
    enabled: false
    host: smtp.gmail.com
    port: 587
    username: ""
    password: ""              # 環境変数 CYNOVELA_SMTP_PASSWORD 推奨
    from_address: ""
    to_addresses: []
    notify_on:
      - scan_completed
      - scan_error
      - circuit_breaker_opened
```

---

## 8. 運用上の注意

- `--demo` モードは検証用です。デモの DB（`db/demo.db`）は起動のたびに消えるわけではなく、書いたものが残り続けるため、本番データを置かないでください。
- 以前あった `--mock` モードは撤去済みです。いま指定するとエラーで止まります。
- バックアップは「SQLite と ChromaDB を同時に」スナップショットしてください。片方だけの復元は整合性を壊します。
- `audit_logs` は改ざん防止が必要です。SQLite ファイルそのものへの不用意な書き込みは避けてください。

---
