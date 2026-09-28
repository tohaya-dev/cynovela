**日本語版はこちら → [README.ja.md](README.ja.md)**

# Cynovela

## Login (read this first)

This is a tool for trying things out. The initial login information is:

- URL: http://localhost:8765
- Administrator: user name `cynovela` / password `Cynovela1!` (you are asked to change it at the first sign-in)
- Viewer: user name `demo` / password `demo1234` (you are not asked to change it)

If you use it on a shared network, change the viewer's password too.
To keep other machines from opening it, start it with `./launch.sh --local-only`.

A small-scale model of an enterprise AI data pipeline: ingest files, mask
personal information, publish them, and get answers with citations, with what
each role can see kept separate.

Cynovela is a tool for personal use, small internal demos, and learning.
It is not a commercial offering and is not intended for production use.

It is built with Japanese documents in mind, and its masking rules are written
for Japanese text.

The name is a coined word, from *cynosure* (a guiding star) and *Vela* (the
constellation of the Sail).

<!-- screenshot: place one image here once it has been captured and checked -->

## Quick start

If this is your first time, follow this section alone, from top to bottom. The
details come later, in [`tender/QUICKSTART.md`](tender/QUICKSTART.md) and
[`tender/START-HERE.md`](tender/START-HERE.md).

**Apple silicon Macs only. Neither Python nor conda is needed. Nothing is
installed on this Mac.**

> 🔴 **This is a tool for trying things out and checking them.** It is not
> something to put on a production site. Do not put real confidential material
> through it, and do not treat its answers as authoritative.

### 1. Download (5 files, into the same folder)

