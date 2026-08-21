# CLI reference / CLI リファレンス

<!-- DD-CYN-0151 §10: cynovela-cli.py の argparse をそのまま読んで作っている。 -->

## English

`cynovela-cli.py` has **18 commands**, **48 counting the sub-commands**.
Every one of them is on this page, with every argument it takes.

### Running it

```
cd <the folder you extracted>
./.venv-cynovela/bin/python cynovela-cli.py <command>
```

It only talks to the server over HTTP. It never opens the database or `store/`
behind the server's back. `doctor` is the exception: it reads local files, and it
changes nothing.

### Where it gets the address and the token

In this order, first one wins:

1. `--url` / `--token` on the command line
2. `~/.cynovela_cli.env`, the lines `CYNOVELA_URL=` and `CYNOVELA_TOKEN=`
3. `http://127.0.0.1:8765` for the address; no token

`login` writes that file for you (mode 600). `logout` removes the token from it.

### Flags every command takes

| Argument | Required | What it is |
|---|---|---|
| `--url` | no | server URL (default: ~/.cynovela_cli.env CYNOVELA_URL, else http://127.0.0.1:8765) |
| `--token` | no | Bearer token (default: ~/.cynovela_cli.env CYNOVELA_TOKEN) |
| `--json` | no | machine-readable JSON output |
| `--lang` | no | message language (default: from LANG) one of `en` / `ja` |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | fine |
| 1 | you typed something the command cannot use |
| 2 | the server could not be reached |
| 3 | the token was rejected |
| 4 | the server answered with an error |

### Two shapes of output

Without `--json` you get lines meant for a person to read. With `--json` you get
one object: `{"ok": ..., "command": ..., "exit_code": ..., "data": {...}}`, or
`{"ok": false, ..., "error": {...}}` when it failed.

### The commands

#### `login`

sign in and remember the token in ~/.cynovela_cli.env

| Argument | Required | What it is |
|---|---|---|
| `--username` | yes | user name |
| `--password` | no | password (discouraged: it stays in the shell history) |
| `--password-stdin` | no | read the password from standard input instead |
| `--hours` | no | make the token expire after this many hours (default: it never expires) |
| `--seconds` | no | make the token expire after this many seconds (default: it never expires) |

#### `logout`

forget the remembered token

(no arguments)

#### `doctor`

what is missing right now (works without the server)

(no arguments)

#### `status`

is the server up (GET /api/health)

(no arguments)

#### `workspaces`

list workspaces (subcommands: create/update/archive/unarchive)

(no arguments)

##### `workspaces create`

create a workspace

| Argument | Required | What it is |
|---|---|---|
| `--name` | yes |  |

##### `workspaces update`

rename / re-describe a workspace, or link a source to it

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | yes | workspace_id |
| `--name` | no |  |
| `--description` | no |  |
| `--add-source` | no | link this source_id to the workspace |

##### `workspaces archive`

archive a workspace (reversible)

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | yes | workspace_id |

##### `workspaces unarchive`

bring an archived workspace back

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | yes | workspace_id |

#### `collections`

list collections (subcommands: create/link)

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | no | filter by workspace_id |

##### `collections create`

create a collection in a workspace

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | yes | workspace_id |
| `--name` | yes |  |
| `--access-level` | no | (default: `public`) |

##### `collections link`

link files to a collection

| Argument | Required | What it is |
|---|---|---|
| `--collection` | yes | collection_id |
| `--files` | no | comma-separated file ids (see: sources --files SOURCE_ID) |
| `--from-source` | no | link every present file of this source |

#### `sources`

list sources; --files SOURCE_ID lists the files of one source

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | no | filter by workspace_id |
| `--files` | no | list the files of this source |

#### `audit-logs`

recent audit log entries

| Argument | Required | What it is |
|---|---|---|
| `--limit` | no | 1-200 (default 50) (default: `50`) |

#### `search`

search; shows source fragments only (no answer)

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | yes | workspace_id (see: workspaces) |
| `--collection` | yes | collection_id (see: collections) |
| `--query` | yes | query text |
| `--preset` | no | one of `lite` / `standard` / `hq` (default: `standard`) |

#### `chat`

ask a question; prints the answer and its sources

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | yes | workspace_id |
| `--query` | yes | question text |
| `--collection` | no | restrict to one collection_id |

#### `ingest`

register a folder and start scanning it (one line)

| Argument | Required | What it is |
|---|---|---|
| `--path` | yes | folder to bring in |
| `--name` | no | source name (default: folder name) |
| `--workspace` | no | also link the new source to this workspace_id |

#### `scan`

start / status / cancel a scan

(no arguments)

##### `scan start`

start a scan; returns a job_id immediately

| Argument | Required | What it is |
|---|---|---|
| `--source` | yes | source_id (see: sources) |

##### `scan status`

progress of a scan job

| Argument | Required | What it is |
|---|---|---|
| `--job` | yes | job_id returned by scan start / ingest |

##### `scan cancel`

request cancellation of a running scan

| Argument | Required | What it is |
|---|---|---|
| `--source` | yes | source_id |

#### `publish`

start / status / stop / recover a publish

(no arguments)

##### `publish start`

start a publish; returns a job_id immediately

| Argument | Required | What it is |
|---|---|---|
| `--collection` | yes | collection_id |

##### `publish status`

progress of a publish job

| Argument | Required | What it is |
|---|---|---|
| `--job` | yes | job_id returned by publish start |

##### `publish stop`

stop a running publish

| Argument | Required | What it is |
|---|---|---|
| `--collection` | yes | collection_id |

##### `publish recover`

recover a collection stuck in publishing

| Argument | Required | What it is |
|---|---|---|
| `--collection` | yes | collection_id |

#### `index-status`

chunk counts per collection

| Argument | Required | What it is |
|---|---|---|
| `--workspace` | no | filter by workspace_id |

#### `delete`

delete a source / collection / workspace (--yes required)

(no arguments)

##### `delete source`

delete a source

| Argument | Required | What it is |
|---|---|---|
| `id` | yes (positional) | source_id |
| `--yes` | no | actually delete |

##### `delete collection`

delete a collection

| Argument | Required | What it is |
|---|---|---|
| `id` | yes (positional) | collection_id |
| `--yes` | no | actually delete |

##### `delete workspace`

delete a workspace

| Argument | Required | What it is |
|---|---|---|
| `id` | yes (positional) | workspace_id |
| `--yes` | no | actually delete |

#### `users`

manage users (--yes required for changes)

(no arguments)

##### `users list`

list users

(no arguments)

##### `users create`

create a user

| Argument | Required | What it is |
|---|---|---|
| `--username` | yes |  |
| `--password` | yes |  |
| `--role` | no | (default: `viewer`) |
| `--display-name` | no |  |
| `--yes` | no | actually create |

##### `users update`

change role / name / active state

| Argument | Required | What it is |
|---|---|---|
| `id` | yes (positional) | user_id (see: users list) |
| `--role` | no |  |
| `--display-name` | no |  |
| `--active` | no | true / false |
| `--yes` | no | actually change |

##### `users delete`

delete a user (switch off, or --purge to remove for good)

| Argument | Required | What it is |
|---|---|---|
| `id` | yes (positional) | user_id |
| `--purge` | no | remove the user row for good instead of only switching it off (audit log entries are kept) |
| `--yes` | no | actually delete |

##### `users reset-password`

issue a new password for a user

| Argument | Required | What it is |
|---|---|---|
| `id` | yes (positional) | user_id |
| `--password` | yes | new password (8+ chars) |
| `--yes` | no | actually reset |

#### `backup`

list / create / restore / delete backups (--yes required for changes)

(no arguments)

##### `backup list`

list backups

(no arguments)

##### `backup create`

take a backup of database and settings

| Argument | Required | What it is |
|---|---|---|
| `--label` | no | short label for the backup |
| `--yes` | no | actually create |

##### `backup restore`

restore a backup (replaces current data)

| Argument | Required | What it is |
|---|---|---|
| `name` | yes (positional) | backup name (see: backup list) |
| `--yes` | no | actually restore |

##### `backup delete`

delete a backup

| Argument | Required | What it is |
|---|---|---|
| `name` | yes (positional) | backup name |
| `--yes` | no | actually delete |

#### `settings`

show or change server settings (admin token required)

(no arguments)

##### `settings show`

current settings (api keys shown as set / not set only)

| Argument | Required | What it is |
|---|---|---|
| `name` | yes (positional) | one of `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` (default: `llm`) |

##### `settings models`

models visible at the configured endpoint (GET /api/settings/models)

(no arguments)

##### `settings test`

test the LLM connection (POST /api/settings/test-connection)

| Argument | Required | What it is |
|---|---|---|
| `--provider` | no | test this provider instead of the saved one |
| `--base-url` | no | test this endpoint instead of the saved one |
| `--model` | no | model name to test with |

##### `settings set`

change settings; shows before/after and needs --yes to write

| Argument | Required | What it is |
|---|---|---|
| `name` | yes (positional) | one of `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` (default: `llm`) |
| `--set` | yes | repeatable; e.g. --set model=qwen3-4b --set base_url=http://localhost:1234 |
| `--yes` | no | actually apply the change |
| `--dry-run` | no | show what would change, write nothing |

##### `settings providers`

selectable provider presets (GET /api/llm/presets)

(no arguments)

---

## 日本語

`cynovela-cli.py` の命令は **18件**、下位の命令まで数えると **48件** です。
そのすべてを、引数も含めてここに書いてあります。

### 打ち方

```
cd <展開したフォルダ>
./.venv-cynovela/bin/python cynovela-cli.py <命令>
```

この道具はサーバと HTTP で話すだけです。サーバの背中側で データベースや `store/` を
開くことはしません。`doctor` だけは手元のファイルを読みますが、何も書き換えません。

### 宛先とトークンをどこから取るか

上から順に、先に見つかったものを使います。

1. 打つときの `--url` / `--token`
2. `~/.cynovela_cli.env` の `CYNOVELA_URL=` と `CYNOVELA_TOKEN=` の行
3. 宛先は `http://127.0.0.1:8765`。トークンは無し

`login` がこのファイルを書きます（他人から読めない権限にします）。`logout` が消します。

### どの命令にも付けられる旗

| 引数 | 要る？ | 何か |
|---|---|---|
| `--url` | 省ける | サーバの宛先（既定: ~/.cynovela_cli.env の CYNOVELA_URL。無ければ http://127.0.0.1:8765） |
| `--token` | 省ける | トークン（既定: ~/.cynovela_cli.env の CYNOVELA_TOKEN） |
| `--json` | 省ける | 機械で読む形（JSON）で出す |
| `--lang` | 省ける | 出す言葉（既定: LANG から決める） `en` / `ja` のどれか |

### 終了コード

| 数 | 意味 |
|---|---|
| 0 | うまくいった |
| 1 | 打ち方が違う |
| 2 | サーバに届かない |
| 3 | トークンが受け付けられなかった |
| 4 | サーバが失敗を返した |

### 出方は2つ

`--json` を付けないと、人が読む行が出ます。付けると、次の形の1つの塊が出ます。
`{"ok": …, "command": …, "exit_code": …, "data": {…}}`。
失敗したときは `{"ok": false, …, "error": {…}}` です。

### 命令の一覧

#### `login`

ログインして、トークンを覚えさせる

| 引数 | 要る？ | 何か |
|---|---|---|
| `--username` | 要る | 利用者の名前 |
| `--password` | 省ける | 合言葉（勧めません: ターミナルの履歴に残ります） |
| `--password-stdin` | 省ける | 合言葉を標準入力から読む |
| `--hours` | 省ける | この時間でトークンを切れさせる（既定: 切れない） |
| `--seconds` | 省ける | この秒数でトークンを切れさせる（既定: 切れない） |

#### `logout`

覚えているトークンを忘れさせる

（引数はありません）

#### `doctor`

いま何が足りないか。サーバが動いていなくても答える

（引数はありません）

#### `status`

サーバが起きているか

（引数はありません）

#### `workspaces`

作業場所を並べる（作る・変える・保管する・戻す も）

（引数はありません）

##### `workspaces create`

作業場所を作る

| 引数 | 要る？ | 何か |
|---|---|---|
| `--name` | 要る |  |

##### `workspaces update`

名前や説明を変える。取り込み元を結び付ける

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 要る | 作業場所の番号 |
| `--name` | 省ける |  |
| `--description` | 省ける |  |
| `--add-source` | 省ける | この取り込み元を作業場所へ結ぶ |

##### `workspaces archive`

脇へ置く（戻せる）

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 要る | 作業場所の番号 |

##### `workspaces unarchive`

脇へ置いたものを戻す

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 要る | 作業場所の番号 |

#### `collections`

まとまりを並べる（作る・資料を結ぶ も）

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 省ける | この作業場所のものに絞る |

##### `collections create`

作業場所の中にまとまりを作る

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 要る | 作業場所の番号 |
| `--name` | 要る |  |
| `--access-level` | 省ける | （既定: `public`） |

##### `collections link`

資料をまとまりへ結ぶ

| 引数 | 要る？ | 何か |
|---|---|---|
| `--collection` | 要る | まとまりの番号 |
| `--files` | 省ける | 資料の番号をコンマで並べる（`sources --files 取り込み元の番号` で見られる） |
| `--from-source` | 省ける | この取り込み元の資料を全部結ぶ |

#### `sources`

登録した取り込み元を並べる。`--files` で1つの資料一覧

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 省ける | この作業場所のものに絞る |
| `--files` | 省ける | この取り込み元の資料を並べる |

#### `audit-logs`

直近の監査の記録

| 引数 | 要る？ | 何か |
|---|---|---|
| `--limit` | 省ける | 1〜200（既定 50） （既定: `50`） |

#### `search`

探す。答えは出さず、当たった断片だけを出す

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 要る | 作業場所の番号（`workspaces` で見られる） |
| `--collection` | 要る | まとまりの番号（`collections` で見られる） |
| `--query` | 要る | 探す言葉 |
| `--preset` | 省ける | `lite` / `standard` / `hq` のどれか （既定: `standard`） |

#### `chat`

質問する。答えと出典を出す

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 要る | 作業場所の番号 |
| `--query` | 要る | 質問の文 |
| `--collection` | 省ける | 1つのまとまりに絞る |

#### `ingest`

フォルダを登録して走査を始める、を1行で

| 引数 | 要る？ | 何か |
|---|---|---|
| `--path` | 要る | 取り込むフォルダ |
| `--name` | 省ける | 取り込み元の名前（既定: フォルダ名） |
| `--workspace` | 省ける | 作った取り込み元を、この作業場所にも結び付ける |

#### `scan`

走査を 始める / 進み具合を見る / 止める

（引数はありません）

##### `scan start`

走査を始める。すぐに job_id が返る

| 引数 | 要る？ | 何か |
|---|---|---|
| `--source` | 要る | 取り込み元の番号（`sources` で見られる） |

##### `scan status`

走査の進み具合

| 引数 | 要る？ | 何か |
|---|---|---|
| `--job` | 要る | `scan start` / `ingest` が返した job_id |

##### `scan cancel`

走行中の走査に中止を頼む

| 引数 | 要る？ | 何か |
|---|---|---|
| `--source` | 要る | 取り込み元の番号 |

#### `publish`

公開を 始める / 進み具合を見る / 止める / 直す

（引数はありません）

##### `publish start`

公開を始める。すぐに job_id が返る

| 引数 | 要る？ | 何か |
|---|---|---|
| `--collection` | 要る | まとまりの番号 |

##### `publish status`

公開の進み具合

| 引数 | 要る？ | 何か |
|---|---|---|
| `--job` | 要る | `publish start` が返した job_id |

##### `publish stop`

走行中の公開を止める

| 引数 | 要る？ | 何か |
|---|---|---|
| `--collection` | 要る | まとまりの番号 |

##### `publish recover`

公開のまま固まったまとまりを直す

| 引数 | 要る？ | 何か |
|---|---|---|
| `--collection` | 要る | まとまりの番号 |

#### `index-status`

まとまりごとの塊の数

| 引数 | 要る？ | 何か |
|---|---|---|
| `--workspace` | 省ける | この作業場所のものに絞る |

#### `delete`

取り込み元・まとまり・作業場所を消す（`--yes` が要る）

（引数はありません）

##### `delete source`

取り込み元を消す

| 引数 | 要る？ | 何か |
|---|---|---|
| `id` | 要る（位置で渡す） | 取り込み元の番号 |
| `--yes` | 省ける | 実際に消す |

##### `delete collection`

まとまりを消す

| 引数 | 要る？ | 何か |
|---|---|---|
| `id` | 要る（位置で渡す） | まとまりの番号 |
| `--yes` | 省ける | 実際に消す |

##### `delete workspace`

作業場所を消す

| 引数 | 要る？ | 何か |
|---|---|---|
| `id` | 要る（位置で渡す） | 作業場所の番号 |
| `--yes` | 省ける | 実際に消す |

#### `users`

利用者を扱う（変えるときは `--yes` が要る）

（引数はありません）

##### `users list`

利用者を並べる

（引数はありません）

##### `users create`

利用者を作る

| 引数 | 要る？ | 何か |
|---|---|---|
| `--username` | 要る |  |
| `--password` | 要る |  |
| `--role` | 省ける | （既定: `viewer`） |
| `--display-name` | 省ける |  |
| `--yes` | 省ける | 実際に作る |

##### `users update`

役割・表示名・使えるかどうかを変える

| 引数 | 要る？ | 何か |
|---|---|---|
| `id` | 要る（位置で渡す） | 利用者の番号（`users list` で見られる） |
| `--role` | 省ける |  |
| `--display-name` | 省ける |  |
| `--active` | 省ける | true か false |
| `--yes` | 省ける | 実際に変える |

##### `users delete`

利用者を消す（`--purge` で行そのものを消す）

| 引数 | 要る？ | 何か |
|---|---|---|
| `id` | 要る（位置で渡す） | 利用者の番号 |
| `--purge` | 省ける | 使えなくするだけでなく、行そのものを消す（監査の記録は残ります） |
| `--yes` | 省ける | 実際に消す |

##### `users reset-password`

利用者の合言葉を出し直す

| 引数 | 要る？ | 何か |
|---|---|---|
| `id` | 要る（位置で渡す） | 利用者の番号 |
| `--password` | 要る | 新しい合言葉（8文字以上） |
| `--yes` | 省ける | 実際に出し直す |

#### `backup`

控えを 並べる / 取る / 戻す / 消す（変えるときは `--yes` が要る）

（引数はありません）

##### `backup list`

控えを並べる

（引数はありません）

##### `backup create`

控えを取る

| 引数 | 要る？ | 何か |
|---|---|---|
| `--label` | 省ける | 控えに付ける短い札 |
| `--yes` | 省ける | 実際に作る |

##### `backup restore`

控えの中身に戻す（いまのデータを置き換える）

| 引数 | 要る？ | 何か |
|---|---|---|
| `name` | 要る（位置で渡す） | 控えの名前（`backup list` で見られる） |
| `--yes` | 省ける | 実際に戻す |

##### `backup delete`

控えを消す

| 引数 | 要る？ | 何か |
|---|---|---|
| `name` | 要る（位置で渡す） | 控えの名前 |
| `--yes` | 省ける | 実際に消す |

#### `settings`

設定を見る・変える（管理者のトークンが要る）

（引数はありません）

##### `settings show`

いまの設定（APIキーは 設定あり/なし だけ）

| 引数 | 要る？ | 何か |
|---|---|---|
| `name` | 要る（位置で渡す） | `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` のどれか （既定: `llm`） |

##### `settings models`

接続先に見えているモデル

（引数はありません）

##### `settings test`

LLM につながるか試す

| 引数 | 要る？ | 何か |
|---|---|---|
| `--provider` | 省ける | 保存してあるプロバイダーではなく、これで試す |
| `--base-url` | 省ける | 保存してある宛先ではなく、この宛先で試す |
| `--model` | 省ける | 試すモデルの名前 |

##### `settings set`

設定を変える。前後を出し、書くには `--yes` が要る

| 引数 | 要る？ | 何か |
|---|---|---|
| `name` | 要る（位置で渡す） | `llm` / `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` のどれか （既定: `llm`） |
| `--set` | 要る | 何度でも書ける。例: `--set model=qwen3-4b --set base_url=http://localhost:1234` |
| `--yes` | 省ける | 実際に書き換える |
| `--dry-run` | 省ける | 何が変わるかだけ出す。書き込まない |

##### `settings providers`

選べるプロバイダーのひな型

（引数はありません）

---

## この一覧の作り方 / How this list was made

`cynovela-cli.py` の `build_parser()` を実際に呼び、そこに登録されている命令と引数を
そのまま書き出しています。手で並べていません。

`build_parser()` in `cynovela-cli.py` is called for real, and what it registers is
written out as-is. Nothing here was typed from memory.
