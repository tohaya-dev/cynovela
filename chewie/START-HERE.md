# START HERE

> **はじめての方は [`QUICKSTART.md`](QUICKSTART.md) を開いてください。**
> 落とすところから、最初の質問に答えが返るところまでを1本にまとめてあります。
> この文書は、そのあとに読むくわしい説明です。
>
> **If this is your first time, open [`QUICKSTART.md`](QUICKSTART.md).**
> It takes you from the download to your first answer in one place.
> This document is the detailed reference you read afterwards.

**日本語版はこちら → [日本語](#日本語)**

## English

**This is the only entry document. You can get started with this document alone.**
Everything else under `docs/` is reference material — open it only when you need it.
**Every one of those documents is listed in [`docs/INDEX.md`](docs/INDEX.md), sorted by
reader: using it / installing and running it / looking things up. When you do not know
which file you want, open that one.** The same list is repeated at the end of this page.

This package is the **application build (runs on macOS directly, no container)**.

---

### 1. About this download

**This is the package edition.** Extract it and run one line. No Python and no
conda are needed. Nothing is installed on this Mac. To remove it, delete the
folder. **It runs on Apple silicon only.**

**The AI models are downloaded separately** (`...models-1.2.0.tar.gz.part00` to
`part02` on the release page). They are not inside this download. How to connect
them is in section 2 of [`QUICKSTART.md`](QUICKSTART.md).
**The AI models go in `store/models/` — they will not be found anywhere else.**

If you want to build it from source yourself, get the repository and run
`./launch.sh` from `chewie/`. No source archive is placed on the release page.

---

### 2. System requirements

| Item | Requirement |
|---|---|
| macOS | Apple silicon Mac (M1 or later). Intel Macs, Windows and Linux are not verified. **The package edition runs on Apple silicon only.** |
| Python | **3.12 or later** (`pyproject.toml` declares `requires-python = ">=3.12"`; `environment.yml` pins 3.12.13). **3.10 and 3.11 cannot be used.** Not needed for the package edition, nor for source-edition choice 1 (conda fetches its own). |
| conda | **Miniforge recommended** (its default channel is conda-forge). **Not required** — the package edition and source-edition choice 2 work without it. |
| Free disk space | Package edition expanded: **about 3.1 GB** (measured). Source edition: **about 8 MB** before the environment is built (measured). AI models: **4.84 GB** (a separate download for both editions). |
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

Nothing is installed on this Mac; the bundled environment inside the folder is
used as is. The very first time you run `./launch.sh` (whatever the flags), it
runs the bundled `conda-unpack` once by itself to settle that environment into
where you unpacked it — you do not run it yourself, and it does not run again.

Three notes about **where you put the folder**:

- **Do not extract it under a cloud-synced folder** (iCloud Drive, Dropbox,
  OneDrive, Google Drive). Sync replaces files with placeholders that cannot be
  executed. `./launch.sh` warns when it detects this, but the safe move is
  `~/Downloads` or your home folder.
- **A folder received through a browser or a shared link carries macOS's
  quarantine mark.** `./launch.sh` removes that mark — inside the extracted
  folder only — at the start of every launch. To remove it by hand instead:
  `xattr -dr com.apple.quarantine <extracted folder>`. Whether macOS blocks
  anything before that depends on the receiving Mac's settings.
- **You can move the extracted folder to another location later** — documents
  and settings travel with it, because everything it writes lives in `store/`
  inside the folder. Stop it first, move the whole folder, then start it again
  from the new place with the same `./launch.sh`.

**Source edition:** extract the archive, then run `./launch.sh` (or double-click `Cynovela-start.command`). On the first run it asks which of the 2 ways to build the environment (see section 1) and builds it. **Either way, the shared conda environment is never created and never modified.**

Then:

1. **Sign in.**

   **First sign-in. You do not need to look for the password.**
   **It is printed on screen, once, the first time you start.**

       ────────────────────────────────────────────────
         First login / はじめてのログイン
           Open / ひらく          : http://localhost:8765
           User name / ユーザー名 : cynovela
           Password / パスワード  : (it appears here)
         You will be asked to change it on the first sign-in.
         Shown only this once.
       ────────────────────────────────────────────────

   - **Shown on the first start only.** It does not appear again.
   - **The administrator is `cynovela`; the viewer account is `demo`.**
   - **The administrator is asked to change the password on first sign-in.** The viewer is not.
   - **Nothing is sent to you separately.**
   - **If you missed that screen**, the same value is in `cynovela.yaml` in the folder you
     unpacked, next to `launch.sh`: `auth.admin_initial_password`
     (`auth.viewer_initial_password` for the viewer).
2. **Add search targets.** Answer the question shown at startup; or use "Add a search folder" under "Settings" in the app screen; or run `./launch.sh --add` (list with `./launch.sh --list`; icon: `Cynovela-add-folder.command`).
3. **Ask a question.** Open `http://localhost:8765` and type in plain language. Every answer carries the passage it came from — open it and check.
4. **Stop it.** Double-click `Cynovela-stop.command` (or run `bash stop.sh`).

---

### 4. Starting it again later (the next day, after a reboot)

Setup is needed only once. From then on:

- **Start:** double-click `Cynovela-start.command` (or `./launch.sh`). The environment is reused; nothing is rebuilt.
- **Stop:** double-click `Cynovela-stop.command` (or `bash stop.sh`). Your documents and settings remain.
- If a message reports that something is missing and the start does not complete, run `./launch.sh --setup` once, then start again.

---

### 5. Reinstalling

Two different situations, two different routes:

- **Rebuild only the environment** (it broke, or you want it fresh — your ingested documents and settings are kept):
  1. Remove the old environment. Which one you have depends on how you started:
     source edition, conda form → `conda env remove -n cynovela-dist`;
     source edition, in-folder form → delete the `.venv-cynovela` folder.
  2. Run `./launch.sh --setup`, then start as usual.

  **Package edition:** this route does not apply. Its Python lives in the bundled
  `.condapack-cynovela` folder, which comes with the download rather than being built
  here, so `./launch.sh --setup` cannot recreate it. If it is broken, extract the
  downloaded archive again (your `store/` folder holds the ingested documents and
  settings — copy it across before you replace the folder).
- **Reinstall from scratch** (everything goes, including ingested documents and settings):
  1. Run `bash uninstall.sh` (see section 6 — the folder goes to the Trash).
  2. Extract the downloaded archive again and do section 3 from the top.

---

### 6. Uninstalling

**App edition** (`.pkg`) — in preparation; not part of this release.

**Package edition and source editions** — `bash uninstall.sh`. It confirms twice, then:

| It removes / stops | It does NOT touch |
|---|---|
| The running Cynovela started from this folder | conda itself (kept for your other uses) |
| Source editions only: the dedicated conda environment (`cynovela-dist`). The package edition never created one — its Python lives in `.condapack-cynovela` inside this folder and goes with it | **Shared conda environments — never** |
| This folder, including ingested documents and settings (moved to the **Trash**, not deleted) | Anything whose name does not match |

Disk space returns only after you empty the Trash. You can restore from the Trash.

---

### 7. What each script is (the names alone do not tell you)

| File | What it does |
|---|---|
| `Cynovela-start.command` | **Starts it (production, empty database). Double-click.** |
| `Cynovela-demo.command` | **Starts the demo with the bundled sample material. Double-click.** Same as `./launch.sh --demo`; the material is ingested automatically at the first start |
| `Cynovela-stop.command` | **Stops it. Double-click.** |
| `Cynovela-add-folder.command` | **Adds a folder to be ingested. Double-click.** |
| `check-managed-mac.command` | **Checks whether this Mac will let you run it. Double-click.** It only measures — it changes no setting, needs no administrator password, and works around no management policy. Useful on a managed Mac (under MDM): it prints a judgement for each item it checks and ends with an overall verdict, and when something is blocked it states which edition that blocks. The same file is also downloadable from the release page, so you can run it *before* downloading anything big. |
| `launch.sh` | **What the three above call internally. Use this one from the terminal.** |
| `uninstall.sh` | **Removes what this package created.** |
| `cynovela-cli.py` | **Use it from the terminal. Run `doctor` first — it tells you what is missing.** |

`launcher-core.sh` and `tools/launch-body.sh` are internal parts. You never need to touch them.

**The `./launch.sh` flags** (the same list is printed by `./launch.sh --help` and
kept in `docs/USE-FROM-TERMINAL.txt`):

| Flag | What it does |
|---|---|
| (none) | Starts by asking questions you answer with a number |
| `--demo` | Starts the demo with the bundled dummy documents (they are ingested automatically at the first start). Double-clicking `Cynovela-demo.command` does the same |
| `--add` / `--list` / `--remove <name>` | Add / list / remove folders to be read |
| `--setup` | Installs what is required to run, then stops |
| `--check` | Does not start; only checks the conditions for running |
| `--base conda\|venv\|none` | Decides in advance where python is prepared (used with `--setup`) |
| `--port <number>` | Changes the number it listens on (default 8765) |
| `--local-only` | Limits listening to the inside of your own machine only |
| `--help` / `--help-all` | The list above / the testing and development flags as well |

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

Every command accepts `--json` (machine-readable) and `--lang en|ja`. Exit codes: **0** = OK, **1** = bad input, **2** = server unreachable, **3** = authentication failed, **4** = server error. Commands other than `doctor`/`status` need a token. The shortest way to get one is `cynovela-cli login --username cynovela`, which writes it into `~/.cynovela_cli.env` for you. You can also pass one with `--token`, or write `CYNOVELA_URL=` / `CYNOVELA_TOKEN=` into that file by hand. The full list of commands and arguments is in `docs/reference/cli.md`. (The `./launch.sh` flags themselves are covered in `docs/USE-FROM-TERMINAL.txt` — a different topic.)

**MCP — connecting an AI client.** `mcp_server.py` exposes Cynovela's tools to MCP clients (protocol revision 2026-07-28, stdio): searching, viewing, bringing material in (`ingest_source`, progress via `get_job_status`), publishing, and settings — 25 tools, of which 22 are visible by default. The three admin tools (`delete_item` / `manage_users` / `manage_backups`) appear only when the MCP server's env sets `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1`. Point your client at it like this (the same snippet is served signed-in at `/api/mcp/config`):

```json
{"mcpServers": {"cynovela": {
  "command": "/path/to/.condapack-cynovela/bin/python3",
  "args": ["/path/to/mcp_server.py", "--cynovela-url", "http://127.0.0.1:8765"],
  "env": {"CYNOVELA_TOKEN": "<token issued at web sign-in>"}
}}}
```

What the connected AI can see follows the token's role: a viewer token gets masked text, an admin token does not. Two common problems: in LM Studio the file to edit is `mcp.json` (open it from the **Program** panel → **Install** → **Edit mcp.json**), and after registering, **LM Studio still asks you on screen to allow each tool call** — until you allow it, no tool ever runs. The token does not expire unless the caller asked for an expiry when signing in (see `docs/reference/api.md`). Every tool, with what you hand it and what comes back, is in `docs/reference/mcp.md`; the walkthrough of connecting a client, the settings tools, and the write guard (`CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1`) are in `docs/operations.md`.

---

### 9. Before you rely on any of it, read these three points

- **This is for learning and experimentation.** It is not built to be a production system, and it comes with no warranty.
- **Masking is not complete.** Names, phone numbers and the like are masked automatically, but some slip through. Do not load confidential material on the assumption that it will be protected.
- **Answers can be wrong.** Always open the citation and check the original text before acting on an answer.

---

### 10. Open only when you need it

**The whole list lives in [`docs/INDEX.md`](docs/INDEX.md)** — every document that ships
here, sorted by reader (using it / installing and running it / looking things up), each
with a line saying what is in it. If you remember only one path from this page, remember
that one. The same documents are repeated below.

| File | What it covers (how it differs from the others) |
|---|---|
| [`docs/INDEX.md`](docs/INDEX.md) | **The index of every document. Open this when you do not know which file you want** |
| `README.md` | What this tool is, what it can and cannot do, and the environment it runs in |
| `docs/getting-started.md` | Never opened Terminal? From the downloaded file to the first answer, nothing skipped — and the day-to-day start and stop after that |
| `docs/editions.md` | Which edition to take, on one page |
| `docs/concept.md` | What this tool is for, and how it differs from the tools it refers to |
| `docs/architecture.md` | How it works inside: ingest and classification, search, the scores, the shape of an answer |
| `docs/security.md` | Roles and permissions, PII detection and masking, the guardrails, and the ways of use that are not recommended |
| `docs/limits.md` | What it cannot do: what masking misses, formats it cannot read, features that are only a skeleton |
| `docs/operations.md` | Installing it and keeping it running: placing it, connecting an LLM, MCP from external tools, LAN sharing, backup and restore, logs, users, the port |
| `docs/handson.md` | Exercises against the sample material bundled in `dummy-corpus/` |
| `docs/faq.md` | The questions asked most often, answered short |
| `docs/reference/cli.md` | Every terminal command and every argument |
| `docs/reference/mcp.md` | Every MCP tool: what you hand each one, what comes back |
| `docs/reference/api.md` | Every HTTP endpoint, read out of the code |
| `docs/reference/changelog.md` | What changed in each version |
| `docs/USE-FROM-TERMINAL.txt` | Running it from the terminal instead of the icons (every `./launch.sh` flag) |
| `docs/READ-BEFORE-DISTRIBUTING.md` | Read this before you pass the package on to anyone |
| `docs/NOTICE.md` | Before you start: no warranty, masking limits, checking answers |
| `docs/BUNDLED-DATA.md` | What sample material is bundled, and what is created on this machine at the first startup |

---

# 日本語

**この文書が唯一の入口です。この文書だけで始められます。**
`docs/` 配下の他の文書は参照用です。必要になったときだけ開いてください。
**その全数は [`docs/INDEX.md`](docs/INDEX.md) に、読み手ごと（使う人 / 入れる人・回す人 /
引く人）に並べてあります。どのファイルが要るか分からないときは、まずこれを開いてください。**
同じ一覧はこのページの末尾にもあります。

この配布物は **アプリ版（Mac の上で直に動く形。コンテナは使いません）** です。

---

### 1. この配布物について

**これはパッケージ版です。** 展開して1行叩くだけで動きます。Python も conda も
要りません。この Mac には何も入れません。消すときはフォルダごと削除します。
**Apple シリコン専用です。**

**AIモデルは別に落とします**（リリースのページの `...models-1.2.0.tar.gz.part00`〜
`part02`）。この配布物には入っていません。つなぎ方は
[`QUICKSTART.md`](QUICKSTART.md) の2節にあります。
**AIモデルは `store/models/` に置きます。この場所でないと見つけられません。**

ソースから自分で組み立てたい方は、リポジトリを取得して `chewie/` から
`./launch.sh` を叩いてください。リリースのページにソースの書庫は置いていません。

---

### 2. システム要件

| 項目 | 要件 |
|---|---|
| macOS | Apple シリコン搭載の Mac（M1 以降）。Intel の Mac・Windows・Linux では動作を確認していません。**パッケージ版は Apple シリコン専用です。** |
| Python | **3.12 以上**（`pyproject.toml` が `requires-python = ">=3.12"` を宣言。`environment.yml` は 3.12.13 を固定）。**3.10・3.11 は使えません。** パッケージ版と、ソース版の選択肢1（conda）では、事前の Python は不要です。 |
| conda | **Miniforge を推奨**（既定のチャネルが conda-forge のため）。**必須ではありません** — パッケージ版とソース版の選択肢2 は conda 無しで動きます。 |
| ディスクの空き | パッケージ版の展開後: **約 3.1 GB**（実測）。ソース版: 環境を作る前は**約 8 MB**（実測）。AIモデル: **4.84 GB**（どちらの形でも別に落とします）。 |
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
いちばん最初に `./launch.sh` を叩いたとき（どの指定でも）、同梱の `conda-unpack` が
1回だけ自動で走り、展開した場所に環境をなじませます。自分で叩く必要はなく、
2回目からは走りません。

**フォルダをどこに置くか**について、3つ:

- **クラウド同期のフォルダの下には展開しないでください**（iCloud Drive・Dropbox・
  OneDrive・Google Drive）。同期はファイルを実行できない置き代わりに差し替えます。
  `./launch.sh` は検出して警告しますが、安全なのは `~/Downloads` かホームフォルダです。
- **ブラウザや共有リンク経由で受け取ったフォルダには、macOS の検疫の印が付きます。**
  `./launch.sh` は毎回の起動の頭で、この印を**展開したフォルダの中に限って**外します。
  手で外すなら `xattr -dr com.apple.quarantine <展開したフォルダ>` です。それより前に
  macOS が何かを止めるかどうかは、受け取った Mac の設定によります。
- **展開したフォルダは、あとから別の場所へ移せます。** 資料と設定も一緒に移ります。
  書き込む先がすべてフォルダの中の `store/` だからです。止めてから、フォルダごと移し、
  移した先で同じ `./launch.sh` で起こしてください。

**ソース版:** 展開して `./launch.sh` を叩きます（または `Cynovela-start.command` をダブルクリック）。初回に、環境の作り方（1節の2択）を聞かれ、作られます。**どちらを選んでも、共有の conda 環境は作りません・書き換えません。**

そのあとは:

1. **ログインする。**

   **最初のログイン。パスワードを探す必要はありません。**
   **はじめて起動したとき、ターミナルの画面に1回だけ出ます。**

       ────────────────────────────────────────────────
         First login / はじめてのログイン
           Open / ひらく          : http://localhost:8765
           User name / ユーザー名 : cynovela
           Password / パスワード  : （ここに出ます）
         最初のログインで変更を求められます。
         この表示が出るのは初回だけです。
       ────────────────────────────────────────────────

   - **出るのは初回だけです。**2回目からは出ません。
   - **管理者は `cynovela`、閲覧者は `demo` です。**
   - **管理者は最初のログインでパスワードの変更を求められます。**閲覧者には求めません。
   - **別便で届くものはありません。**
   - **この画面を見逃した場合**は、展開したフォルダの `cynovela.yaml`
     （`launch.sh` と同じ場所）の `auth.admin_initial_password` に同じ値が書いてあります
     （閲覧者のぶんは `auth.viewer_initial_password`）。
2. **検索の対象を足す。** 起動したときに聞かれる画面で足す / アプリ画面の「設定」の「検索の対象フォルダを足す」から足す / ターミナルで `./launch.sh --add`（一覧は `./launch.sh --list`。アイコンなら `Cynovela-add-folder.command`）。
3. **質問する。** `http://localhost:8765` を開き、普通の言葉で聞きます。答えには必ず根拠にした箇所が付きます。開いて原文を確かめてください。
4. **止める。** `Cynovela-stop.command` をダブルクリックします（または
   `bash stop.sh`）。

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
  1. 古い環境を消します。どちらを持っているかは、どの形で始めたかで決まります。
     ソース版・conda の形 → `conda env remove -n cynovela-dist`。
     ソース版・フォルダ内の形 → `.venv-cynovela` フォルダを削除。
  2. `./launch.sh --setup` を実行し、あとは普段どおり起動します。

  **パッケージ版はこの道を使えません。** パッケージ版の Python は、同梱の
  `.condapack-cynovela` フォルダに入っています。ここで作るものではなく落とした物に
  最初から入っているため、`./launch.sh --setup` では作り直せません。壊れているときは、
  落とした配布物をもう一度展開してください（取り込んだ資料と設定は `store/` フォルダに
  入っています。フォルダを入れ替える前に、こちらを写しておいてください）。
- **まっさらから入れ直す**（取り込んだ資料・設定も含めて全部消えます）:
  1. `bash uninstall.sh` を実行します（6節参照。フォルダはゴミ箱へ入ります）。
  2. 落とした配布物をもう一度展開し、3節を最初からやり直します。

---

### 6. 消すには

**アプリ版**（`.pkg`）は準備中です。この版には入っていません。

**パッケージ版とソース版**は `bash uninstall.sh` です。2回確認したあと、次を行います。

| 消す・止めるもの | 触らないもの |
|---|---|
| このフォルダから起こした稼働中の Cynovela | conda そのもの（他の用途のため残します） |
| ソース版のみ: 専用の conda 環境（`cynovela-dist`）。パッケージ版はこれを作っておらず、Python はこのフォルダの中の `.condapack-cynovela` に在り、フォルダと一緒に消えます | **共有の conda 環境 — 決して消しません** |
| このフォルダ全体（取り込んだ資料・設定を含む。削除ではなく**ゴミ箱へ**） | 名前が一致しないもの |

ディスクの容量は、ゴミ箱を空にするまで戻りません。ゴミ箱から戻すこともできます。

---

### 7. スクリプトの名前の対応表（名前だけでは分からないため）

| ファイル | 何をするもの |
|---|---|
| `Cynovela-start.command` | **起動する（本番＝空のデータベース）。ダブルクリック** |
| `Cynovela-demo.command` | **同梱のサンプル資料のデモで起動する。ダブルクリック**。`./launch.sh --demo` と同じで、資料は初回起動時に自動で取り込まれます |
| `Cynovela-stop.command` | **止める。ダブルクリック** |
| `Cynovela-add-folder.command` | **読み込むフォルダを足す。ダブルクリック** |
| `check-managed-mac.command` | **この Mac で動かせるかを下調べする。ダブルクリック**。測るだけで、設定は変えず、管理者のパスワードも要らず、管理の仕組みも迂回しない。管理された Mac（MDM 配下）で役に立つ: 調べる項目ごとに判定を出し、最後に全体の判定を出す。何かが止められているときは、それがどの形を止めるのかまで言う。同じファイルはリリースのページにも置いてあり、大きなものを落とす**前**に試せる |
| `launch.sh` | **上の3つが内側で呼んでいるもの。ターミナルから使うときはこれ** |
| `uninstall.sh` | **この配布物が作ったものを消す** |
| `cynovela-cli.py` | **端末から使う。まず `doctor` を叩けば、足りないものが分かる** |

`launcher-core.sh` と `tools/launch-body.sh` は内側の部品です。触る必要はありません。

**`./launch.sh` の指定の一覧**（同じ一覧は `./launch.sh --help` でも見られ、
`docs/USE-FROM-TERMINAL.txt` にも置いてあります）:

| 指定 | すること |
|---|---|
| （何も付けない） | 聞かれたことに番号で答えるだけで起動します |
| `--demo` | 同梱のダミー資料を使うデモで起動します（初回起動時に自動で取り込まれます）。`Cynovela-demo.command` のダブルクリックでも同じです |
| `--add` / `--list` / `--remove <名前>` | 読み込むフォルダを足す / 一覧で出す / 外す |
| `--setup` | 動かすのに要るものを入れます（入れたら止まります） |
| `--check` | 起動せず、動く条件だけを調べます |
| `--base conda\|venv\|none` | python を用意する場所を先に決めます（`--setup` と一緒に使います） |
| `--port <番号>` | 待ち受ける番号を変えます（既定 8765） |
| `--local-only` | 待ち受けを自分のマシンの中だけに絞ります |
| `--help` / `--help-all` | 上の一覧 / 試験・開発のための指定も含めた全数 |

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

全命令に `--json`（機械で読める形）と `--lang en|ja` があります。終了コード: **0** = 正常、**1** = 入力の誤り、**2** = サーバへ到達できない、**3** = 認証に失敗、**4** = サーバが誤りを返した。`doctor`・`status` 以外はトークンが要ります。いちばん短い道は `cynovela-cli login --username cynovela` で、これが `~/.cynovela_cli.env` へ書いてくれます。`--token` で渡すことも、そのファイルへ自分で `CYNOVELA_URL=` / `CYNOVELA_TOKEN=` を書くこともできます。命令と引数の全数は `docs/reference/cli.md` にあります。（`./launch.sh` 自体のフラグは別の話で、`docs/USE-FROM-TERMINAL.txt` にあります。）

**MCP — AI クライアントを繋ぐ。** `mcp_server.py` が Cynovela の道具を MCP クライアントへ出します（プロトコル版 2026-07-28・stdio）: 検索・見る・資料を入れる（`ingest_source`。進み具合は `get_job_status`）・公開・設定の 25 個で、既定で見えるのは 22 個です。管理系の 3 個（`delete_item` / `manage_users` / `manage_backups`）は、MCP サーバの env に `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を書いたときだけ現れます。クライアントには次の形で指します（同じスニペットはログイン後の `/api/mcp/config` でも取れます）:

```json
{"mcpServers": {"cynovela": {
  "command": "/path/to/.condapack-cynovela/bin/python3",
  "args": ["/path/to/mcp_server.py", "--cynovela-url", "http://127.0.0.1:8765"],
  "env": {"CYNOVELA_TOKEN": "<画面のログインで発行されたトークン>"}
}}}
```

繋いだ AI に見えるものはトークンの資格に従います: 閲覧者のトークンでは伏字済みの本文、管理者のトークンでは伏字前の本文です。つまずきやすい点が2つあります: LM Studio で書くファイルは `mcp.json` です（**Program** パネル → **Install** → **Edit mcp.json** から開けます）。そして登録した後も、**LM Studio は道具の呼び出しごとに画面で許可を求めます** — 許可を出すまで道具は一度も動きません。トークンは、ログインのときに期間を渡さないかぎり切れません（`docs/reference/api.md` を参照）。道具ごとに何を渡すと何が返るかは `docs/reference/mcp.md` に、クライアントを繋ぐ手順の全体・設定系の道具・書き込みの守り（`CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1`）は `docs/operations.md` にあります。

---

### 9. 使う前に、次の3つをお読みください

- **これは学習と試用のためのものです。** 本番システムとして使うことを想定して作られていません。無保証です。
- **マスキングは完全ではありません。** 氏名・電話番号などを自動で伏せますが、取りこぼしは起こります。伏せられることを前提に機密資料を入れないでください。
- **答えは間違うことがあります。** 必ず出典を開き、原文で確かめてからお使いください。

---

### 10. 必要になったときに開くもの

**全数の一覧は [`docs/INDEX.md`](docs/INDEX.md) にあります。** ここに同梱される文書のすべてを、
読み手ごと（使う人 / 入れる人・回す人 / 引く人）に並べ、それぞれに何が書いてあるかを 1 行で
添えてあります。このページから 1 つだけ覚えるなら、この道です。同じものを下にも並べます。

| ファイル | 何が書いてあるか（他とどう違うか） |
|---|---|
| [`docs/INDEX.md`](docs/INDEX.md) | **文書の全数の索引。どのファイルが要るか分からないときはこれ** |
| `README.md` | このツールが何か・できること できないこと・動作環境 |
| `docs/getting-started.md` | ターミナルを開いたことが無い方へ。落としたファイルから最初の答えまで。省略なし。その後の毎日の起動と停止も |
| `docs/editions.md` | どの形を選ぶか。1枚 |
| `docs/concept.md` | このツールが何のためのものか。参照元のツールとの違い |
| `docs/architecture.md` | 内側の作り: 取り込みと分類・検索のしくみ・スコアの読み方・回答のかたち |
| `docs/security.md` | 役割と権限・PII の検出とマスキング・ガードレール・推奨しない使用方法 |
| `docs/limits.md` | できないこと: マスキングの取りこぼし・読み込めない形式・骨組みだけの機能 |
| `docs/operations.md` | 据え方と使い続けるための運用: 置き方・LLM の接続・外部の道具から MCP で使う・LAN 共有・backup と restore・ログ・利用者・番号 |
| `docs/handson.md` | `dummy-corpus/` の同梱資料を相手にする演習 |
| `docs/faq.md` | よく聞かれることへの短い答え |
| `docs/reference/cli.md` | ターミナルの命令と引数の全数 |
| `docs/reference/mcp.md` | MCP の道具の全数。何を渡すと何が返るか |
| `docs/reference/api.md` | HTTP の口の全数。コードから起こしたもの |
| `docs/reference/changelog.md` | 版ごとの変更点 |
| `docs/USE-FROM-TERMINAL.txt` | アイコンではなくターミナルから使う方法（`./launch.sh` の指定の全数） |
| `docs/READ-BEFORE-DISTRIBUTING.md` | 誰かに配る前にお読みください |
| `docs/NOTICE.md` | 使う前のご注意。無保証・マスキングの限界・答えの確かめ方 |
| `docs/BUNDLED-DATA.md` | 同梱のサンプル資料に何が入っているか。初回起動時にこの機材の上で作られるものの内訳 |
