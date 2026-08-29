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

This document is for the people who install Cynovela and keep it running. It collects, in one place, starting and stopping, how to put it on a machine, connecting an LLM provider, using it from external tools over MCP, sharing it over a LAN, backup and restore, logs, the audit log, user management, health checks, notifications, and the port.

Sections:

1. Normal startup and shutdown
2. Installing and placing
3. Connecting an LLM provider
4. Using Cynovela from external tools with MCP
5. Sharing over a LAN
6. backup and restore
7. Logs
8. Exporting the audit log
9. User management
10. Health checks and monitoring
11. Notifications (email)
12. Changing the port
13. Operational notes

---

**Contents**

- [1. Normal Startup and Shutdown](#1-normal-startup-and-shutdown)
  - [1-1. Startup](#1-1-startup)
  - [1-2. Shutdown](#1-2-shutdown)
  - [1-3. Background Startup](#1-3-background-startup)
- [2. Installing and Placing](#2-installing-and-placing)
  - [2-1. Verified Environments](#2-1-verified-environments)
  - [2-2. Setting Up the Environment](#2-2-setting-up-the-environment)
  - [2-3. List of Startup Flags](#2-3-list-of-startup-flags)
  - [2-4. `--mode` Selection Guide](#2-4---mode-selection-guide)
  - [2-5. First-Time Model Download Procedure](#2-5-first-time-model-download-procedure)
  - [2-6. Main Environment Variables](#2-6-main-environment-variables)
  - [2-7. Overall Startup Flow Diagram](#2-7-overall-startup-flow-diagram)
  - [2-8. Setting Up an External Inference Server](#2-8-setting-up-an-external-inference-server)
- [3. Connecting an LLM Provider](#3-connecting-an-llm-provider)
  - [3-1. Connection Architecture](#3-1-connection-architecture)
  - [3-2. Setting the Provider from the Screen](#3-2-setting-the-provider-from-the-screen)
  - [3-3. Connecting to LM Studio](#3-3-connecting-to-lm-studio)
  - [3-4. Connecting to Ollama](#3-4-connecting-to-ollama)
  - [3-5. Connecting to an LLM on a Remote Machine](#3-5-connecting-to-an-llm-on-a-remote-machine)
  - [3-6. List of Supported Providers](#3-6-list-of-supported-providers)
  - [3-7. Related Environment Variables](#3-7-related-environment-variables)
  - [3-8. Reranker Providers](#3-8-reranker-providers)
- [4. Using Cynovela from External Tools with MCP](#4-using-cynovela-from-external-tools-with-mcp)
  - [4-1. What MCP is](#4-1-what-mcp-is)
  - [4-2. MCP tools Cynovela exposes (25 in total)](#4-2-mcp-tools-cynovela-exposes-25-in-total)
  - [4-3. Connecting from LM Studio](#4-3-connecting-from-lm-studio)
  - [4-4. Which Python Runs the MCP Server](#4-4-which-python-runs-the-mcp-server)
  - [4-5. Notes on Authentication](#4-5-notes-on-authentication)
  - [4-6. Troubleshooting](#4-6-troubleshooting)
- [5. Sharing over a LAN](#5-sharing-over-a-lan)
  - [5-1. Default behaviour](#5-1-default-behaviour)
  - [5-2. LAN sharing mode](#5-2-lan-sharing-mode)
  - [5-3. Tailscale sharing mode](#5-3-tailscale-sharing-mode)
  - [5-4. Security notes](#5-4-security-notes)
  - [5-5. Summary of related startup flags](#5-5-summary-of-related-startup-flags)
- [6. backup and restore](#6-backup-and-restore)
  - [6-1. Default Storage Locations](#6-1-default-storage-locations)
  - [6-2. What `store/` Holds](#6-2-what-store-holds)
  - [6-3. Manual Backup](#6-3-manual-backup)
  - [6-4. Restore](#6-4-restore)
  - [6-5. Points to Note](#6-5-points-to-note)
  - [6-6. Backups Taken in the App (`backup create`) — Where They Go](#6-6-backups-taken-in-the-app-backup-create--where-they-go)
  - [6-7. Whole-store Backup (recommended)](#6-7-whole-store-backup-recommended)
  - [6-8. Restore from a Whole-store Copy (do it with Cynovela stopped)](#6-8-restore-from-a-whole-store-copy-do-it-with-cynovela-stopped)
  - [6-9. Restore from a Backup Taken in the App (do it with Cynovela stopped)](#6-9-restore-from-a-backup-taken-in-the-app-do-it-with-cynovela-stopped)
  - [6-10. Moving to Another Mac](#6-10-moving-to-another-mac)
- [7. Logs](#7-logs)
  - [7-1. Log Level](#7-1-log-level)
  - [7-2. Request ID](#7-2-request-id)
  - [7-3. Preflight Log](#7-3-preflight-log)
  - [7-4. Watching the Server Log](#7-4-watching-the-server-log)
- [8. Exporting the Audit Log](#8-exporting-the-audit-log)
  - [8-1. What the Audit Log Is](#8-1-what-the-audit-log-is)
  - [8-2. Tamper Prevention](#8-2-tamper-prevention)
  - [8-3. Viewing from the GUI](#8-3-viewing-from-the-gui)
  - [8-4. Via the API](#8-4-via-the-api)
  - [8-5. Extracting Directly from SQLite](#8-5-extracting-directly-from-sqlite)
- [9. User Management](#9-user-management)
  - [9-1. Roles](#9-1-roles)
  - [9-2. The Initial Administrator](#9-2-the-initial-administrator)
  - [9-3. Login Information of the Shipped demo.db](#9-3-login-information-of-the-shipped-demodb)
  - [9-4. Adding and Deleting Users, and Changing Passwords](#9-4-adding-and-deleting-users-and-changing-passwords)
  - [9-5. Vault Access and Masking by Role](#9-5-vault-access-and-masking-by-role)
  - [9-6. Authentication](#9-6-authentication)
- [10. Health Checks and Monitoring](#10-health-checks-and-monitoring)
  - [10-1. Main Health Endpoints](#10-1-main-health-endpoints)
  - [10-2. Publish History](#10-2-publish-history)
  - [10-3. Circuit Breaker](#10-3-circuit-breaker)
- [11. Notifications (Email)](#11-notifications-email)
- [12. Changing the Port](#12-changing-the-port)
  - [12-1. Ports and Access Control](#12-1-ports-and-access-control)
  - [12-2. Changing the Port Number](#12-2-changing-the-port-number)
- [13. Operational Notes](#13-operational-notes)

## 1. Normal Startup and Shutdown

### 1-1. Startup

```bash
# The entry point is launch.sh
./launch.sh --demo
```

To start by hand instead (the dedicated environment name is `cynovela-dist`; never create or modify a shared environment):

```bash
conda activate cynovela-dist
python server.py --demo
```

For details of the options, see 2-3 "List of Startup Flags".

### 1-2. Shutdown

Send `Ctrl + C` once in the terminal. The FastAPI / Uvicorn shutdown hook runs, and a stop request is propagated to any Publish job in progress (the SSE path).

### 1-3. Background Startup

You can also keep it resident with `nohup`, or with a terminal multiplexer such as `tmux` / `screen`.

```bash
nohup python server.py --demo > ~/cynovela.out 2>&1 &
```

---

## 2. Installing and Placing

### 2-1. Verified Environments

Cynovela is a tool for personal verification, and the environments in which it has been verified are limited. Use the following as a reference.

| Item | Verified content |
|------|------------|
| OS | macOS (Apple Silicon) |
| Python runtime | conda (Miniforge) |
| Local LLM | LM Studio (OpenAI-compatible `/v1` API) |
| Embedding | BAAI/bge-m3, paraphrase-multilingual-MiniLM-L12-v2, paraphrase-MiniLM-L3-v2, TF-IDF |

Windows / Linux / Docker environments have not been verified. The details of using a GPU (the CUDA version and a memory guideline) have not been verified either.

### 2-2. Setting Up the Environment

**The recommended way is `./launch.sh`** — on the first run it builds the environment in a dedicated place, and the shared conda environment is never created and never modified.

#### 2-2-1. Creating the environment by hand (only if you cannot use launch.sh)

Use the dedicated name `cynovela-dist`. Do not create or modify a shared environment.

```bash
conda create -n cynovela-dist python=3.12 -y
conda activate cynovela-dist
```

#### 2-2-2. Installing the dependencies

```bash
pip install -r requirements.txt
```

Main dependencies:

| Library | Purpose |
|----------|------|
| FastAPI | the API server itself |
| Uvicorn | ASGI server |
| SQLite (bundled with the standard library) | metadata, audit logs, chunk storage |
| ChromaDB | vector search |
| cryptography (Fernet) | encryption of the raw body text |
| huggingface_hub | model download |
| BM25Okapi | keyword search |
| fugashi / MeCab | Japanese morphological analysis (BM25 tokenization) |

### 2-3. List of Startup Flags

These are all the flags you can pass to `python server.py`.

| Flag | Type | Default | Description |
|--------|-----|------|------|
| `--demo` | bool | False | Starts using the demo database `store/db/demo.db` and index `store/vector/demo/chroma`. Without it, the production `store/db/cynovela.db` and `store/vector/default/chroma` are used. Neither is erased on restart |
| `--lmstudio-url` | str | `http://localhost:1234` | Base URL of LM Studio |
| `--mode` | str | `text` | Startup mode (`full` / `text` / `lite` / `lite-en` / `minimal`) |
| `--host` | str | `0.0.0.0` | Bind address (the default is all addresses; use `--local-only` to narrow it) |
| `--lan` | bool | False | LAN exposure (explicitly sets host=0.0.0.0) |
| `--port` | int | `8765` | Port number |
| `--local-only` | bool | False | Restricts to the local machine only (listens on `host=127.0.0.1`) |
| `--allow-tailscale` | bool | False | Allows access from the Tailscale network |
| `--reset-admin` | bool | False | Resets the administrator password, displays it, and exits (add `--demo` when fixing the demo) |
| `--ingest PATH` | str (can be given multiple times) | none | Folders allowed as ingest sources |
| `--allow-subnet` | list | `[]` | Allowed subnets (can be given multiple times) |

#### 2-3-1. Frequently used combinations

```bash
# 通常起動（LM Studio 必要）
python server.py --demo

# LAN 共有 + Tailscale
python server.py --demo --lan --allow-tailscale

# 表示名を変えて起動する例（動作は text と同じ・切替は未配線）
python server.py --demo --mode lite
```

> **PII detection mode**: `--pii-mode` has been removed as a CLI argument. Specify it with the `pii_mode` key (`lite` / `standard` / `quality`) in `cynovela.yaml`.

### 2-4. `--mode` Selection Guide

The startup mode changes the Embedding and Reranker configuration.

#### 2-4-1. Model size comparison table

| `--mode` | Embedding model | approx. size | Reranker | recommended environment |
|--------|---------------|---------|---------|---------|
| `text` (default) | BAAI/bge-m3 | about 2.3GB | selectable in the settings (`reranker.provider`) | no GPU required, general purpose |
| `lite` | the switch is **not wired**, so it is actually BAAI/bge-m3 (behavior is the same as text; only the display name changes) | — | — | — |
| `lite-en` | the switch is **not wired**, so it is actually BAAI/bge-m3 (behavior is the same as text; only the display name changes) | — | — | — |

#### 2-4-2. How to choose

- General Japanese RAG: `text`

#### 2-4-3. Provider wiring precedence

2. The `reranker.provider` setting in `cynovela.yaml` (`cross_encoder` / `flashrank` / `mlx` / `http` / `none`, etc.)
3. The legacy `rag.reranker_enabled` + `reranker_url` are absorbed as the `http` path

### 2-5. First-Time Model Download Procedure

#### 2-5-1. Preflight check

Unless the mode is `--mode minimal`, the presence of the required models is checked at startup.

Skip conditions:

- `--mode minimal`
- The list of required models for that mode is empty

#### 2-5-2. Prompt when models are missing

If models are missing, an interactive prompt is displayed.

```
[1] 今すぐダウンロードして起動する
[2] 代替モードで起動する（例: text / lite / minimal）
[3+] キャンセル
```

| Choice | Behavior |
|------|------|
| `[1]` | Downloads from the HuggingFace Hub into `~/.cynovela/models/` |
| `[2]` | Offers an alternative mode (in the order `full → text → lite → lite-en → minimal`) |
| `[3+]` | Cancels startup |

#### 2-5-3. Aborting startup in a non-interactive environment

When you do not want an interactive prompt, for example in CI, set the environment variable `CYNOVELA_NONINTERACTIVE=1`. It exits immediately when a model is absent.

```bash
CYNOVELA_NONINTERACTIVE=1 python server.py --mode text
```

#### 2-5-4. Storage location

- Download destination: `~/.cynovela/models/`
- Naming rule: the slash in the HuggingFace repository name is replaced with `__` (e.g. `BAAI__bge-m3`)

#### 2-5-5. Overriding the model path

Placing the models under a cloud-synced folder such as OneDrive is not recommended (when the sync moves the actual files out, loading fails). Pointing to a different, non-synced location with the `models` section of `cynovela.yaml` is still possible.

```yaml
models:
  embedding:
    path: "/path/to/bge-m3"
    name: "BAAI/bge-m3"
  reranker:
    path: ""
    name: "BAAI/bge-reranker-v2-m3"
```

### 2-6. Main Environment Variables

We recommend passing secrets through environment variables rather than writing them directly in `cynovela.yaml`.

#### 2-6-1. Data and paths

| Environment variable | Purpose |
|---------|------|
| `CYNOVELA_DB` | SQLite DB path (the default is `~/.cynovela/db/...`) |
| `CYNOVELA_CHROMA` | ChromaDB directory |
| `CYNOVELA_BACKUP_DIR` | Backup directory |
| `CYNOVELA_LOG_DIR` | Log directory |
| `CYNOVELA_DATA_DIR` | Application data root |

#### 2-6-2. LLM / Embedding / Reranker

| Environment variable | Purpose |
|---------|------|
| `CYNOVELA_LLM_BASE_URL` | LLM base URL |
| _(no environment variable)_ | The LLM API key is entered in the settings UI (kept for this session only, never saved) |
| `CYNOVELA_LLM_MODEL` | LLM model name |
| `CYNOVELA_LLM_PROVIDER` | LLM provider |
| `CYNOVELA_LLM_MAX_CONCURRENT` | Upper limit of concurrent LLM calls |
| `CYNOVELA_EMBEDDING_PROVIDER` | Embedding provider |
| `CYNOVELA_EMBEDDING_MODEL` | Embedding model name |
| `CYNOVELA_EMBEDDING_BASE_URL` | Embedding base URL |
| `CYNOVELA_EMBEDDING_API_KEY` | Embedding API key |
| `CYNOVELA_RERANKER_API_KEY` | Reranker API key |
| `CYNOVELA_CLASSIFIER_API_KEY` | Classifier API key |

#### 2-6-3. Operations

| Environment variable | Purpose |
|---------|------|
| `CYNOVELA_NONINTERACTIVE` | `1` skips the preflight dialog and exits immediately |
| `CYNOVELA_DISABLE_RATE_LIMIT` | Disables the rate limit |
| `CYNOVELA_MAX_UPLOAD_BYTES` | Maximum file upload size (default 100MB) |
| `CYNOVELA_MCP_PYTHON` | Python path used to run the MCP server |
| `CYNOVELA_SECRET_KEY` | Fernet encryption key (recommended in production) |

#### 2-6-4. Initialization

| Environment variable | Purpose |
|---------|------|
| `CYNOVELA_ADMIN_INITIAL_PASSWORD` | The admin password at first startup |
| `CYNOVELA_ADMIN_USERNAME` | The admin user name at first startup (default: `cynovela`) |
| `CYNOVELA_SMTP_PASSWORD` | SMTP password |

### 2-7. Overall Startup Flow Diagram

```
main() called
  ↓
parse CLI arguments with argparse
  ↓
preflight check (verify the required models exist)
  ├─ models missing → user choice (download / alternative mode / cancel)
  └─ abort startup if the return value is False
  ↓
get the LLM adapter
  └─ otherwise → LM Studio, etc.
  ↓
build AppConfig (reflecting mode / demo / mock)
  ↓
load cynovela.yaml
  ├─ override with CYNOVELA_* environment variables
  └─ initialize CircuitBreaker / Semaphore
  ↓
wire providers (Embedding / Reranker)
  ↓
set the PII detection mode (yaml.pii_mode)
  ↓
initialize the DB (store/db/demo.db with --demo, store/db/cynovela.db without it)
  ↓
start FastAPI with Uvicorn
```

### 2-8. Setting Up an External Inference Server

This package (the host direct-start version) starts up directly on the Mac host with `./launch.sh`.
There is no container.

- **The embedding is by default run by this application itself on the Mac GPU (MPS).** An external inference server is not required.
- **Only the rerank calls an external inference server by default** (`reranker.device: external` in `cynovela.yaml`).
  If there is no external inference server, it automatically falls back to the same model inside the application, so it works even without setting one up.

In other words, an external inference server is not "mandatory"; it is something you set up when you want to
**move the rerank outside / gather the inference onto 1 machine among several Macs**. It is the same way of thinking as
setting up the answering LLM (LM Studio etc.) separately.

#### 2-8-1. How to set up the external inference server

To run the external inference server, you need a python that has the 4 items `torch` / `sentence-transformers` / `fastapi` / `uvicorn`.
**A bare `python` most often does not have these 4 items.**
Separately from the environment that runs the application body (conda's `cynovela-dist`,
the source edition's `.venv-cynovela`, or the package edition's bundled `.condapack-cynovela`),
please create a place for the external inference server inside this package, and then set it up.

```bash
# アプリと同じ Mac のホスト側で。まず、この配布物のフォルダへ移動します。
cd<この配布物のフォルダ>

# (1) 外部の推論サーバを動かす場所を、この配布物の中に作る。どちらか一方を選びます。
#     conda を使う場合 (共有の環境ではなく、場所を指定して作ります)
conda create -y -p .mas-env python=3.12
#     venv を使う場合 (3.10 以上の python3 を指定してください)
python3.12 -m venv .mas-env

# (2) 部品を入れる
.mas-env/bin/python -m pip install -r mas/mas-requirements.txt

# (3) 立てる
.mas-env/bin/python mas/mas_server.py --preload
```

If you already have a python that has the 4 items, skip (1) and (2) and do (3) with that python.
How to check: `<その python> -c 'import torch, sentence_transformers, fastapi, uvicorn'`

`.mas-env` is created only inside this package. **Nothing is written to conda's shared environments (envs).**
The parts to install are the 4 items written in `mas/mas-requirements.txt`. The `requirements.txt` for the application body
(39 items) and `environment.yml` are not used for the purpose of setting up an external inference server.

- By default it stands at `127.0.0.1:18850` (to change it, use server.host / server.port in `mas/mas.yaml`).
- Check: it is running if `curl http://127.0.0.1:18850/health` returns `"status":"ok"`.
  If you use the rerank too, `"reranker_loaded":true` must also appear in the same response (0.2.0 and later).
- With `curl http://127.0.0.1:18850/capabilities` you can see the model name, the revision, and the device (mps/cpu).
- The application and the external inference server talk **over 127.0.0.1 inside the same Mac**. The application is not
  inside a container, so a rewrite such as `host.containers.internal` is not needed.

#### 2-8-2. Use "the same revision as the package" of bge-m3 / bge-reranker-v2-m3 for the models

- Embedding model: **BAAI/bge-m3, snapshot revision `5617a9f61b028005a4858fdac845db406aefb181`**
- Rerank model: **BAAI/bge-reranker-v2-m3**
- **If the revision differs, the numbers of the vectors change, they mix with the bundled vector collection, and the search ranking breaks.**
- Where to save: `store/models/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181/` of this package (the HF cache format).
  Under `store/models`, do not place it in any place other than this form.
  When `models.embedding.path` in `mas/mas.yaml` is `''`, it is resolved read-only from this same place as the application.
  Write the path only when you have placed it somewhere else.
- In the unlikely event that the revision differs, at startup and at publish, the warning "ベクターコレクションの埋め込み識別と現在の経路が
  食い違っています" (the embedding identity of the vector collection and the current path disagree) is **explicitly shown on the screen and in the log**
  If the warning appears, either align the revisions or rebuild everything.

#### 2-8-3. How to write the specification of the call destination

The default of `cynovela.yaml` (move only the rerank outside):

```yaml
reranker:
  provider: cross_encoder
  model: BAAI/bge-reranker-v2-m3
  device: external                 # external = 外部の推論サーバへ出す / cpu / mps = アプリ内で回す
  base_url: http://localhost:18850
  top_n: 5

embedding:
  provider: local                  # 既定はアプリ内。外へ出すなら openai_compat
  device: mps                      # local_cpu / mps / external_accelerator
  model: BAAI/bge-m3
  base_url: ''
```

When you want to move the embedding to the external inference server too (to gather the inference onto 1 separate Mac, etc.):

```yaml
embedding:
  provider: openai_compat
  device: external_accelerator
  model: BAAI/bge-m3
  base_url: http://127.0.0.1:18850   # 別の Mac なら その Mac の IP:18850
```

If you changed the port, please match base_url to it. It can also be changed from the administration screen (Settings > Embedding).

**A note for the case of moving it to a separate Mac**: because text will go outside the application, please set
`policy.allow_raw_content: false` in `mas/mas.yaml` on the external inference server side, so that it accepts
only what has already been masked.

#### 2-8-4. The behavior when the endpoint is not there

- Rerank: when the external inference server cannot be reached, **it falls back to processing with the model inside the application (store/models)**
  (this package is all-in-one and bundles the rerank model). When you have not placed the rerank model,
  it does not rerank and returns the search results as they are. In either case the processing does not stop.
- Embedding (only when you have set it to go outside): when it cannot be reached, **it explicitly falls back to the local processing inside the application**,
  and **"⚠️ 外部の推論サーバに届かないためローカルへ退避中"** (falling back to local because the external inference server cannot be reached) is displayed on the administration screen (Settings > Embedding).
  It never becomes slow silently. If you set the endpoint up again, it automatically returns from the next embedding.

#### 2-8-5. How to check that it is running

1. External inference server: `curl http://127.0.0.1:18850/health` → `"status":"ok"` (also
   `"reranker_loaded":true` if you use the rerank)
2. Start the application with `./launch.sh` → log in as an administrator
3. Throw 1 question → if `rerank_requests` has increased in `curl http://127.0.0.1:18850/metrics`
   of the external inference server, the rerank is being executed on the external inference server (MPS)
4. If you have also set the embedding to go outside, ingest (publish) 1 document and
   confirm that `embeddings_texts` in the same `/metrics` increases
   (if it is left at the default `provider: local`, it does not increase. This is normal)

Supplement: the image endpoint remains only an entry point for future use and is unimplemented (calling it gives 501).

---

## 3. Connecting an LLM Provider

Cynovela connects over HTTP to an external LLM (large language model) server to generate answers. This section explains the representative connection methods and the procedure for switching between them.

### 3-1. Connection Architecture

Cynovela's LLM connection layer (`llm_adapter.py`) is designed to connect to any service that has an OpenAI-compatible `/v1/chat/completions` endpoint. With `LMStudioAdapter` (an OpenAI-compatible adapter) as the mainstay, replacing the URL lets it support several local LLM runners.

```
Cynovela server
  ↓ HTTP POST /v1/chat/completions
LLM runner (LM Studio / Ollama / vLLM, etc.)
  ↓ streamed response
Cynovela server (guardrails → returned to the user)
```

### 3-2. Setting the Provider from the Screen

The bundled default is **LM Studio** (`llm.provider: lmstudio` /
`llm.base_url: http://localhost:1234` in `cynovela.yaml`). Please use this default as it is at first.

#### 3-2-1. When using LM Studio (default, recommended)

1. Start LM Studio and **load a model for chat (for generation)**.
2. Start the local server on the "Developer" tab of LM Studio (default port 1234).
3. Open **Settings > LLM Provider** in the left menu of Cynovela, and set
   - Provider: `LM Studio`
   - Base URL: `http://localhost:1234` (this form starts directly from the host, so localhost)
   - Model: **press "📋 fetch the model list" and choose an existing chat model from the list**
4. Confirm success with "🔌 connection test", and save with "💾 apply the LLM settings together".

**Please do not leave Model blank (`auto`).**
When the model name is not specified, the **first** entry of the model list returned by LM Studio is used.
If the first one is an embedding-only model (bge-m3 and so on), the generation request is refused, no answer comes back,
and it becomes an error (HTTP 400). Choosing a **chat model** from the list resolves it.
(Measured 2026-07-29: an answer was obtained just by changing the model name to an existing chat model.
Whether or not `/v1` is added to the end of the Base URL does not affect the result.)

- LM Studio does not refuse even if you specify the name of a model that is not loaded,
  and it may answer with a different model that is already loaded. In the Model field, enter
  an existing model name chosen from the list.
- If you run several large models at the same time in LM Studio, the answers may break down or
  become slow. It returns to normal automatically after a while.

#### 3-2-2. When using Ollama (it is not the default)

It also works with Ollama, but that is not the bundled default configuration. The procedure below is only for when you use it.

```bash
# Get the chat model you want to use (the model name is up to you. The following is one example)
ollama pull qwen3:8b
```

In Settings > LLM Provider, set Provider: `Ollama`, Base URL: `http://localhost:11434`,
and for Model, enter **the model name that appears in `ollama list`** as it is
(as with LM Studio, always specify an existing chat model name).

**Note**: When using LM Studio and Ollama at the same time, be careful about memory.
When switching, it is recommended to unload the LM Studio model before switching.

### 3-3. Connecting to LM Studio

LM Studio is a desktop LLM runner with a GUI. It is Cynovela's default connection target (`llm.provider: lmstudio`). Cynovela can also connect to any service that has a `/v1`-compatible API.

#### 3-3-1. Startup option

```bash
python server.py --lmstudio-url http://localhost:1234
```

`--lmstudio-url` is optional, and the default value is `http://localhost:1234`.

#### 3-3-2. Preparation on the LM Studio side

1. Start LM Studio and load any model (for example, a Japanese-capable model).
2. In the "Local Server" tab, enable the OpenAI-compatible API and put it in a listening state on port 1234.
3. When you start the Cynovela server, it connects via `/v1/chat/completions`.

#### 3-3-3. URL normalization behavior

The LLM adapter normalizes the URL by automatically removing a trailing `/` and `/v1`. All of the following are treated as the same connection target.

- `http://localhost:1234`
- `http://localhost:1234/`
- `http://localhost:1234/v1`

#### 3-3-4. Configuration example in `cynovela.yaml`

```yaml
llm:
  provider: lmstudio
  base_url: http://localhost:1234
  api_key: ""
  model: ""
  max_concurrent: 3
  timeout_seconds: 120
```

> **Important**: Do not pass `max_tokens` to the LM Studio API. It causes the thinking token budget to be exhausted on reasoning models.

### 3-4. Connecting to Ollama

Ollama is a CLI-centric local LLM runner. Because it provides an OpenAI-compatible API, you can connect simply by specifying Ollama's OpenAI-compatible endpoint in `--lmstudio-url`.

#### 3-4-1. Startup example

```bash
python server.py --lmstudio-url http://localhost:11434
```

#### 3-4-2. Using Ollama as a Reranker

Ollama can be connected not only for LLM inference but also as a Reranker provider. Configure it in `cynovela.yaml` as follows.

```yaml
reranker:
  provider: ollama
  base_url: http://localhost:11434
  model: bge-reranker-v2-m3
```

#### 3-4-3. Ollama / OpenRouter / vLLM through `openai_compat`

Setting `llm.provider` to `openai_compat` lets you switch to an OpenAI-compatible endpoint other than LM Studio (vLLM, Ollama's `/v1`-compatible gateway, etc.).

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:11434/v1   # 例: Ollama
  model: llama3
```

### 3-5. Connecting to an LLM on a Remote Machine

You can also run LM Studio / Ollama on another machine and connect to it from Cynovela over the network. This is useful when you want to consolidate GPUs on a separate machine.

```bash
python server.py --lmstudio-url http://192.168.1.50:1234
```

On the target machine, you need to configure LM Studio or Ollama to listen on "all interfaces".

> **Security note**: LLM communication is plaintext HTTP. Exposing it outside the LAN is not recommended. We recommend connecting over a VPN such as Tailscale.

> **Egress block for the CRAG preview (crag-egress-guard)**: When a remote / non-local LLM endpoint is specified, the CRAG (self-corrective RAG) preview (`context_preview`) is not sent outside. Before sending, it determines whether the endpoint is local, and if it is non-local (including cases where it cannot be determined) it does not send the preview and skips CRAG. This prevents fragments of raw body text from leaking to an external LLM even for an administrator. With a local LLM (LM Studio / Ollama running locally), CRAG remains enabled as before.

### 3-6. List of Supported Providers

Switch with the `llm.provider` key in `cynovela.yaml`.

| Provider | Value | Description |
|---|---|---|
| LM Studio | `lmstudio` | Connects to LM Studio's OpenAI-compatible API (default) |
| OpenAI-compatible (generic) | `openai_compat` | Any service that has an OpenAI-compatible `/v1` API (vLLM / OpenRouter / Ollama, etc.) |
| Mock | `mock` | Returns a fixed string without calling the LLM (for testing) |

#### 3-6-1. Configuration example for an OpenAI-compatible connection

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:8000
  model: meta-llama/Llama-3-8B-Instruct
  api_key: ""          # 設定UIで入力（このセッションのみ保持・保存しない）
  max_concurrent: 3
  timeout_seconds: 120
```

#### 3-6-2. The `mock` provider, and the removed `--mock`

The former `--mock` (a verification mode that did not call the LLM at all) has been removed as a startup flag. Specifying it now stops with an error. The `mock` value of `llm.provider` in `cynovela.yaml` remains, and returns a fixed string without calling the LLM.

The start that needs no model is `--mode minimal`. In that mode the Embedding also switches to TF-IDF (a lightweight vocabulary-frequency-based embedding), and no external model download occurs. It is not suitable for checking RAG (retrieval-augmented generation) quality, but it is useful for verifying the UI and the flow.

### 3-7. Related Environment Variables

The main environment variables available for the LLM connection are as follows.

| Environment variable | Purpose |
|---|---|
| `CYNOVELA_LLM_BASE_URL` | Overrides the LLM base URL |
| _(no environment variable)_ | The LLM API key is entered in the settings UI (kept for this session only, never saved) |
| `CYNOVELA_LLM_MODEL` | LLM model name (used only for OpenAI-compatible connections) |
| `CYNOVELA_LLM_PROVIDER` | LLM provider name |
| `CYNOVELA_LLM_MAX_CONCURRENT` | Upper limit of concurrent calls |

### 3-8. Reranker Providers

Apart from the LLM, the Reranker that reorders the search results is also replaceable. Specify it with `reranker.provider` in `cynovela.yaml`.

| Provider | Value | Description |
|---|---|---|
| Disabled | `none` | Does not use a Reranker |
| CrossEncoder | `cross_encoder` | A local CrossEncoder model (the default high-quality configuration) |
| FlashRank | `flashrank` | A lightweight Reranker library |
| MLX | `mlx` | A skeleton implementation for Apple Silicon (the actual body is a future item) |
| Ollama | `ollama` | A Reranker via Ollama |
| HTTP | `http` | Any HTTP endpoint |

---

## 4. Using Cynovela from External Tools with MCP

Cynovela can expose its own features to external LLM clients as an MCP server for MCP (Model Context Protocol, the AI tool integration protocol proposed by Anthropic). This section explains the concept of MCP, the MCP tools that Cynovela exposes, and the connection procedure.

The server (`mcp_server.py`) implements protocol revision **2026-07-28** over stdio: it answers `server/discover` (no handshake and no session id is required — `initialize` from older clients is answered too), declares tool inputs and outputs with JSON Schema 2020-12, and returns results as `structuredContent` in addition to plain text. When the target material does not exist it returns JSON-RPC error `-32602`.

### 4-1. What MCP is

MCP is a standard protocol by which an AI assistant (the client) calls features (tools) of an external system.

- **Client**: the side the user talks to, such as LM Studio or another supported LLM client
- **Server**: the side that provides features (Cynovela is this side)
- **Tool**: an operation the server exposes (search, registration, reference, and so on)

With MCP, when a user says to an LLM client "search our internal documents", the LLM calls Cynovela's search tool and generates an answer based on the result.

### 4-2. MCP tools Cynovela exposes (25 in total)

22 tools are visible by default. The three administration tools in 4-2-6 are closed by default: they appear in `tools/list` only when the MCP server's `env` sets `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` (see 4-5-5).

#### 4-2-1. RAG search tools (4)

##### `search_collection`

- **Arguments (required)**: `query`, `workspace_id`, `collection_id`
- **Arguments (optional)**: `preset`
- **Description**: Performs a RAG search against a single Collection (a group of documents).

##### `search_across_collections`

- **Arguments (required)**: `query`, `workspace_id`, `collection_ids`
- **Arguments (optional)**: `preset`
- **Description**: Performs a RAG search across multiple Collections.

##### `rag_with_role`

- **Arguments (required)**: `query`, `workspace_id`, `collection_id`, `style_role`
- **Arguments (optional)**: `preset`
- **Description**: Performs a RAG search while switching the answer style by role (for administrators / for general users, and so on).

##### `rag_general`

- **Arguments (required)**: `query`, `workspace_id`
- **Description**: Generates an answer using only the LLM's general knowledge, without using RAG. It is for general questions that do not depend on internal documents.

#### 4-2-2. Information retrieval tools (6)

##### `list_workspaces`

- **Arguments**: none
- **Description**: Gets a list of all workspaces and their collections.

##### `get_workspace_info`

- **Arguments (required)**: `workspace_id`
- **Description**: Returns detailed information about the specified workspace (name, guardrail policy, creation time, and so on).

##### `get_collection_info`

- **Arguments (required)**: `workspace_id`, `collection_id`
- **Description**: Returns details of the collection (document count, status, access level).

##### `get_audit_logs`

- **Arguments (required)**: `workspace_id`
- **Arguments (optional)**: `limit` (default 10, maximum 50)
- **Description**: Gets the audit log (chat history, PII detection, errors).

##### `list_sources`

- **Arguments (required)**: `workspace_id`
- **Description**: Returns a list of the data sources under the workspace (file path, status, file count).

##### `server_status`

- **Arguments**: none
- **Description**: Shows whether the server is up and the state of the index (collections and their chunk counts).

#### 4-2-3. Ingestion and progress tools (3)

##### `ingest_source`

- **Arguments (required)**: `path`
- **Arguments (optional)**: `name`, `workspace_id`
- **Description**: Ingests material in one tool: adds the folder as a data source, registers the material, and starts the scan. The scan returns a `job_id` the moment it starts and the call comes back immediately; watch the progress with `get_job_status`.

##### `get_job_status`

- **Arguments (required)**: `job_id`
- **Description**: Shows the progress of a scan or a publish. Pass the `job_id` returned by `ingest_source` or `publish_collection`.

##### `cancel_scan`

- **Arguments (required)**: `source_id`
- **Description**: Requests cancellation of a running scan.

#### 4-2-4. Publishing and creation tools (4)

##### `publish_collection`

- **Arguments (required)**: `collection_id`
- **Description**: Starts publishing the collection and returns a `job_id` immediately — it does not wait for the publish to finish. Watch the progress with `get_job_status`. Once published, the collection can be searched by RAG.

##### `create_collection`

- **Arguments (required)**: `workspace_id`, `name`
- **Arguments (optional)**: `source_id`
- **Description**: Creates a collection inside the workspace. When `source_id` is given, all files of that data source are linked to the new collection.

##### `publish_control`

- **Arguments (required)**: `collection_id`, `action` (`stop` or `recover`)
- **Description**: Stops a running publish, or recovers a collection stuck in the publishing state.

##### `create_workspace`

- **Arguments (required)**: `name`
- **Arguments (optional)**: `description`
- **Description**: Creates a new workspace.

#### 4-2-5. Settings tools (5)

All five require an **admin** token. API keys are write-only: responses carry only the
`api_key_set` boolean (set / not set), never a key value.

##### `settings_show`

- **Arguments (optional)**: `name` — one of `llm` (default), `reranker`, `classifier`, `embedding`, `pii`, `vector-store`, `datasync`
- **Description**: Shows the current settings of the chosen target.

##### `settings_models`

- **Arguments**: none
- **Description**: Lists the models at the configured inference endpoint. Note: this is the *downloaded* list — it does not mean a model is loaded.

##### `settings_test`

- **Arguments (optional)**: `provider`, `base_url`, `model` (when given, these are tested instead of the saved settings)
- **Description**: Tests the LLM connection and answers in words (connected / not connected, with the reason).

##### `settings_set`

- **Arguments (required)**: `values` — an object with only the items to change (e.g. `{"model": "..."}`)
- **Arguments (optional)**: `name` — same choices as `settings_show` (default `llm`)
- **Description**: Changes settings. **Closed by default**: it runs only when the MCP server process was started with the environment variable `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` (see 4-5-4). When closed, the call returns an error text explaining exactly that, and nothing is executed.

##### `settings_providers`

- **Arguments**: none
- **Description**: Lists the selectable LLM provider presets.

#### 4-2-6. Administration tools (3) — closed by default

These three appear in `tools/list` only when the MCP server's `env` sets `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` (see 4-5-5). This is not a removed feature: it is a guard that stops an AI, swayed by material it has just read, from firing destructive operations on its own.

##### `delete_item`

- **Arguments (required)**: `kind` (`source` / `collection` / `workspace`), `id`
- **Description**: Deletes a data source, a collection, or a workspace.

##### `manage_users`

- **Arguments (required)**: `action` (`list` / `create` / `update` / `delete` / `reset_password`)
- **Arguments (optional)**: `user_id`, `username`, `password`, `role`, `display_name`, `is_active`
- **Description**: Manages users (list, create, update, delete, reset a password).

##### `manage_backups`

- **Arguments (required)**: `action` (`list` / `create` / `restore` / `delete`)
- **Arguments (optional)**: `name`, `label`
- **Description**: Handles backups (list, create, restore, delete). `restore` replaces the current data with the contents of the backup; a server restart is required for the restore to take effect.

#### 4-2-7. How to use the long-running operations

Scanning (`ingest_source`) and publishing (`publish_collection`) return a `job_id` the moment they start and come back immediately. Watch the progress by passing that `job_id` to `get_job_status`, repeatedly. To cancel, use `cancel_scan` for a scan and `publish_control` with `stop` for a publish.

### 4-3. Connecting from LM Studio

LM Studio has MCP client features, and an MCP server can be registered in its configuration file.

#### 4-3-1. Connection flow

```
LM Studio（ユーザー対話）
  ↓ MCP プロトコル（標準入出力経由）
Cynovela MCP サーバー（mcp_server.py）
  ↓ HTTP API
Cynovela 本体（FastAPI サーバー）
```

#### 4-3-2. Where LM Studio's configuration file is

The MCP registration lives in a single JSON file named `mcp.json` inside LM Studio's home
directory. Measured locations on macOS (measured on LM Studio 0.4.x):

- `~/.cache/lm-studio/mcp.json` — the location measured on the development machine
- `~/.lmstudio/mcp.json` — the location when LM Studio's home is the newer default

You do not have to guess which one your machine uses: inside LM Studio, open the
right-hand **Program** panel → **Install** → **Edit mcp.json** — that editor opens the
correct file, and saving it there is the same as editing the file directly.

#### 4-3-3. Getting the token (`CYNOVELA_TOKEN`) — full procedure

1. Start Cynovela (`./launch.sh` or `./launch.sh --demo`) and confirm `http://127.0.0.1:8765` answers.
2. Ask the server for a token with your login name and password (the same values you use on the web screen):

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"<your username>","password":"<your password>"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
```

3. The printed string is the token. Put it into the `env` block of `mcp.json` (next step).
4. **The token does not expire unless you ask it to.** Signing in gives a token with no expiry; pass `expires_in_hours` to the login call if you want one that does. If tool calls start failing with an authentication error, issue a new token with the same command and update `mcp.json`.

Note: for the settings tools (and other admin tools) the login must be the **administrator** account; a viewer token is rejected by the server with 403.

#### 4-3-4. Configuration example

Register the following in `mcp.json` (merge into the existing `mcpServers` object if the file already has one):

```json
{
  "mcpServers": {
    "cynovela": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp_server.py",
        "--cynovela-url", "http://127.0.0.1:8765"
      ],
      "env": {
        "CYNOVELA_TOKEN": "<the token from 3-3>"
      }
    }
  }
}
```

- `command`: any Python 3.12+ — the natural choice is the one this package prepared (see 4-4).
- To allow `settings_set`, add `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` to the `env` block (see 4-5-4). Leave it out to keep settings read-only.
- To expose the three administration tools (`delete_item` / `manage_users` / `manage_backups`), add `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` to the `env` block (see 4-5-5). Leave it out and they do not appear at all.

#### 4-3-5. LM Studio asks a person for permission — this part is yours

Registering the server in `mcp.json` is **not** the last step. LM Studio guards local MCP
tools behind an explicit, human confirmation in its own window:

- **Where**: when the model first tries to call a Cynovela tool in a chat, LM Studio shows a confirmation dialog in the chat window asking whether to allow the tool call (per call, or "always allow" per tool). The server can also be switched on and off in the **Program** panel where `mcp.json` was edited.
- **After you allow it**: the tool call runs, and the result (with `structuredContent`) is handed to the model — from then on the flow of 4-3-1 works end to end.
- **If you never allow it**: the registration itself still looks fine (the server appears in the panel), but no tool is ever called — this is the single most common "it does not work" state. It is not an error in Cynovela; grant the permission in the LM Studio window.

### 4-4. Which Python Runs the MCP Server

`mcp_server.py` uses the standard library only — it has no external dependencies, so **any Python 3.12 or later can run it**; no environment needs to be activated. The natural choice is the Python this package prepared (package edition: `.condapack-cynovela/bin/python3`; source edition choice 1: the `cynovela-dist` conda environment).

#### 4-4-1. Specifying the Python path

The environment variable `CYNOVELA_MCP_PYTHON` can specify the absolute path of the Python that the `/api/mcp/config` snippet points clients at.

```bash
export CYNOVELA_MCP_PYTHON=/path/to/.condapack-cynovela/bin/python3
```

### 4-5. Notes on Authentication

#### 4-5-1. Bearer token

The MCP server authenticates to the main Cynovela API with the `Authorization: Bearer<token>` header. The token is passed through an environment variable on the client side.

- Authentication is the JWT issued by `POST /api/auth/login` (the procedure is in 4-3-3). The old `Bearer demo-token-<user_id>` form has been abolished and is not accepted.
- The token does not expire unless the login call asked for an expiry (`expires_in_hours`). Issue a new one with the same login call whenever you need to.

#### 4-5-2. Role permissions

Calls made through MCP also pass the same role permission checks (admin / curator / viewer) as the main API. In particular, tools that write — such as `ingest_source`, `publish_collection` and `create_workspace` — may require admin permission, and all five settings tools require it.

#### 4-5-3. Audit log

Operations made through MCP are also recorded in the same audit log (the `audit_logs` table) as the main body. You can check the history with `get_audit_logs`.

#### 4-5-4. Write guard for the settings tools (default: read-only)

The settings tools are split into reading and writing:

- **Reading** (`settings_show`, `settings_models`, `settings_test`, `settings_providers`) works whenever the token is an admin token. No extra switch.
- **Writing** (`settings_set`) is **closed by default**. It runs only when the MCP server process was started with `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` in its environment — in LM Studio, that means adding the line to the `env` block of `mcp.json` (4-3-4). When closed, the call returns an error message saying exactly this, and nothing is executed.

Why: the caller of an MCP tool is an AI that can be swayed by whatever material it has just read. If a document says "rewrite the settings", a path exists in principle for the AI to treat that as an instruction. Writing therefore requires an explicit, human-made decision on the client side. This guard is *not* a replacement for the server-side role check — that check still runs as before; this is a thin extra layer in front of it.

#### 4-5-5. Guard for the administration tools (default: hidden)

The three administration tools (`delete_item`, `manage_users`, `manage_backups`) are **closed by default**. They appear in `tools/list` — and run — only when the MCP server process was started with `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` in its environment; in LM Studio, that means adding the line to the `env` block of `mcp.json` (4-3-4). The reason is the same as in 4-5-4: deletion, user management and backup restore are exactly the operations an AI must not fire on its own after being swayed by material it has just read. This is not a removed feature — it is a thin, explicit switch a human turns on; the server-side role check still runs as before.

### 4-6. Troubleshooting

| Symptom | What to check |
|---|---|
| The tools are not found | Whether the Cynovela main body (`server.py`) is already running at `http://127.0.0.1:8765` |
| The server appears in LM Studio but no tool is ever called | The human permission in LM Studio has not been granted yet — see 4-3-5. The registration alone does not allow calls; allow the tool call in the chat window's confirmation dialog |
| Authentication error | The value of the `CYNOVELA_TOKEN` environment variable, and whether the token is still valid — **a token has no expiry unless the login call asked for one**; re-issue with the login call in 4-3-3 |
| `settings_set` answers "the write is closed by default" | That is the write guard (4-5-4), not a fault. Add `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` to the `env` block of `mcp.json` if you really want writes |
| `delete_item` / `manage_users` / `manage_backups` do not appear in the tool list | That is the guard (4-5-5), not a fault. Add `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` to the `env` block of `mcp.json` if you really want them |
| ImportError appears | Whether the Python is 3.12 or later (`mcp_server.py` itself has no external dependencies) |
| The result is empty | Whether the target Collection has reached the `ready` status |

---

## 5. Sharing over a LAN

Cynovela listens on `0.0.0.0` by default. That means other machines on the same LAN (local
network) can reach it with no extra flags (original specification). If you want to close it off
to your own machine only, add `--local-only`. For access via Tailscale (a VPN service), or to
narrow down where access may come from, use the flags below.

### 5-1. Default behaviour

```bash
python server.py
```

- **Bind address**: `0.0.0.0` (`127.0.0.1` only when `--local-only` is added)
- **Clients that can access it**: with the default, browsers and CLIs on other machines of the
  same LAN can reach it as well; only the same machine when `--local-only` is added
- **Seen from outside**: the port appears to be closed only when `--local-only` is added

With `--local-only` added, access over the network cannot occur in principle. That configuration
is recommended for verification and personal use.

### 5-2. LAN sharing mode

If you want to access Cynovela from another machine on the same LAN, add the `--lan` flag.

#### 5-2-1. Startup command

```bash
python server.py --lan
```

This flag switches the bind address to `0.0.0.0` (all interfaces), making it connectable from
other machines on the LAN.

#### 5-2-2. Connection example

If the LAN IP of the server machine is `192.168.1.20`, connect from a browser on another
machine as follows.

```
http://192.168.1.20:8765
```

#### 5-2-3. IP allowlist

Cynovela has an IP allowlist feature. It is applied only when you pass `--allow-subnet` /
`--allow-tailscale`; with neither of them the access source is not restricted. Once it is applied,
`127.0.0.1` and `localhost` are always permitted, and any other source must be permitted
explicitly. You can add source subnets with `--allow-subnet`.

```bash
python server.py --lan --allow-subnet 192.168.1.0/24
```

To specify more than one, repeat `--allow-subnet`.

```bash
python server.py --lan --allow-subnet 192.168.1.0/24 --allow-subnet 10.0.0.0/24
```

Requests from a source that is not permitted receive HTTP 403 Forbidden.

To close it to the inside of your own machine only, add `--local-only`.

### 5-3. Tailscale sharing mode

With Tailscale you can connect over a VPN even between separate networks, such as home and a
remote location. Cynovela has an `--allow-tailscale` flag that automatically permits the
Tailscale subnet (`100.64.0.0/10`).

#### 5-3-1. Preconditions

- The Tailscale client is installed on the server machine and logged in
- The connecting machine is logged in to the same Tailscale account
- The `tailscale ip -4` command returns a Tailscale IP on the server side

#### 5-3-2. Startup command

```bash
python server.py --lan --allow-tailscale
```

#### 5-3-3. Behaviour

- At startup it runs `tailscale ip -4` to detect the assigned Tailscale IP (3 second timeout).
- It automatically adds the `100.64.0.0/10` subnet to the IP allowlist.
- Clients connecting via Tailscale become able to connect.

To display the Tailscale name or IP of a source, run `tailscale status` on the Tailscale client
side.

### 5-4. Security notes

LAN sharing and Tailscale sharing are convenient, but there are several risks to be aware of.

#### 5-4-1. Communication is plaintext HTTP

The Cynovela main body listens over HTTP. HTTPS is not built in, so the contents of
communication travel as plaintext within the network. If you handle highly confidential
documents, consider one of the following.

- Access only over an encrypted VPN such as Tailscale
- Terminate TLS at a reverse proxy (nginx, etc.)

#### 5-4-2. Direct exposure to the internet is prohibited

Given the incompleteness of authentication and the lack of encryption, you must absolutely
avoid exposing it directly to the internet side while bound to `0.0.0.0`.

#### 5-4-3. Constraints of authentication

Authentication is JWT (issued by `POST /api/auth/login`), and is required even when started
with `--demo`. The legacy `Bearer demo-token-<user_id>` form has been abolished and is not
accepted. When sharing over a LAN, operate on the premise that only trusted users are on the
network.

#### 5-4-4. Permission for file upload

Because the configuration can end up accepting file uploads from any user on the LAN, always
check the validation of the `path` argument of `/api/sources` and the upload limit setting
(`CYNOVELA_MAX_UPLOAD_BYTES`, default 100 MB).

#### 5-4-5. Recommended configurations

Even for verification and learning use, one of the following is recommended.

- Fully local: add no flags and operate on `127.0.0.1` only
- Personal VPN: add only `--allow-tailscale` and avoid exposure to the LAN
- Restricted LAN: narrow the sources strictly with `--lan --allow-subnet`

### 5-5. Summary of related startup flags

| Flag | Default | Description |
|---|---|---|
| `--host` | `0.0.0.0` | Bind address (all addresses by default; narrow it with `--local-only`) |
| `--port` | `8765` | Port number |
| `--lan` | disabled | Explicitly set `host=0.0.0.0` and listen on all interfaces |
| `--allow-tailscale` | disabled | Permit the Tailscale subnet (`100.64.0.0/10`) |
| `--allow-subnet` | empty | Add a custom subnet (can be specified multiple times) |

---

## 6. backup and restore

### 6-1. Default Storage Locations

Cynovela's data is stored under `~/.cynovela/`.

| Use | Path | Environment variable for override |
|------|------|------------|
| SQLite DB (normal) | `~/.cynovela/db/cynovela.db` | `CYNOVELA_DB` |
| SQLite DB (demo) | `~/.cynovela/db/demo.db` | `CYNOVELA_DB` |
| ChromaDB (normal) | `~/.cynovela/vector/default/chroma` | `CYNOVELA_CHROMA` |
| ChromaDB (demo) | `~/.cynovela/vector/demo/chroma` | `CYNOVELA_CHROMA` |
| Backups | `store/backups` under the folder where the package was extracted | `CYNOVELA_BACKUP_DIR` |
| Models | `~/.cynovela/models` | (can be specified individually with `cynovela.yaml.models.*.path`) |
| Logs | `~/.cynovela` | `CYNOVELA_LOG_DIR` |

> The above are the storage locations of the host (conda) edition. The actual location for the host edition is `store/` under the folder where the package was extracted. In the container edition, the DB and vector data are stored in named volumes, and the ingest entry point bind-mounts the ingest sources passed at startup (multiple allowed) read-only at `/app/ingest/<inner name>`. The former default ingest folder `~/Cynovela` has been abolished.

### 6-2. What `store/` Holds

`store/` holds the index of the ingested documents, the database, the settings, and the keys.
The signing key for the passes is newly created on this machine at the first startup.

### 6-3. Manual Backup

With the server stopped, copy the directories above.

```bash
# サーバー停止後に実行
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/cynovela-backups/$TS
cp -R ~/.cynovela/db ~/cynovela-backups/$TS/db
cp -R ~/.cynovela/vector ~/cynovela-backups/$TS/vector
```

### 6-4. Restore

```bash
# サーバー停止後に実行
cp -R ~/cynovela-backups/20260526-093000/db ~/.cynovela/db
cp -R ~/cynovela-backups/20260526-093000/vector ~/.cynovela/vector
```

### 6-5. Points to Note

- **Always back up and restore SQLite and ChromaDB together.** If you restore only one of them, the consistency between the `chunks` table and the vector IDs breaks.
- Deleting a source / workspace / collection is implemented so that both SQLite and ChromaDB are cleaned up. Keep this principle of "both from the same snapshot" in backup operations as well.
- Starting with `--demo` uses `db/demo.db` and `vector/demo/chroma`; starting without it, for production, uses `db/cynovela.db` and `vector/default/chroma`. Neither one is wiped on every startup — what you write stays as it is. Do not mix them up with production operation.

### 6-6. Backups Taken in the App (`backup create`) — Where They Go

```bash
python3 cynovela-cli.py backup create --yes          # take a backup
python3 cynovela-cli.py backup list                  # list what you have
```

Backups are written under `store/backups` inside the folder where the package was extracted, for example `store/backups/backup-20260821-225606`. Nothing is written under your home folder. Each backup folder holds `cynovela.db` (a copy of the database actually in use — the name inside the backup is always `cynovela.db`, whether or not you started with `--demo`), a `chroma` folder, and `meta.json`.

To keep a copy somewhere else, pack that one folder and record its fingerprint:

```bash
BK=store/backups/backup-20260821-225606
tar -czf <destination>/$(basename $BK).tar.gz -C store/backups $(basename $BK)
shasum -a 256 <destination>/$(basename $BK).tar.gz
```

### 6-7. Whole-store Backup (recommended)

`python3 cynovela-cli.py backup create --yes` makes a backup. In addition, copy the whole `store` folder with `tar`: a backup alone still needs some manual assembly when you restore, whereas a `tar` copy restores in one step.

```bash
bash stop.sh
tar -czf <destination>/cynovela-store-$(date +%Y%m%d).tar.gz -C <the Cynovela folder> store
./launch.sh
```

The simplest form is a plain copy of the whole folder (also with Cynovela stopped):

```bash
# Backup of the DB and Chroma
cp -r store/ ~/cynovela-backup-$(date +%Y%m%d)/
```

### 6-8. Restore from a Whole-store Copy (do it with Cynovela stopped)

Do restore operations with Cynovela stopped. Do not restore while it is running.

```bash
bash stop.sh
mv store store.old            # move the current store aside under another name
tar -xzf <destination>/cynovela-store-YYYYMMDD.tar.gz
./launch.sh
```

Do not use any restore control from the screen or the API. Reason: it swaps the foundation out from under a running server, so no response comes back and a restart is required anyway. The restore control has been removed from the screen: the backup list now shows this note in its place. The API endpoint still exists, but do not use it for the same reason.

### 6-9. Restore from a Backup Taken in the App (do it with Cynovela stopped)

```bash
bash stop.sh
BK=store/backups/backup-20260821-225606          # the backup you want to go back to
mkdir -p store/aside
mv store/db/demo.db store/aside/                 # move aside only the database file
mv store/db/demo.db-wal store/aside/ 2>/dev/null # and its journal, if there is one
mv store/db/demo.db-shm store/aside/ 2>/dev/null
mv store/vector/demo/chroma store/aside/chroma   # and only the vector folder
cp "$BK/cynovela.db" store/db/demo.db            # without --demo, use store/db/cynovela.db
cp -R "$BK/chroma" store/vector/demo/chroma      # without --demo, use store/vector/default/chroma
./launch.sh --demo
```

Move aside only the database file and the vector folder, as shown above. Do not move the whole `store/db` folder: it also holds the sign-in key under `store/db/jwt`, which a backup does not contain. If you move that away, the key is lost, a new one is generated at startup, and everyone has to sign in again.

Move the journal files (`demo.db-wal` / `demo.db-shm`) aside together with the database file. They belong to the database you are replacing. If you leave them behind, they are replayed onto the restored file at startup and the restore silently has no effect.

Then check that what you expected is back, and only after that delete what you moved aside:

```bash
python3 cynovela-cli.py workspaces
python3 cynovela-cli.py collections
rm -rf store/aside
```

### 6-10. Moving to Another Mac

Make a ZIP including vectors with full-export, and import it on the destination. The embedding model on the destination must be the same as on the source.

```bash
# On the source (admin token in $CYNOVELA_TOKEN)
curl -s -H "Authorization: Bearer $CYNOVELA_TOKEN" \
  "http://127.0.0.1:8765/api/workspaces/<workspace_id>/full-export" \
  -o cynovela-migration.zip

# On the destination (admin token in $CYNOVELA_TOKEN)
curl -s -H "Authorization: Bearer $CYNOVELA_TOKEN" \
  -F "file=@cynovela-migration.zip" \
  "http://127.0.0.1:8765/api/workspaces/import"
```

---

## 7. Logs

### 7-1. Log Level

Controlled by `logging.level` (or `server.log_level`) in `cynovela.yaml`. The default is `INFO`.

```yaml
logging:
  level: INFO
  request_id: true   # 全リクエストに X-Request-ID を付与
```

### 7-2. Request ID

When you enable `request_id: true`, an `X-Request-ID` header is added to all API responses. It can be used during troubleshooting to link requests on the client side with logs on the server side.

### 7-3. Preflight Log

The preflight check at startup outputs logs such as the following.

```
[Cynovela] PII detection mode: standard (from cynovela.yaml)
```

### 7-4. Watching the Server Log

```bash
# Server log (real time). When using the demo, add --demo as well
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

---

## 8. Exporting the Audit Log

### 8-1. What the Audit Log Is

Cynovela records important operations in the `audit_logs` table in SQLite.

Main recorded targets:

- Creation and deletion of workspaces, collections, and sources
- Execution and completion of Publish
- Chat (questions and answers)
- PII detection (`PII_DETECTED` / `pii_detected`)
- Prompt injection detection (`PROMPT_INJECTION_BLOCKED`)
- Authentication failures

### 8-2. Tamper Prevention

`audit_logs` cannot be deleted or modified through the API. Keep this principle in your operating policy as well.

### 8-3. Viewing from the GUI

After logging in with the `admin` role, you can view them with filters on the "監査ログ" (audit log) screen.

### 8-4. Via the API

- `GET /api/guardrails/pii-detections` — aggregates PII detections from `audit_logs` (administrator required)
- `GET /api/pii-detections` — aggregates from the `chunks` table (administrator required)
- `GET /api/audit-logs` — retrieves the audit log (administrator required)

### 8-5. Extracting Directly from SQLite

If you want to export to CSV or similar, SELECT directly from a SQLite client.

```bash
sqlite3 ~/.cynovela/db/cynovela.db \
  "SELECT timestamp, action, target, detail FROM audit_logs ORDER BY timestamp DESC LIMIT 100;"
```

---

## 9. User Management

### 9-1. Roles

Cynovela has 2 kinds of roles.

| Role | Permissions |
|--------|------|
| `admin` | All features (user management, system settings, viewing the PII detection history, and so on) |
| `viewer` | Viewing only |

> Names such as `curator` / `data-scientist` are accepted as backward-compatible values, but in the current implementation they are normalized to `viewer` and have no specific permissions. The roles held by the DB are the 2 values `admin` / `viewer`.

### 9-2. The Initial Administrator

An administrator user is created at first startup. The user name and password can be overridden with environment variables.

| Environment variable | Use | Default |
|---------|------|------|
| `CYNOVELA_ADMIN_USERNAME` | User name of the first administrator | `cynovela` |
| `CYNOVELA_ADMIN_INITIAL_PASSWORD` | Password of the first administrator | (If neither the env var nor `auth.admin_initial_password` in `cynovela.yaml` is set, a password change is forced at first login. No known fixed password is distributed. Set a value only if you want to fix it.) |

### 9-3. Login Information of the Shipped demo.db

The `demo.db` distributed with `--demo` already has the following accounts loaded.

| User name | Role | Password |
|-----------|--------|-----------|
| `cynovela` | admin | A change is forced at first login (no fixed password is distributed) |
| `demo` | viewer | See `viewer_password` in the bundled credential file (`*.admin-password.txt`, received separately from the package tar). No fixed password is distributed |

### 9-4. Adding and Deleting Users, and Changing Passwords

After logging in with the administrator role, you can do this from the "ユーザー管理" (user management) screen. Operation via the API is also possible, but the user management endpoints are protected by `_require_admin` or `_require_admin_or_self` (the person themselves or an administrator only).

### 9-5. Vault Access and Masking by Role

- `admin` → searches the raw (original text) vault. No exit masking in the answer display.
- `viewer` (`curator` and so on are normalized to viewer) → searches the masked vault. Exit masking is applied.

> However, when an external (non-local) LLM is used, crag-egress-guard prevents the raw preview (context_preview) from being sent outside even for an administrator (CRAG is skipped). Note that it is not the case that "administrator = raw text is always passed to the external LLM."

For details, see the section on how the view differs by role, in the hands-on guide.

### 9-6. Authentication

API authentication is done with the HTTP `Authorization` header. The token is a JWT issued by `POST /api/auth/login`. The old `Bearer demo-token-{user_id}` form has been abolished and is not accepted.

---

## 10. Health Checks and Monitoring

### 10-1. Main Health Endpoints

`/api/health` and other monitoring endpoints for administrators are provided (protected by `_require_admin`).

### 10-2. Publish History

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

### 10-3. Circuit Breaker

When failures of LLM or external API calls exceed a certain number, the circuit breaker OPENs and calls are stopped temporarily. The behavior can be adjusted in the `circuit_breaker` section of `cynovela.yaml`.

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 3
  recovery_timeout_seconds: 30
```

---

## 11. Notifications (Email)

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

## 12. Changing the Port

### 12-1. Ports and Access Control

| Default | Content |
|------|------|
| 8765 | Server port |
| 0.0.0.0 | Bind address (narrowed to 127.0.0.1 with `--local-only`) |
| Allowed IPs | No restriction by default (applied only when `--allow-subnet` / `--allow-tailscale` is given) |

To allow access from a LAN or from Tailscale, use `--lan` / `--allow-tailscale` / `--allow-subnet` together (see 5 "Sharing over a LAN").

### 12-2. Changing the Port Number

The port **is decided by the argument at startup**. Even if you rewrite `server.port` in `cynovela.yaml`,
it is not reflected in the listening port (the setting is loaded, but it is not passed to the listener).

```bash
# Specify it with --port (default 8765). The arguments passed to launch.sh reach server.py as they are.
# When using the demo, please add --demo as well.
./launch.sh --port 8900

# If you activate the conda environment yourself, doing it directly is the same
python server.py --mode text --port 8900
```

When it does not work: if the specified port is already in use, startup fails.
Check the process that is using it with `lsof -i :8900`, and choose another port.
Note that `./launch.sh` only looks at the usage of the default port 8765 and prompts you to confirm.
When you specify another port, check with `lsof` yourself.

When sharing over a LAN, combine it with the sharing flags:

```bash
python server.py --lan --port 9000
```

Using a privileged port such as 80 or 443 requires administrator privileges, so going through a reverse proxy (nginx, etc.) is recommended.

---

## 13. Operational Notes

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

このドキュメントは、Cynovela を入れる人・回す人のためのものです。起動と停止、機械への入れ方・置き方、LLM プロバイダーの繋ぎ方、MCP で外部ツールから使う手順、LAN で分け合う設定、backup と restore、ログ、監査ログ、利用者の管理、健全性の確認、通知、ポートの変更を 1 か所にまとめています。

目次:

1. 通常の起動と停止
2. 入れ方・置き方
3. LLM プロバイダーを繋ぐ
4. MCP で外部ツールから使う
5. LAN で分け合う
6. backup と restore
7. ログ
8. 監査ログの Export
9. 利用者の管理
10. 健全性の確認と監視
11. 通知（メール）
12. ポートを変える
13. 運用上の注意

---

**目次**

- [1. 通常の起動と停止](#1-通常の起動と停止)
  - [1-1. 起動](#1-1-起動)
  - [1-2. 停止](#1-2-停止)
  - [1-3. バックグラウンド起動](#1-3-バックグラウンド起動)
- [2. 入れ方・置き方](#2-入れ方置き方)
  - [2-1. 動作確認済み環境](#2-1-動作確認済み環境)
  - [2-2. 環境セットアップ](#2-2-環境セットアップ)
  - [2-3. 起動フラグ一覧](#2-3-起動フラグ一覧)
  - [2-4. `--mode` 選択ガイド](#2-4---mode-選択ガイド)
  - [2-5. 初回モデルダウンロード手順](#2-5-初回モデルダウンロード手順)
  - [2-6. 主要な環境変数](#2-6-主要な環境変数)
  - [2-7. 起動フロー全体図](#2-7-起動フロー全体図)
  - [2-8. 外部の推論サーバを立てる](#2-8-外部の推論サーバを立てる)
- [3. LLM プロバイダーを繋ぐ](#3-llm-プロバイダーを繋ぐ)
  - [3-1. 接続アーキテクチャ](#3-1-接続アーキテクチャ)
  - [3-2. 画面から設定する](#3-2-画面から設定する)
  - [3-3. LM Studio との接続](#3-3-lm-studio-との接続)
  - [3-4. Ollama との接続](#3-4-ollama-との接続)
  - [3-5. リモートマシン上の LLM への接続](#3-5-リモートマシン上の-llm-への接続)
  - [3-6. 対応プロバイダー一覧](#3-6-対応プロバイダー一覧)
  - [3-7. 関連する環境変数](#3-7-関連する環境変数)
  - [3-8. Reranker（再ランク付け）プロバイダー](#3-8-reranker再ランク付けプロバイダー)
- [4. MCP で外部ツールから使う](#4-mcp-で外部ツールから使う)
  - [4-1. MCP とは](#4-1-mcp-とは)
  - [4-2. Cynovela が公開する MCP ツール（全 25 件）](#4-2-cynovela-が公開する-mcp-ツール全-25-件)
  - [4-3. LM Studio からの接続](#4-3-lm-studio-からの接続)
  - [4-4. MCP サーバーを動かす Python](#4-4-mcp-サーバーを動かす-python)
  - [4-5. 認証の注意](#4-5-認証の注意)
  - [4-6. トラブルシューティング](#4-6-トラブルシューティング)
- [5. LAN で分け合う](#5-lan-で分け合う)
  - [5-1. 既定の動作](#5-1-既定の動作)
  - [5-2. LAN 共有モード](#5-2-lan-共有モード)
  - [5-3. Tailscale 共有モード](#5-3-tailscale-共有モード)
  - [5-4. セキュリティ上の注意](#5-4-セキュリティ上の注意)
  - [5-5. 関連する起動フラグまとめ](#5-5-関連する起動フラグまとめ)
- [6. backup と restore](#6-backup-と-restore)
  - [6-1. 既定の保存場所](#6-1-既定の保存場所)
  - [6-2. `store/` に入っているもの](#6-2-store-に入っているもの)
  - [6-3. 手動バックアップ](#6-3-手動バックアップ)
  - [6-4. 復元](#6-4-復元)
  - [6-5. 注意点](#6-5-注意点)
  - [6-6. アプリで取る控え（`backup create`）と、その置き場](#6-6-アプリで取る控えbackup-createとその置き場)
  - [6-7. store を丸ごと控える（推奨）](#6-7-store-を丸ごと控える推奨)
  - [6-8. store の写しから戻す（Cynovela を止めた状態で行う）](#6-8-store-の写しから戻すcynovela-を止めた状態で行う)
  - [6-9. アプリで取った控えから戻す（Cynovela を止めた状態で行う）](#6-9-アプリで取った控えから戻すcynovela-を止めた状態で行う)
  - [6-10. 別の Mac へ移す](#6-10-別の-mac-へ移す)
- [7. ログ](#7-ログ)
  - [7-1. ログレベル](#7-1-ログレベル)
  - [7-2. Request ID](#7-2-request-id-1)
  - [7-3. Preflight ログ](#7-3-preflight-ログ)
  - [7-4. サーバーログを流しながら見る](#7-4-サーバーログを流しながら見る)
- [8. 監査ログの Export](#8-監査ログの-export)
  - [8-1. 監査ログとは](#8-1-監査ログとは)
  - [8-2. 改ざん防止](#8-2-改ざん防止)
  - [8-3. GUI からの参照](#8-3-gui-からの参照)
  - [8-4. API 経由](#8-4-api-経由)
  - [8-5. SQLite から直接抽出](#8-5-sqlite-から直接抽出)
- [9. 利用者の管理](#9-利用者の管理)
  - [9-1. ロール](#9-1-ロール)
  - [9-2. 初期 admin](#9-2-初期-admin)
  - [9-3. 出荷 demo.db のログイン情報](#9-3-出荷-demodb-のログイン情報)
  - [9-4. ユーザー追加・削除・パスワード変更](#9-4-ユーザー追加削除パスワード変更)
  - [9-5. ロール別の保管庫アクセスとマスキング](#9-5-ロール別の保管庫アクセスとマスキング)
  - [9-6. 認証](#9-6-認証)
- [10. 健全性の確認と監視](#10-健全性の確認と監視)
  - [10-1. 主要なヘルスエンドポイント](#10-1-主要なヘルスエンドポイント)
  - [10-2. Publish 履歴](#10-2-publish-履歴)
  - [10-3. サーキットブレーカー](#10-3-サーキットブレーカー)
- [11. 通知（メール）](#11-通知メール)
- [12. ポートを変える](#12-ポートを変える)
  - [12-1. ポートとアクセス制御](#12-1-ポートとアクセス制御)
  - [12-2. ポート番号の変更](#12-2-ポート番号の変更)
- [13. 運用上の注意](#13-運用上の注意)

## 1. 通常の起動と停止

### 1-1. 起動

```bash
# 入口は launch.sh です
./launch.sh --demo
```

手で起動する場合（専用の環境名は `cynovela-dist`。共有の環境は作らない・書き換えないでください）:

```bash
conda activate cynovela-dist
python server.py --demo
```

オプションの詳細は 2-3「起動フラグ一覧」を参照してください。

### 1-2. 停止

ターミナル上で `Ctrl + C` を 1 回送信します。FastAPI / Uvicorn のシャットダウンフックが走り、進行中の Publish ジョブ（SSE 経路）には停止リクエストが伝達されます。

### 1-3. バックグラウンド起動

`nohup` や `tmux` / `screen` などのターミナル多重化ツールで常駐させることもできます。

```bash
nohup python server.py --demo > ~/cynovela.out 2>&1 &
```

---

## 2. 入れ方・置き方

### 2-1. 動作確認済み環境

Cynovela は個人検証用のツールであり、動作確認している環境は限定的です。以下を参考にしてください。

| 項目 | 確認済みの内容 |
|------|------------|
| OS | macOS（Apple Silicon） |
| Python 実行系 | conda（Miniforge） |
| ローカル LLM | LM Studio（OpenAI 互換 `/v1` API） |
| Embedding | BAAI/bge-m3、paraphrase-multilingual-MiniLM-L12-v2、paraphrase-MiniLM-L3-v2、TF-IDF |

Windows / Linux / Docker 環境での動作は確認していません。GPU 利用時の詳細（CUDA バージョン、メモリ目安）も確認していません。

### 2-2. 環境セットアップ

**推奨は `./launch.sh` です** — 初回に専用の場所へ環境を作ります。共有の conda 環境は作りません・書き換えません。

#### 2-2-1. 手で環境を作る場合（launch.sh を使えないときのみ）

配布物専用の名前 `cynovela-dist` を使ってください。共有の環境は作らない・書き換えないでください。

```bash
conda create -n cynovela-dist python=3.12 -y
conda activate cynovela-dist
```

#### 2-2-2. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

主要な依存:

| ライブラリ | 用途 |
|----------|------|
| FastAPI | API サーバー本体 |
| Uvicorn | ASGI サーバー |
| SQLite（標準同梱） | メタデータ・監査ログ・チャンク保存 |
| ChromaDB | ベクター検索 |
| cryptography（Fernet） | raw 本文の暗号化 |
| huggingface_hub | モデルダウンロード |
| BM25Okapi | キーワード検索 |
| fugashi / MeCab | 日本語形態素解析（BM25 トークン化） |

### 2-3. 起動フラグ一覧

`python server.py` に渡せる全フラグです。

| フラグ | 型 | 既定値 | 説明 |
|--------|-----|------|------|
| `--demo` | bool | False | デモのデータベース `store/db/demo.db` とインデックス `store/vector/demo/chroma` を使って起動。付けなければ本番の `store/db/cynovela.db` と `store/vector/default/chroma`。どちらも再起動では消えません |
| `--lmstudio-url` | str | `http://localhost:1234` | LM Studio のベース URL |
| `--mode` | str | `text` | 起動モード（`full` / `text` / `lite` / `lite-en` / `minimal`） |
| `--host` | str | `0.0.0.0` | バインドアドレス（既定は全アドレス。絞るのは `--local-only`） |
| `--lan` | bool | False | LAN 公開（host=0.0.0.0 を明示） |
| `--port` | int | `8765` | ポート番号 |
| `--local-only` | bool | False | 自マシン内だけに絞る（`host=127.0.0.1` で待ち受け） |
| `--allow-tailscale` | bool | False | Tailscale ネットワークからのアクセス許可 |
| `--reset-admin` | bool | False | 管理者パスワードをリセットして表示し終了（デモを直すときは `--demo` を併記） |
| `--ingest PATH` | str（複数指定可） | なし | 取り込み元として許可するフォルダ |
| `--allow-subnet` | list | `[]` | 許可するサブネット（複数指定可） |

#### 2-3-1. よく使う組み合わせ

```bash
# 通常起動（LM Studio 必要）
python server.py --demo

# LAN 共有 + Tailscale
python server.py --demo --lan --allow-tailscale

# 表示名を変えて起動する例（動作は text と同じ・切替は未配線）
python server.py --demo --mode lite
```

> **PII 検出モード**: `--pii-mode` は CLI 引数として廃止されました。`cynovela.yaml` の `pii_mode` キー（`lite` / `standard` / `quality`）で指定します。

### 2-4. `--mode` 選択ガイド

起動モードによって Embedding と Reranker の構成が変わります。

#### 2-4-1. モデルサイズ比較表

| `--mode` | Embedding モデル | サイズ目安 | Reranker | 推奨環境 |
|--------|---------------|---------|---------|---------|
| `text`（既定） | BAAI/bge-m3 | 約 2.3GB | 設定で選択可（`reranker.provider`） | GPU 不要・汎用 |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — | — |

#### 2-4-2. 選び方の目安

- 一般的な日本語 RAG: `text`

#### 2-4-3. Provider 配線の優先順位

2. `cynovela.yaml` の `reranker.provider` の指定（`cross_encoder` / `flashrank` / `mlx` / `http` / `none` ほか）
3. 旧来の `rag.reranker_enabled` + `reranker_url` は `http` 経路として吸収

### 2-5. 初回モデルダウンロード手順

#### 2-5-1. Preflight チェック

`--mode minimal` でない場合、起動時に必要モデルの存在を確認します。

スキップ条件:

- `--mode minimal`
- そのモードの必要モデルリストが空

#### 2-5-2. 不足時のプロンプト

不足モデルがあると、対話プロンプトが表示されます。

```
[1] 今すぐダウンロードして起動する
[2] 代替モードで起動する（例: text / lite / minimal）
[3+] キャンセル
```

| 選択 | 動作 |
|------|------|
| `[1]` | HuggingFace Hub から `~/.cynovela/models/` 配下にダウンロード |
| `[2]` | 代替モードを提示（`full → text → lite → lite-en → minimal` の順） |
| `[3+]` | 起動キャンセル |

#### 2-5-3. 非対話環境での起動中止

CI などで対話プロンプトを出したくない場合は、環境変数 `CYNOVELA_NONINTERACTIVE=1` を設定します。モデル不在時は即座に終了します。

```bash
CYNOVELA_NONINTERACTIVE=1 python server.py --mode text
```

#### 2-5-4. 保存先

- ダウンロード先: `~/.cynovela/models/`
- 命名規則: HuggingFace のリポジトリ名のスラッシュを `__` に置換（例: `BAAI__bge-m3`）

#### 2-5-5. モデルパスの上書き

OneDrive 等のクラウド同期の下にモデルを置くことは勧めません（同期が実体を退避すると読み込みが失敗します）。同期の外の別の場所を `cynovela.yaml` の `models` セクションで指す使い方は可能です。

```yaml
models:
  embedding:
    path: "/path/to/bge-m3"
    name: "BAAI/bge-m3"
  reranker:
    path: ""
    name: "BAAI/bge-reranker-v2-m3"
```

### 2-6. 主要な環境変数

機密情報は `cynovela.yaml` に直書きせず、環境変数で渡すことを推奨します。

#### 2-6-1. データ・パス

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_DB` | SQLite DB パス（既定は `~/.cynovela/db/...`） |
| `CYNOVELA_CHROMA` | ChromaDB ディレクトリ |
| `CYNOVELA_BACKUP_DIR` | バックアップディレクトリ |
| `CYNOVELA_LOG_DIR` | ログディレクトリ |
| `CYNOVELA_DATA_DIR` | アプリデータルート |

#### 2-6-2. LLM / Embedding / Reranker

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_LLM_BASE_URL` | LLM ベース URL |
| _(環境変数なし)_ | LLM API キーは設定UIで入力（このセッションのみ保持・保存しない） |
| `CYNOVELA_LLM_MODEL` | LLM モデル名 |
| `CYNOVELA_LLM_PROVIDER` | LLM プロバイダー |
| `CYNOVELA_LLM_MAX_CONCURRENT` | LLM 同時実行数上限 |
| `CYNOVELA_EMBEDDING_PROVIDER` | Embedding プロバイダー |
| `CYNOVELA_EMBEDDING_MODEL` | Embedding モデル名 |
| `CYNOVELA_EMBEDDING_BASE_URL` | Embedding ベース URL |
| `CYNOVELA_EMBEDDING_API_KEY` | Embedding API キー |
| `CYNOVELA_RERANKER_API_KEY` | Reranker API キー |
| `CYNOVELA_CLASSIFIER_API_KEY` | 分類器 API キー |

#### 2-6-3. 運用

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_NONINTERACTIVE` | `1` で Preflight 対話をスキップして即終了 |
| `CYNOVELA_DISABLE_RATE_LIMIT` | レートリミット無効化 |
| `CYNOVELA_MAX_UPLOAD_BYTES` | ファイルアップロード最大サイズ（既定 100MB） |
| `CYNOVELA_MCP_PYTHON` | MCP サーバー実行用 Python パス |
| `CYNOVELA_SECRET_KEY` | Fernet 暗号化鍵（本番推奨） |

#### 2-6-4. 初期化

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_ADMIN_INITIAL_PASSWORD` | 初回起動時の admin パスワード |
| `CYNOVELA_ADMIN_USERNAME` | 初回起動時の admin ユーザー名（既定: `cynovela`） |
| `CYNOVELA_SMTP_PASSWORD` | SMTP パスワード |

### 2-7. 起動フロー全体図

```
main() 呼び出し
  ↓
argparse で CLI 引数パース
  ↓
Preflight チェック（必要モデルの存在確認）
  ├─ モデル不足 → ユーザー選択（DL / 代替 mode / キャンセル）
  └─ 戻り値 False なら起動中止
  ↓
LLM アダプター取得
  └─ それ以外 → LM Studio など
  ↓
AppConfig 構築（mode / demo / mock 反映）
  ↓
cynovela.yaml 読み込み
  ├─ CYNOVELA_* 環境変数で上書き
  └─ CircuitBreaker / Semaphore 初期化
  ↓
Provider 配線（Embedding / Reranker）
  ↓
PII 検出モード設定（yaml.pii_mode）
  ↓
DB 初期化（--demo なら store/db/demo.db、付けなければ store/db/cynovela.db）
  ↓
Uvicorn で FastAPI 起動
```

### 2-8. 外部の推論サーバを立てる

本配布物 (ホスト直起動版) は `./launch.sh` で Mac のホスト上に直接立ち上がります。
コンテナはありません。

- **埋め込みは既定でこのアプリ自身が Mac の GPU (MPS) で回します。** 外部の推論サーバは要りません。
- **再ランクだけは既定で外部の推論サーバを呼びます** (`cynovela.yaml` の `reranker.device: external`)。
  外部の推論サーバが居なければアプリ内の同じモデルへ自動で退避するので、立てなくても動きます。

つまり外部の推論サーバは「必須」ではなく、**再ランクを外へ出す / 複数の Mac で 1 台に推論を寄せる**
ときに立てるものです。回答用 LLM (LM Studio 等) を別に立てるのと同じ考え方です。

#### 2-8-1. 外部の推論サーバの立て方

外部の推論サーバを動かすには、`torch` / `sentence-transformers` / `fastapi` / `uvicorn` の4件が入った
python が要ります。**裸の `python` にはこの4件が入っていないことがほとんどです。**
アプリ本体を動かす環境 (conda の `cynovela-dist`、ソース版の `.venv-cynovela`、
またはパッケージ版に同梱の `.condapack-cynovela`) とは別に、
外部の推論サーバ用の場所をこの配布物の中に作ってから立ててください。

```bash
# アプリと同じ Mac のホスト側で。まず、この配布物のフォルダへ移動します。
cd<この配布物のフォルダ>

# (1) 外部の推論サーバを動かす場所を、この配布物の中に作る。どちらか一方を選びます。
#     conda を使う場合 (共有の環境ではなく、場所を指定して作ります)
conda create -y -p .mas-env python=3.12
#     venv を使う場合 (3.10 以上の python3 を指定してください)
python3.12 -m venv .mas-env

# (2) 部品を入れる
.mas-env/bin/python -m pip install -r mas/mas-requirements.txt

# (3) 立てる
.mas-env/bin/python mas/mas_server.py --preload
```

既に4件が入っている python をお持ちの場合は、(1) と (2) を飛ばし、その python で (3) を
行ってください。確かめ方: `<その python> -c 'import torch, sentence_transformers, fastapi, uvicorn'`

`.mas-env` はこの配布物の中だけに作られます。**conda の共有の環境 (envs) には何も書きません。**
入れる部品は `mas/mas-requirements.txt` に書いた4件です。本体アプリ用の `requirements.txt`
(39件) や `environment.yml` は、外部の推論サーバを立てる目的には使いません。

- 既定で `127.0.0.1:18850` に立ちます (変更は `mas/mas.yaml` の server.host / server.port)。
- 確認: `curl http://127.0.0.1:18850/health` が `"status":"ok"` を返せば稼働。
  再ランクまで使うなら同じ応答に `"reranker_loaded":true` が出ていること (0.2.0 以降)。
- `curl http://127.0.0.1:18850/capabilities` で モデル名・版 (revision)・デバイス (mps/cpu) が見えます。
- アプリと外部の推論サーバは**同じ Mac の中で 127.0.0.1 越し**に話します。アプリはコンテナの中に
  居ないので `host.containers.internal` のような読み替えは不要です。

#### 2-8-2. モデルは bge-m3 / bge-reranker-v2-m3 の「配布物と同一の版」を使うこと

- 埋め込みモデル: **BAAI/bge-m3、snapshot 版 `5617a9f61b028005a4858fdac845db406aefb181`**
- 再ランクモデル: **BAAI/bge-reranker-v2-m3**
- **版が違うとベクトルの数値が変わり、同梱済みのベクターコレクションと混ざって検索順位が壊れます。**
- 保存先: この配布物の `store/models/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181/` (HF キャッシュ形式)。
  `store/models` 配下では、この形以外の場所に置かないでください。
  `mas/mas.yaml` の `models.embedding.path` が `''` のときは、アプリと同じこの場所から
  読み取り専用で解決します。別の場所に置いたときだけパスを書いてください。
- 万一版が違う場合、起動時とpublish時に「ベクターコレクションの埋め込み識別と現在の経路が
  食い違っています」と **画面とログに明示的に警告**が出ます。
  警告が出たら版を揃えるか全再構築してください。

#### 2-8-3. 呼び先の指定の書き方

`cynovela.yaml` の既定 (再ランクだけ外へ出す):

```yaml
reranker:
  provider: cross_encoder
  model: BAAI/bge-reranker-v2-m3
  device: external                 # external = 外部の推論サーバへ出す / cpu / mps = アプリ内で回す
  base_url: http://localhost:18850
  top_n: 5

embedding:
  provider: local                  # 既定はアプリ内。外へ出すなら openai_compat
  device: mps                      # local_cpu / mps / external_accelerator
  model: BAAI/bge-m3
  base_url: ''
```

埋め込みも外部の推論サーバへ出したい場合 (推論を別の Mac 1 台に寄せる等):

```yaml
embedding:
  provider: openai_compat
  device: external_accelerator
  model: BAAI/bge-m3
  base_url: http://127.0.0.1:18850   # 別の Mac なら その Mac の IP:18850
```

ポートを変えた場合は base_url を合わせてください。管理画面 (設定 > Embedding) からも変更できます。

**別の Mac へ出す場合の注意**: アプリの外へ文字が出ることになるため、外部の推論サーバ側の
`mas/mas.yaml` で `policy.allow_raw_content: false` にして、マスキング済みのものだけを
受け付ける形にしてください。

#### 2-8-4. 口が居ないときの振る舞い

- 再ランク: 外部の推論サーバに届かない場合、**アプリ内のモデル (store/models) での処理へ退避**します
  (本配布物は全部入りで、再ランクのモデルを同梱しています)。再ランクのモデルを置いていない
  場合は、再ランクを行わず検索結果をそのまま返します。どちらの場合も処理は止まりません。
- 埋め込み (外へ出す設定にしたときのみ): 届かない場合は**アプリ内のローカル処理へ明示的に退避**し、
  管理画面 (設定 > Embedding) に **「⚠️ 外部の推論サーバに届かないためローカルへ退避中」** と表示されます。
  黙って遅くなることはありません。口を立て直せば次回の埋め込みから自動復帰します。

#### 2-8-5. 稼働確認のしかた

1. 外部の推論サーバ: `curl http://127.0.0.1:18850/health` → `"status":"ok"` (再ランクを使うなら
   `"reranker_loaded":true` も)
2. `./launch.sh` でアプリを起動 → 管理者でログイン
3. 質問を 1 回投げる → 外部の推論サーバの `curl http://127.0.0.1:18850/metrics` で
   `rerank_requests` が増えていれば、再ランクは外部の推論サーバ (MPS) で実行されています
4. 埋め込みも外へ出す設定にした場合は、資料を 1 本取り込み (publish) して
   同じ `/metrics` の `embeddings_texts` が増えることを確認してください
   (既定の `provider: local` のままなら増えません。これは正常です)

補足: 画像の口は将来用の入口のみで未実装 (呼ぶと 501) のままです。

---

## 3. LLM プロバイダーを繋ぐ

Cynovela は外部の LLM（大規模言語モデル）サーバーに HTTP 経由で接続して回答生成を行います。この節では、代表的な接続方法と切り替え手順を説明します。

### 3-1. 接続アーキテクチャ

Cynovela の LLM 接続層（`llm_adapter.py`）は、OpenAI 互換の `/v1/chat/completions` エンドポイントを持つ任意のサービスに接続できる設計です。`LMStudioAdapter`（OpenAI 互換アダプター）を主軸として、URL を差し替えることで複数のローカル LLM ランナーに対応します。

```
Cynovela サーバー
  ↓ HTTP POST /v1/chat/completions
LLM ランナー（LM Studio / Ollama / vLLM 等）
  ↓ ストリーム応答
Cynovela サーバー（ガードレール → ユーザーへ返却）
```

### 3-2. 画面から設定する

同梱の既定は **LM Studio** です（`cynovela.yaml` の `llm.provider: lmstudio` /
`llm.base_url: http://localhost:1234`）。まずはこの既定のまま使ってください。

#### 3-2-1. LM Studio を使う場合（既定・推奨）

1. LM Studio を起動し、**チャット用（生成用）のモデルをロード**する。
2. LM Studio の「Developer」タブでローカルサーバーを開始する（既定ポート 1234）。
3. Cynovela の左メニュー **Settings > LLM Provider** を開き、
   - Provider: `LM Studio`
   - Base URL: `http://localhost:1234`（本形態はホストから直接起動するため localhost）
   - Model: **「📋 モデル一覧を取得」を押し、一覧から実在するチャット用モデルを選ぶ**
4. 「🔌 接続テスト」で成功を確認し、「💾 LLM設定をまとめて適用」で保存する。

**Model を空欄（`auto`）のままにしないでください。**
モデル名が未指定のときは LM Studio が返すモデル一覧の**先頭**が使われます。
先頭が埋め込み専用モデル（bge-m3 等）だと生成要求が拒否され、回答が返らず
エラー（HTTP 400）になります。一覧から**チャット用モデル**を選べば解消します。
（2026-07-29 実測: モデル名を実在のチャット用モデルに変えるだけで回答が成立。
Base URL の末尾に `/v1` を付けるかどうかは結果に影響しません。）

・LM Studio は、読み込んでいないモデルの名前を指定しても断らず、
  読み込み済みの別のモデルで答えることがあります。Model 欄には、
  一覧から選んだ実在のモデル名を入れてください。
・LM Studio で大きなモデルを同時にいくつも動かすと、回答が崩れたり
  遅くなったりすることがあります。時間が経つと自動で元に戻ります。

#### 3-2-2. Ollama を使う場合（既定ではありません）

Ollama でも動きますが、同梱の既定構成ではありません。使う場合のみ次の手順です。

```bash
# 使いたいチャット用モデルを取得する（モデル名は任意。以下は一例）
ollama pull qwen3:8b
```

Settings > LLM Provider で Provider: `Ollama`、Base URL: `http://localhost:11434`、
Model は **`ollama list` に出るモデル名**をそのまま入力します
（LM Studio と同じく、実在するチャット用モデル名を必ず指定）。

**注意**: LM Studio と Ollama を同時使用する場合はメモリに注意。
切り替え時はLM Studioのモデルをアンロードしてから切り替えることを推奨。

### 3-3. LM Studio との接続

LM Studio はデスクトップ向けの GUI 付き LLM ランナーです。Cynovela の既定接続先になっています（`llm.provider: lmstudio`）。Cynovela は `/v1` 互換 API を持つ任意のサービスにも接続できます。

#### 3-3-1. 起動時オプション

```bash
python server.py --lmstudio-url http://localhost:1234
```

`--lmstudio-url` は省略可能で、既定値は `http://localhost:1234` です。

#### 3-3-2. LM Studio 側の準備

1. LM Studio を起動して任意のモデル（例: 日本語対応モデル）をロードします。
2. 「Local Server」タブで OpenAI 互換 API を有効化し、ポート 1234 で待ち受け状態にします。
3. Cynovela サーバーを起動すると、`/v1/chat/completions` 経由で接続されます。

#### 3-3-3. URL 正規化の挙動

LLM アダプターは URL 末尾の `/` および `/v1` を自動的に除去して正規化します。以下はいずれも同じ接続先として扱われます。

- `http://localhost:1234`
- `http://localhost:1234/`
- `http://localhost:1234/v1`

#### 3-3-4. `cynovela.yaml` での設定例

```yaml
llm:
  provider: lmstudio
  base_url: http://localhost:1234
  api_key: ""
  model: ""
  max_concurrent: 3
  timeout_seconds: 120
```

> **重要**: LM Studio API には `max_tokens` を渡さないでください。Reasoning モデルで思考用トークン予算が枯渇する原因となります。

### 3-4. Ollama との接続

Ollama は CLI 中心のローカル LLM ランナーです。OpenAI 互換 API を提供しているため、`--lmstudio-url` に Ollama の OpenAI 互換エンドポイントを指定するだけで接続できます。

#### 3-4-1. 起動例

```bash
python server.py --lmstudio-url http://localhost:11434
```

#### 3-4-2. Reranker としての Ollama 利用

Ollama は LLM 推論だけでなく、Reranker（再ランク付け）プロバイダーとしても接続できます。`cynovela.yaml` で次のように設定します。

```yaml
reranker:
  provider: ollama
  base_url: http://localhost:11434
  model: bge-reranker-v2-m3
```

#### 3-4-3. `openai_compat` 経由の Ollama / OpenRouter / vLLM

`llm.provider` を `openai_compat` にすると、LM Studio 以外の OpenAI 互換エンドポイント（vLLM、Ollama の `/v1` 互換ゲートウェイなど）に切り替えられます。

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:11434/v1   # 例: Ollama
  model: llama3
```

### 3-5. リモートマシン上の LLM への接続

LM Studio / Ollama を別マシンで動かして、Cynovela からネットワーク経由で接続することもできます。これは GPU を別マシンに集約したい場合に有用です。

```bash
python server.py --lmstudio-url http://192.168.1.50:1234
```

接続先マシン側で、LM Studio または Ollama を「すべてのインターフェイス」で待ち受けるよう設定しておく必要があります。

> **セキュリティ上の注意**: LLM 通信は HTTP 平文です。LAN 外への公開は推奨しません。Tailscale などの VPN 経由で接続することを推奨します。

> **CRAG 下読みの egress 封鎖（crag-egress-guard）**: リモート／非ローカルの LLM エンドポイントを指定した場合、CRAG（自己修正 RAG）の下読み（`context_preview`）は外部へ送出されません。送信前にエンドポイントがローカルかを判定し、非ローカル（判定不能を含む）なら下読みを送らず CRAG をスキップします。これにより admin であっても raw 本文の断片が外部 LLM へ漏れることを防ぎます。ローカル LLM（LM Studio / Ollama をローカルで実行）では従来どおり CRAG が有効です。

### 3-6. 対応プロバイダー一覧

`cynovela.yaml` の `llm.provider` キーで切り替えます。

| プロバイダー | 値 | 説明 |
|---|---|---|
| LM Studio | `lmstudio` | LM Studio の OpenAI 互換 API へ接続（既定） |
| OpenAI 互換（汎用） | `openai_compat` | OpenAI 互換 `/v1` API を持つ任意のサービス（vLLM / OpenRouter / Ollama 等） |
| モック | `mock` | LLM を呼び出さず、固定文字列を返す（テスト用） |

#### 3-6-1. OpenAI 互換接続の設定例

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:8000
  model: meta-llama/Llama-3-8B-Instruct
  api_key: ""          # 設定UIで入力（このセッションのみ保持・保存しない）
  max_concurrent: 3
  timeout_seconds: 120
```

#### 3-6-2. `mock` プロバイダーと、撤去された `--mock`

以前あった `--mock`（LLM を全く呼び出さない検証モード）は起動フラグとしては撤去済みです。いま指定するとエラーで止まります。`cynovela.yaml` の `llm.provider` の値としての `mock` は残っており、LLM を呼び出さず固定文字列を返します。

モデルが要らない起動は `--mode minimal` です。このモードでは Embedding（埋め込み）も TF-IDF（語彙頻度ベースの軽量埋め込み）に切り替わり、外部モデルのダウンロードも発生しません。RAG（検索拡張生成）の品質確認には適しませんが、UI とフロー検証には有用です。

### 3-7. 関連する環境変数

LLM 接続関係で使用できる主な環境変数は以下です。

| 環境変数 | 用途 |
|---|---|
| `CYNOVELA_LLM_BASE_URL` | LLM ベース URL を上書き |
| _(環境変数なし)_ | LLM API キーは設定UIで入力（このセッションのみ保持・保存しない） |
| `CYNOVELA_LLM_MODEL` | LLM モデル名（OpenAI 互換時のみ使用） |
| `CYNOVELA_LLM_PROVIDER` | LLM プロバイダー名 |
| `CYNOVELA_LLM_MAX_CONCURRENT` | 同時実行数の上限 |

### 3-8. Reranker（再ランク付け）プロバイダー

LLM とは別に、検索結果の並び替えを担う Reranker も差し替え可能です。`cynovela.yaml` の `reranker.provider` で指定します。

| プロバイダー | 値 | 説明 |
|---|---|---|
| 無効 | `none` | Reranker を使わない |
| CrossEncoder | `cross_encoder` | ローカルの CrossEncoder モデル（既定の高品質構成） |
| FlashRank | `flashrank` | 軽量 Reranker ライブラリ |
| MLX | `mlx` | Apple Silicon 向けの骨格実装（実体は将来対応） |
| Ollama | `ollama` | Ollama 経由の Reranker |
| HTTP | `http` | 任意の HTTP エンドポイント |

---

## 4. MCP で外部ツールから使う

Cynovela は MCP（Model Context Protocol、Anthropic が提唱する AI ツール連携プロトコル）の MCP サーバーとして自身の機能を外部の LLM クライアントへ公開できます。この節では MCP の概念と Cynovela が公開している MCP ツール、接続手順を説明します。

サーバー（`mcp_server.py`）はプロトコル版 **2026-07-28** を stdio で実装しています: `server/discover` に応え（握手もセッション ID も要求しません — 旧世代クライアントの `initialize` にも応えます）、道具の入出力を JSON Schema 2020-12 で宣言し、結果を平文に加えて `structuredContent` で構造化して返します。対象の資料が無いときは JSON-RPC エラー `-32602` を返します。

### 4-1. MCP とは

MCP は、AI アシスタント（クライアント）が外部システムの機能（ツール）を呼び出すための標準プロトコルです。

- **クライアント**: LM Studio や対応する LLM クライアントなど、ユーザーが対話する側
- **サーバー**: 機能を提供する側（Cynovela がここに該当）
- **ツール**: サーバーが公開する操作（検索、登録、参照など）

MCP を使うと、ユーザーが LLM クライアントに「うちの社内文書を検索して」と話しかけたときに、LLM が Cynovela の検索ツールを呼び出し、結果を踏まえて回答を生成する、という連携が成立します。

### 4-2. Cynovela が公開する MCP ツール（全 25 件）

既定で見えるのは 22 件です。4-2-6 の管理系 3 件は既定で閉じており、MCP サーバの `env` に `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を書いたときだけ `tools/list` に現れます（4-5-5）。

#### 4-2-1. RAG 検索系（4 件）

##### `search_collection`

- **引数（必須）**: `query`, `workspace_id`, `collection_id`
- **引数（任意）**: `preset`
- **説明**: 単一の Collection（コレクション、文書群）に対して RAG 検索を行います。

##### `search_across_collections`

- **引数（必須）**: `query`, `workspace_id`, `collection_ids`
- **引数（任意）**: `preset`
- **説明**: 複数の Collection を横断して RAG 検索を行います。

##### `rag_with_role`

- **引数（必須）**: `query`, `workspace_id`, `collection_id`, `style_role`
- **引数（任意)**: `preset`
- **説明**: ロール別の回答スタイル（管理者向け / 一般ユーザー向けなど）を切り替えて RAG 検索します。

##### `rag_general`

- **引数（必須）**: `query`, `workspace_id`
- **説明**: RAG を使わず、LLM の一般知識のみで回答を生成します。社内文書に依存しない一般的な質問用です。

#### 4-2-2. 情報取得系（6 件）

##### `list_workspaces`

- **引数**: なし
- **説明**: 全ワークスペースとそのコレクション一覧を取得します。

##### `get_workspace_info`

- **引数（必須）**: `workspace_id`
- **説明**: 指定ワークスペースの詳細情報（名前、ガードレールポリシー、作成日時など）を返します。

##### `get_collection_info`

- **引数（必須）**: `workspace_id`, `collection_id`
- **説明**: コレクションの詳細（ドキュメント数、ステータス、アクセスレベル）を返します。

##### `get_audit_logs`

- **引数（必須）**: `workspace_id`
- **引数（任意）**: `limit`（既定 10、上限 50）
- **説明**: 監査ログ（チャット履歴、PII 検出、エラー）を取得します。

##### `list_sources`

- **引数（必須）**: `workspace_id`
- **説明**: ワークスペース配下のデータソース一覧（ファイルパス、ステータス、ファイル数）を返します。

##### `server_status`

- **引数**: なし
- **説明**: サーバの稼働と索引の状態（まとまりごとの塊の数）を見ます。

#### 4-2-3. 資料を入れる・進み具合（3 件）

##### `ingest_source`

- **引数（必須）**: `path`
- **引数（任意）**: `name`, `workspace_id`
- **説明**: 資料を入れます。取り込み元を足す→資料として登録する→走査を始める、を 1 道具で行います。走査は始めた時点で `job_id` を返してすぐ戻ります。進み具合は `get_job_status` で見ます。

##### `get_job_status`

- **引数（必須）**: `job_id`
- **説明**: 走査と公開の進み具合を見ます。`ingest_source` / `publish_collection` が返した `job_id` を渡します。

##### `cancel_scan`

- **引数（必須）**: `source_id`
- **説明**: 走行中の走査に中止を要求します。

#### 4-2-4. 公開と作成系（4 件）

##### `publish_collection`

- **引数（必須）**: `collection_id`
- **説明**: 指定コレクションの公開を始め、`job_id` を即座に返します — 終わるまで待ちません。進み具合は `get_job_status` で見ます。公開後は RAG 検索が可能になります。

##### `create_collection`

- **引数（必須）**: `workspace_id`, `name`
- **引数（任意）**: `source_id`
- **説明**: 作業場所の中にまとまり（コレクション）を作ります。`source_id` を渡すと、その資料の全ファイルを結び付けます。

##### `publish_control`

- **引数（必須）**: `collection_id`, `action`（`stop` / `recover`）
- **説明**: 走行中の公開を止める、または固着した公開から復旧します。

##### `create_workspace`

- **引数（必須）**: `name`
- **引数（任意）**: `description`
- **説明**: 新規ワークスペースを作成します。

#### 4-2-5. 設定系（5 件）

5 件とも**管理者**のトークンが必要です。API キーは書き込み専用で、応答には
設定あり / なし の bool（`api_key_set`）だけが載り、値は決して返しません。

##### `settings_show`

- **引数（任意）**: `name` — `llm`（既定）/ `reranker` / `classifier` / `embedding` / `pii` / `vector-store` / `datasync` のいずれか
- **説明**: 選んだ対象のいまの設定を見ます。

##### `settings_models`

- **引数**: なし
- **説明**: 設定された推論サーバの接続先にあるモデルの一覧を出します。注意: これは*ダウンロード済み*の一覧で、読み込み済みを意味しません。

##### `settings_test`

- **引数（任意）**: `provider`, `base_url`, `model`（渡すと保存済み設定の代わりにその値で試します）
- **説明**: LLM への接続を確かめ、通ったか通らなかったかを理由つきの言葉で返します。

##### `settings_set`

- **引数（必須）**: `values` — 変える項目だけを入れた object（例: `{"model": "..."}`）
- **引数（任意）**: `name` — `settings_show` と同じ選択肢（既定 `llm`）
- **説明**: 設定を変えます。**既定で閉じています**: MCP サーバのプロセスが環境変数 `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` 付きで起動されたときだけ実行されます（4-5-4）。閉じているときに呼ぶと、その旨を説明するエラー文が返り、何も実行されません。

##### `settings_providers`

- **引数**: なし
- **説明**: 選べる LLM プロバイダーのプリセット一覧を出します。

#### 4-2-6. 管理系（3 件）— 既定で閉

この 3 件は、MCP サーバの `env` に `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を書いたときだけ `tools/list` に現れます（4-5-5）。これは機能を削っているのではなく、直前に読んだ資料に引きずられた AI の暴発を止める仕掛けです。

##### `delete_item`

- **引数（必須）**: `kind`（`source` / `collection` / `workspace`）, `id`
- **説明**: 資料・まとまり・作業場所を消します。

##### `manage_users`

- **引数（必須）**: `action`（`list` / `create` / `update` / `delete` / `reset_password`）
- **引数（任意）**: `user_id`, `username`, `password`, `role`, `display_name`, `is_active`
- **説明**: 利用者を管理します（一覧・作成・変更・削除・パスワード再設定）。

##### `manage_backups`

- **引数（必須）**: `action`（`list` / `create` / `restore` / `delete`）
- **引数（任意）**: `name`, `label`
- **説明**: 控えを扱います（一覧・作成・復元・削除）。`restore` はいまのデータを控えの中身に置き換えます。反映にはサーバの再起動が要ります。

#### 4-2-7. 時間のかかる処理の使い方

走査（`ingest_source`）と公開（`publish_collection`）は、開始した時点で `job_id` を返してすぐ戻ります。進み具合は `get_job_status` に `job_id` を渡して繰り返し見ます。中止は、走査なら `cancel_scan`、公開なら `publish_control` の `stop` です。

### 4-3. LM Studio からの接続

LM Studio は MCP クライアント機能を備えており、設定ファイルで MCP サーバーを登録できます。

#### 4-3-1. 接続フロー

```
LM Studio（ユーザー対話）
  ↓ MCP プロトコル（標準入出力経由）
Cynovela MCP サーバー（mcp_server.py）
  ↓ HTTP API
Cynovela 本体（FastAPI サーバー）
```

#### 4-3-2. LM Studio の設定ファイルの場所

MCP の登録は、LM Studio のホームディレクトリにある `mcp.json` という 1 つの JSON
ファイルに書きます。macOS での位置（LM Studio 0.4.x での実測）:

- `~/.cache/lm-studio/mcp.json` — 開発機で実測した位置
- `~/.lmstudio/mcp.json` — LM Studio のホームが新しい既定のときの位置

どちらか迷う必要はありません: LM Studio の画面で右側の **Program** パネル →
**Install** → **Edit mcp.json** を開くと正しいファイルが開き、そこで保存すれば
ファイルを直接書いたのと同じになります。

#### 4-3-3. トークン（`CYNOVELA_TOKEN`）の取り出し方 — 最初から最後まで

1. Cynovela を起動し（`./launch.sh` または `./launch.sh --demo`）、`http://127.0.0.1:8765` が応答することを確かめます。
2. 画面のログインと同じ利用者名とパスワードで、サーバへトークンを頼みます:

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"<利用者名>","password":"<パスワード>"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
```

3. 出力された文字列がトークンです。次の手順の `mcp.json` の `env` に貼ります。
4. **トークンは、頼まないかぎり切れません。** ログインすると期限の無いトークンが渡されます。切れる形が欲しいときは、ログインの呼び出しに `expires_in_hours` を渡してください。道具の呼び出しが認証エラーで失敗しはじめたら、同じコマンドで新しいトークンを発行して `mcp.json` を書き替えてください。

注意: 設定系の道具（と他の管理系の道具）を使うには、ログインは**管理者**のアカウントで行います。閲覧者のトークンはサーバ側が 403 で拒否します。

#### 4-3-4. 設定例

`mcp.json` に以下を登録します（既に `mcpServers` がある場合は、その中へ合流させます）:

```json
{
  "mcpServers": {
    "cynovela": {
      "command": "/path/to/python",
      "args": [
        "/path/to/mcp_server.py",
        "--cynovela-url", "http://127.0.0.1:8765"
      ],
      "env": {
        "CYNOVELA_TOKEN": "<3-3 で取り出したトークン>"
      }
    }
  }
}
```

- `command`: Python 3.12 以上ならどれでも動きます。自然な選択は、この配布物が用意した Python です（4-4）。
- `settings_set` を許すときだけ、`env` に `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` を足します（4-5-4）。書かなければ設定は読み取り専用のままです。
- 管理系の 3 件（`delete_item` / `manage_users` / `manage_backups`）を出すときだけ、`env` に `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` を足します（4-5-5）。書かなければ 3 件はそもそも現れません。

#### 4-3-5. LM Studio が画面で許可を求めます — ここからは人の操作です

`mcp.json` への登録は最後の手順では**ありません**。LM Studio は手元の MCP の道具を、
自分の画面での明示的な人の同意の内側に置いています:

- **どこで**: チャットの中でモデルが Cynovela の道具をはじめて呼ぼうとしたとき、LM Studio がチャット画面に「この道具の呼び出しを許可するか」の確認ダイアログを出します（1 回ずつ、または道具ごとに常に許可）。サーバ自体の有効・無効は、`mcp.json` を編集したのと同じ **Program** パネルで切り替えられます。
- **許可を出した後**: 道具が実行され、結果（`structuredContent` 付き）がモデルへ渡ります — 以後 4-3-1 の流れが最後まで通ります。
- **許可を出さないと**: 登録そのものは成立して見える（パネルにサーバが並ぶ）のに、道具は一度も呼ばれません — これが「動かない」の一番よくある状態です。Cynovela 側の誤りではないので、LM Studio の画面で許可を出してください。

### 4-4. MCP サーバーを動かす Python

`mcp_server.py` は標準ライブラリのみで動きます — 外部依存が無いため、**Python 3.12 以上ならどれでも動きます**。環境のアクティブ化も要りません。自然な選択は、この配布物が用意した Python です（パッケージ版: `.condapack-cynovela/bin/python3`、ソース版の選択肢1: conda 環境 `cynovela-dist`）。

#### 4-4-1. Python パスの指定

環境変数 `CYNOVELA_MCP_PYTHON` で、`/api/mcp/config` のスニペットがクライアントへ示す Python の絶対パスを指定できます。

```bash
export CYNOVELA_MCP_PYTHON=/path/to/.condapack-cynovela/bin/python3
```

### 4-5. 認証の注意

#### 4-5-1. ベアラートークン

MCP サーバーは Cynovela 本体 API に対して `Authorization: Bearer<token>` ヘッダーで認証します。トークンはクライアント側の環境変数で渡します。

- 認証は `POST /api/auth/login` が発行する JWT です（手順は 4-3-3）。旧 `Bearer demo-token-<user_id>` 形式は廃止済みで受理しません。
- トークンは、ログインの呼び出しで期間（`expires_in_hours`）を渡さないかぎり切れません。要るときは同じ呼び出しで発行し直してください。

#### 4-5-2. ロール権限

MCP 経由の呼び出しも本体 API と同じロール（admin / curator / viewer）の権限チェックを通過します。特に `ingest_source` や `publish_collection`、`create_workspace` など書き込みを伴うツールは admin 権限を要する場合があり、設定系の 5 件はすべて admin 権限が必要です。

#### 4-5-3. 監査ログ

MCP 経由の操作も本体と同じ監査ログ（`audit_logs` テーブル）に記録されます。`get_audit_logs` で履歴を確認できます。

#### 4-5-4. 設定系の書き込みの守り（既定: 読み取りのみ）

設定系の道具は、読むものと書くものに分かれています:

- **読むもの**（`settings_show`・`settings_models`・`settings_test`・`settings_providers`）は、トークンが管理者のものであればいつでも動きます。追加のスイッチはありません。
- **書くもの**（`settings_set`）は**既定で閉じています**。MCP サーバのプロセスが環境変数 `CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1` 付きで起動されたときだけ実行されます — LM Studio では `mcp.json` の `env` にこの 1 行を足すことがそれに当たります（4-3-4）。閉じているときに呼ぶと、その旨を説明するエラー文が返り、何も実行されません。

理由: MCP の道具を呼ぶのは、直前に読んだ資料の中身に引きずられうる AI です。資料の中に「設定を書き換えろ」と書かれていれば、それを指示と受け取って実行する経路が原理的に存在します。∴ 書き込みには、クライアント側での人の明示的な判断を要します。この守りはサーバ側のロール検査の代わりでは*なく*、従来どおり動くその検査の手前に重ねる薄い層です。

#### 4-5-5. 管理系の道具の守り（既定: 見えない）

管理系の 3 件（`delete_item`・`manage_users`・`manage_backups`）は**既定で閉じています**。MCP サーバのプロセスが環境変数 `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` 付きで起動されたときだけ `tools/list` に現れ、実行できます — LM Studio では `mcp.json` の `env` にこの 1 行を足すことがそれに当たります（4-3-4）。理由は 4-5-4 と同じです: 削除・利用者管理・控えの復元は、直前に読んだ資料に引きずられた AI が独断で撃ってはならない操作そのものです。これは機能を削っているのではなく、人が明示的に入れる薄いスイッチです。サーバ側のロール検査は従来どおり動きます。

### 4-6. トラブルシューティング

| 症状 | 確認ポイント |
|---|---|
| ツールが見つからない | Cynovela 本体（`server.py`）が `http://127.0.0.1:8765` で起動済みか |
| LM Studio にサーバは並ぶのに道具が一度も呼ばれない | LM Studio の画面での人の許可がまだ出ていません — 4-3-5 を見てください。登録だけでは呼び出しは許可されません。チャット画面の確認ダイアログで許可を出します |
| 認証エラー | `CYNOVELA_TOKEN` 環境変数の値、トークンの有効性 — **トークンは、ログインで期間を渡さないかぎり切れません**。4-3-3 のログインの呼び出しで発行し直してください |
| `settings_set` が「書き込みは既定で閉じています」と答える | それは守り（4-5-4）であって故障ではありません。本当に書き込みたいときだけ `mcp.json` の `env` に `"CYNOVELA_MCP_ALLOW_SETTINGS_WRITE": "1"` を足します |
| `delete_item` / `manage_users` / `manage_backups` が一覧に出ない | それは守り（4-5-5）であって故障ではありません。本当に使いたいときだけ `mcp.json` の `env` に `"CYNOVELA_MCP_ALLOW_ADMIN_WRITE": "1"` を足します |
| ImportError が出る | Python が 3.12 以上か（`mcp_server.py` 自体に外部依存はありません） |
| 結果が空 | 対象 Collection が `ready` ステータスに到達済みか |

---

## 5. LAN で分け合う

Cynovela は既定で `0.0.0.0` で待ち受けます。つまり同じ LAN（ローカルネットワーク）内の他のマシンからは、追加のフラグ無しで到達できます（元仕様）。自分のマシンの中だけに閉じたい場合は `--local-only` を付けてください。Tailscale（VPN サービス）経由のアクセスや、アクセス元を絞りたい場合は、以下のフラグを使います。

### 5-1. 既定の動作

```bash
python server.py
```

- **バインドアドレス**: `0.0.0.0`（`--local-only` を付けたときだけ `127.0.0.1`）
- **アクセス可能なクライアント**: 既定では同じ LAN 内の他のマシンのブラウザ・CLI からも到達できます。`--local-only` を付けたときだけ、同じマシン上のブラウザ・CLI のみになります
- **外部から見ると**: `--local-only` を付けたときだけ、ポートが閉じているように見えます

`--local-only` を付けて運用すると、ネットワーク経由でのアクセスは原理的に発生しません。検証や個人利用にはこの構成が推奨です。

### 5-2. LAN 共有モード

同じ LAN 内の別マシンから Cynovela にアクセスしたい場合は `--lan` フラグを付けます。

#### 5-2-1. 起動コマンド

```bash
python server.py --lan
```

このフラグはバインドアドレスを `0.0.0.0`（すべてのインターフェイス）に切り替え、LAN 内の他のマシンから接続可能になります。

#### 5-2-2. 接続例

サーバー側マシンの LAN IP が `192.168.1.20` の場合、別マシンのブラウザから次のように接続します。

```
http://192.168.1.20:8765
```

#### 5-2-3. IP アローリスト

Cynovela には IP アローリスト機能があります。これは `--allow-subnet` / `--allow-tailscale` を渡したときだけ働き、どちらも渡さなければアクセス元を制限しません。働いているときは `127.0.0.1` と `localhost` は常に許可され、それ以外の接続元は明示的に許可する必要があります。`--allow-subnet` で接続元サブネットを追加できます。

```bash
python server.py --lan --allow-subnet 192.168.1.0/24
```

複数指定する場合は `--allow-subnet` を繰り返します。

```bash
python server.py --lan --allow-subnet 192.168.1.0/24 --allow-subnet 10.0.0.0/24
```

許可されていない接続元からのリクエストには HTTP 403 Forbidden を返します。

自分のマシンの中だけに閉じるには `--local-only` を付けます。

### 5-3. Tailscale 共有モード

Tailscale を使えば、自宅と外出先など離れたネットワーク間でも VPN 経由で接続できます。Cynovela は Tailscale サブネット（`100.64.0.0/10`）を自動的に許可する `--allow-tailscale` フラグを備えています。

#### 5-3-1. 前提

- Tailscale クライアントがサーバー側マシンにインストール・ログイン済みであること
- 接続元マシンも同じ Tailscale アカウントでログインしていること
- サーバー側で `tailscale ip -4` コマンドが Tailscale IP を返すこと

#### 5-3-2. 起動コマンド

```bash
python server.py --lan --allow-tailscale
```

#### 5-3-3. 動作

- 起動時に `tailscale ip -4` を実行して Tailscale 割り当て IP を検出します（タイムアウト 3 秒）。
- IP アローリストに `100.64.0.0/10` サブネットを自動追加します。
- Tailscale 経由のクライアントから接続できるようになります。

接続元の Tailscale 名や IP を表示するには、`tailscale status` を Tailscale クライアント側で実行してください。

### 5-4. セキュリティ上の注意

LAN 共有・Tailscale 共有は便利な反面、注意すべきリスクが複数あります。

#### 5-4-1. 通信は HTTP 平文

Cynovela 本体は HTTP で待ち受けています。HTTPS 化は組み込まれていないため、通信内容はネットワーク内で平文流通します。機密性の高い文書を扱う場合は次のいずれかを検討してください。

- Tailscale など暗号化された VPN 経由でのみアクセスする
- リバースプロキシ（nginx 等）で TLS を終端する

#### 5-4-2. インターネットへの直接公開は禁止

`0.0.0.0` でバインドしたままインターネット側に直接公開することは、認証の不完全さや暗号化の欠如を考慮すると、絶対に避けてください。

#### 5-4-3. 認証の制約

認証は JWT（`POST /api/auth/login` が発行）で、`--demo` 起動でも必要です。旧 `Bearer demo-token-<user_id>` 形式は廃止済みで受理しません。LAN 共有時は信頼できるユーザーのみがネットワーク上にいる前提で運用してください。

#### 5-4-4. ファイルアップロードの権限

LAN 内の任意のユーザーからファイルアップロードを受け付ける構成になり得るため、`/api/sources` の path 引数のバリデーションやアップロード上限の設定値（`CYNOVELA_MAX_UPLOAD_BYTES`、既定 100 MB）を必ず確認してください。

#### 5-4-5. 推奨構成

検証・学習用途であっても、以下のいずれかを推奨します。

- 完全ローカル: 何もフラグを付けず `127.0.0.1` のみで運用
- 個人 VPN: `--allow-tailscale` のみ付与、LAN への暴露は避ける
- 限定 LAN: `--lan --allow-subnet` で接続元を厳密に絞る

### 5-5. 関連する起動フラグまとめ

| フラグ | 既定 | 説明 |
|---|---|---|
| `--host` | `0.0.0.0` | バインドアドレス（既定は全アドレス。絞るのは `--local-only`） |
| `--port` | `8765` | ポート番号 |
| `--lan` | 無効 | `host=0.0.0.0` を明示してすべてのインターフェイスで待ち受け |
| `--allow-tailscale` | 無効 | Tailscale サブネット（`100.64.0.0/10`）を許可 |
| `--allow-subnet` | 空 | カスタムサブネットを追加（複数指定可） |

---

## 6. backup と restore

### 6-1. 既定の保存場所

Cynovela のデータは `~/.cynovela/` 配下に格納されます。

| 用途 | パス | 上書き用環境変数 |
|------|------|------------|
| SQLite DB（通常） | `~/.cynovela/db/cynovela.db` | `CYNOVELA_DB` |
| SQLite DB（demo） | `~/.cynovela/db/demo.db` | `CYNOVELA_DB` |
| ChromaDB（通常） | `~/.cynovela/vector/default/chroma` | `CYNOVELA_CHROMA` |
| ChromaDB（demo） | `~/.cynovela/vector/demo/chroma` | `CYNOVELA_CHROMA` |
| バックアップ | 配布物を展開したフォルダ配下の `store/backups` | `CYNOVELA_BACKUP_DIR` |
| モデル | `~/.cynovela/models` | （`cynovela.yaml.models.*.path` で個別指定可） |
| ログ | `~/.cynovela` | `CYNOVELA_LOG_DIR` |

> 上記はホスト（conda）版の保存場所です。ホスト版の実体は配布物を展開したフォルダ配下の `store/` です。コンテナ版では DB／ベクターは名前付きボリュームに格納され、取り込みの入口は起動時に渡した取り込み元（複数可）を `/app/ingest/<中の名前>` へ読み取り専用で bind します。既定の取り込みフォルダ `~/Cynovela` は廃止しました。

### 6-2. `store/` に入っているもの

`store/` には、取り込んだ資料の索引・データベース・設定・鍵が入っています。
通行証の署名鍵は、初回起動時にその機械で新しく作られます。

### 6-3. 手動バックアップ

サーバーを停止した状態で、上記ディレクトリをコピーします。

```bash
# サーバー停止後に実行
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/cynovela-backups/$TS
cp -R ~/.cynovela/db ~/cynovela-backups/$TS/db
cp -R ~/.cynovela/vector ~/cynovela-backups/$TS/vector
```

### 6-4. 復元

```bash
# サーバー停止後に実行
cp -R ~/cynovela-backups/20260526-093000/db ~/.cynovela/db
cp -R ~/cynovela-backups/20260526-093000/vector ~/.cynovela/vector
```

### 6-5. 注意点

- SQLite と ChromaDB は **必ず一緒にバックアップ・復元**してください。片方だけ復元すると `chunks` テーブルとベクター ID の整合性が崩れます。
- ソース／ワークスペース／コレクション削除では SQLite と ChromaDB の両方をクリーンアップする実装になっています。バックアップ運用でもこの「両方を同じスナップショット」原則を守ってください。
- `--demo` 起動は `db/demo.db` と `vector/demo/chroma` を、付けない本番起動は `db/cynovela.db` と `vector/default/chroma` を使います。どちらも起動のたびに消えることはなく、書いたものはそのまま残ります。取り違えないよう本運用と混ぜないでください。

### 6-6. アプリで取る控え（`backup create`）と、その置き場

```bash
python3 cynovela-cli.py backup create --yes          # 控えを取る
python3 cynovela-cli.py backup list                  # 取ってある控えを並べる
```

控えは、配布物を展開したフォルダ配下の `store/backups` へ書かれます（例: `store/backups/backup-20260821-225606`）。ホームフォルダの下には何も書きません。ひとつの控えのフォルダには、`cynovela.db`（実際に使われているデータベースの写し。控えの中の名前は `--demo` の有無によらず常に `cynovela.db` です）、`chroma` フォルダ、`meta.json` が入ります。

別の場所へ保管する場合は、その控えのフォルダを固め、指紋を控えておきます。

```bash
BK=store/backups/backup-20260821-225606
tar -czf <保存先>/$(basename $BK).tar.gz -C store/backups $(basename $BK)
shasum -a 256 <保存先>/$(basename $BK).tar.gz
```

### 6-7. store を丸ごと控える（推奨）

`python3 cynovela-cli.py backup create --yes` で控えを作れます。加えて、`store` フォルダを丸ごと `tar` で写しておいてください。控えだけでは戻すときに手で組み立てる作業が要りますが、`tar` の写しなら一手で戻せます。

```bash
bash stop.sh
tar -czf <保存先>/cynovela-store-$(date +%Y%m%d).tar.gz -C <Cynovela のフォルダ> store
./launch.sh
```

いちばん簡単な形は、フォルダを丸ごとそのまま写すことです（これも Cynovela を止めた状態で行ってください）:

```bash
# DBとChromaのバックアップ
cp -r store/ ~/cynovela-backup-$(date +%Y%m%d)/
```

### 6-8. store の写しから戻す（Cynovela を止めた状態で行う）

戻す操作は Cynovela を止めた状態で行ってください。動かしたまま戻さないでください。

```bash
bash stop.sh
mv store store.old            # いまの store を別の名前へ退ける
tar -xzf <保存先>/cynovela-store-YYYYMMDD.tar.gz
./launch.sh
```

画面や API から戻す口は使わないでください。理由: 動いている最中に土台を差し替えるため、応答が返らず、起動し直しが要るためです。 画面から戻す押しボタンは無くなりました。控えの一覧には、代わりにこの案内が出ます。API の口は残っていますが、同じ理由から使わないでください。

### 6-9. アプリで取った控えから戻す（Cynovela を止めた状態で行う）

```bash
bash stop.sh
BK=store/backups/backup-20260821-225606          # 戻したい控え
mkdir -p store/aside
mv store/db/demo.db store/aside/                 # データベースのファイルだけを退ける
mv store/db/demo.db-wal store/aside/ 2>/dev/null # その日誌も退ける（無いこともある）
mv store/db/demo.db-shm store/aside/ 2>/dev/null
mv store/vector/demo/chroma store/aside/chroma   # ベクターのフォルダだけを退ける
cp "$BK/cynovela.db" store/db/demo.db            # --demo を付けない場合は store/db/cynovela.db
cp -R "$BK/chroma" store/vector/demo/chroma      # --demo を付けない場合は store/vector/default/chroma
./launch.sh --demo
```

退けるのは、上のとおりデータベースのファイルとベクターのフォルダだけにしてください。`store/db` を丸ごと退けてはいけません。`store/db/jwt` の下には入り口の鍵が置かれており、控えはこれを含みません。丸ごと退けると鍵が失われ、起動のときに新しい鍵が作られ、全員が入り直すことになります。

日誌のファイル（`demo.db-wal` / `demo.db-shm`）は、データベースのファイルと一緒に退けてください。これらは差し替える前のデータベースのものです。残したままにすると、起動のときに復元したファイルへ書き戻され、戻したことが黙って打ち消されます。

戻したいものが戻ったことを確かめ、確かめてから、退けたものを消します。

```bash
python3 cynovela-cli.py workspaces
python3 cynovela-cli.py collections
rm -rf store/aside
```

### 6-10. 別の Mac へ移す

full-export でベクター込みの ZIP を作り、移した先で import します。移す先の埋め込みのモデルが、元と同じである必要があります。

```bash
# 元の Mac で（管理者トークンを $CYNOVELA_TOKEN に入れておく）
curl -s -H "Authorization: Bearer $CYNOVELA_TOKEN" \
  "http://127.0.0.1:8765/api/workspaces/<workspace_id>/full-export" \
  -o cynovela-migration.zip

# 移した先の Mac で（管理者トークンを $CYNOVELA_TOKEN に入れておく）
curl -s -H "Authorization: Bearer $CYNOVELA_TOKEN" \
  -F "file=@cynovela-migration.zip" \
  "http://127.0.0.1:8765/api/workspaces/import"
```

---

## 7. ログ

### 7-1. ログレベル

`cynovela.yaml` の `logging.level`（または `server.log_level`）で制御します。既定は `INFO` です。

```yaml
logging:
  level: INFO
  request_id: true   # 全リクエストに X-Request-ID を付与
```

### 7-2. Request ID

`request_id: true` を有効にすると、全 API レスポンスに `X-Request-ID` ヘッダーが付与されます。トラブルシュート時にクライアント側のリクエストとサーバー側ログを紐付けるのに使えます。

### 7-3. Preflight ログ

起動時の Preflight チェックでは、次のようなログが出力されます。

```
[Cynovela] PII detection mode: standard (from cynovela.yaml)
```

### 7-4. サーバーログを流しながら見る

```bash
# サーバーログ（リアルタイム）。デモで使う場合は --demo も付ける
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

---

## 8. 監査ログの Export

### 8-1. 監査ログとは

Cynovela は重要操作を SQLite の `audit_logs` テーブルに記録します。

主な記録対象:

- ワークスペース・コレクション・ソースの作成と削除
- Publish の実行と完了
- チャット（質問・回答）
- PII 検出（`PII_DETECTED` / `pii_detected`）
- プロンプトインジェクション検出（`PROMPT_INJECTION_BLOCKED`）
- 認証失敗

### 8-2. 改ざん防止

`audit_logs` は API 経由での削除・変更ができません。運用ポリシー上もこの原則を守ってください。

### 8-3. GUI からの参照

`admin` ロールでログイン後、「監査ログ」画面でフィルタしながら参照できます。

### 8-4. API 経由

- `GET /api/guardrails/pii-detections` — `audit_logs` から PII 検出を集計（admin 必須）
- `GET /api/pii-detections` — `chunks` テーブルから集計（admin 必須）
- `GET /api/audit-logs` — 監査ログ取得（admin 必須）

### 8-5. SQLite から直接抽出

CSV 等にエクスポートしたい場合は、SQLite クライアントから直接 SELECT します。

```bash
sqlite3 ~/.cynovela/db/cynovela.db \
  "SELECT timestamp, action, target, detail FROM audit_logs ORDER BY timestamp DESC LIMIT 100;"
```

---

## 9. 利用者の管理

### 9-1. ロール

Cynovela には 2 種類のロールがあります。

| ロール | 権限 |
|--------|------|
| `admin` | 全機能（ユーザー管理、システム設定、PII 検出履歴閲覧など） |
| `viewer` | 閲覧のみ |

> `curator` / `data-scientist` 等の名称は後方互換の値として受理されますが、現行実装では `viewer` に正規化され、固有権限はありません。DB が保持するロールは `admin` / `viewer` の 2 値です。

### 9-2. 初期 admin

初回起動時に admin ユーザーが作成されます。ユーザー名とパスワードは環境変数で上書きできます。

| 環境変数 | 用途 | 既定値 |
|---------|------|------|
| `CYNOVELA_ADMIN_USERNAME` | 初回 admin ユーザー名 | `cynovela` |
| `CYNOVELA_ADMIN_INITIAL_PASSWORD` | 初回 admin パスワード | （env・`cynovela.yaml` の `auth.admin_initial_password` いずれも未設定なら、初回ログインでパスワード変更を強制します。既知の固定 PW は配布しません。固定したい場合のみ値を設定） |

### 9-3. 出荷 demo.db のログイン情報

`--demo` で配布される `demo.db` には次のアカウントが投入済みです。

| ユーザー名 | ロール | パスワード |
|-----------|--------|-----------|
| `cynovela` | admin | 初回ログイン時に変更を強制（固定 PW は配布しません） |
| `demo` | viewer | 同梱の資格情報ファイル（配布物の tar とは別便で受け取る `*.admin-password.txt`）の `viewer_password` を参照。固定 PW は配布しません |

### 9-4. ユーザー追加・削除・パスワード変更

admin ロールでログイン後、「ユーザー管理」画面から実行できます。API での操作も可能ですが、ユーザー管理系エンドポイントは `_require_admin` または `_require_admin_or_self`（本人か admin のみ）で保護されています。

### 9-5. ロール別の保管庫アクセスとマスキング

- `admin` → raw（生本文）保管庫を検索。回答表示では出口マスクなし。
- `viewer`（`curator` 等は viewer に正規化）→ masked（マスク済み）保管庫を検索。出口マスクあり。

> ただし外部（非ローカル）LLM を使う場合は、crag-egress-guard により admin でも raw の下読み（context_preview）が外部へ送出されません（CRAG スキップ）。「admin＝常に生本文が外部 LLM へ渡る」ではない点に注意してください。

詳しくはハンズオンの、役割による見え方の違いの節を参照してください。

### 9-6. 認証

API 認証は HTTP `Authorization` ヘッダーで行います。トークンは `POST /api/auth/login` が発行する JWT です。旧 `Bearer demo-token-{user_id}` 形式は廃止済みで受理しません。

---

## 10. 健全性の確認と監視

### 10-1. 主要なヘルスエンドポイント

`/api/health` ほか admin 向けの監視系エンドポイントが用意されています（`_require_admin` で保護）。

### 10-2. Publish 履歴

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

### 10-3. サーキットブレーカー

LLM や外部 API 呼び出しの失敗が一定数を超えると、サーキットブレーカーが OPEN し、一時的に呼び出しを停止します。`cynovela.yaml` の `circuit_breaker` セクションで挙動を調整できます。

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 3
  recovery_timeout_seconds: 30
```

---

## 11. 通知（メール）

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

## 12. ポートを変える

### 12-1. ポートとアクセス制御

| 既定値 | 内容 |
|------|------|
| 8765 | サーバーポート |
| 0.0.0.0 | バインドアドレス（`--local-only` で 127.0.0.1 に絞る） |
| 許可 IP | 既定は制限なし（`--allow-subnet` / `--allow-tailscale` 指定時のみ適用） |

LAN や Tailscale からのアクセスを許可するには、`--lan` / `--allow-tailscale` / `--allow-subnet` を併用します（5「LAN で分け合う」を参照）。

### 12-2. ポート番号の変更

ポートは**起動時の引数で決まります**。`cynovela.yaml` の `server.port` を書き換えても
待ち受けポートには反映されません（設定は読み込まれますが待ち受けには渡っていません）。

```bash
# --port で指定する（既定 8765）。launch.sh に渡した引数はそのまま server.py へ届きます。
# デモで使う場合は --demo も付けてください。
./launch.sh --port 8900

# conda 環境を自分で有効化している場合は直接でも同じです
python server.py --mode text --port 8900
```

うまくいかないとき: 指定したポートが既に使われていると起動に失敗します。
`lsof -i :8900` で使用中のプロセスを確認し、別のポートを選んでください。
なお `./launch.sh` は既定ポート 8765 の使用状況だけを見て確認を促します。
別ポートを指定したときは自分で `lsof` を確認してください。

LAN で分け合うときは、共有のフラグと併せて指定します:

```bash
python server.py --lan --port 9000
```

ポート 80 や 443 など特権ポートを使う場合は管理者権限が必要なため、リバースプロキシ（nginx 等）経由を推奨します。

---

## 13. 運用上の注意

- `--demo` モードは検証用です。デモの DB（`db/demo.db`）は起動のたびに消えるわけではなく、書いたものが残り続けるため、本番データを置かないでください。
- 以前あった `--mock` モードは撤去済みです。いま指定するとエラーで止まります。
- バックアップは「SQLite と ChromaDB を同時に」スナップショットしてください。片方だけの復元は整合性を壊します。
- `audit_logs` は改ざん防止が必要です。SQLite ファイルそのものへの不用意な書き込みは避けてください。

---
