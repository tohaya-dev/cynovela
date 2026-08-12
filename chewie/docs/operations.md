# 運用ガイド

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
最終更新: 2026-05-26 / Alpha GA 対応版
