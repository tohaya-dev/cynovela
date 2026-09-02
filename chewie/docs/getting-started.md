# Getting started — from the downloaded file to your first answer / はじめかた — 落としたファイルから最初の答えまで

**日本語版はこちら → [日本語](#日本語)**

---

## English

This single page takes you all the way to your first answer.
**The route that needs nothing but the screen is written first.** The route that uses
the terminal is collected further down.

> The single entry document is [START-HERE.md](../START-HERE.md). If this is your first time, start there.

Rough time required: 30-60 minutes for the first run (most of it is waiting for the runtime
environment to be created and for the model to load).
Run the steps in this guide in order from the top.

Sections 2 and 3 assume you have never opened Terminal, and nothing is skipped there. If you
are used to a terminal, section 4 is the short route. The everyday routine is section 16.

| If this is you | Read |
|---|---|
| You have never opened Terminal | Section 0, then sections 2 and 3 |
| You are in a hurry and know your way around a terminal | Section 4 |
| You want the first run explained step by step (source edition included) | Sections 5 to 15 |
| You already ran it once and just want to start it again | Sections 16 to 20 |
| Something is not working | Section 22 |

Operational topics — the LLM provider settings in detail (including Ollama), backup and
restore, changing the port, and reading the logs — are in [operations.md](operations.md).

---

**Contents**

- [0. Read this first (this is where most people get stuck)](#0-read-this-first-this-is-where-most-people-get-stuck)
- [1. Which package did you download?](#1-which-package-did-you-download)
- [2. The gentle way in — the package edition, step by step](#2-the-gentle-way-in--the-package-edition-step-by-step)
- [3. Why each of those steps is there](#3-why-each-of-those-steps-is-there)
- [4. The short route, for those in a hurry](#4-the-short-route-for-those-in-a-hurry)
  - [4-1. Setting up the environment (source edition only)](#4-1-setting-up-the-environment-source-edition-only)
  - [4-2. A note on SSL_CERT_FILE (important)](#4-2-a-note-on-ssl_cert_file-important)
  - [4-3. Starting](#4-3-starting)
- [5. What to prepare (source edition)](#5-what-to-prepare-source-edition)
- [6. Extract](#6-extract)
- [7. Create the runtime environment and start](#7-create-the-runtime-environment-and-start)
- [8. First run only: a screen asks you to choose about downloading the AI model](#8-first-run-only-a-screen-asks-you-to-choose-about-downloading-the-ai-model)
- [9. Open it in a browser](#9-open-it-in-a-browser)
- [10. Sign in, and change the initial password](#10-sign-in-and-change-the-initial-password)
  - [Roles](#roles)
  - [How to create a viewer when you started with nothing loaded](#how-to-create-a-viewer-when-you-started-with-nothing-loaded)
- [11. Connect the LLM that writes the answers](#11-connect-the-llm-that-writes-the-answers)
  - [11-1. Preparation on the LM Studio side](#11-1-preparation-on-the-lm-studio-side)
  - [11-2. Settings on the Cynovela side](#11-2-settings-on-the-cynovela-side)
- [12. Ask your first question](#12-ask-your-first-question)
- [13. Add a folder to be read (an ingest source)](#13-add-a-folder-to-be-read-an-ingest-source)
  - [Add it from the screen (recommended)](#add-it-from-the-screen-recommended)
  - [Add by double-clicking](#add-by-double-clicking)
  - [From a terminal](#from-a-terminal)
  - [Passing multiple ingest sources](#passing-multiple-ingest-sources)
- [14. Ingest documents and publish](#14-ingest-documents-and-publish)
- [15. When you place folders or files there later](#15-when-you-place-folders-or-files-there-later)
- [16. Everyday startup](#16-everyday-startup)
  - [There are 2 ways to start it, and 2 things that can start](#there-are-2-ways-to-start-it-and-2-things-that-can-start)
  - [Notes before the first start](#notes-before-the-first-start)
  - [Frequently used operations](#frequently-used-operations)
- [17. Startup options](#17-startup-options)
  - [List of startup forms (--mode) (measured 2026-08-12)](#list-of-startup-forms---mode-measured-2026-08-12)
- [18. The route through the terminal (summary)](#18-the-route-through-the-terminal-summary)
- [19. Stopping, and starting again](#19-stopping-and-starting-again)
- [20. What is going on when you stop and start again](#20-what-is-going-on-when-you-stop-and-start-again)
- [21. Checking behavior (tests)](#21-checking-behavior-tests)
- [22. When things do not work](#22-when-things-do-not-work)
- [23. Where to go next](#23-where-to-go-next)

## 0. Read this first (this is where most people get stuck)

- **The first time you sign in as the administrator, you will always be told to change
  your password.**
- **Until you have finished changing it, every administrative operation (adding an
  ingest source, ingesting documents, changing settings) is rejected.** Change it first.
- The viewer (`demo`) is not asked to change anything. However, a viewer cannot ingest
  documents.

This package runs directly on your own machine.

Two things that will look wrong, and are not:

1. **Most of the terminal steps print nothing when they work.** A command that succeeds
   usually prints nothing at all and just gives you a new line to type on. Silence
   is success here. Only failures produce output.
2. **Some steps take minutes with no sign of life.** Joining the model files and
   the first start are the slow ones. Nothing is frozen. Leave it alone.

---

## 1. Which package did you download?

There are 2 forms, plus the AI models as a separate download. **The package edition comes first** — if you have it, skip the environment setup in section 4 and section 7 entirely. Files named `.part00`–`.part02` are split files: join them in part order before extracting, and verify with `shasum -a 256 --ignore-missing -c SHA256SUMS`. The step-by-step guide is **HOW-TO-ASSEMBLE.md**, published on the releases page next to the files.

| Package | Who it is for | What to do |
|---|---|---|
| **Package edition** `cynovela-chewie-package-1.2.0.tar.gz` (1 file, about 800 MB) | Apple silicon Macs. **No Python and no conda are needed. Nothing is installed on this Mac.** | Extract it, add the AI models (last row), then run `./launch.sh`. To remove it, delete the folder. |
| **Source edition** (not a download — the source is this repository) | Those who want to build the environment themselves | Clone the repository or use GitHub's "Download ZIP", take the `chewie/` tree, add the AI models (last row), then follow section 7 below. |
| **AI models** `cynovela-chewie-models-1.2.0.tar.gz.part00`–`part02` (3 split files) | Needed with the package edition and the source edition. Despite the name, these are the AI models themselves, not conda packages. | Join the parts into one file, then run `tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz` **inside the extracted chewie folder** — `store/models/` is created. |

With the source edition you choose, at startup, one of 2 ways to build the environment.

```
Source edition: how the environment is built (you choose at startup)
  1) Create a dedicated conda environment
       Where the Python comes from : conda downloads it from conda-forge.
       What is created            : one conda environment (dedicated name: cynovela-dist).
       What remains               : that one environment, inside conda's folder. The shared environments are never touched.
  2) Use this Mac's Python and build the environment only inside this package's folder
       Where the Python comes from : the Python 3.12 or later already on this Mac (checked by asking the Python itself).
       What is created            : a venv named .venv-cynovela inside this package's folder.
       What remains               : only files inside this folder. Nothing outside it is changed.
```

The AI models are downloaded separately (see section 8, "First run only").

---

## 2. The gentle way in — the package edition, step by step

This section is for the **package edition** (`cynovela-chewie-package-1.2.0.tar.gz`).
It assumes you have never opened Terminal. Nothing is skipped.

Do these in order. Do not read ahead for reasons; the reasons are in section 3.

#### Step 1. Download five files

On the releases page, download these into your **Downloads** folder:

```
cynovela-chewie-package-1.2.0.tar.gz
cynovela-chewie-models-1.2.0.tar.gz.part00
cynovela-chewie-models-1.2.0.tar.gz.part01
cynovela-chewie-models-1.2.0.tar.gz.part02
SHA256SUMS
```

Together they are about 5.4 GB. Wait until all five have finished.

#### Step 2. Open Terminal

Press **⌘ (command) + space**. A search box appears in the middle of the screen.
Type `terminal` and press **return**.

A window opens with white or black text and a blinking cursor. That is Terminal.
Everything below is typed into that window. After each line, press **return**.

#### Step 3. Go to the Downloads folder

Type this line and press return:

```
cd ~/Downloads
```

Nothing will be printed. That is correct.

#### Step 4. Join the three model parts into one file

Type this as **one line** and press return:

```
cat cynovela-chewie-models-1.2.0.tar.gz.part* > cynovela-chewie-models-1.2.0.tar.gz
```

This takes **one to three minutes** and prints nothing while it works. When the
cursor comes back, it is done.

#### Step 5. Check that the files arrived intact

```
shasum -a 256 --ignore-missing -c SHA256SUMS
```

This takes **one to three minutes**. It then prints one line per file. Every line
must end in `OK`:

```
cynovela-chewie-models-1.2.0.tar.gz: OK
cynovela-chewie-package-1.2.0.tar.gz: OK
```

If any line shows `FAILED`, download that file again and repeat from step 4. Do
not go on.

#### Step 6. Unpack the program

```
tar -xzf cynovela-chewie-package-1.2.0.tar.gz
```

This takes **three to ten minutes** and prints nothing. A folder named `chewie`
appears in Downloads.

#### Step 7. Go into that folder

```
cd chewie
```

Nothing is printed.

#### Step 8. Unpack the AI models inside it

```
tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz
```

This takes **two to five minutes** and prints nothing.

#### Step 9. Start it

```
./launch.sh --demo
```

`--demo` starts it with the sample documents that came in the package, so you
have something to ask about on the very first day. Without `--demo` it starts
empty and you must add a folder of your own first.

Now it talks to you. What you will see, in order — all of it in Japanese,
because the startup messages are only in Japanese:

```
先に、いま動いているものを調べました。
  動いているものは 0個 でした。
このまま進みます。

同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました。選択の画面は出さず、これを使って起動します。
記録はこのファイルへ書きます: /Users/…/Downloads/chewie/store/launch-app.log
起動しています (本体はこのターミナルから切り離して動かします)
```

The second line means "the bundled environment was found, so the screen that
asks how to build one is not shown". You are not being asked anything here.

**The first start takes three to eight minutes.** Nothing appears during that
time. When it is ready you will see:

```
立ち上がりました。
  開くところ : http://127.0.0.1:8765/
  記録       : /Users/…/Downloads/chewie/store/launch-app.log
止めるときは、次のように叩いてください。
  bash stop.sh
```

#### Step 10. Open it in your browser

Hold **⌘** and click `http://127.0.0.1:8765/`, or type that address into Safari
or Chrome yourself.

A sign-in screen appears.

#### Step 11. Sign in

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

It will ask you to choose a new password straight away. Do that.

#### Step 12. Ask your first question

Because you started with `--demo`, the sample documents were ingested automatically at the first start and are searchable
(if the startup log still shows the ingest running, wait for it to finish). Type a question in plain language into
the box and press return, for example:

```
特別休暇は結婚のとき何日もらえますか
```

**The first answer takes one to four minutes** — the AI model has to be loaded
into memory first. Later answers are much faster.

Under every answer there is a list of the passages the answer came from. Open
one and check it against the answer. That is the point of this tool.

#### Step 13. Stop it when you are done

In Terminal:

```
bash stop.sh
```

It prints:

```
Cynovela を停止します (PID: 12345)...
停止完了
```

Your documents and settings stay where they are.

---

## 3. Why each of those steps is there

#### Why five files instead of one

GitHub does not accept a single file larger than a few gigabytes, so the AI
models are cut into three pieces of 1.5 GB. Step 4 glues them back together.
`SHA256SUMS` is a list of fingerprints; step 5 recomputes the fingerprint of
what landed on your disk and compares it. A download that stopped halfway looks
like a normal file until you try to use it, which is why the check is worth the
three minutes.

#### Why `cd ~/Downloads`

Terminal always has one folder it is "standing in". `cd` moves it. `~` is
shorthand for your home folder — the one with your name on it in Finder. So
`~/Downloads` is the same Downloads folder Finder shows you. Every later command
acts on files in the folder Terminal is standing in, which is why step 7 moves
into `chewie` before unpacking the models: the models must land inside the
program's folder, not next to it.

#### Why nothing is printed

Unix commands were written to be chained together, so they stay quiet unless
something is wrong. `cd`, `cat` and `tar` all follow that habit. This is the
single most common reason people think the tool is broken when it is not.

#### Why the package edition needs no Python and no conda

The folder you unpacked already contains its own Python and every library it
needs, in a directory called `.condapack-cynovela`. It starts with a dot, so Finder
hides it — that is a macOS convention for "not for you to touch", not a sign
that something went wrong. (Press **⌘ + shift + .** in Finder to show hidden
items, and again to hide them.) Because everything lives inside the folder,
nothing is written anywhere else on your Mac, and deleting the folder removes
the tool completely.

That is also why step 9 prints *"同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました"*
and does **not** ask you to choose how to build an environment. The source
editions do ask, because they have no environment yet.

#### Why the first start is slow, and later ones are not

On the first start the tool reads the AI model off the disk, builds its search
index over the bundled demo documents, and prepares its database. From then on
all three already exist and are reused.

#### Why the first answer is slow

Answering needs a language model, which runs outside Cynovela (LM Studio, or any
OpenAI-compatible service). The first question makes that service load the model
into memory — several gigabytes — before a single word comes back. The tool
waits up to 120 seconds per request for that. If you get a message about a
timeout, load the model in LM Studio first and ask again.

#### Why the password is also in a file

The first password appears on the terminal screen once, the very first time you
start — you do not need to look for it. The same value is also written into
`cynovela.yaml` at packaging time, so you can still find it there if you missed
that screen. Each package is built with a different first password: if it were
the same for everyone, anyone who had downloaded the tool would know yours.
Changing it on first sign-in is required for the same reason: administrator
actions are rejected until you do.

#### Why you should not put the folder in iCloud Drive, Dropbox or OneDrive

Those services copy every file to a server and can replace local files with
placeholders. Several gigabytes of libraries would be uploaded, and a
placeholder cannot be executed, so the tool stops working in ways that are hard
to diagnose. `./launch.sh` warns you if it detects one of those folders, but it
lets you go on. Put the folder somewhere plain instead — `~/Downloads` or
directly in your home folder is fine.

#### Why the terminal can be closed

`./launch.sh` detaches the program from the Terminal window before it finishes.
Closing the window does not stop it. That is why there is a separate
`bash stop.sh`.

---

## 4. The short route, for those in a hurry

These are the shortest steps to start Cynovela for the first time and throw your first RAG question. The target is version `1.2.0` (working directory `<the folder where you extracted the package>`).

### 4-1. Setting up the environment (source edition only)

**The recommended way is to let `./launch.sh` do it.** On the first run it offers the 2 choices below, and either way **the shared conda environment is never created and never modified** (everything goes into a dedicated place):

```bash
cd <the folder where you extracted the package>
./launch.sh
#   1) Create a dedicated conda environment (name: cynovela-dist)
#   2) Create a Python environment only inside this package's folder
```

If you cannot use `launch.sh` and must build it by hand, use the **dedicated name `cynovela-dist`**. Do not create or modify a shared environment:

```bash
# Create a dedicated environment for this package (do NOT use a shared name)
conda create -n cynovela-dist python=3.12 -y

# Install the dependencies
conda run -n cynovela-dist python -m pip install -r requirements.txt
```

Main dependencies: FastAPI / uvicorn / ChromaDB / sentence-transformers / spaCy + ja-ginza / torch / pypdf and others (see `requirements.txt`).

### 4-2. A note on SSL_CERT_FILE (important)

In a conda environment, `SSL_CERT_FILE` may point to a wrong certificate path, and the HuggingFace model download at startup fails. Please `unset` it and use the system default certificates.

```bash
unset SSL_CERT_FILE
```

The bundled `launch.sh` contains this `unset`, so it is unnecessary if you use it. **Only when you run `conda run` manually**, please run it yourself.

### 4-3. Starting

**Method 1: the bundled launcher (recommended)**

```bash
cd<配布物を展開したフォルダ>

# launch.sh に渡した引数は、そのまま server.py へ届きます
# （実装: launch.sh の `exec "$PY" server.py "${APP_ARGS[@]}"`。2026-08-02 実測）。
# 引数なしは本番（空のデータベース）です。デモを見るなら --demo を明示します。
./launch.sh --demo            # デモデータ + 実 LLM（既定は 0.0.0.0 で待ち受け。自分の機械の中だけに絞るなら --local-only）
./launch.sh --demo --lan      # デモデータ + LAN 公開
./launch.sh --check           # 起動せずに動く条件だけを調べる
```

To stop:

```bash
./stop.sh
```

**Method 2: manual start**

```bash
cd<配布物を展開したフォルダ>
unset SSL_CERT_FILE

# デモデータ + 実 LLM（LM Studio を http://localhost:1234 で起動しておく）
# 名前は配布物専用の cynovela-dist。共有の環境は作らない・書き換えない
conda run -n cynovela-dist python server.py --demo
```

To access:

```bash
open http://127.0.0.1:8765
```

> ⚠️ **A real LLM is required**: To produce answers to questions, an LLM such as LM Studio is required. The `--mock` option that used to exist (a setting to run without calling an LLM) has been removed, and specifying it now stops with an error.

From here, go on to signing in (section 10), the first question (section 12), and ingesting your own documents (sections 13 and 14).

---

## 5. What to prepare (source edition)

| What you need | How to check it |
|---|---|
| macOS (Apple silicon recommended) | — |
| conda (miniforge recommended) | Run `conda --version` in a terminal and confirm that a version is printed |
| Python 3.12 or later | `pyproject.toml` declares `requires-python = ">=3.12"`. 3.10 and 3.11 cannot be used. conda prepares the 3.12 series for you in section 7 |
| LM Studio (the LLM that writes the answers) | You can start the app (it is used in section 11) |
| 20GB or more of free space | The Avail column of `df -h /` |

If conda is not installed, install miniforge.
(From https://github.com/conda-forge/miniforge/releases/latest, get `Miniforge3-MacOSX-arm64.sh` for Apple silicon and run it.)

On a managed Mac (under MDM), the download sources themselves (conda-forge, PyPI,
github.com, huggingface.co) may not be allowed. In that case, choose the package edition,
which needs no downloading.

(The package edition needs neither Python nor conda; see section 3, "Why the package edition needs no Python and no conda".)

What to check when it does not work:

- `conda: command not found` → In most cases the terminal has not been reopened after the installation.
  Open a new terminal and check again.

---

## 6. Extract

```bash
cd ~/Downloads                # tar.gz を置いた場所へ
tar -xzf<配布物名>.tar.gz
cd<展開してできたフォルダ>      # 名前は cynovela- で始まります (ls で確認できます)
ls launch.sh                  # このファイルが見えれば展開できています
```

What to check when it does not work:

- `tar: Error opening archive` → The download was cut off partway. Please receive it again.
- "No such file or directory" on `cd` → The name of the extracted folder is different.
  Replace it with the folder name that `ls` printed.

---

## 7. Create the runtime environment and start

For your first time, we recommend trying the **demo**, which comes with the bundled dummy documents. Start it with `--demo` (if you start it without `--demo`, it starts as **production**, that is, with an empty database).

```bash
./launch.sh --demo
```

This single command goes all the way from creating the conda environment (the dedicated name `cynovela-dist` — the shared conda environment is never created and never modified), to installing the required components, to starting up.
The screen prints the following in order.

```
[Step 1] conda を確認中...
✅ conda: /Users/xxx/miniforge3
[Step 2] conda環境 'cynovela-dist' を確認中...
⚠️  環境 'cynovela-dist' が見つかりません。作成します...
   （初回は5〜15分かかります）
[Step 3] 環境 'cynovela-dist' をアクティベート中...
[Step 4] pip パッケージを確認中...
[Step 5] ポート8765の状態を確認中...
[Step 6] Cynovela を起動します...
Cynovela を起動します... (http://localhost:8765)
```

- The listening port is **8765** by default. To change it, use `./launch.sh --demo --port 8900`.
- From the second time on, the environment creation is skipped and it starts in about 1 minute.

What to check when it does not work:

- **You are asked "ポート8765はすでに使用中です" (port 8765 is already in use)** → A previous run is still there.
  Choosing `r` (stop the existing one and start again) is the safe option.
- **The environment creation in Step 2 fails** → Check the free space and the internet connection
  (a connection is needed only for the first run, to fetch the components).
- **When you want to stop it** → Run `bash stop.sh` in another terminal.

---

## 8. First run only: a screen asks you to choose about downloading the AI model

In the forms that do not bundle the model (the package edition, or the source
taken from this repository), the AI model that reads documents (the
embedding model bge-m3) is not yet present on the first run. Only when it is missing, the following three choices
appear in the middle of startup.

1. **Download it now** — receives about 2.2-2.3 GB from the internet (download source:
   Hugging Face). A network connection is required.
2. **Choose a folder you already have** — connects a model folder you already hold.
3. **Start with the lightest settings without downloading** — starts with no network
   access.

No network access begins until you choose one of them.
(If you started by double-clicking `Cynovela-start.command`, the same content appears on
a "Download / Cancel" screen.)

---

## 9. Open it in a browser

Open the following in a browser (if you changed the port in section 7, read it as that number).

```
http://localhost:8765
```

If the login screen ("ユーザー名／パスワードでログイン") appears, it worked.

What to check when it does not work:

- The page does not appear → Check whether an error is printed in the terminal you started it from.
- The display is blank white → Right after startup it may still be preparing. Wait about 10 seconds and reload.

---

## 10. Sign in, and change the initial password

| | |
|---|---|
| Administrator user name | `cynovela` |
| Viewer user name | `demo` |

The default user names are **administrator `cynovela`** / **viewer `demo`** (not `admin`).
**The administrator's initial password appears on the terminal screen once, the
very first time `./launch.sh` starts — you do not need to look for it.** It
appears on the `--demo` start as well as on the ordinary start, because neither
database ships in the package. **The viewer's value is in this package's own
`cynovela.yaml`** (`viewer_initial_password:`). **If you missed that screen**,
the administrator's value is also written into `cynovela.yaml` — read it with
`grep admin_initial_password cynovela.yaml`. They are not written in this
documentation, so that a copy of the documentation cannot be used to sign in.

1. Enter **`cynovela`** as the user name.
2. For the password, enter the administrator value shown on the terminal at the
   first start (if you missed it, read it out of `cynovela.yaml`).
3. When you log in, "**初回パスワードの変更**" (change your initial password) appears.
   Enter the value you received in "現在のパスワード" (current password), a value of your own choosing in
   "新しいパスワード（8文字以上）" (new password, 8 characters or more), enter the same value in the confirmation
   field as well, and press "**パスワードを変更して続行**" (change the password and continue).

**Until you finish this change, administrative operations such as settings will not go through** (only the change operation goes through).
Be sure to change it here.

The administrator is asked to change the password at the first login. After changing it, enter with the new value.
The viewer can be used as it is. **After you receive it, change the administrator password first.**

What to check when it does not work:

- "ユーザー名またはパスワードが正しくありません" (the user name or password is incorrect) → Copy and paste the value
  and enter it again (leading/trailing spaces and newlines easily get mixed in here).
- After the change, the admin screen shows "初回パスワードの変更が必要です" (the initial password must be changed) → Log out once
  and log in again with the new password.
- You forgot the admin password → It can be reissued with `conda run -n cynovela-dist python server.py --reset-admin`.

### Roles

With `--demo`, demo users are inserted automatically, but authentication is enforced as usual (a user name and password are required). The roles that the DB holds are the **2 values `admin` / `viewer`**.

| Role | Rights | Search target |
|---|---|---|
| `admin` | All features | The raw vault (no output masking) |
| `viewer` | Mainly viewing | The masked vault (with exit masking) |

> Names such as `curator` / `data-scientist` are normalized internally to `viewer`.

| User name (default. It is not `admin`) | Role | Password |
|---|---|---|
| `cynovela` | admin | The first value is printed on the terminal once, at the first start. If you missed it: this package's `cynovela.yaml` (`admin_initial_password:`). A change is forced at the first login |
| `demo` | viewer | The first value is in this package's `cynovela.yaml` (`viewer_initial_password:`) |

### How to create a viewer when you started with nothing loaded

If you started with nothing loaded, at first only the administrator exists. You create the viewer yourself.
Enter as the administrator, add a new user from user management, and choose viewer as the role.
If you started with the trial documents, a viewer is prepared in advance.

---

## 11. Connect the LLM that writes the answers

Cynovela is responsible up to the point of finding the documents, and **leaves the text generation to an LLM running on the same Mac**.
The bundled default is **LM Studio** (`llm.provider: lmstudio` / `llm.base_url: http://localhost:1234` in `cynovela.yaml`). Please use this default as it is at first.

### 11-1. Preparation on the LM Studio side

1. Start LM Studio.
2. Download and load a **model for chat (for generation)**.
   Example: a conversational model such as `gemma-4-12b-it`.
   **Embedding-only models (those with `embed` or `bge` in the name) cannot write answers.**
3. In the "**Developer**" tab on the left, **Start** the local server (default port 1234).

### 11-2. Settings on the Cynovela side

Open **Settings** → **LLM Provider** in the left menu and set it as follows.

| Item | Value to enter |
|---|---|
| Provider | `LM Studio` |
| Base URL | `http://localhost:1234` |
| Model | Press "📋 モデル一覧を取得" (get the model list) and choose the **chat model you loaded in 11-1** |

Press "🔌 接続テスト" (connection test) to confirm success,
and save with "💾 LLM設定をまとめて適用" (apply the LLM settings together).

**Do not leave Model blank.**
When it is blank, the **first entry** of the model list returned by LM Studio is used. If the first entry is an
embedding-only model, the generation request is rejected, no answer comes back, and you get an error (HTTP 400).
Always choose a chat model from the list.

What to check when it does not work:

- The connection test fails → Check in the LM Studio Developer tab whether the server is in the Start state.
- Nothing appears with "モデル一覧を取得" → No model is loaded in LM Studio.
  Load a model on the LM Studio side and press it again.

- Even if you specify the name of a model that is not loaded, LM Studio may not reject the
  request and may answer with a different model that is loaded. In the Model field, enter a model name that
  actually exists, chosen from the list.
- If you run several large models at the same time in LM Studio, the answers may break down or
  become slow. It returns to normal automatically after some time.
- The quality is not stable → Please check the model and settings on the LM Studio side.

For the LLM provider settings in detail — including using Ollama instead — see [operations.md](operations.md).

---

## 12. Ask your first question

1. Open **RAG Chat** in the left menu.
2. Choose the target workspace in "🏢 Workspace" at the top.
3. Write your question in the input field at the bottom and press **▶** on the right (Shift+Enter also sends it).
4. If the answer text appears with **the list of documents it referred to** below it, it worked.

Ask against a collection in the `ready` state, for example:

```
このドキュメントで扱われている主なトピックは何ですか？
```

In the answer, chunks are shown as sources with citation numbers like `[1][2]`. `admin` searches the raw body text and `viewer` the masked body text, and for `viewer` the exit masking is also applied to the LLM output.

What to check when it does not work:

- **Only "該当なし" (no match) comes back** → There are no published documents in that workspace.
  Ingest and publish documents in sections 13 and 14.
- **You get an error / the answer is empty** → Check whether Model in section 11-2 is a chat model
  (this is the most common cause).
- **It is very slow** → A large model takes tens of seconds for a single answer. Try a smaller model first.

---

## 13. Add a folder to be read (an ingest source)

The only thing this application can read is **a folder that has been added as an ingest
source**. It cannot open a location that has not been added, not even as the
administrator.

When you have added nothing, **the dummy documents inside this package
(`dummy-corpus`) are the ingest source from the start.**
If you only want to try it as it is, you may skip this section.

### Add it from the screen (recommended)

1. Open **Settings** on the left
2. Open **"📁 取り込み元" (Ingest sources)**
3. Press **"取り込み元を足す" (Add an ingest source)**
4. Browse the folders until you reach the folder you want it to read
5. Press **"このフォルダを足す" (Add this folder)**

What you added can be used immediately. It also survives a restart. **No restart is needed.**
To remove it, press **"外す" (Remove)** on the same screen. The folder and the documents
inside it are not touched.

### Add by double-clicking

Double-click **`Cynovela-add-folder.command`** in the package.
A folder chooser appears, and when you choose one it is written to the backup and becomes selectable immediately
from the screen that is already running.

* When you use it for the first time, press `Cynovela-start.command` once first. The Python (the 3.12 series) that
handles the backup is prepared during that first run. If you try to add without it, the installation steps are
printed and it stops (it does not fall back to the old python3 that comes with the Mac).

### From a terminal

```bash
# フォルダを選ぶ画面から追加する（macOS）
./launch.sh --add

# パスを直接指定して追加する
./launch.sh --add-path ~/Documents/契約

# 今どれが登録されているか見る／消す
./launch.sh --list
./launch.sh --remove<一覧に出た名前>
```

Your own documents are used in **production** (no arguments). Do not add `--demo` here.

### Passing multiple ingest sources

You can pass any number of ingest sources (the root folders of documents) at startup (`--ingest` of `server.py` is an append option. Measured 2026-08-02).

```bash
# 起動時に複数指定（それぞれがフォルダ参照画面の一覧に並ぶ）
./launch.sh --demo --ingest ~/Documents/契約 --ingest /path/to/資料

# 起動せずに追加だけ行う（動いている画面からすぐに選べます）
# ※ 追加・一覧・外すは 3.12 系の python を使います（はじめてなら先に一度
#    Cynovela-start.command を押すと用意されます）
./launch.sh --add-path /path/to/新しい取り込み元

# フォルダ選択画面から追加（macOS。Cynovela-add-folder.command のダブルクリックでも同じ）
./launch.sh --add

# 一覧・削除（足す・見る・外すは画面の Settings → 📁 取り込み元 からもできます）
./launch.sh --list
./launch.sh --remove<internal name>
```

You can also pass them all at once at startup in production.

```bash
./launch.sh --ingest ~/Documents/契約 --ingest ~/資料
```

- In this form, **adding and removing from the screen take effect as they are. A restart is not required** (the backup is re-read every time it is referenced).
- Registered roots are kept in the backup file `store/ingest-roots.json`.
- If you pass no root at all, it starts with the dummy documents inside this package (`dummy-corpus`) as the ingest source. When there is no root at all in the folder browsing of the screen, "there is not even one ingest source yet" appears, and you can add one from "add an ingest source" right there.
- Paths outside the roots are rejected with 403 (please add them with "add an ingest source" on the screen, then use them).

---

## 14. Ingest documents and publish

1. Left menu **Data Sources** → "**＋ソース追加**" (add source) at the top right.
2. Enter an easy-to-understand name in "名前" (name), choose with "📁 参照" (browse) the folder you registered in
   section 13 (or a subfolder inside it), and press "次へ" (next). A local path is entered directly
   (example: `/Users/username/Documents/`).
3. Choose the workspace to add it to (if there is none, "新しいワークスペースを作成" = create a new workspace) → "追加" (add).
4. Wait for the scan to finish.
5. Left menu **Collections** → "**＋ Collection作成**" (create a Collection) to link the workspace and the source.
   Specify a name and a RAG strategy.
6. Press "**Publish**" on the Collection you created. For how to read PDFs you can choose from
   fast, quality, or vision (read as images / OCR). Wait until it finishes (large PDFs take time).
7. When the "**✅ Publish 完了**" (publish complete) receipt appears, go back to section 12 and ask a question.

On a `--demo` start, **3 workspaces containing the bundled dummy material** (全社 / 営業 / 人事) are included; the viewer account belongs to 全社 only. Create your own workspace from "新しいワークスペースを作成".

In Publish, text extraction -> chunk splitting -> PII detection/masking -> embedding generation (saved to ChromaDB) -> BM25 index construction are performed. The progress is returned by SSE, and on completion the counts and elapsed time are recorded in `publish_history`, and the collection reaches the `ready` state.

While ingest is running, the progress is shown on the screen. The stages advance in this
order.

```
読み込み中 → チャンク書き込み中 → マスキング処理中 → マスキング処理中(まとめ) → Embedding生成中 → 完了
```

(In English: loading -> writing chunks -> masking -> masking (aggregation) ->
generating embeddings -> done)

**Ingest continues even if you close the screen.** When you open it again, you return to
the current stage and the number of items processed.
For large documents the masking stage takes time, but as long as the count keeps moving
it is making progress.

What to check when it does not work:

- **"取り込み元がまだ1件もありません" (there is not a single ingest source yet) appears** → You have not done the registration in section 13 yet.
  Add one from "取り込み元を足す" on the screen. It is usable immediately.
- **You cannot choose a folder in the browse screen / you get a 403** → You are pointing outside the range registered in section 13.
  Choose a folder inside the registered range.
- **Publish does not finish** → It takes time when there are many large PDFs. Try fast first.

---

## 15. When you place folders or files there later

Placing a folder or a file under an ingest source that is already registered does not
make it appear in the list immediately. It is reflected by any one of the following.

1. Start the application again (every start scans the registered ingest sources once;
   files that have not changed are not read again, so it is fast)
2. On the screen, the **"🔄 すべて読み込み直す"** (reload everything) button above the
   "資料" (documents) list, or **"🔄 再スキャン"** (rescan) on each row (administrators only)
3. Terminal: `python3 cynovela-cli.py ingest --path <folder>` (new) /
   `python3 cynovela-cli.py scan start --source <ID>` (already registered)
4. MCP: `ingest_source` / `get_job_status`

The scan returns immediately once started; you follow the progress with the toast on the
screen, or with `scan status --job <job_id>` of the CLI (stop it with
`scan cancel --source <ID>`). To appear in search, go on as in section 14: link it to a
collection and publish it.

---

## 16. Everyday startup

There are two ways to start. **No argument is production** (it starts from an empty database, and you ingest and use your own documents), and **adding `--demo` is the demo** (the demo DB with the bundled dummy documents; they are ingested automatically at the first start).

```bash
# The entry point is launch.sh (or double-click Cynovela-start.command)
./launch.sh            # production: an empty database
./launch.sh --demo     # if you want to try it first, use the demo (with the dummy documents)

# Open it in a browser
# http://localhost:8765
```

### There are 2 ways to start it, and 2 things that can start

**Start it by double-clicking (the easiest way)**

In the folder you extracted, double-click **`Cynovela-start.command`**.
To stop it, double-click **`Cynovela-stop.command`**.
To add a folder to be read, double-click **`Cynovela-add-folder.command`**
(the first time you use it, press `Cynovela-start.command` once first. The Python used
to handle folder backups is prepared during that first run).

**This procedure starts up with an empty database (production).** To try it with the
bundled dummy documents, double-click **`Cynovela-demo.command`** (or run
`./launch.sh --demo` from the terminal).
Right after it opens, you can ask questions about the bundled documents. Both the
administrator and the viewer can sign in with the passwords described in section 10.

To use it with your own documents only, run it from the terminal **with no arguments**.
That starts from an **empty database** (production). There is no viewer in an empty
production database (you sign in as the administrator and ingest documents first).

| What starts | What happens | How to get it |
|---|---|---|
| Demo | Starts with the bundled dummy documents (they are **ingested automatically at the first start**; once that finishes you can ask questions) | Double-click `Cynovela-demo.command`, or `./launch.sh --demo` from the terminal |
| Production | Starts with an empty database. When there are 0 ingest sources, the dummy documents inside this package become the ingest source | Double-click `Cynovela-start.command`, or `./launch.sh` (no arguments) |

**Start it from the terminal**

In the folder you extracted, run the following single line. **This is the only entry
point when you use the terminal.**

```bash
./launch.sh --demo
```

This starts the demo. At the first start, the bundled dummy documents are
ingested automatically (progress is printed to the startup log).
To use it with your own documents, run `./launch.sh` with nothing attached.

If something needed to run it is missing, you are told **before it starts**: "something
is missing, so it will not start".
In that case, run the following.

```bash
./launch.sh --setup
```

You can print the list of everything it can do at any time with this.

```bash
./launch.sh --help
```

### Notes before the first start

- macOS attaches a mark (`com.apple.quarantine`) to a downloaded package, and confirmations
  can appear again and again, one per component. `./launch.sh` removes all of these marks
  inside the package by itself at the very beginning of startup. To do it by hand:
  `xattr -rc <folder>`.
- Do not place the package under a cloud-synced folder (iCloud Drive, Dropbox, OneDrive,
  Google Drive). `./launch.sh` detects this before starting and shows a warning (it goes
  on without stopping).
- When the bundled environment (`.condapack-cynovela`) is already there and works, `./launch.sh`
  starts as it is, without showing the screen for choosing the base (the choice screen
  appears only when it is broken).

If you must start the server by hand instead of through `launch.sh` (the environment must already exist — the dedicated name is `cynovela-dist`; never create or modify a shared environment):

```bash
# 1. Activate the dedicated environment of this package
conda activate cynovela-dist

# 2. Countermeasure for the SSL certificate error (macOS. launch.sh does this for you)
unset SSL_CERT_FILE

# 3. Start the server
python server.py --mode text          # production
python server.py --mode text --demo   # demo
```

### Frequently used operations

```bash
# 起動（2 回目以降）。引数なしは本番。デモで使っていた場合は --demo を付ける
./launch.sh

# 停止
bash stop.sh

# ログを流しながら起動したいとき（デモで使う場合は --demo も付ける）
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

- For backup and restore, changing the port, and reading the logs, see [operations.md](operations.md).
- Do not put passwords or tokens in a memo app or a shared folder.
  For a token when calling the API directly, use the one issued each time by login (`POST /api/auth/login`).
  A fixed, password-like token is not accepted.

---

## 17. Startup options

| Option | Description |
|---|---|
| `--mode text` | Text mode (standard) |
| `--demo` | Start with the demo DB that uses the bundled dummy documents (ingested automatically at the first start; if not given, production = an empty database) |
| `--reset-admin` | Reset the administrator password, show the new value, and exit. **The target database is chosen by the same rule as the other options, so when fixing the administrator of the demo, write `--demo` together** (without it, production `store/db/cynovela.db` becomes the target, and it is newly created if it does not exist. The demo side does not change, so the demo login stays 401. Measured 2026-08-02) |
| `--local-only` | Restrict to inside your own machine only (the default listens on all addresses, `0.0.0.0`) |
| `--port N` | Port number (default 8765) |

### List of startup forms (--mode) (measured 2026-08-12)

| Form | Required model | Approximate size | What changes |
|---|---|---|---|
| `--mode text` | BAAI/bge-m3 | About 2.3GB | Default. It runs with all features of text RAG |
| `--mode lite` | The switch is **not wired** = it is actually BAAI/bge-m3 | — | Switching is not wired, so only the displayed name changes (behavior is the same as text) |
| `--mode lite-en` | The switch is **not wired** = it is actually BAAI/bge-m3 | — | Switching is not wired, so only the displayed name changes (behavior is the same as text) |

All of them can be specified in the form `./launch.sh --demo --mode<name> --port<number>` (measured).

If the model has not been fetched at the first start, an interactive prompt from the preflight check (download / switch to another mode / cancel) is displayed. In a non-interactive environment, if you set `CYNOVELA_NONINTERACTIVE=1` it stops with exit code 2 when the model is not cached.

```bash
# 例: 表示名を変えて起動する（動作と必要モデルは text と同じ・切替は未配線）
./launch.sh --demo --mode lite
```

---

## 18. The route through the terminal (summary)

This is the same as what `./launch.sh --help` prints.

| What you type | What happens |
|---|---|
| `./launch.sh` | Starts in production (an empty database). If there are 0 ingest sources, it uses the bundled dummy documents |
| `./launch.sh --demo` | Starts the demo with the bundled dummy documents (ingested automatically at the first start) |
| `./launch.sh --setup` | Installs what is needed to run it (it stops once installed) |
| `./launch.sh --check` | Does not start; only checks the conditions for running and writes them to a single file |
| `./launch.sh --add` | Shows a folder chooser and adds an ingest source |
| `./launch.sh --add-path<path>` | Adds an ingest source by specifying a location |
| `./launch.sh --list` | Lists the ingest sources that have been added |
| `./launch.sh --remove<name>` | Removes an ingest source (the name is the one shown by `--list`) |
| `./launch.sh --ingest<path>` | Adds it and starts up straight away |
| `./launch.sh --base conda` | Creates a new dedicated conda environment |
| `./launch.sh --base venv` | Creates it inside this package only |
| `./launch.sh --base none` | Creates nothing |
| `./launch.sh --env-name<name>` | Changes the name of the conda environment (default `cynovela-dist`) |
| `./launch.sh --verbose` | Prints the raw output during installation as it is |
| `./launch.sh --port<number>` | Changes the port number it opens on (default 8765) |
| `./launch.sh --local-only` | Restricts listening to this machine only |
| `bash stop.sh` | Stops it |

If you type an option it does not know, it does not fail silently: this list (the help)
is printed.

---

## 19. Stopping, and starting again

#### Stop it

Open Terminal, go into the folder you unpacked, and run one line:

```
cd ~/Downloads/chewie
bash stop.sh
```

It prints one of these:

```
Cynovela を停止します (PID: 12345)...
停止完了
```

```
PIDファイル(/Users/…/store/server.pid)がありません。停止対象なし。
```

The second one means it was not running. Nothing is wrong.

If you prefer clicking: double-click **`Cynovela-stop.command`** in the folder.

#### Start it again

```
cd ~/Downloads/chewie
./launch.sh --demo
```

Leave off `--demo` if you are using your own folders instead of the bundled
sample documents. **Use the same choice every time** — see section 20.

Or double-click **`Cynovela-start.command`**.

Starting again takes **20 to 60 seconds**, not the three to eight minutes the
very first start took.

**You may run `./launch.sh` again while it is still up.**
It stops what is already running and brings it back up. If it could not be stopped, it
shows you what is running and how to stop it by hand, and stops there.

#### If something else is already running

`./launch.sh` looks first, and if it finds a running copy it shows you this:

```
先に、いま動いているものを調べました。
  server.py（PID 12345）  : 動いています（待ち受け 8765）
このまま新しく起こすと、同じものが二重に立ち上がります。
どうしますか。
  1) 動いているものを止めて、新しく起こす
  2) 止まっているものを、そのまま起こし直す
  3) 動いているものへ、そのままつなぐ
  4) 動いているものを止めて、終わる
  5) 何もせずに終わる
番号を入れてください [1/2/3/4/5]:
```

* Pick **3** if you just want the address of the copy that is already up.
* Pick **1** if you changed a setting and want a fresh start.
* Pick **4** to stop it and go away.

None of these delete anything.

#### After restarting your Mac

The tool does not start itself. Do the "start it again" steps above.

---

## 20. What is going on when you stop and start again

#### Why `--demo` has to be the same every time

`--demo` does not mean "with sample data on top of my data". It selects a
**different database and a different index**:

| Started with | Database it uses | Index it uses |
|---|---|---|
| `./launch.sh` | `store/db/cynovela.db` | `store/vector/default/chroma` |
| `./launch.sh --demo` | `store/db/demo.db` | `store/vector/demo/chroma` |

So a folder you added while running with `--demo` is not there when you start
without it, and the other way round. Nothing was lost — you are looking at the
other set. Start it again the way you started it before and your work is back.

The two never mix, which is the point: the sample documents cannot end up in
your real answers.

#### Why `stop.sh` is safe

It reads the process number out of `store/server.pid`, checks that the process
with that number really is `server.py`, and only then stops it. It never
searches for something listening on a port and never uses `pkill`, so it cannot
stop a different program that happens to be using port 8765.

If it reports that the PID file is missing, the tool had already stopped and cleaned up
after itself.

#### Why closing the Terminal window does not stop it

`./launch.sh` detaches the program from the window before it finishes. That is
deliberate: the tool is meant to keep running while you use the browser, and
people close Terminal windows. `bash stop.sh` is the way back.

#### What survives a stop

Everything: documents you ingested, the search index, users, settings, the
audit log. They all live in `store/` inside the folder. Stopping only ends the
process.

The only thing that goes away is anything that was still running when you
stopped it — a scan or a publish in progress. Start those again from the screen
or with `cynovela-cli scan start` / `cynovela-cli publish start`.

#### When the environment itself is broken

If it fails to start and reports that something is missing:

```
./launch.sh --setup
```

That rebuilds the Python environment and does not start the tool. Then start
normally. Your documents and settings are untouched.

---

## 21. Checking behavior (tests)

> **The package does not contain `tests/`** (it is taken out when the package is built). On the package you received, `pytest` / `make test` cannot be run.
> To check the behavior, please use `conda run -n cynovela-dist python scripts/test_comprehensive_e2e.py`.

```bash
# 開発ツリー（tests/ が在る側）での実行

# 手動 pytest（軽量・最初の失敗で停止）
cd<開発ツリーのフォルダ>
unset SSL_CERT_FILE
conda run -n cynovela-dist python -m pytest -x -q
```

`make test` / `make test-quick` / `make verify-live` in the `Makefile` can also be used. The `live` family assumes that the server is running at `http://127.0.0.1:8765`.

---

## 22. When things do not work

| What you see on the screen | What to do |
|---|---|
| "取り込み元がまだ1件もありません" (There is not a single ingest source yet) | Press **"取り込み元を足す" (Add an ingest source)** on the screen (section 13). A button leading there appears below this message |
| "初回パスワードの変更が必要です" (The initial password must be changed) | Section 0 and section 10. Change the password first |
| "ポート 8765 を別のものが使っています" (Port 8765 is used by something else) | Bring it up on a different port: `./launch.sh --port<another number>` |
| "足りないものがあるので起動しません" (Something is missing, so it will not start) | Run `./launch.sh --setup` |
| The progress looks stuck | If the count is moving, it is making progress. The masking stage takes time |

- **The model download or HTTPS fails with SSL** -> Please `unset SSL_CERT_FILE` before starting or testing (unnecessary when using the launcher).
- **It cannot be opened from another device on the LAN** -> Since it listens on `0.0.0.0` by default, first check the port and the destination IP (if you added `--local-only`, it is narrowed to your own machine).
- **The quality is not stable** -> Please check the model and settings on the LM Studio side.
- **You forgot the admin password** -> It can be reissued with `conda run -n cynovela-dist python server.py --reset-admin`.
- **Port 8765 is in use** -> Check with `lsof -i :8765`. Because `./stop.sh` stops only the PID recorded at startup (the Cynovela server itself), even if 8765 is used for another purpose that process is not affected. If there is no recorded PID and you stop it manually, please confirm that the target is Cynovela and then use something like `pkill -f "python server.py"`.

Each section above also has its own "what to check when it does not work" list.
For anything else, please see [faq.md](faq.md).

---

## 23. Where to go next

- [operations.md](operations.md) — The LLM provider settings in detail (including Ollama), backup and restore, changing the port, reading the logs
- [architecture.md](architecture.md) — Understand the system configuration
- [handson.md](handson.md) — Try the basic operations
- [architecture.md](architecture.md) §4 "How search works" — Understand the RAG pipeline
- [faq.md](faq.md) — Frequently asked questions

More detail is in the bundled `README.md`.

---

# 日本語

この1枚だけで、最初の質問が返るところまで行けます。
**画面だけで済む道を先に書いています。** ターミナルを使う道は後ろにまとめました。

> 唯一の入口の文書は [START-HERE.md](../START-HERE.md) です。初めての方はそちらから始めてください。

所要時間の目安: 初回 30〜60 分（うち大半は動作環境の作成待ちとモデルの読み込み待ち）。
このガイドの手順は上から順に実行してください。

2節と3節は、ターミナルを一度も開いたことが無い方を想定して書いています。省略はしていません。
ターミナルに慣れている方は、4節が最短の道です。日々の起動は16節です。

| こういう方 | 読むところ |
|---|---|
| ターミナルを一度も開いたことが無い | 0節、そのあと 2節と3節 |
| 急いでいて、ターミナルは分かる | 4節 |
| 初回の流れを順に読みたい（ソース版を含む） | 5節〜15節 |
| 一度動かしていて、起こし直したいだけ | 16節〜20節 |
| うまくいかない | 22節 |

運用の話 — LLMプロバイダーの詳しい設定（Ollama を含む）・バックアップと復元・ポート変更・
ログ確認 — は [operations.md](operations.md) にあります。

---

**目次**

- [0. 先に知っておくこと（ここでつまずく人が一番多いところ）](#0-先に知っておくことここでつまずく人が一番多いところ)
- [1. どの配布物を落としましたか](#1-どの配布物を落としましたか)
- [2. やさしい入口 — パッケージ版を一歩ずつ](#2-やさしい入口--パッケージ版を一歩ずつ)
- [3. なぜその手順なのか](#3-なぜその手順なのか)
- [4. 急ぐ人のための最短の道](#4-急ぐ人のための最短の道)
  - [4-1. 環境のセットアップ（ソース版のみ）](#4-1-環境のセットアップソース版のみ)
  - [4-2. SSL_CERT_FILE の注意（重要）](#4-2-ssl_cert_file-の注意重要)
  - [4-3. 起動](#4-3-起動)
- [5. 用意するもの（ソース版）](#5-用意するものソース版)
- [6. 展開する](#6-展開する)
- [7. 動作環境を作って起動する](#7-動作環境を作って起動する)
- [8. 初回だけ：AIモデルのダウンロードを選ぶ画面が出ます](#8-初回だけaiモデルのダウンロードを選ぶ画面が出ます)
- [9. ブラウザで開く](#9-ブラウザで開く)
- [10. ログインと初回のパスワード変更](#10-ログインと初回のパスワード変更)
  - [ロール](#ロール)
  - [何も入れずに始めた場合の、閲覧者の作り方](#何も入れずに始めた場合の閲覧者の作り方)
- [11. 回答を作る LLM をつなぐ](#11-回答を作る-llm-をつなぐ)
  - [11-1. LM Studio 側の準備](#11-1-lm-studio-側の準備)
  - [11-2. Cynovela 側の設定](#11-2-cynovela-側の設定)
- [12. 最初の質問をする](#12-最初の質問をする)
- [13. 検索の対象フォルダ（取り込み元）を足す](#13-検索の対象フォルダ取り込み元を足す)
  - [画面から足す（おすすめ）](#画面から足すおすすめ)
  - [ダブルクリックで足す](#ダブルクリックで足す)
  - [ターミナルから足す](#ターミナルから足す)
  - [取り込み元を複数渡す](#取り込み元を複数渡す)
- [14. 資料を取り込んで公開する](#14-資料を取り込んで公開する)
- [15. 後からフォルダやファイルを置いたとき](#15-後からフォルダやファイルを置いたとき)
- [16. 日常の起動手順](#16-日常の起動手順)
  - [起動の仕方は 2 通り、起動の中身も 2 通りあります](#起動の仕方は-2-通り起動の中身も-2-通りあります)
  - [はじめて起動する前の注意](#はじめて起動する前の注意)
  - [よく使う操作](#よく使う操作)
- [17. 起動オプション](#17-起動オプション)
  - [起動の形（--mode）の一覧（実測・2026-08-12）](#起動の形--modeの一覧実測2026-08-12)
- [18. ターミナルで行う道（まとめ）](#18-ターミナルで行う道まとめ)
- [19. 止め方と、起こし直し方](#19-止め方と起こし直し方)
- [20. 止めて起こし直すとき何が起きているのか](#20-止めて起こし直すとき何が起きているのか)
- [21. 動作確認（テスト）](#21-動作確認テスト)
- [22. うまくいかないとき](#22-うまくいかないとき)
- [23. 次に読むもの](#23-次に読むもの)

## 0. 先に知っておくこと（ここでつまずく人が一番多いところ）

- **管理者で最初に入ると、必ず「パスワードを変えてください」と出ます。**
- **変え終わるまで、管理の操作（取り込み元を足す・資料を取り込む・設定を変える）は
  すべて拒否されます。** 先に変えてください。
- 閲覧者（demo）は変更を求められません。ただし閲覧者は取り込みができません。

この配布物は、お使いの機械の上で直接動きます。

壊れて見えるが壊れていない2つのこと:

1. **ここに出てくる命令は、うまくいったときほど何も出しません。** 成功すると、
   何も言わずに次の行を打てる状態に戻るだけです。ここでは沈黙が成功です。
   しゃべるのは失敗したときだけです。
2. **数分のあいだ、まったく反応が無い場面があります。** モデルのファイルをつなぐ
   ところと、最初の起動がそれです。固まっていません。触らずに待ってください。

---

## 1. どの配布物を落としましたか

配布物は 2 つの形と、別便の AIモデルです。**パッケージ版が先です** — お持ちなら4節と7節の環境づくりは丸ごと飛ばせます。`.part00`〜`.part02` という名前のファイルは分割ファイルです: 展開の前に part の順に 1 本へつなぎ、`shasum -a 256 --ignore-missing -c SHA256SUMS` で確かめます。手引きは Releases のファイルの並びに置いてある **HOW-TO-ASSEMBLE.md** です。

| 配布物 | 対象 | することは |
|---|---|---|
| **パッケージ版** `cynovela-chewie-package-1.2.0.tar.gz`（1本・約800MB） | Apple silicon の Mac。**Python も conda も要りません。この Mac には何も入れません。** | 展開し、AIモデル（最終行）を重ねてから `./launch.sh` を叩きます。消すときはフォルダごと削除します。 |
| **ソース版**（ダウンロードではありません。ソースはこのリポジトリです） | 自分で環境を作りたい方 | リポジトリを clone するか GitHub の「Download ZIP」で取り、`chewie/` の木に AIモデル（最終行）を重ねてから、下の7節へ。 |
| **AIモデル** `cynovela-chewie-models-1.2.0.tar.gz.part00`〜`part02`（分割3本） | パッケージ版とソース版に必要です。名前は models ですが、conda のパッケージではなく **AIモデル本体**です。 | part を 1 本につないでから、**展開済みの chewie フォルダの中で** `tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz` を実行します（`store/models/` が作られます）。 |

ソース版では、起動時に、環境の作り方を2つから選びます。

```
ソース版：環境の作り方（起動時に選びます）
  1) conda に専用の環境を作る
       Python の出どころ : conda が conda-forge から取り寄せます。
       作られるもの      : conda の環境1つ（専用の名前: cynovela-dist）。
       残るもの          : conda のフォルダの中にその環境1つ。共有の環境には触りません。
  2) この Mac の Python を使い、この配布物のフォルダの中だけに作る
       Python の出どころ : この Mac に既に在る 3.12 以上の Python（版はその Python 自身に答えさせて確かめます）。
       作られるもの      : この配布物のフォルダの中の .venv-cynovela という venv。
       残るもの          : このフォルダの中だけ。外には何も変更を加えません。
```

AIモデルは別に落とします（8節「初回だけ」を参照）。

---

## 2. やさしい入口 — パッケージ版を一歩ずつ

この節は**パッケージ版**（`cynovela-chewie-package-1.2.0.tar.gz`）向けです。
ターミナルを一度も開いたことが無い方を想定して書いています。省略はしていません。

上から順に行ってください。理由は3節にあります。先に読む必要はありません。

#### 手順1. ファイルを5つ落とす

リリースのページから、次の5つを**ダウンロード**フォルダへ落とします。

```
cynovela-chewie-package-1.2.0.tar.gz
cynovela-chewie-models-1.2.0.tar.gz.part00
cynovela-chewie-models-1.2.0.tar.gz.part01
cynovela-chewie-models-1.2.0.tar.gz.part02
SHA256SUMS
```

合わせて約 5.4 GB です。5つとも終わるまで待ってください。

#### 手順2. ターミナルを開く

**⌘（コマンド）キーと スペースキー**を同時に押します。画面の真ん中に検索の枠が
出ます。`terminal` と打ち、**return** を押します。

白か黒の文字とカーソルが点滅する窓が開きます。これがターミナルです。
以下はすべてこの窓に打ちます。1行打つごとに **return** を押します。

#### 手順3. ダウンロードのフォルダへ移る

次の1行を打って return を押します。

```
cd ~/Downloads
```

何も出ません。それで合っています。

#### 手順4. モデルの3つの分割ファイルを1本につなぐ

次を**1行で**打って return を押します。

```
cat cynovela-chewie-models-1.2.0.tar.gz.part* > cynovela-chewie-models-1.2.0.tar.gz
```

**1〜3分**かかります。そのあいだ何も出ません。カーソルが戻ってきたら終わりです。

#### 手順5. ちゃんと落ちているかを確かめる

```
shasum -a 256 --ignore-missing -c SHA256SUMS
```

**1〜3分**かかります。そのあとファイルごとに1行ずつ出ます。全部の行が `OK` で
終わっていなければなりません。

```
cynovela-chewie-models-1.2.0.tar.gz: OK
cynovela-chewie-package-1.2.0.tar.gz: OK
```

`FAILED` と出た行があれば、そのファイルを落とし直して手順4からやり直します。
先へ進まないでください。

#### 手順6. 本体を取り出す

```
tar -xzf cynovela-chewie-package-1.2.0.tar.gz
```

**3〜10分**かかります。何も出ません。ダウンロードの中に `chewie` という名前の
フォルダができます。

#### 手順7. そのフォルダの中へ移る

```
cd chewie
```

何も出ません。

#### 手順8. その中で AIモデルを取り出す

```
tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz
```

**2〜5分**かかります。何も出ません。

#### 手順9. 起こす

```
./launch.sh --demo
```

`--demo` を付けると、配布物に入っているお試しの資料を使うデモで立ち上がります
（初回起動時に自動で取り込まれます）。初日から質問できる材料が付いている、
ということです。付けないと中身が空の状態で立ち上がるので、先に自分のフォルダを
足す必要があります。

ここからは向こうがしゃべります。出てくる順に書きます。

```
先に、いま動いているものを調べました。
  動いているものは 0個 でした。
このまま進みます。

同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました。選択の画面は出さず、これを使って起動します。
記録はこのファイルへ書きます: /Users/…/Downloads/chewie/store/launch-app.log
起動しています (本体はこのターミナルから切り離して動かします)
```

2行目は「同梱の環境が見つかったので、環境の作り方を聞く画面は出しません」という
意味です。ここでは何も聞かれません。

**最初の起動は3〜8分かかります。** そのあいだ何も出ません。用意ができると
次が出ます。

```
立ち上がりました。
  開くところ : http://127.0.0.1:8765/
  記録       : /Users/…/Downloads/chewie/store/launch-app.log
止めるときは、次のように叩いてください。
  bash stop.sh
```

#### 手順10. ブラウザで開く

**⌘** を押しながら `http://127.0.0.1:8765/` をクリックします。または Safari や
Chrome のアドレス欄にそのまま打ち込みます。

ログインの画面が出ます。

#### 手順11. ログインする

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

入るとすぐに、新しい合言葉を決めるよう求められます。決めてください。

#### 手順12. 最初の質問をする

`--demo` で起こしたので、お試しの資料は初回起動時に自動で取り込まれ、探せる状態になっています
（起動ログに取り込みの進捗がまだ出ている間は、終わるのを待ってください）。ふつうの言葉で枠に打ち込んで return を
押します。たとえば次のようにです。

```
特別休暇は結婚のとき何日もらえますか
```

**最初の答えは1〜4分かかります。** AIモデルをいったん記憶に読み込む必要が
あるためです。2回目からはずっと速くなります。

答えの下には、その答えの元になった文の断片が並びます。開いて、答えと突き合わせて
ください。この道具はそのために在ります。

#### 手順13. 終わったら止める

ターミナルで次を打ちます。

```
bash stop.sh
```

次が出ます。

```
Cynovela を停止します (PID: 12345)...
停止完了
```

読み込んだ資料と設定はそのまま残ります。

---

## 3. なぜその手順なのか

#### なぜ1本ではなく5つなのか

GitHub は数ギガバイトを超える1本のファイルを置かせてくれません。∴ AIモデルは
1.5 GB ずつ3つに切ってあります。手順4がそれを貼り合わせています。
`SHA256SUMS` は指紋の一覧です。手順5は、あなたのディスクに落ちたものの指紋を
その場で計算し直して突き合わせています。途中で止まったダウンロードは、使おうと
するまで普通のファイルに見えます。∴ この3分は払う価値があります。

#### なぜ `cd ~/Downloads` なのか

ターミナルには「いま立っているフォルダ」が1つあります。`cd` はそれを移す命令です。
`~` は自分のホームフォルダ（Finder で自分の名前が付いているところ）の略記です。
∴ `~/Downloads` は Finder で見えているダウンロードと同じ場所です。
以降の命令は、ターミナルが立っているフォルダのファイルに対して働きます。
手順7で `chewie` の中へ移ってからモデルを取り出しているのはそのためです。
モデルは本体のフォルダの**中**に置かれなければならず、隣ではいけません。

#### なぜ何も出ないのか

Unix の命令は互いにつなぎ合わせて使うために作られたので、異常が無いかぎり黙って
います。`cd` も `cat` も `tar` もその流儀です。壊れていないのに壊れたと思われる
いちばんの理由がこれです。

#### なぜパッケージ版は Python も conda も要らないのか

取り出したフォルダの中に、そのフォルダ専用の Python と、必要な部品一式が
`.condapack-cynovela` という入れ物で既に入っているからです。名前が点で始まるので
Finder は隠します。これは「触らなくてよいもの」という macOS の決まりであって、
何かがおかしい印ではありません。（Finder で **⌘ + shift + .** を押すと隠れている
ものが出ます。もう一度押すと戻ります。）
全部がフォルダの中で完結しているので、この Mac の他の場所には何も書きません。
フォルダごと消せば、それで完全に取り除いたことになります。

手順9で *「同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました」* と出て、環境の作り方を
**聞かれない**のもこれが理由です。ソース版は環境をまだ持っていないので聞きます。

#### なぜ最初の起動だけ遅いのか

最初の起動では、AIモデルをディスクから読み、同梱のデモ資料に対する索引を作り、
データベースを用意します。2回目からは3つとも既に在るので、そのまま使われます。

#### なぜ最初の答えが遅いのか

答えを作るには言語モデルが要ります。これは Cynovela の外で動いています
（LM Studio や、OpenAI と同じ形の口を持つもの）。最初の質問で、その向こう側が
モデルを記憶へ読み込みます。数ギガバイトです。1語も返らないうちにその時間が
かかります。Cynovela は1回の呼び出しにつき 120秒 まで待ちます。時間切れの
知らせが出たときは、先に LM Studio でモデルを読み込んでから、もう一度
聞いてください。

#### なぜ合言葉がファイルにも書いてあるのか

最初の合言葉は、はじめて起動したときにターミナルの画面へ1回だけ出ます。探す
必要はありません。同じ値がパッケージングのときに `cynovela.yaml` へも書き込まれる
ので、画面を見逃した場合でもそこで確かめられます。配布物は1本ごとに違う最初の
合言葉を持って作られます。全員同じだったら、この道具をダウンロードした人は
誰でもあなたの合言葉を知っていることになります。最初のログインで変えるよう
求めるのも同じ理由です。変えるまで、管理の操作は通しません。

#### なぜ iCloud Drive・Dropbox・OneDrive の中に置いてはいけないのか

これらは全てのファイルを向こうのサーバへ写し、手元のファイルを実体のない
代わりのファイルだけに置き換えることがあります。数ギガバイトの部品がまるごと送られますし、
その代わりのファイルは実行できないので、原因の分かりにくい形で動かなくなります。
`./launch.sh` はそういう場所を見つけると知らせますが、止めはしません。
`~/Downloads` かホームフォルダの直下のような、素直な場所へ置いてください。

#### なぜターミナルを閉じてよいのか

`./launch.sh` は、終わる前に本体をターミナルの窓から切り離します。窓を閉じても
本体は止まりません。∴ 止めるための `bash stop.sh` が別に在ります。

---

## 4. 急ぐ人のための最短の道

Cynovela を初めて起動し、最初の RAG 質問を投げるまでの最短手順です。対象は版 `1.2.0`（作業ディレクトリ `<配布物を展開したフォルダ>`）です。

### 4-1. 環境のセットアップ（ソース版のみ）

**推奨は `./launch.sh` に作らせる形です。** 初回に下の 2 択が出ます。どちらを選んでも**共有の conda 環境は作りません・書き換えません**（すべて専用の場所に作られます）:

```bash
cd <配布物を展開したフォルダ>
./launch.sh
#   1) 専用の conda 環境を作る（名前: cynovela-dist）
#   2) この配布物のフォルダの中だけに Python の環境を作る
```

`launch.sh` を使えず手で作るしかない場合は、**配布物専用の名前 `cynovela-dist`** を使ってください。共有の環境は作らない・書き換えないでください:

```bash
# この配布物専用の環境を作る（共有の名前を使わない）
conda create -n cynovela-dist python=3.12 -y

# 依存ライブラリをインストール
conda run -n cynovela-dist python -m pip install -r requirements.txt
```

主な依存: FastAPI / uvicorn / ChromaDB / sentence-transformers / spaCy + ja-ginza / torch / pypdf ほか（`requirements.txt` 参照）。

### 4-2. SSL_CERT_FILE の注意（重要）

conda 環境では `SSL_CERT_FILE` が誤った証明書パスを指すことがあり、起動時の HuggingFace モデルダウンロードが失敗します。`unset` してシステムデフォルトの証明書を使ってください。

```bash
unset SSL_CERT_FILE
```

同梱の `launch.sh` はこの `unset` を内包しているため、これを使う場合は不要です。**手動で `conda run` を実行する場合のみ**、各自で実行してください。

### 4-3. 起動

**方法 1: 同梱ランチャー（推奨）**

```bash
cd<配布物を展開したフォルダ>

# launch.sh に渡した引数は、そのまま server.py へ届きます
# （実装: launch.sh の `exec "$PY" server.py "${APP_ARGS[@]}"`。2026-08-02 実測）。
# 引数なしは本番（空のデータベース）です。デモを見るなら --demo を明示します。
./launch.sh --demo            # デモデータ + 実 LLM（既定は 0.0.0.0 で待ち受け。自分の機械の中だけに絞るなら --local-only）
./launch.sh --demo --lan      # デモデータ + LAN 公開
./launch.sh --check           # 起動せずに動く条件だけを調べる
```

停止:

```bash
./stop.sh
```

**方法 2: 手動起動**

```bash
cd<配布物を展開したフォルダ>
unset SSL_CERT_FILE

# デモデータ + 実 LLM（LM Studio を http://localhost:1234 で起動しておく）
# 名前は配布物専用の cynovela-dist。共有の環境は作らない・書き換えない
conda run -n cynovela-dist python server.py --demo
```

アクセス:

```bash
open http://127.0.0.1:8765
```

> ⚠️ **実 LLM が要ります**: 質問への答えを作るには LM Studio などの LLM が要ります。以前あった `--mock`（LLM を呼ばずに動かす指定）は撤去済みで、いま指定するとエラーで止まります。

ここから先は、ログイン（10節）・最初の質問（12節）・自分の資料の取り込み（13節と14節）へ進みます。

---

## 5. 用意するもの（ソース版）

| 必要なもの | 確認のしかた |
|---|---|
| macOS（Apple シリコン推奨） | — |
| conda（miniforge 推奨） | ターミナルで `conda --version` を実行して版が出ること |
| Python 3.12 以上 | `pyproject.toml` が `requires-python = ">=3.12"` を宣言しています。3.10・3.11 は使えません。7節で conda が 3.12 系を用意します |
| LM Studio（回答を作る LLM） | アプリを起動できること（11節で使います） |
| 空き容量 20GB 以上 | `df -h /` の Avail 欄 |

conda が入っていない場合は miniforge を入れてください。
（https://github.com/conda-forge/miniforge/releases/latest から、Apple シリコンなら
`Miniforge3-MacOSX-arm64.sh` を取得して実行します。）

管理された Mac（MDM 配下）では、取り寄せ先そのもの（conda-forge・PyPI・github.com・huggingface.co）が
許可されていないことがあります。その場合は、取り寄せの要らないパッケージ版を選んでください。

（パッケージ版は Python も conda も要りません。3節「なぜパッケージ版は Python も conda も要らないのか」を参照。）

うまくいかないときに確認すること:

- `conda: command not found` → インストール後にターミナルを開き直していないことが多いです。
  新しいターミナルを開いてもう一度確認してください。

---

## 6. 展開する

```bash
cd ~/Downloads                # tar.gz を置いた場所へ
tar -xzf<配布物名>.tar.gz
cd<展開してできたフォルダ>      # 名前は cynovela- で始まります (ls で確認できます)
ls launch.sh                  # このファイルが見えれば展開できています
```

うまくいかないときに確認すること:

- `tar: Error opening archive` → ダウンロードが途中で切れています。もう一度受け取り直してください。
- `cd` で「No such file or directory」→ 展開先のフォルダ名が違います。
  `ls` で出てきたフォルダ名に読み替えてください。

---

## 7. 動作環境を作って起動する

はじめての方は、同梱のダミー資料を使う**デモ**で試すのがおすすめです。`--demo` を付けて起動してください（ダミー資料は初回起動時に自動で取り込まれます。付けずに起動すると**本番**＝空のデータベースで始まります）。

```bash
./launch.sh --demo
```

このコマンド 1 本で、conda 環境の作成（専用の名前 `cynovela-dist`。共有の conda 環境は作りません・書き換えません）→ 必要な部品の導入 → 起動まで進みます。
画面には次の順で出ます。

```
[Step 1] conda を確認中...
✅ conda: /Users/xxx/miniforge3
[Step 2] conda環境 'cynovela-dist' を確認中...
⚠️  環境 'cynovela-dist' が見つかりません。作成します...
   （初回は5〜15分かかります）
[Step 3] 環境 'cynovela-dist' をアクティベート中...
[Step 4] pip パッケージを確認中...
[Step 5] ポート8765の状態を確認中...
[Step 6] Cynovela を起動します...
Cynovela を起動します... (http://localhost:8765)
```

- 待ち受けポートは既定 **8765** です。変えたいときは `./launch.sh --demo --port 8900`。
- 2 回目以降は環境の作成が省かれ、1 分ほどで起動します。

うまくいかないときに確認すること:

- **「ポート8765はすでに使用中です」と聞かれる** → 前回の起動が残っています。
  `r`（既存を止めて起動し直す）を選ぶのが安全です。
- **Step 2 の環境作成でエラーになる** → 空き容量とインターネット接続を確認してください
  （初回だけ部品の取得に接続が必要です）。
- **止めたいとき** → 別のターミナルで `bash stop.sh` を実行します。

---

## 8. 初回だけ：AIモデルのダウンロードを選ぶ画面が出ます

モデルを同梱しない形（パッケージ版や、このリポジトリのソースをそのまま使う形）では、
資料を読み取るための AI モデル（埋め込みモデル bge-m3）が初回はまだ入っていません。無いときだけ、
起動の途中で次の三択が出ます。

1. **いまダウンロードする** — インターネットから約 2.2〜2.3 GB を受け取ります（ダウンロード元: Hugging Face）。通信が要ります。
2. **すでに持っているフォルダを選ぶ** — 手元にあるモデルのフォルダをつなぎます。
3. **ダウンロードせずに、いちばん軽い設定で始める** — 通信なしで始めます。

どれかを選ぶまで、通信は始まりません。
（`Cynovela-start.command` のダブルクリックから始めた場合は、同じ内容が「ダウンロードする／キャンセル」の画面で出ます。）

---

## 9. ブラウザで開く

ブラウザで次を開きます（7節でポートを変えた場合はその番号に読み替え）。

```
http://localhost:8765
```

ログイン画面（「ユーザー名／パスワードでログイン」）が出れば成功です。

うまくいかないときに確認すること:

- ページが出ない → 起動したターミナルにエラーが出ていないか見てください。
- 表示が真っ白 → 起動直後は準備中のことがあります。10 秒ほど待って再読み込みしてください。

---

## 10. ログインと初回のパスワード変更

| | |
|---|---|
| 管理者の利用者名 | `cynovela` |
| 閲覧者の利用者名 | `demo` |

既定の利用者名は **管理者 `cynovela`** / **閲覧者 `demo`** です（`admin` ではありません）。
**管理者の初期パスワードは、はじめて `./launch.sh` を起動したときにターミナルの
画面へ1回だけ出ます。探す必要はありません。** 配布物にはどちらのデータベースも
入っていないため、`--demo` の起動でも普通の起動でも初回に出ます。
**閲覧者の値は、この配布物自身の `cynovela.yaml`（`viewer_initial_password:`）に
あります。** 画面を見逃した場合は、管理者の値も同じ `cynovela.yaml` で読めます
（`grep admin_initial_password cynovela.yaml`）。この文書には書いて
いません。文書のコピーだけでログインできてしまうのを避けるためです。

1. ユーザー名に **`cynovela`** を入力します。
2. パスワードは、初回起動のときにターミナルへ出た管理者の値を入力します
   （見逃した場合は `cynovela.yaml` から読み取ります）。
3. ログインすると「**初回パスワードの変更**」が出ます。
   「現在のパスワード」に受け取った値、「新しいパスワード（8文字以上）」に自分で決めた値を入れ、
   確認欄にも同じ値を入れて「**パスワードを変更して続行**」を押します。

**この変更を済ませるまで、設定などの管理操作は通りません**（変更操作だけが通ります）。
必ずここで変更してください。

管理者は初回ログインでパスワードの変更を求められます。変更したあとは新しい値で入ってください。
閲覧者はそのまま使えます。**受け取ったあと、最初に管理者のパスワードを変えてください。**

うまくいかないときに確認すること:

- 「ユーザー名またはパスワードが正しくありません」→ 値をコピー＆貼り付けで
  入れ直してください（前後の空白や改行が混ざりやすいところです）。
- 変更後に管理画面で「初回パスワードの変更が必要です」と出る → 一度ログアウトして、
  新しいパスワードでログインし直してください。
- admin パスワードを忘れた → `conda run -n cynovela-dist python server.py --reset-admin` で再発行できます。

### ロール

`--demo` ではデモ用ユーザーが自動投入されますが、認証は通常どおり強制されます（ユーザー名とパスワードの入力が要ります）。DB が保持するロールは **`admin` / `viewer` の 2 値**です。

| ロール | 権限 | 検索対象 |
|---|---|---|
| `admin` | 全機能 | raw 保管庫（出力マスクなし） |
| `viewer` | 閲覧中心 | masked 保管庫（出口マスクあり） |

> `curator` / `data-scientist` 等の名称は内部的に `viewer` へ正規化されます。

| ユーザー名（既定。`admin` ではありません） | ロール | パスワード |
|---|---|---|
| `cynovela` | admin | 最初の値は初回起動のときにターミナルへ1回だけ出ます。見逃した場合はこの配布物の `cynovela.yaml`（`admin_initial_password:`）に在ります。初回ログイン時に変更を強制 |
| `demo` | viewer | 最初の値はこの配布物の `cynovela.yaml`（`viewer_initial_password:`）に在ります |

### 何も入れずに始めた場合の、閲覧者の作り方

何も入れずに始めた場合、最初に居るのは管理者だけです。閲覧者はご自身で作ります。
管理者で入り、利用者の管理から新しい利用者を追加し、役割に閲覧者を選んでください。
お試しの資料で始めた場合は、閲覧者があらかじめ用意されています。

---

## 11. 回答を作る LLM をつなぐ

Cynovela は資料を探すところまでを担当し、**文章の生成は同じ Mac で動く LLM に任せます**。
同梱の既定は **LM Studio** です（`cynovela.yaml` の `llm.provider: lmstudio` /
`llm.base_url: http://localhost:1234`）。まずはこの既定のまま使ってください。

### 11-1. LM Studio 側の準備

1. LM Studio を起動する。
2. **チャット用（生成用）のモデル**をダウンロードしてロードする。
   例: `gemma-4-12b-it` のような会話用のモデル。
   **埋め込み専用のモデル（名前に `embed` や `bge` が入るもの）は回答を作れません。**
3. 左の「**Developer**」タブでローカルサーバーを **Start** する（既定ポート 1234）。

### 11-2. Cynovela 側の設定

左メニューの **Settings** → **LLM Provider** を開き、次のように設定します。

| 項目 | 入れる値 |
|---|---|
| Provider | `LM Studio` |
| Base URL | `http://localhost:1234` |
| Model | 「📋 モデル一覧を取得」を押し、**11-1 でロードしたチャット用モデル**を選ぶ |

「🔌 接続テスト」を押して成功を確認し、
「💾 LLM設定をまとめて適用」で保存します。

**Model を空欄のままにしないでください。**
空欄のときは LM Studio が返すモデル一覧の**先頭**が使われます。先頭が埋め込み専用モデルだと
生成要求が拒否され、回答が返らずエラー（HTTP 400）になります。
必ず一覧からチャット用モデルを選んでください。

うまくいかないときに確認すること:

- 接続テストが失敗する → LM Studio の Developer タブでサーバーが Start 状態か確認してください。
- 「モデル一覧を取得」で何も出ない → LM Studio にモデルがロードされていません。
  LM Studio 側でモデルを読み込んでから、もう一度押してください。

・LM Studio は、読み込んでいないモデルの名前を指定しても断らず、
  読み込み済みの別のモデルで答えることがあります。Model 欄には、
  一覧から選んだ実在のモデル名を入れてください。
・LM Studio で大きなモデルを同時にいくつも動かすと、回答が崩れたり
  遅くなったりすることがあります。時間が経つと自動で元に戻ります。
・品質が安定しない → LM Studio 側のモデルと設定を確認してください。

LLMプロバイダーの詳しい設定 — Ollama を使う場合を含む — は [operations.md](operations.md) にあります。

---

## 12. 最初の質問をする

1. 左メニューの **RAG Chat** を開きます。
2. 上部の「🏢 Workspace」で対象のワークスペースを選びます。
3. 下の入力欄に質問を書き、右の **▶** を押します（Shift+Enter でも送信できます）。
4. 回答本文と、その下に**参照した資料の一覧**が出れば成功です。

`ready` 状態のコレクションに対して、たとえば次のように質問します。

```
このドキュメントで扱われている主なトピックは何ですか？
```

回答には出典として `[1][2]` の引用番号付きでチャンクが表示されます。`admin` は raw 本文、`viewer` はマスク済み本文を検索し、`viewer` では LLM 出力にも出口マスクが適用されます。

うまくいかないときに確認すること:

- **「該当なし」しか返らない** → そのワークスペースに公開済みの資料がありません。
  13節と14節で資料を取り込んで公開してください。
- **エラーになる／回答が空** → 11-2 の Model がチャット用モデルになっているか確認してください
  （ここが原因のことが最も多いところです）。
- **とても遅い** → 大きなモデルは 1 回の回答に数十秒かかります。まずは小さめのモデルで試してください。

---

## 13. 検索の対象フォルダ（取り込み元）を足す

このアプリが読めるのは、**取り込み元として足したフォルダだけ**です。
足していない場所は、たとえ管理者でも開けません。

何も足していないときは、**この配布物の中のダミー資料（`dummy-corpus`）が最初から取り込み元になっています。**
そのまま試すだけなら、この節は飛ばして構いません。

### 画面から足す（おすすめ）

1. 左の **Settings** を開く
2. **「📁 取り込み元」** を開く
3. **「取り込み元を足す」** を押す
4. フォルダを辿って、検索の対象にしたいフォルダまで進む
5. **「このフォルダを足す」** を押す

足したものはすぐ使えます。起動し直しても残ります。**起動し直しは要りません。**
外すときは、同じ画面の **「外す」** を押します。フォルダと中の資料には触りません。

### ダブルクリックで足す

配布物の中の **`Cynovela-add-folder.command`** をダブルクリックします。
フォルダを選ぶ画面が出て、選ぶとバックアップに書かれ、いま動いている画面からすぐに選べます。

※ はじめて使うときは、先に `Cynovela-start.command` を一度押してください。バックアップを扱う
Python（3.12 系）はその最初の一度で用意されます。無いまま足そうとすると、入れ方の手順が
出て止まります（Mac に元から入っている古い python3 へは倒れません）。

### ターミナルから足す

```bash
# フォルダを選ぶ画面から追加する（macOS）
./launch.sh --add

# パスを直接指定して追加する
./launch.sh --add-path ~/Documents/契約

# 今どれが登録されているか見る／消す
./launch.sh --list
./launch.sh --remove<一覧に出た名前>
```

自分の資料は**本番**（引数なし）で使います。ここでは `--demo` は付けません。

### 取り込み元を複数渡す

取り込み元（ドキュメントのルートフォルダ）は起動時に何件でも渡せます（`server.py` の `--ingest` は append 指定。2026-08-02 実測）。

```bash
# 起動時に複数指定（それぞれがフォルダ参照画面の一覧に並ぶ）
./launch.sh --demo --ingest ~/Documents/契約 --ingest /path/to/資料

# 起動せずに追加だけ行う（動いている画面からすぐに選べます）
# ※ 追加・一覧・外すは 3.12 系の python を使います（はじめてなら先に一度
#    Cynovela-start.command を押すと用意されます）
./launch.sh --add-path /path/to/新しい取り込み元

# フォルダ選択画面から追加（macOS。Cynovela-add-folder.command のダブルクリックでも同じ）
./launch.sh --add

# 一覧・削除（足す・見る・外すは画面の Settings → 📁 取り込み元 からもできます）
./launch.sh --list
./launch.sh --remove<中の名前>
```

本番でも、起動時にまとめて渡すことができます。

```bash
./launch.sh --ingest ~/Documents/契約 --ingest ~/資料
```

- この形態では、**画面から足す・外すがそのまま効きます。起動し直しは要りません**（バックアップは参照のたびに読み直されます）。
- 登録済みのルートはバックアップファイル `store/ingest-roots.json` に保持されます。
- ルートを1件も渡さない場合は、この配布物の中のダミー資料（`dummy-corpus`）を取り込み元にして起動します。画面のフォルダ参照でルートが1件も無いときは「取り込み元がまだ1件もありません」と出て、その場の「取り込み元を足す」から足せます。
- ルートの外のパスは 403 で拒否されます（画面の「取り込み元を足す」で足してから使ってください）。

---

## 14. 資料を取り込んで公開する

1. 左メニュー **Data Sources** →右上の「**＋ソース追加**」。
2. 「名前」に分かりやすい名前を入れ、「📁 参照」で 13節で登録したフォルダ（またはその中の
   サブフォルダ）を選び、「次へ」。ローカルパス（例: `/Users/username/Documents/`）を直接入力します。
3. 追加先のワークスペースを選ぶ（無ければ「新しいワークスペースを作成」）→「追加」。
4. スキャンが終わるのを待ちます。
5. 左メニュー **Collections** → 「**＋ Collection作成**」でワークスペースとソースを結び付けます。
   名前と RAG 戦略を指定します。
6. 作った Collection の「**Publish**」を押します。PDF の読み取り方は
   fast（速い）/ quality（高品質）/ vision（画像として読む・OCR）から選べます。完了まで待ちます（大容量PDFは時間がかかります）。
7. 「**✅ Publish 完了**」の受領書が出たら、12節に戻って質問できます。

`--demo` 起動では、**同梱のダミー資料が入ったワークスペースが 3 件**（全社・営業・人事）入っています。閲覧者アカウントが所属するのは「全社」だけです。自分用のワークスペースは「新しいワークスペースを作成」から作ります。

Publish では テキスト抽出 → チャンク分割 → PII 検出/マスキング → Embedding 生成（ChromaDB 保存）→ BM25 インデックス構築 が行われます。進捗は SSE で返り、完了時に `publish_history` へ件数・所要時間が記録され、コレクションは `ready` 状態になります。

取り込みの間は、進み具合が画面に出ます。段は次の順に進みます。

```
読み込み中 → チャンク書き込み中 → マスキング処理中 → マスキング処理中(まとめ) → Embedding生成中 → 完了
```

**画面を閉じても取り込みは続きます。** 開き直すと、いまの段と何件目かに戻ります。
大きな資料ではマスキングの段に時間がかかりますが、件数が動き続けていれば進んでいます。

うまくいかないときに確認すること:

- **「取り込み元がまだ1件もありません」と出る** → 13節の登録をまだ行っていません。
  画面の「取り込み元を足す」から足してください。すぐに使えます。
- **参照画面でフォルダを選べない／403 になる** → 13節で登録した範囲の外を指しています。
  登録した範囲の中のフォルダを選んでください。
- **Publish が終わらない** → 大きな PDF が多いと時間がかかります。まず fast で試してください。

---

## 15. 後からフォルダやファイルを置いたとき

登録済みの取り込み元の下に、後からフォルダやファイルを置いただけでは、即座には一覧に
出ません。次のどれかで反映されます。

1. 本体を起動し直す（起動のたびに登録済みの取り込み元を1回走査します。変わっていない
   ファイルは読み直さないので速いです）
2. 画面の「資料」一覧の上にある **「🔄 すべて読み込み直す」** ボタン、または各行の
   **「🔄 再スキャン」**（管理者のみ）
3. ターミナル: `python3 cynovela-cli.py ingest --path <フォルダ>`（新規）/
   `python3 cynovela-cli.py scan start --source <ID>`（登録済み）
4. MCP: `ingest_source` / `get_job_status`

走査は「開始」で即戻ります。進み具合は画面のトースト、または CLI の
`scan status --job <job_id>` で見ます（中止は `scan cancel --source <ID>`）。
検索に出るには、この後は 14節と同じく、Collection へ結び付けて公開（Publish）
まで行います。

---

## 16. 日常の起動手順

起動は 2 通りあります。**引数なしは本番**（空のデータベースから始まり、自分の資料を取り込んで使う）、**`--demo` を付けるとデモ**（同梱のダミー資料を使うデモDB。初回起動時に自動で取り込まれます）です。

```bash
# 入口は launch.sh です（または Cynovela-start.command をダブルクリック）
./launch.sh            # 本番: 空のデータベース
./launch.sh --demo     # 最初に試すならデモ（ダミー資料入り）で

# ブラウザで開く
# http://localhost:8765
```

### 起動の仕方は 2 通り、起動の中身も 2 通りあります

**押して起動する（いちばん簡単）**

展開したフォルダの中の **`Cynovela-start.command`** をダブルクリックします。
止めるときは **`Cynovela-stop.command`** をダブルクリックします。
読み込むフォルダを足すときは **`Cynovela-add-folder.command`** をダブルクリックします
（はじめて使うときは、先に `Cynovela-start.command` を一度押してください。フォルダの
バックアップを扱う Python はその最初の一度で用意されます）。

**この操作手順は、中身が空のデータベース（本番）で立ち上がります。** 同梱のダミー資料で試すときは、**`Cynovela-demo.command`** をダブルクリックします（またはターミナルから `./launch.sh --demo`）。
開いてすぐ、同梱の資料に質問できます。管理者・閲覧者とも、10節のパスワードでそのまま入れます。

自分の資料だけで使いたいときは、ターミナルから**引数なし**で叩きます。こちらは**中身が空のデータベース**
（本番）から始まります。空の本番に閲覧者は居ません（管理者で入って資料を取り込んでから使います）。

| 起動の中身 | どうなるか | 出し方 |
|---|---|---|
| デモ | 同梱のダミー資料を使って立ち上がる（**初回起動時に自動で取り込まれ**、終わると質問できる） | `Cynovela-demo.command` をダブルクリック、またはターミナルから `./launch.sh --demo` |
| 本番 | 中身が空のデータベースで立ち上がる。取り込み元が 0 件のときは、この配布物の中のダミー資料が取り込み元になる | `Cynovela-start.command` をダブルクリック、または `./launch.sh`（引数なし） |

**ターミナルから起動する**

展開したフォルダの中で、次の1行を実行します。**ターミナルから使うときの入口はこの1本だけです。**

```bash
./launch.sh --demo
```

これはデモで立ち上がります。初回起動時に同梱のダミー資料が自動で取り込まれます
（進捗は起動ログに出ます）。
自分の資料で使うときは、何も付けずに `./launch.sh` を実行します。

動かすのに足りないものがあると、**起動する前に**「足りないものがあるので起動しません」と出ます。
そのときは次を実行してください。

```bash
./launch.sh --setup
```

できることの一覧は、いつでもこれで出せます。

```bash
./launch.sh --help
```

### はじめて起動する前の注意

- ダウンロードした配布物には macOS が拡張属性（`com.apple.quarantine`）を付け、部品ごとに
  何度も確認が出ることがあります。`./launch.sh` は起動の最初に、配布物の中の拡張属性を全部
  自分で取り除きます。手動で行うなら `xattr -rc <フォルダ>` です。
- クラウド同期（iCloud Drive・Dropbox・OneDrive・Google Drive）の下に配布物を置かないで
  ください。`./launch.sh` が起動前に検知して注意を出します（止めずに進みます）。
- 同梱の環境（`.condapack-cynovela`）が既に在って動くときは、`./launch.sh` は土台の選択画面を
  出さずにそのまま起動します（壊れているときだけ選択画面が出ます）。

`launch.sh` を通さず手でサーバーを起動する場合（環境が既に在ることが前提です。専用の名前は `cynovela-dist`。共有の環境は作らない・書き換えないでください）:

```bash
# 1. この配布物専用の環境を有効化
conda activate cynovela-dist

# 2. SSL証明書エラー対策（macOS。launch.sh はこれを内包しています）
unset SSL_CERT_FILE

# 3. サーバー起動
python server.py --mode text          # 本番
python server.py --mode text --demo   # デモ
```

### よく使う操作

```bash
# 起動（2 回目以降）。引数なしは本番。デモで使っていた場合は --demo を付ける
./launch.sh

# 停止
bash stop.sh

# ログを流しながら起動したいとき（デモで使う場合は --demo も付ける）
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

- バックアップと復元・ポート変更・ログ確認は [operations.md](operations.md) を見てください。
- パスワードやトークンをメモ帳や共有フォルダに置かないでください。
  API を直接叩く場合のトークンは、ログイン（`POST /api/auth/login`）で毎回発行されるものを使います。
  固定のパスワードのようなトークンは受け付けません。

---

## 17. 起動オプション

| オプション | 説明 |
|---|---|
| `--mode text` | テキストモード（標準） |
| `--demo` | 同梱のダミー資料を使うデモDBで起動（初回起動時に自動で取り込まれる。付けなければ本番＝空のデータベース） |
| `--reset-admin` | 管理者パスワードをリセットし、新しい値を表示して終了する。**対象のデータベースは他の指定と同じ規則で選ばれるため、デモの管理者を直すときは `--demo` を併記する**（付けないと本番の `store/db/cynovela.db` が対象になり、無ければ新規作成される。デモ側は変わらないのでデモのログインは 401 のまま。2026-08-02 実測） |
| `--local-only` | 自分のマシンの中だけに絞る（既定は全アドレス `0.0.0.0` で待ち受け） |
| `--port N` | ポート番号（既定 8765） |

### 起動の形（--mode）の一覧（実測・2026-08-12）

| 形 | 必要モデル | サイズ目安 | 何が変わるか |
|---|---|---|---|
| `--mode text` | BAAI/bge-m3 | 約 2.3GB | 既定。テキストRAGの全機能で動きます |
| `--mode lite` | 切替は**未配線**＝実際は BAAI/bge-m3 | — | 切替は未配線のため、表示名が変わるだけです（動作は text と同じ） |
| `--mode lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3 | — | 切替は未配線のため、表示名が変わるだけです（動作は text と同じ） |

いずれも `./launch.sh --demo --mode<名前> --port<番号>` の形で指定できます（実測済み）。

初回起動でモデルが未取得の場合、Preflight チェックの対話プロンプト（ダウンロード / 別モードへ切替 / キャンセル）が表示されます。非対話環境では `CYNOVELA_NONINTERACTIVE=1` を設定すると、未キャッシュ時に終了コード 2 で停止します。

```bash
# 例: 表示名を変えて起動する（動作と必要モデルは text と同じ・切替は未配線）
./launch.sh --demo --mode lite
```

---

## 18. ターミナルで行う道（まとめ）

`./launch.sh --help` に出るものと同じです。

| 打つもの | 何が起きるか |
|---|---|
| `./launch.sh` | 本番（空のデータベース）で起動。取り込み元が0件なら同梱のダミー資料を使う |
| `./launch.sh --demo` | 同梱のダミー資料を使うデモで起動（初回起動時に自動で取り込まれる） |
| `./launch.sh --setup` | 動かすのに要るものを入れる（入れたら止まる） |
| `./launch.sh --check` | 起動せず、動く条件だけを調べて1本のファイルへ書く |
| `./launch.sh --add` | フォルダを選ぶ画面を出して取り込み元を足す |
| `./launch.sh --add-path<パス>` | 場所を指定して取り込み元を足す |
| `./launch.sh --list` | 足してある取り込み元を一覧で出す |
| `./launch.sh --remove<名前>` | 取り込み元を外す（名前は `--list` に出るもの） |
| `./launch.sh --ingest<パス>` | 足して、そのまま起動する |
| `./launch.sh --base conda` | 専用の conda 環境を新しく作る |
| `./launch.sh --base venv` | この配布物の中だけに作る |
| `./launch.sh --base none` | 何も作らない |
| `./launch.sh --env-name<名前>` | conda 環境の名前を変える（既定 `cynovela-dist`） |
| `./launch.sh --verbose` | 入れている間の素の出力をそのまま出す |
| `./launch.sh --port<番号>` | 開く番号を変える（既定 8765） |
| `./launch.sh --local-only` | 待ち受けを自分のマシンの中だけに絞ります |
| `bash stop.sh` | 止める |

知らない指定を打ったときは、黙って落ちずにこの一覧（ヘルプ）が出ます。

---

## 19. 止め方と、起こし直し方

#### 止める

ターミナルを開き、取り出したフォルダへ移って、1行打ちます。

```
cd ~/Downloads/chewie
bash stop.sh
```

次のどちらかが出ます。

```
Cynovela を停止します (PID: 12345)...
停止完了
```

```
PIDファイル(/Users/…/store/server.pid)がありません。停止対象なし。
```

2つめは「そもそも動いていなかった」という意味です。異常ではありません。

クリックで済ませたい方は、フォルダの中の **`Cynovela-stop.command`** を
ダブルクリックしてください。

#### もう一度起こす

```
cd ~/Downloads/chewie
./launch.sh --demo
```

同梱のお試し資料ではなく自分のフォルダを使っているなら `--demo` は付けません。
**毎回同じ形で起こしてください。** 理由は20節にあります。

**`Cynovela-start.command`** のダブルクリックでも同じです。

起こし直しは **20〜60秒** です。いちばん最初の3〜8分はかかりません。

**上がったまま、もう一度 `./launch.sh` を実行しても構いません。**
先に上がっているものを止めてから上げ直します。止められなかったときは、
何が上がっているかと手で止める方法を画面に出して、そこで止まります。

#### もう動いているものが在るとき

`./launch.sh` は先に調べます。動いているものが在れば、次を出します。

```
先に、いま動いているものを調べました。
  server.py（PID 12345）  : 動いています（待ち受け 8765）
このまま新しく起こすと、同じものが二重に立ち上がります。
どうしますか。
  1) 動いているものを止めて、新しく起こす
  2) 止まっているものを、そのまま起こし直す
  3) 動いているものへ、そのままつなぐ
  4) 動いているものを止めて、終わる
  5) 何もせずに終わる
番号を入れてください [1/2/3/4/5]:
```

* いま動いているものの開き先を知りたいだけなら **3** です。
* 設定を変えたので入れ直したいなら **1** です。
* 止めて終わりたいなら **4** です。

どれを選んでも、何も消えません。

#### Mac を再起動したあと

この道具は自分では起き上がりません。上の「もう一度起こす」を行ってください。

---

## 20. 止めて起こし直すとき何が起きているのか

#### なぜ `--demo` を毎回そろえる必要があるのか

`--demo` は「自分のデータの上にお試し資料を重ねる」という意味ではありません。
**別のデータベースと別の索引**を選ぶ指定です。

| 起こし方 | 使うデータベース | 使う索引 |
|---|---|---|
| `./launch.sh` | `store/db/cynovela.db` | `store/vector/default/chroma` |
| `./launch.sh --demo` | `store/db/demo.db` | `store/vector/demo/chroma` |

∴ `--demo` を付けて動かしているときに足したフォルダは、付けずに起こすと在りません。
逆も同じです。消えたのではなく、もう一方を見ています。前と同じ形で起こし直せば
戻ってきます。

2つは決して混ざりません。それがこの作りの狙いです。お試しの資料が、あなたの
本当の答えの中に紛れ込むことはありません。

#### なぜ `stop.sh` は安全なのか

`store/server.pid` から番号を読み、その番号のプロセスが本当に `server.py` かを
確かめてから止めます。待ち受けの番号から探すことも `pkill` を使うこともしません。
∴ たまたま 8765 を使っている別のプログラムを巻き込むことはありません。

「PIDファイルがありません」と出たときは、既に止まっていて、後片づけも済んでいた
ということです。

#### なぜターミナルの窓を閉じても止まらないのか

`./launch.sh` は、終わる前に本体を窓から切り離します。わざとそうしています。
ブラウザを使っているあいだ動き続けてほしいものであり、窓は閉じられるものだからです。
戻る道が `bash stop.sh` です。

#### 止めても残るもの

全部です。読み込んだ資料・索引・利用者・設定・監査の記録。どれもフォルダの中の
`store/` に在ります。止めるのはプロセスを終わらせるだけです。

消えるのは、止めた時点でまだ走っていたものだけです。走査や公開の途中がそれに
当たります。画面から、または `cynovela-cli scan start` / `cynovela-cli publish start`
で始め直してください。

#### 環境そのものが壊れたとき

足りないものが在るというエラーが出て起動しないときは、次を1回叩きます。

```
./launch.sh --setup
```

Python の環境を作り直すだけで、起動はしません。そのあと普通に起こしてください。
読み込んだ資料と設定には触りません。

---

## 21. 動作確認（テスト）

> **配布物には `tests/` は入っていません**（配布物を作るときに外されます）。受け取った配布物では `pytest` / `make test` は実行できません。
> 動作を確かめるには `conda run -n cynovela-dist python scripts/test_comprehensive_e2e.py` を使ってください。

```bash
# 開発ツリー（tests/ が在る側）での実行

# 手動 pytest（軽量・最初の失敗で停止）
cd<開発ツリーのフォルダ>
unset SSL_CERT_FILE
conda run -n cynovela-dist python -m pytest -x -q
```

`Makefile` の `make test` / `make test-quick` / `make verify-live` も利用できます。`live` 系はサーバが `http://127.0.0.1:8765` で稼働していることが前提です。

---

## 22. うまくいかないとき

| 画面に出ること | どうするか |
|---|---|
| 「取り込み元がまだ1件もありません」 | 画面の **「取り込み元を足す」** を押す（13節）。このメッセージの下にその道へ行くボタンが出ます |
| 「初回パスワードの変更が必要です」 | 0節と10節。先にパスワードを変える |
| 「ポート 8765 を別のものが使っています」 | 別の番号で上げる: `./launch.sh --port<別の番号>` |
| 「足りないものがあるので起動しません」 | `./launch.sh --setup` を実行する |
| 進み具合が止まって見える | 件数が動いていれば進んでいます。マスキングの段は時間がかかります |

- **モデルダウンロードや HTTPS が SSL で失敗** → `unset SSL_CERT_FILE` してから起動・テストしてください（ランチャー使用時は不要）。
- **LAN の他の端末から開けない** → 既定で `0.0.0.0` 待ち受けなので、まずポートと接続先 IP を確認してください（`--local-only` を付けていると自マシン内に絞られます）。
- **品質が安定しない** → LM Studio 側のモデルと設定を確認してください。
- **admin パスワードを忘れた** → `conda run -n cynovela-dist python server.py --reset-admin` で再発行できます。
- **ポート 8765 が使用中** → `lsof -i :8765` で確認します。`./stop.sh` は起動時に記録した PID（Cynovela サーバー自身）のみを停止するため、8765 を他用途で使っている場合でもそのプロセスには影響しません。記録 PID が無く手動で止める場合は、対象が Cynovela であることを確認したうえで `pkill -f "python server.py"` などを使ってください。

上の各節にも、それぞれ「うまくいかないときに確認すること」があります。
その他は [faq.md](faq.md) を参照してください。

---

## 23. 次に読むもの

- [operations.md](operations.md) — LLMプロバイダーの詳しい設定（Ollama を含む）・バックアップと復元・ポート変更・ログ確認
- [architecture.md](architecture.md) — システム構成を理解する
- [handson.md](handson.md) — 基本操作を試す
- [architecture.md](architecture.md) §4「検索のしくみ」 — RAG パイプラインを理解する
- [faq.md](faq.md) — よくある質問

より詳しい話は同梱の `README.md` にあります。