Download them from the [releases page](https://github.com/tohaya-dev/cynovela/releases).
These are the 2.0.2 files. The previous version, v1.2.0, remains available on
the releases page.

| File | What it is |
|---|---|
| `cynovela-tender-package-2.0.2.tar.gz` | **Cynovela itself.** `package` is the application itself |
| `cynovela-tender-models-2.0.2.tar.gz.part00`〜`part02` | **The AI models Cynovela uses.** The embedding models that turn documents into vectors (BGE-M3 and others) and the model that reranks search results — **not the answering LLM** (you set that up separately in step 5). GitHub caps a release file at 2 GiB, so they are split into three parts |
| `SHA256SUMS` | The list for checking that nothing is corrupted |

If you are on a managed Mac (under MDM), download `check-managed-mac.command` first
and double-click it. It only checks whether this Mac can run Cynovela; it
changes no settings.

### 2. Join the AI models and put them inside the application

Open Terminal (`Applications` → `Utilities` → `Terminal`) and run these in the
folder you downloaded into, in order.

**2-1. Join the three parts.**

    cd ~/Downloads
    cat cynovela-tender-models-2.0.2.tar.gz.part00 cynovela-tender-models-2.0.2.tar.gz.part01 cynovela-tender-models-2.0.2.tar.gz.part02 > cynovela-tender-models-2.0.2.tar.gz

**2-2. Check that nothing is corrupted.** If every printed line says `OK`, it
worked.

    shasum -a 256 --ignore-missing -c SHA256SUMS

**2-3. Extract the application.** A `tender` folder appears.

    tar -xzf cynovela-tender-package-2.0.2.tar.gz

**2-4. Unpack the AI models inside the application.**

    cd tender
    tar -xzf ../cynovela-tender-models-2.0.2.tar.gz

**This creates `tender/store/models/` — it will not be found anywhere else.**
If you already extracted the models somewhere else, move the resulting `models`
folder into `tender/store/`.

**Do not put any of this inside a cloud-synced folder (iCloud Drive, Dropbox,
OneDrive, Google Drive).** Files get replaced with forms that cannot be run.

### 3. Start it

    ./launch.sh

Your browser opens automatically. If it does not, open the address shown in the
Terminal window yourself. **It is `http://localhost:8765`. If port 8765 is
taken, another number is chosen and shown on screen.**

### 4. Sign in and change the password

Sign in with the user names and passwords in "Login (read this first)" at the
top of this page. The administrator's password is also printed on the terminal
once, at the first start, and both values are under `auth:` in `cynovela.yaml`
in the folder you unpacked (next to `launch.sh`).

🔴 **The administrator must change the password on first sign-in.** No
administrative operation is possible until it is changed. **Change it.**

**The viewer (`demo`) is not asked to.** And **Cynovela listens on the local
network by default** — other machines on the same network can open it. That
default exists so you can try it from another Mac. **When trying it on a shared
network, change the viewer's password too, from `Settings`.** To keep it closed
inside this Mac only, start with `./launch.sh --local-only`.

### 5. Connect the answering LLM

🔴 **If you skip this, questions get no answers. Do it first.**

Start the thing you will connect to beforehand (**running inside this Mac** =
LM Studio or Ollama; **an external service** = anything exposing an
OpenAI-compatible endpoint — OpenRouter and the like belong here; an API key is
required).

Then, in the `Settings` screen, press **in this order**:

1. **Choose a provider** — one of `LM Studio` / `Ollama` / `OpenAI 互換`
   (OpenAI-compatible)
2. **Enter the Base URL** — `http://localhost:1234` for LM Studio,
   `http://localhost:11434` for Ollama. For an external service, follow its
   instructions
3. Press **`🔌 接続テスト`** (connection test) and confirm it succeeds
4. Press **`📋 モデル一覧を取得`** (fetch the model list) and **choose the
   model to use**
5. Press **`💾 LLM 設定をまとめて適用`** (apply the LLM settings together)

🔴 **Nothing is saved until you press 5.** The `保存` (save) and `✅ 適用完了`
(applied) buttons that appear along the way belong to other items. **When you
change models, repeat 3–5 in the same order.**

### 6. Try it

    ./launch.sh --demo

**The 21 bundled sample documents are ingested on the first start, and you can
ask questions in `RAG Chat` right away** (ingestion takes about 40 seconds,
measured on an M4 Max). Start by asking
「この資料の概要を教えてください」 ("give me an overview of these documents").
**A local LLM takes time before the answer comes back.** Wait for it.

**There are only two ways to start it.**

| What you run | What you get |
|---|---|
| `./launch.sh` | **Production. It starts empty.** Put your own documents in and use it |
| `./launch.sh --demo` | **Starts with the sample documents in place.** This is the one to try |

**Each keeps its own separate database.** Trying the demo mixes nothing into
the production side. If you would rather double-click, there are
`Cynovela-start.command` (production) and `Cynovela-demo.command` (demo).

### 7. Feed it your own documents

Either way works:

    ./launch.sh --add               a folder picker appears
    ./launch.sh --add-path <path>   name the location as text

From the screen, it is **「検索の対象フォルダを足す」** (add a folder to
search) in `Settings`.

- 🔴 **Folders are the only unit you can add. You cannot point at a single
  file.**
- 🔴 **Until you add something, only the bundled sample documents are covered.**
  To ask about your own documents, you must add their folder.
- After adding, ingest the documents and `Publish`; they then become
  searchable. **Ingestion runs in the background. Closing the browser does not
  stop it.**

## Upgrading from 1.2.0

2.0.2 unpacks into a new folder, `tender`, and does not read the `store/` of
the folder of 1.2.0 (the folder that 1.2.0 was unpacked into). To keep your
documents, users and settings, copy that `store/` into `tender/store/` before
the first start of 2.0.2. The steps
are in [HOW-TO-ASSEMBLE.md](HOW-TO-ASSEMBLE.md#upgrading-from-120). Compared
with 1.2.0, some behaviour also changes (the first-password change, rate limits,
ingest roots, tokens); the list is in the 2.0.0 section of
[RELEASE-NOTES.md](RELEASE-NOTES.md#200-2026-09-26). Upgrading from 2.0.0 or
2.0.1 is covered in [HOW-TO-ASSEMBLE.md](HOW-TO-ASSEMBLE.md#upgrading-from-200-or-201).

## What is in this repository

| Directory | What it is | Distribution package |
|---|---|---|
| `tender` | Runs directly on macOS. | Published on GitHub Releases (v2.0.2). The v2.0.2 files are named `cynovela-tender-…` and unpack into a folder named `tender`. v1.2.0 and earlier used a former name. |

The container edition is not included from this version; if you need it, see the v1.2.0 release on the Releases page.

## Requirements

- macOS on Apple silicon.
- `tender`, App edition (`.pkg`): **in preparation.** It is not part of this
  release.
- `tender`, Package edition: **neither Python nor conda is needed.** The folder
  carries its own Python inside it, and nothing is installed on this Mac.
- `tender`, Source editions: Python 3.12 or later. `launch.sh` builds the
  environment for you — it offers a dedicated `conda` environment, and where
  `conda` is not present it builds the environment inside the distribution
  folder instead.
- An internet connection is needed on first start for the source editions,
  because they build their environment at that point.
- 8 GB of RAM or more, and an LM Studio or OpenAI-compatible API for the
  answering model.

## Downloads

Everything is on GitHub Releases (v2.0.2):
https://github.com/tohaya-dev/cynovela/releases

The one-page answer to "which of these do I take" is in
[tender/docs/editions.md](tender/docs/editions.md).

| Edition | Runs as | Models bundled | Download shape | What it needs |
|---|---|---|---|---|
| **App edition** (`.pkg`) | — | — | **In preparation.** Not part of this release | — |
| **Package edition** `cynovela-tender-package-2.0.2.tar.gz` | a folder you run in place | no — take the AI models as well | single file | **Neither Python nor conda.** Nothing is installed on this Mac |
| **Source edition** | a folder you run in place | no — take the AI models as well | not a download — the source is this repository (clone it, or use GitHub's "Download ZIP") | Python 3.12 or later, or conda |
| **AI models** `cynovela-tender-models-2.0.2.tar.gz.part00`–`part02` | — | — | split into parts — needs assembling | Despite the name, these are the AI models themselves, not conda packages |

The **App edition** (`.pkg`) is **in preparation** and is not part of this
release.

Take the **Package edition** if you would rather not install anything: extract it,
unpack the AI models into `tender/store/models/`, and run `./launch.sh`. It writes inside its own folder, and the
extracted folder can be moved to another location later — start it again from the
new place with the same `./launch.sh`.

Take the **source edition** if you want to see and control what is installed:
the source is this repository — take the `tender/` tree, add the AI models, and
run `./launch.sh`; on the first start it builds the environment for you. No
source archive is distributed on the releases page.

The release also carries `HOW-TO-ASSEMBLE.md`, the checksum list `SHA256SUMS`
for the package edition and the AI models, and `check-managed-mac.command`, a
diagnostic that tells you — without changing any setting — whether a
managed Mac (under MDM) will let you run this. A single release file cannot exceed
2 GiB, so the AI models are split into parts; join them as
[HOW-TO-ASSEMBLE.md](HOW-TO-ASSEMBLE.md) describes and check the result against
`SHA256SUMS` before starting.

## First time here

For `tender` there is one entrance:
**[tender/START-HERE.md](tender/START-HERE.md)**. Open that first; it carries
the map of every other document.

| Document | What it covers |
|---|---|
| [tender/START-HERE.md](tender/START-HERE.md) | The entrance. First start, restart, reinstall, uninstall, and where everything else is |
| [tender/docs/editions.md](tender/docs/editions.md) | Which edition to take, on one page |
| [tender/docs/getting-started.md](tender/docs/getting-started.md) | Never opened a terminal? From the downloaded file to the first answer, nothing skipped |
| [tender/docs/operations.md](tender/docs/operations.md) | Keeping it running: stopping and starting, connecting an LLM, backup and restore, users, logs |
| [tender/docs/reference/cli.md](tender/docs/reference/cli.md) | Every terminal command and every argument |
| [tender/docs/reference/mcp.md](tender/docs/reference/mcp.md) | Every MCP tool: what you hand each one, what comes back |
| [tender/docs/reference/api.md](tender/docs/reference/api.md) | Every HTTP endpoint, read out of the code |
| [tender/docs/handson.md](tender/docs/handson.md) | Exercises against the bundled sample material, once it is running |

Every guide is bilingual: English first, Japanese after.

**First sign-in.** The login information is in "Login (read this first)" at the
top of this page. The administrator's password is also printed on screen, once,
the first time you start:

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

## What it does not do

- **Masking has limits.** It applies pattern-based replacement before text
  leaves the machine, and it does not catch everything. Known gaps include names
  written in kana readings, the block-and-number part of addresses, and some
  landline area codes.
- It is a tool for learning and experimentation. Do not put real confidential
  material through it, and do not treat its output as authoritative.

## License

MIT. See `LICENSE`.

---

- https://note.com/tocchidegozaru
- https://huggingface.co/tocchitocchi
