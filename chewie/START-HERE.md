# START HERE

**日本語版はこちら → [日本語](#日本語)**

## English

**This is the only entry document. You can get started with this document alone.**
Everything else under `docs/` is reference material — open it only when you need it (the list is at the end).

This package is the **application build (runs on macOS directly, no container)**.

---

### 1. Which package did you download?

```
1) Package edition (for Apple silicon Macs — ready to use)
     Extract it and run one line. No Python and no conda are needed.
     Nothing is installed on this Mac. To remove it, delete the folder.
2) Source edition (for everyone else, or those who want to build the environment themselves)
     At startup you choose one of 2 ways to build the environment:
       1) create a dedicated conda environment (name: cynovela-dist), or
       2) use this Mac's Python (3.12 or later) and build a venv only inside this folder.
```

**The AI models are downloaded separately** (a separate file on the release page, or the first start offers to fetch them). Neither package contains them.

---

### 2. System requirements

| Item | Requirement |
|---|---|
| macOS | Apple silicon Mac (M1 or later). Intel Macs, Windows and Linux are not verified. **The package edition runs on Apple silicon only.** |
| Python | **3.12 or later** (`pyproject.toml` declares `requires-python = ">=3.12"`; `environment.yml` pins 3.12.13). **3.10 and 3.11 cannot be used.** Not needed for the package edition, nor for source-edition choice 1 (conda fetches its own). |
| conda | **Miniforge recommended** (its default channel is conda-forge). **Not required** — the package edition and source-edition choice 2 work without it. |
| Free disk space | Package edition expanded: **about 3.1 GB** (measured). Source edition expanded: all-in-one **about 5.2 GB** / model-separate edition **about 8 MB** (measured). AI models: **4.84 GB** (separate download for the package and model-separate editions; already inside the all-in-one). |
| Memory | 8 GB or more recommended (existing record; not re-measured). |
| Network | Package edition: not needed to run — only to fetch the AI models. Source edition setup fetches from: conda-forge / PyPI / github.com (2 wheels) / huggingface.co (models). |
| LLM for answers | LM Studio or an OpenAI-compatible API (answers need a real LLM). |

**Installing by hand, without the launch sequence** (only if you cannot use `./launch.sh`): you need Python **3.12 or later** yourself; create a dedicated environment (conda name `cynovela-dist`, or a venv inside this folder — never create or modify a shared environment), run `pip install -r requirements.txt` in it, place the models, and start with `python server.py`. The requirements above still apply unchanged.

---

### 3. Set up and start for the first time

**Package edition:** extract the archive, then in Terminal run:

```
./launch.sh
```

Nothing is installed on this Mac; the bundled environment inside the folder is used as is.

**Source edition:** extract the archive, then run `./launch.sh` (or double-click `Cynovela-start.command`). On the first run it asks which of the 2 ways to build the environment (see section 1) and builds it. **Either way, the shared conda environment is never created and never modified.**

Then:

1. **Sign in.** The user name and the first password are printed on the screen at the first start. You will be asked to change the password straight away.
2. **Add search targets.** Answer the question shown at startup; or use "Add a search folder" under "Settings" in the app screen; or run `./launch.sh --add` (list with `./launch.sh --list`; icon: `Cynovela-add-folder.command`).
3. **Ask a question.** Open `http://localhost:8765` and type in plain language. Every answer carries the passage it came from — open it and check.
4. **Stop it.** Double-click `Cynovela-stop.command` (or run `bash stop.sh`).

---

### 4. Starting it again later (the next day, after a reboot)

Setup is needed only once. From then on:

- **Start:** double-click `Cynovela-start.command` (or `./launch.sh`). The environment is reused; nothing is rebuilt.
- **Stop:** double-click `Cynovela-stop.command` (or `bash stop.sh`). Your documents and settings remain.
- If it says something is missing and refuses to start, run `./launch.sh --setup` once, then start again.

---

### 5. Reinstalling

Two different situations, two different routes:

- **Rebuild only the environment** (it broke, or you want it fresh — your ingested documents and settings are kept):
  1. Remove the old environment: conda form → `conda env remove -n cynovela-dist`; in-folder form → delete the `.venv-cynovela` folder.
  2. Run `./launch.sh --setup`, then start as usual.
- **Reinstall from scratch** (everything goes, including ingested documents and settings):
  1. Run `bash uninstall.sh` (see section 6 — the folder goes to the Trash).
  2. Extract the downloaded archive again and do section 3 from the top.

---

### 6. Uninstalling

`bash uninstall.sh` — it confirms twice, then:

| It removes / stops | It does NOT touch |
|---|---|
| The running Cynovela started from this folder | conda itself (kept for your other uses) |
| The dedicated conda environment (`cynovela-dist`) | **Shared conda environments — never** |
| This folder, including ingested documents and settings (moved to the **Trash**, not deleted) | Anything whose name does not match |

Disk space returns only after you empty the Trash. You can restore from the Trash.

---

### 7. What each script is (the names alone do not tell you)

| File | What it does |
|---|---|
| `Cynovela-start.command` | **Starts it. Double-click.** |
| `Cynovela-stop.command` | **Stops it. Double-click.** |
| `Cynovela-add-folder.command` | **Adds a folder to be ingested. Double-click.** |
| `launch.sh` | **What the three above call internally. Use this one from the terminal.** |
| `uninstall.sh` | **Removes what this package created.** |
| `cynovela-cli.py` | **Use it from the terminal. Run `doctor` first — it tells you what is missing.** |

`launcher-core.sh` and `tools/launch-body.sh` are internal parts. You never need to touch them.

---

### 8. Using it from the terminal (CLI), and connecting an AI client (MCP)

**CLI — `cynovela-cli.py`.** It talks only to the running server's API. The commands cover the same work the screen can do: see, ask, bring material in, publish, clean up, manage people, and back up. Dangerous operations (`delete` / `users` / `backup` / `settings set`) always show what would happen first and never run without an explicit `--yes`. Standard library only — no extra installs. Run it with the Python this package prepared (package edition: `./.condapack-cynovela/bin/python3`; source edition choice 1: `conda run -n cynovela-dist python3`; or any Python 3.12+):

```
./.condapack-cynovela/bin/python3 cynovela-cli.py doctor
```

**Run `doctor` first.** It works even when the server is not running, and for every missing piece it prints the one line to run next.

| Command | What it does |
|---|---|
| `login --username <name>` | Signs in and remembers the token in `~/.cynovela_cli.env` (mode 600). Reads the password from the terminal, or from standard input with `--password-stdin`. The token has no expiry unless `--hours` / `--seconds` is given. The token itself is never printed |
| `logout` | Forgets the remembered token and tells the server |
| `doctor` | What is missing right now: Python version, models, inference server (LM Studio / Ollama), **whether the configured model is actually loaded**, port, database, conda |
| `status` | Is the server up |
| `workspaces` | List. Also: `create --name <name>` / `update --workspace <id> [--name] [--description] [--add-source <source_id>]` / `archive` / `unarchive` |
| `collections` | List. Also: `create --workspace <id> --name <name>` / `link --collection <id> --from-source <source_id>` (or `--files id,id`) |
| `sources` | List registered sources. `--files <source_id>` lists the files of one source |
| `audit-logs [--limit N]` | Recent audit log entries (admin token) |
| `search --workspace <id> --collection <id> --query "..."` | Returns source fragments only (no answer is shown) |
| `chat --workspace <id> --query "..." [--collection <id>]` | Asks a question and prints the answer with its sources |
| `ingest --path <folder> [--name <name>] [--workspace <id>]` | One line that registers a folder as a source and starts scanning it. Returns a `job_id` at once |
| `scan start --source <id>` / `scan status --job <job_id>` / `scan cancel --source <id>` | Start a scan (returns a `job_id` at once) / see its progress / cancel it |
| `publish start --collection <id>` / `publish status --job <job_id>` / `publish stop` / `publish recover` | Start a publish (returns a `job_id` at once) / progress / stop / recover a stuck one |
| `index-status` | Chunk counts per collection |
| `delete source\|collection\|workspace <id>` | Deletes it. Without `--yes` it only shows what would happen (admin token) |
| `users list` / `create` / `update` / `delete` / `reset-password` | Manage users. Changes need `--yes` (admin token) |
| `backup list` / `create` / `restore` / `delete` | Backups of the database and settings. Changes need `--yes`; after `restore`, restart the server (admin token) |
| `settings show [name]` | Current settings. `name` is one of `llm` (default), `reranker`, `classifier`, `embedding`, `pii`, `vector-store`, `datasync`. API keys are shown only as set / not set, never as values (admin token) |
| `settings models` / `settings test` / `settings providers` | Models at the endpoint / test the LLM connection / selectable presets (admin token) |
| `settings set [name] --set KEY=VALUE` | Changes server settings. Shows before → after, then does nothing unless `--yes` is added; `--dry-run` previews only (admin token) |

Every command accepts `--json` (machine-readable) and `--lang en|ja`. Exit codes: **0** = OK, **1** = bad input, **2** = server unreachable, **3** = authentication failed, **4** = server error. Commands other than `doctor`/`status` need a token. The shortest way to get one is `cynovela-cli login --username cynovela`, which writes it into `~/.cynovela_cli.env` for you. You can also pass one with `--token`, or write `CYNOVELA_URL=` / `CYNOVELA_TOKEN=` into that file by hand. The full list of commands and arguments is in `docs/cli-reference.md`. (The `./launch.sh` flags themselves are covered in `docs/USE-FROM-TERMINAL.txt` — a different topic.)

**MCP — connecting an AI client.** `mcp_server.py` exposes Cynovela's tools to MCP clients (protocol revision 2026-07-28, stdio): searching, viewing, bringing material in (`ingest_source`, progress via `get_job_status`), publishing, and settings — 25 tools, of which 22 are visible by default. The three admin tools (`delete_item` / `manage_users` / `manage_backups`) appear only when the MCP server's env sets `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`. Point your client at it like this (the same snippet is served signed-in at `/api/mcp/config`):

```json
{"mcpServers": {"cynovela": {
  "command": "/path/to/.venv-cynovela/bin/python3",
  "args": ["/path/to/mcp_server.py", "--cynovela-url", "http://127.0.0.1:8765"],
  "env": {"CYNOVELA_TOKEN": "<token issued at web sign-in>"}
}}}
```

What the connected AI can see follows the token's role: a viewer token gets masked text, an admin token does not. Two things people trip over: in LM Studio the file to edit is `mcp.json` (open it from the **Program** panel → **Install** → **Edit mcp.json**), and after registering, **LM Studio still asks you on screen to allow each tool call** — until you allow it, no tool ever runs. The token does not expire unless the caller asked for an expiry when signing in (see `docs/api-reference.md`). The full walkthrough, the settings tools, and the write guard (`CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1`) are in `docs/mcp-guide.md`.

---

### 9. Before you rely on any of it, read these three points

- **This is for learning and experimentation.** It is not built to be a production system, and it comes with no warranty.
- **Masking is not complete.** Names, phone numbers and the like are masked automatically, but some slip through. Do not load confidential material on the assumption that it will be protected.
- **Answers can be wrong.** Always open the citation and check the original text before acting on an answer.

---

### 10. Open only when you need it

| File | What it covers (how it differs from the others) |
|---|---|
| `README.md` | What this tool is, what it can and cannot do, and the environment it runs in |
| `docs/first-run.md` | Never opened Terminal? From the downloaded file to the first answer, nothing skipped |
| `docs/restart.md` | Stopping it, starting it again, and why `--demo` has to stay the same |
| `docs/editions.md` | Which of the four downloads to take, on one page |
| `docs/cli-reference.md` | Every terminal command and every argument |
| `docs/mcp-reference.md` | All 25 MCP tools: what you hand each one, what comes back |
| `docs/api-reference.md` | Every HTTP endpoint (186), read out of the code |
| `docs/HAJIMETE.md` | The gentlest walkthrough, from opening the package to the first answer (screen-first) |
| `docs/GETTING-STARTED.md` | The same first run in more detail, step by step, with what each step prints |
| `docs/quickstart.md` | The short version for people in a hurry (includes the manual, non-launcher route) |
| `docs/STARTUP.md` | Day-to-day start/stop, ports, sign-in, and what to do when it will not start |
| `docs/manual-complete.md` | The complete reference manual for every feature |
| `docs/operations.md` | Operating it over time: logs, backups, maintenance |
| `docs/deployment.md` | Deployment details behind the setup |
| `docs/SETUP-ACCELERATOR.md` | Setting up the external inference server (only if you want it) |
| `docs/USE-FROM-TERMINAL.txt` | Running it from the terminal instead of the icons (same as `./launch.sh --help`) |
| `docs/READ-BEFORE-DISTRIBUTING.md` | Read this before you pass the package on to anyone |
| `docs/NOTICE.md` | Before you start: no warranty, masking limits, checking answers |
| `docs/` | Further reference: how masking works, permissions, the API, and more |

---

# 日本語

**この文書が唯一の入口です。この文書だけで始められます。**
`docs/` 配下の他の文書は参照用です。必要になったときだけ開いてください（一覧は末尾）。

この配布物は **アプリ版（Mac の上で直に動く形。コンテナは使いません）** です。

---

### 1. どちらの配布物を落としましたか

```
1) パッケージ版（M系 Mac の方はこちら・すぐ使える形）
     展開して1行叩くだけで動きます。Python も conda も要りません。
     この Mac には何も入れません。消すときはフォルダごと削除します。
2) ソース版（上記以外の方、または自分で環境を作りたい方）
     起動時に、環境の作り方を2つから選びます:
       1) conda に専用の環境を作る（名前: cynovela-dist）
       2) この Mac の Python（3.12 以上）を使い、このフォルダの中だけに venv を作る
```

**AIモデルは別に落とします**（リリースページの別ファイル、または初回起動が取得を提案します）。どちらの配布物にも入っていません。

---

### 2. システム要件

| 項目 | 要件 |
|---|---|
| macOS | Apple シリコン搭載の Mac（M1 以降）。Intel の Mac・Windows・Linux では動作を確認していません。**パッケージ版は Apple シリコン専用です。** |
| Python | **3.12 以上**（`pyproject.toml` が `requires-python = ">=3.12"` を宣言。`environment.yml` は 3.12.13 を固定）。**3.10・3.11 は使えません。** パッケージ版と、ソース版の選択肢1（conda）では、事前の Python は不要です。 |
| conda | **Miniforge を推奨**（既定のチャネルが conda-forge のため）。**必須ではありません** — パッケージ版とソース版の選択肢2 は conda 無しで動きます。 |
| ディスクの空き | パッケージ版の展開後: **約 3.1 GB**（実測）。ソース版の展開後: 全部入り **約 5.2 GB**／モデル別取得版 **約 8 MB**（実測）。AIモデル: **4.84 GB**（パッケージ版とモデル別取得版は別に落とします。全部入りには入っています）。 |
| メモリ | 8 GB 以上を推奨（既存の記録による値。今回は測り直していません）。 |
| ネットワーク | パッケージ版: 動かすのに不要。AIモデルの取得時のみ必要。ソース版のセットアップは次から取り寄せます: conda-forge / PyPI / github.com（wheel 2本）/ huggingface.co（モデル）。 |
| 回答用の LLM | LM Studio もしくは OpenAI 互換 API（答えを作るには実 LLM が要ります）。 |

**起動シークエンスを使わずに手で入れる場合**（`./launch.sh` を使えないときのみ）: Python は **3.12 以上**をご自身で用意し、専用の環境を作り（conda なら名前 `cynovela-dist`、またはこのフォルダの中の venv。共有の環境は作らない・書き換えない）、その中で `pip install -r requirements.txt` を実行し、モデルを配置して `python server.py` で起動します。上の要件はそのまま適用されます。

---

### 3. セットアップと初回の起動

**パッケージ版:** 展開して、ターミナルで次の1行を叩きます。

```
./launch.sh
```

この Mac には何も入れません。フォルダの中に同梱された環境をそのまま使います。

**ソース版:** 展開して `./launch.sh` を叩きます（または `Cynovela-start.command` をダブルクリック）。初回に、環境の作り方（1節の2択）を聞かれ、作られます。**どちらを選んでも、共有の conda 環境は作りません・書き換えません。**

そのあとは:

1. **ログインする。** ユーザー名と最初のパスワードは、はじめて起動したときに画面に出ます。入るとすぐパスワードの変更を求められます。
2. **検索の対象を足す。** 起動したときに聞かれる画面で足す / アプリ画面の「設定」の「検索の対象フォルダを足す」から足す / ターミナルで `./launch.sh --add`（一覧は `./launch.sh --list`。アイコンなら `Cynovela-add-folder.command`）。
3. **質問する。** `http://localhost:8765` を開き、普通の言葉で聞きます。答えには必ず根拠にした箇所が付きます。開いて原文を確かめてください。
4. **止める。** `Cynovela-stop.command` をダブルクリックします（または `bash stop.sh`）。

---

### 4. 途中から起動し直すには（翌日・再起動のあと）

セットアップは最初の1回だけです。以後は:

- **起動:** `Cynovela-start.command` をダブルクリック（または `./launch.sh`）。環境はそのまま使われ、作り直しは起きません。
- **停止:** `Cynovela-stop.command` をダブルクリック（または `bash stop.sh`）。資料と設定はそのまま残ります。
- 「足りないものがあるので起動しません」と出たときは、`./launch.sh --setup` を1回実行してから、もう一度起動してください。

---

### 5. 再インストールするには

状況が2つ、道も2つあります。

- **環境だけ作り直す**（環境が壊れた・作り直したい。取り込んだ資料と設定は残ります）:
  1. 古い環境を消します。conda の形 → `conda env remove -n cynovela-dist`。フォルダ内の形 → `.venv-cynovela` フォルダを削除。
  2. `./launch.sh --setup` を実行し、あとは普段どおり起動します。
- **まっさらから入れ直す**（取り込んだ資料・設定も含めて全部消えます）:
  1. `bash uninstall.sh` を実行します（6節参照。フォルダはゴミ箱へ入ります）。
  2. 落とした配布物をもう一度展開し、3節を最初からやり直します。

---

### 6. 消すには

`bash uninstall.sh` — 2回確認したあと、次を行います。

| 消す・止めるもの | 触らないもの |
|---|---|
| このフォルダから起こした稼働中の Cynovela | conda そのもの（他の用途のため残します） |
| 専用の conda 環境（`cynovela-dist`） | **共有の conda 環境 — 決して消しません** |
| このフォルダ全体（取り込んだ資料・設定を含む。削除ではなく**ゴミ箱へ**） | 名前が一致しないもの |

ディスクの容量は、ゴミ箱を空にするまで戻りません。ゴミ箱から戻すこともできます。

---

### 7. スクリプトの名前の対応表（名前だけでは分からないため）

| ファイル | 何をするもの |
|---|---|
| `Cynovela-start.command` | **起動する。ダブルクリック** |
| `Cynovela-stop.command` | **止める。ダブルクリック** |
| `Cynovela-add-folder.command` | **読み込むフォルダを足す。ダブルクリック** |
| `launch.sh` | **上の3つが内側で呼んでいるもの。ターミナルから使うときはこれ** |
| `uninstall.sh` | **この配布物が作ったものを消す** |
| `cynovela-cli.py` | **端末から使う。まず `doctor` を叩けば、足りないものが分かる** |

`launcher-core.sh` と `tools/launch-body.sh` は内側の部品です。触る必要はありません。

---

### 8. 端末から使う（CLI）と、AI クライアントを繋ぐ（MCP）

**CLI — `cynovela-cli.py`。** 稼働中のサーバの API だけを叩きます。命令は画面でできる作業と同じ範囲を覆います: 見る・探す・資料を入れる・公開する・片づける・利用者を管理する・控えを取る。危険な操作（`delete` / `users` / `backup` / `settings set`）は必ず「何が起きるか」を先に見せ、明示的な `--yes` なしには決して実行しません。標準ライブラリのみで、追加の導入は不要です。この配布物が用意した Python で叩きます（パッケージ版: `./.condapack-cynovela/bin/python3`、ソース版の選択肢1: `conda run -n cynovela-dist python3`、または任意の Python 3.12 以上）:

```
./.condapack-cynovela/bin/python3 cynovela-cli.py doctor
```

**最初に `doctor` を叩いてください。** サーバが起きていなくても動き、足りないものごとに「次に打つ1行」を出します。

| 命令 | すること |
|---|---|
| `login --username <名前>` | ログインして、トークンを `~/.cynovela_cli.env` へ覚えさせます（自分だけが読める権限）。合言葉はターミナルから、または `--password-stdin` で標準入力から受け取ります。`--hours` / `--seconds` を渡さないかぎりトークンに期限はつきません。トークンそのものは画面に出しません |
| `logout` | 覚えているトークンを忘れ、サーバにも伝えます |
| `doctor` | いま何が足りないか: Python の版・モデル・推論サーバ（LM Studio / Ollama）・**設定されたモデルが実際に読み込まれているか**・番号・データベース・conda |
| `status` | サーバが起きているか |
| `workspaces` | 一覧。ほかに: `create --name <名前>` / `update --workspace <id> [--name] [--description] [--add-source <資料のid>]` / `archive` / `unarchive` |
| `collections` | 一覧。ほかに: `create --workspace <id> --name <名前>` / `link --collection <id> --from-source <資料のid>`（または `--files id,id`） |
| `sources` | 登録済みの取り込み元の一覧。`--files <資料のid>` でその中のファイル一覧 |
| `audit-logs [--limit N]` | 監査ログの直近の記録（管理者トークン） |
| `search --workspace <id> --collection <id> --query "..."` | 出典の断片だけを返します（回答は表示しません） |
| `chat --workspace <id> --query "..." [--collection <id>]` | 質問して、回答と出典を表示します |
| `ingest --path <フォルダ> [--name <名前>] [--workspace <id>]` | フォルダを資料として登録し走査を始める、を1行で。`job_id` を即返します |
| `scan start --source <id>` / `scan status --job <job_id>` / `scan cancel --source <id>` | 走査を始める（`job_id` を即返す）/ 進み具合を見る / 中止する |
| `publish start --collection <id>` / `publish status --job <job_id>` / `publish stop` / `publish recover` | 公開を始める（`job_id` を即返す）/ 進み具合 / 止める / 固着からの復旧 |
| `index-status` | コレクションごとの塊の数 |
| `delete source\|collection\|workspace <id>` | 消します。`--yes` を付けないときは「何が起きるか」を見せるだけです（管理者トークン） |
| `users list` / `create` / `update` / `delete` / `reset-password` | 利用者の管理。変更には `--yes` が必須（管理者トークン） |
| `backup list` / `create` / `restore` / `delete` | データベースと設定の控え。変更には `--yes` が必須。`restore` の後はサーバを起動し直してください（管理者トークン） |
| `settings show [対象]` | いまの設定。対象は `llm`（既定）/ `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync`。API キーは設定あり / なし だけを示し、値は出しません（管理者トークン） |
| `settings models` / `settings test` / `settings providers` | 接続先のモデル一覧 / LLM 接続の確認 / 選べるプリセット（管理者トークン） |
| `settings set [対象] --set KEY=VALUE` | サーバの設定を変えます。変更前 → 変更後を見せてから、`--yes` を足さない限り何もしません。`--dry-run` は確認だけ（管理者トークン） |

全命令に `--json`（機械で読める形）と `--lang en|ja` があります。終了コード: **0** = 正常、**1** = 入力の誤り、**2** = サーバへ到達できない、**3** = 認証に失敗、**4** = サーバが誤りを返した。`doctor`・`status` 以外はトークンが要ります。いちばん短い道は `cynovela-cli login --username cynovela` で、これが `~/.cynovela_cli.env` へ書いてくれます。`--token` で渡すことも、そのファイルへ自分で `CYNOVELA_URL=` / `CYNOVELA_TOKEN=` を書くこともできます。命令と引数の全数は `docs/cli-reference.md` にあります。（`./launch.sh` 自体のフラグは別の話で、`docs/USE-FROM-TERMINAL.txt` にあります。）

**MCP — AI クライアントを繋ぐ。** `mcp_server.py` が Cynovela の道具を MCP クライアントへ出します（プロトコル版 2026-07-28・stdio）: 検索・見る・資料を入れる（`ingest_source`。進み具合は `get_job_status`）・公開・設定の 25 個で、既定で見えるのは 22 個です。管理系の 3 個（`delete_item` / `manage_users` / `manage_backups`）は、MCP サーバの env に `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を書いたときだけ現れます。クライアントには次の形で指します（同じスニペットはログイン後の `/api/mcp/config` でも取れます）:

```json
{"mcpServers": {"cynovela": {
  "command": "/path/to/.venv-cynovela/bin/python3",
  "args": ["/path/to/mcp_server.py", "--cynovela-url", "http://127.0.0.1:8765"],
  "env": {"CYNOVELA_TOKEN": "<画面のログインで発行されたトークン>"}
}}}
```

繋いだ AI に見えるものはトークンの資格に従います: 閲覧者のトークンでは伏字済みの本文、管理者のトークンでは伏字前の本文です。つまずきやすい点が2つあります: LM Studio で書くファイルは `mcp.json` です（**Program** パネル → **Install** → **Edit mcp.json** から開けます）。そして登録した後も、**LM Studio は道具の呼び出しごとに画面で許可を求めます** — 許可を出すまで道具は一度も動きません。トークンは、ログインのときに期間を渡さないかぎり切れません（`docs/api-reference.md` を参照）。手順の全体・設定系の道具・書き込みの守り（`CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1`）は `docs/mcp-guide.md` にあります。

---

### 9. 使う前に、次の3つをお読みください

- **これは学習と試用のためのものです。** 業務の本番システムとして使うことを想定して作られていません。無保証です。
- **マスキングは完全ではありません。** 氏名・電話番号などを自動で伏せますが、取りこぼしは起こります。伏せられることを前提に機密資料を入れないでください。
- **答えは間違うことがあります。** 必ず出典を開き、原文で確かめてからお使いください。

---

### 10. 必要になったときに開くもの

| ファイル | 何が書いてあるか（他とどう違うか） |
|---|---|
| `README.md` | このツールが何か・できること できないこと・動作環境 |
| `docs/first-run.md` | ターミナルを開いたことが無い方へ。落としたファイルから最初の答えまで。省略なし |
| `docs/restart.md` | 止め方と起こし直し方。`--demo` を毎回そろえる理由 |
| `docs/editions.md` | 4つの落とし物のどれを選ぶか。1枚 |
| `docs/cli-reference.md` | ターミナルの命令と引数の全数 |
| `docs/mcp-reference.md` | MCP の道具25件。何を渡すと何が返るか |
| `docs/api-reference.md` | HTTP の口の全数（186件）。コードから起こしたもの |
| `docs/HAJIMETE.md` | いちばんやさしいガイド。開いてから最初の答えが返るまで（画面中心） |
| `docs/GETTING-STARTED.md` | 同じ初回の道のりをより詳しく、順を追って。各段で画面に出るものつき |
| `docs/quickstart.md` | 急ぐ方向けの短い手順（launch.sh を使わない手動の道も含む） |
| `docs/STARTUP.md` | 日常の起動と停止・ポート・ログイン・起動しないときの対処 |
| `docs/manual-complete.md` | 全機能の完全マニュアル（リファレンス） |
| `docs/operations.md` | 使い続けるための運用: ログ・バックアップ・保守 |
| `docs/deployment.md` | セットアップの裏側にある導入の詳細 |
| `docs/SETUP-ACCELERATOR.md` | 外部の推論サーバの立て方（使いたいときだけ） |
| `docs/USE-FROM-TERMINAL.txt` | アイコンではなくターミナルから使う方法（`./launch.sh --help` と同一） |
| `docs/READ-BEFORE-DISTRIBUTING.md` | 誰かに配る前にお読みください |
| `docs/NOTICE.md` | 使う前のご注意。無保証・マスキングの限界・答えの確かめ方 |
| `docs/` | さらに参照用: マスキングの仕組み・権限・API など |
