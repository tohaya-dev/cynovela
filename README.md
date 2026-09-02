**日本語版はこちら → [README.ja.md](README.ja.md)**

# Cynovela

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
details come later, in [`chewie/QUICKSTART.md`](chewie/QUICKSTART.md) and
[`chewie/START-HERE.md`](chewie/START-HERE.md).

**Apple silicon Macs only. Neither Python nor conda is needed. Nothing is
installed on this Mac.**

> 🔴 **This is a tool for trying things out and checking them.** It is not
> something to put on a production site. Do not put real confidential material
> through it, and do not treat its answers as authoritative. **The initial user
> names and passwords written in this section are there so you can try it right
> away.**

### 1. Download (5 files, into the same folder)

Download them from the [releases page](https://github.com/tohaya-dev/cynovela/releases).

| File | What it is |
|---|---|
| `cynovela-chewie-package-1.2.0.tar.gz` | **Cynovela itself.** `package` is the application itself |
| `cynovela-chewie-models-1.2.0.tar.gz.part00`〜`part02` | **The AI models Cynovela uses.** The embedding models that turn documents into vectors (BGE-M3 and others) and the model that reranks search results — **not the answering LLM** (you set that up separately in step 5). GitHub caps a release file at 2 GiB, so they are split into three parts |
| `SHA256SUMS` | The list for checking that nothing is corrupted |

If you are on a company-issued Mac, download `check-managed-mac.command` first
and double-click it. It only checks whether this Mac can run Cynovela; it
changes no settings.

### 2. Join the AI models and put them inside the application

Open Terminal (`Applications` → `Utilities` → `Terminal`) and run these in the
folder you downloaded into, in order.

**2-1. Join the three parts.**

    cd ~/Downloads
    cat cynovela-chewie-models-1.2.0.tar.gz.part00 cynovela-chewie-models-1.2.0.tar.gz.part01 cynovela-chewie-models-1.2.0.tar.gz.part02 > cynovela-chewie-models-1.2.0.tar.gz

**2-2. Check that nothing is corrupted.** If every printed line says `OK`, it
worked.

    shasum -a 256 --ignore-missing -c SHA256SUMS

**2-3. Extract the application.** A `chewie` folder appears.

    tar -xzf cynovela-chewie-package-1.2.0.tar.gz

**2-4. Unpack the AI models inside the application.**

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz

**This creates `chewie/store/models/` — it will not be found anywhere else.**
If you already extracted the models somewhere else, move the resulting `models`
folder into `chewie/store/`.

**Do not put any of this inside a cloud-synced folder (iCloud Drive, Dropbox,
OneDrive, Google Drive).** Files get replaced with forms that cannot be run.

### 3. Start it

    ./launch.sh

Your browser opens automatically. If it does not, open the address shown in the
Terminal window yourself. **It is `http://localhost:8765`. If port 8765 is
taken, another number is chosen and shown on screen.**

### 4. Sign in and change the password

| Role | User name | First password |
|---|---|---|
| **Administrator** (full control) | `cynovela` | `Cynovela1!` |
| **Viewer** (read-only) | `demo` | `demo1234` |

**The same values are printed once in the Terminal window at the first start.**
They are also under `auth:` in `cynovela.yaml` in the folder you unpacked (next
to `launch.sh`).

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
ask questions in `RAG Chat` right away** (ingestion takes about 39 seconds,
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

## The three forms in this repository

| Directory | What it is | Distribution package |
|---|---|---|
| `chewie` | Runs directly on macOS. | Published on GitHub Releases (v1.2.0). |
| `falcon` | Runs inside a container (Podman). | Built from the source in this repository. No distribution package is provided. |
| `falcon-docker-beta` | Runs inside a container (Docker; in-development beta, no bundled models). | Built from the source in this repository. No distribution package is provided. |

You only need one of them. They are three ways of running the same thing.

## Requirements

- macOS on Apple silicon.
- `chewie`, App edition (`.pkg`): **in preparation.** It is not part of this
  release.
- `chewie`, Package edition: **neither Python nor conda is needed.** The folder
  carries its own Python inside it, and nothing is installed on this Mac.
- `chewie`, Source editions: Python 3.12 or later. `launch.sh` builds the
  environment for you — it offers a dedicated `conda` environment, and where
  `conda` is not present it builds the environment inside the distribution
  folder instead.
- `falcon`: Podman.
- Docker and other container engines can be selected, but we have not verified
  them here. You will need to adjust the setup yourself.
- An internet connection is needed on first start for the source editions,
  because they build their environment at that point.
- 8 GB of RAM or more, and an LM Studio or OpenAI-compatible API for the
  answering model.

## Downloads

Everything is on GitHub Releases (v1.2.0):
https://github.com/tohaya-dev/cynovela/releases

The one-page answer to "which of these do I take" is in
[chewie/docs/editions.md](chewie/docs/editions.md).

| Edition | Runs as | Models bundled | Download shape | What it needs |
|---|---|---|---|---|
| **App edition** (`.pkg`) | — | — | **In preparation.** Not part of this release | — |
| **Package edition** `cynovela-chewie-package-1.2.0.tar.gz` | a folder you run in place | no — take the AI models as well | single file | **Neither Python nor conda.** Nothing is installed on this Mac |
| **Source edition** | a folder you run in place | no — take the AI models as well | not a download — the source is this repository (clone it, or use GitHub's "Download ZIP") | Python 3.12 or later, or conda |
| **AI models** `cynovela-chewie-models-1.2.0.tar.gz.part00`–`part02` | — | — | split into parts — needs assembling | Despite the name, these are the AI models themselves, not conda packages |

The **App edition** (`.pkg`) is **in preparation** and is not part of this
release.

Take the **Package edition** if you would rather not install anything: extract it,
unpack the AI models into `chewie/store/models/`, and run `./launch.sh`. It writes inside its own folder, and the
extracted folder can be moved to another location later — start it again from the
new place with the same `./launch.sh`.

Take the **source edition** if you want to see and control what is installed:
the source is this repository — take the `chewie/` tree, add the AI models, and
run `./launch.sh`; on the first start it builds the environment for you. No
source archive is distributed on the releases page.

The release also carries `HOW-TO-ASSEMBLE.md`, the checksum list `SHA256SUMS`
for the package edition and the AI models, and `check-managed-mac.command`, a
diagnostic that tells you — without changing any setting — whether a
managed Mac (under MDM) will let you run this. A single release file cannot exceed
2 GiB, so the AI models are split into parts; join them as
[HOW-TO-ASSEMBLE.md](HOW-TO-ASSEMBLE.md) describes and check the result against
`SHA256SUMS` before starting.

`falcon` and `falcon-docker-beta` are built from the source in this repository.
Distribution packages for them are not provided.

## First time here

For `chewie` there is one entrance:
**[chewie/START-HERE.md](chewie/START-HERE.md)**. Open that first; it carries
the map of every other document.

| Document | What it covers |
|---|---|
| [chewie/START-HERE.md](chewie/START-HERE.md) | The entrance. First start, restart, reinstall, uninstall, and where everything else is |
| [chewie/docs/editions.md](chewie/docs/editions.md) | Which edition to take, on one page |
| [chewie/docs/getting-started.md](chewie/docs/getting-started.md) | Never opened a terminal? From the downloaded file to the first answer, nothing skipped |
| [chewie/docs/operations.md](chewie/docs/operations.md) | Keeping it running: stopping and starting, connecting an LLM, backup and restore, users, logs |
| [chewie/docs/reference/cli.md](chewie/docs/reference/cli.md) | Every terminal command and every argument |
| [chewie/docs/reference/mcp.md](chewie/docs/reference/mcp.md) | Every MCP tool: what you hand each one, what comes back |
| [chewie/docs/reference/api.md](chewie/docs/reference/api.md) | Every HTTP endpoint, read out of the code |
| [chewie/docs/handson.md](chewie/docs/handson.md) | Exercises against the bundled sample material, once it is running |

For `falcon`, start from [falcon/docs/HAJIMETE.md](falcon/docs/HAJIMETE.md),
then [falcon/docs/STARTUP.md](falcon/docs/STARTUP.md). For
`falcon-docker-beta`, start from
[falcon-docker-beta/docs/HAJIMETE.md](falcon-docker-beta/docs/HAJIMETE.md),
then [falcon-docker-beta/docs/STARTUP.md](falcon-docker-beta/docs/STARTUP.md).

Every guide is bilingual: English first, Japanese after.

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

| Role | User name | First password |
|---|---|---|
| **Administrator** (full control) | `cynovela` | `Cynovela1!` |
| **Viewer** (read-only) | `demo` | `demo1234` |

## What it does not do

- **Masking has limits.** It applies pattern-based replacement before text
  leaves the machine, and it does not catch everything. Known gaps include names
  written in kana readings, the block-and-number part of addresses, and some
  landline area codes.
- It is a tool for learning and experimentation. Do not put real confidential
  material through it, and do not treat its output as authoritative.
- Behaviour with Docker, or with container engines other than Podman, has not
  been verified here.

## License

MIT. See `LICENSE`.

---

- https://note.com/tocchidegozaru
- https://huggingface.co/tocchitocchi
