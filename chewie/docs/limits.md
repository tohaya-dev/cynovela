# このツールにできないこと（既知の制限）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built so that one individual could
> understand the concepts behind AI infrastructure tools by working through them by hand.
> It is not a commercial product and not an official implementation.
> The implementation is entirely original, built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any organization or product.

This document describes what Cynovela **cannot** do, and what to watch out for. Explanations
of what it can do are in [getting-started.md](getting-started.md) and
[concept.md](concept.md). Only the things that will disappoint you if you expect them are
written here.

The version is `1.2.0` (`APP_VERSION` in `core/version.py` is the only source, and
`GET /api/health` and `/docs` read it from there).

---

**Contents**

- [1. What masking cannot do](#1-what-masking-cannot-do)
  - [1.1 Rules can only catch the 13 types that have a fixed shape](#11-rules-can-only-catch-the-13-types-that-have-a-fixed-shape)
  - [1.2 Personal names and addresses depend on language analysis; with `lite` nothing is masked at all](#12-personal-names-and-addresses-depend-on-language-analysis-with-lite-nothing-is-masked-at-all)
  - [1.3 Organisation names and place names exist in name only, with nothing behind them](#13-organisation-names-and-place-names-exist-in-name-only-with-nothing-behind-them)
  - [1.4 Without a language model, even `standard` degrades to rules only](#14-without-a-language-model-even-standard-degrades-to-rules-only)
  - [1.5 Passwords and API keys are cut off by whitespace, Japanese text, or newlines](#15-passwords-and-api-keys-are-cut-off-by-whitespace-japanese-text-or-newlines)
  - [1.6 Whitespace can enter text extracted from a PDF, letting an email escape masking](#16-whitespace-can-enter-text-extracted-from-a-pdf-letting-an-email-escape-masking)
  - [1.7 Whether an administrator can see the original text depends on the encryption key and the destination](#17-whether-an-administrator-can-see-the-original-text-depends-on-the-encryption-key-and-the-destination)
- [2. Document formats that cannot be read](#2-document-formats-that-cannot-be-read)
- [3. Speaking to it by voice](#3-speaking-to-it-by-voice)
- [4. There is no endpoint for uploading documents](#4-there-is-no-endpoint-for-uploading-documents)
- [5. Conditions under which sending to the outside is stopped](#5-conditions-under-which-sending-to-the-outside-is-stopped)
- [6. Constraints when used concurrently](#6-constraints-when-used-concurrently)
- [7. Constraints on replacing models](#7-constraints-on-replacing-models)
- [8. Features that are only a skeleton with nothing inside](#8-features-that-are-only-a-skeleton-with-nothing-inside)
- [9. The Kubernetes set does not work as-is](#9-the-kubernetes-set-does-not-work-as-is)
- [10. Other limitations and notes](#10-other-limitations-and-notes)
  - [Startup forms and where data lives](#startup-forms-and-where-data-lives)
  - [Cross-collection search](#cross-collection-search)
  - [Workspace separation](#workspace-separation)
  - [MCP](#mcp)
  - [How answers are built](#how-answers-are-built)
  - [Removed features](#removed-features)
  - [The pass (login token)](#the-pass-login-token)
  - [Pitfalls](#pitfalls)
- [11. Things recorded in 1.0.7](#11-things-recorded-in-107)
  - [11.1 Restoring a backup through the API does not reliably give you the backup](#111-restoring-a-backup-through-the-api-does-not-reliably-give-you-the-backup)
  - [11.2 A backup holds data, not settings](#112-a-backup-holds-data-not-settings)
  - [11.3 The "dimension" written into an export is a fixed number](#113-the-dimension-written-into-an-export-is-a-fixed-number)
  - [11.4 With Ollama, the context length is whatever Ollama defaults to](#114-with-ollama-the-context-length-is-whatever-ollama-defaults-to)
  - [11.5 An imported workspace searches by vector only](#115-an-imported-workspace-searches-by-vector-only)
  - [11.6 Not measured: the package edition on a Mac without conda](#116-not-measured-the-package-edition-on-a-mac-without-conda)
  - [11.7 Fixed in chewie, not in falcon](#117-fixed-in-chewie-not-in-falcon)
- [12. Authentication, authorization and communication](#12-authentication-authorization-and-communication)
- [13. Linkages that are defined but not integrated](#13-linkages-that-are-defined-but-not-integrated)
- [14. Areas skipped in the tests](#14-areas-skipped-in-the-tests)
- [15. Items that are not complete](#15-items-that-are-not-complete)

## 1. What masking cannot do

**This is the most important section of this document.** Masking is a mechanism for hiding
personal information, but the range it can hide has clear limits. **The fact that masking
matched does not mean all personal information in a document has been removed.** Something
that could not be hidden always remains.

### 1.1 Rules can only catch the 13 types that have a fixed shape

The types written in `PII_PATTERNS` of `guardrail.py` are only these 13.

| Type | What it means |
|------|-----------|
| `URL` | An address starting with http / https |
| `EMAIL` | An email address |
| `PHONE_JP` | Mobile phone number (070 / 080 / 090) |
| `PHONE_LAND` | Landline phone number |
| `CREDIT` | Credit card number |
| `MYNUMBER` | My Number (Japanese individual number) |
| `PASSPORT` | Passport number (2 letters + 7 digits) |
| `IPV4` | IPv4 address |
| `PASSWORD` | A labelled value such as "パスワード: XX" |
| `APIKEY` | API key / access token |
| `PRIVATEKEY` | A private key block (`-----BEGIN ... PRIVATE KEY-----`) |
| `SSN` | US Social Security Number (3-2-4 form) |
| `IBAN` | International Bank Account Number |

Nothing else is masked by the rules, not even once. For example employee numbers, customer
numbers, contract numbers, bank account numbers (other than IBAN), vehicle numbers and
insurance card numbers are out of scope.

The rules match on "shape". If the shape is broken they do not match. Conversely, unrelated
numbers that happen to match a shape are masked (a value of exactly 12 digits being masked as
My Number is an example; this is intentional, as the result of prioritising the avoidance of
leaks).

### 1.2 Personal names and addresses depend on language analysis; with `lite` nothing is masked at all

Personal names and addresses are not among the 13 types above. Their shape is not fixed, so
the rules cannot catch them, and they are handled on the language analysis (NER) side.

- The setting is `pii_mode` in `cynovela.yaml`. The default is `standard`.
- Only when it is `standard` do `PERSON_JP` (personal name) and `ADDRESS_JP` (address) work.
- **If you set `pii_mode` to `lite`, neither names nor addresses are masked at all.**
  `lite` switches to a path that judges with regular expressions only, and the name and
  address recognizers are never assembled in the first place (see `get_active_recognizers()`
  and `detect_pii()` in `utils/metadata/pii.py`).

Name detection only matches words registered as family or given names. Rare names, katakana
transcriptions of foreign names, nicknames, and forms written together with a job title are
missed. Addresses are also only looked at in the form that starts from a prefecture and in
the postal code shape; forms such as "本社ビル 3 階" or "◯◯支店" are not treated as addresses.

### 1.3 Organisation names and place names exist in name only, with nothing behind them

`get_active_recognizers()` also returns `ORG_JP` (organisation name) and `LOC_JP` (place name).
The names are returned, but **not a single recognizer that supplies them is registered**
(across the whole tree, these two words appear only on that one line).

In other words, **organisation names and place names are not masked.** Do not assume they are
working just because their names appear in a list.

### 1.4 Without a language model, even `standard` degrades to rules only

Detecting names and addresses requires the spaCy / GiNZA language models. In an environment
where these are not installed, detection degrades to regular expressions only, even with
`pii_mode` left at `standard`.

At startup `launch.sh` checks that they exist, and if they are missing it prints the following
warning.

```
⚠️  spaCy モデル '...' が未導入です (standard PII が regex フォールバックします)。'pip install -r requirements.txt' を実行してください。
```

**While this warning is showing, neither names nor addresses are being masked.** Startup does
not stop, so if you skim past the warning you will keep using the tool believing masking is in
effect.

### 1.5 Passwords and API keys are cut off by whitespace, Japanese text, or newlines

The `PASSWORD` and `APIKEY` rules pick up the value part using only ASCII graphic characters
(the relevant block in `guardrail.py` states explicitly that "値は ASCII 図形文字 `[!-~]` のみ
（空白・CJK で必ず切れる）"). Because of this, the following cannot be caught.

- Values with whitespace in the middle (`パスワード: abc def`) → cut off after `abc`
- Values with Japanese text in the middle
- Values spanning a newline (the whitespace between the label and the value is limited to tabs
  and spaces, and does not span newlines)

Also, anything without a separator (`:` `：` `=` `＝` or "は") between the label and the value
is out of scope. This is by design, to avoid catching common phrases such as
`password protection`, and the price of that is that space-separated forms like
"パスワード　abcdefgh" cannot be caught.

### 1.6 Whitespace can enter text extracted from a PDF, letting an email escape masking

A PDF is composed not as a sequence of characters but as information about where to place
characters. When text is extracted from it, whitespace that was not in the original appearance
can end up in the middle of a word.

The masking rules look at the sequence of characters, so a single inserted space is enough to
stop a match. For an email address, this looks as follows.

- `taro.yamada@example.co.jp` → masked
- `taro.yamada @example.co.jp` → **not masked** (cut off before the `@`)
- `taro.yamada@ example.co.jp` → **not masked** (cut off after the `@`)
- `taro. yamada@example.co.jp` → only the `yamada@example.co.jp` part is masked, and
  `taro.` remains

The same thing can happen with other types such as phone numbers and card numbers.
**When you ingest a PDF, check with your own eyes whether masking matched.**
You can see the actual text from the chunk list after ingest.

### 1.7 Whether an administrator can see the original text depends on the encryption key and the destination

When the role is `admin`, the design lets them see the original text before masking
(`tier_for_role` in `rag.py`). However, in the following 3 cases even an administrator only
gets masked content.

1. **When the destination of the answering LLM points outside.**
   `_effective_send_tier` in `routers/chat.py` drops to masked regardless of role when the
   destination is neither inside the local machine, nor the container's host side, nor a
   private address range. When the destination cannot be determined it also falls back to
   masked.
2. **When the vault (encrypted storage) encryption key (`store/secret.key`) does not match.**
   Original text is stored encrypted, and `_vault_substitute_raw` in `rag.py` decrypts it.
   Lines that cannot be decrypted use the masked text as-is
   (this is deliberate, so that ciphertext is never shown on screen).
   If you replace the encryption key after receiving a package, even an administrator can no longer read
   the original text of documents ingested before that.
3. **The question text itself.**
   Masking of the question text is not divided by role. Even if an administrator writes an IP
   address in the question, that IP is masked before it is passed to search and to the LLM.

An earlier version of this document said "IPs are masked even for administrators (under
investigation)", but the reason is the 3 items above. It is not a defect.

---

## 2. Document formats that cannot be read

The only formats that can be ingested are those written in `SUPPORTED_EXTENSIONS` in `rag.py`.

| Kind | Extensions |
|------|--------|
| Documents | `.txt` `.md` `.csv` `.pdf` `.docx` |
| Spreadsheets / presentations | `.xlsx` `.xls` `.pptx` |
| Web / mail | `.html` `.htm` `.eml` |
| Archives | `.zip` |
| Images | `.jpg` `.jpeg` `.png` `.heic` `.webp` `.gif` |

Anything else is excluded from ingest. Here are the commonly brought-in formats that
**cannot** be handled.

- Old Office formats: `.doc` `.ppt` (only `.xls` can be handled), `.rtf`
- OpenDocument family: `.odt` `.ods` `.odp`
- Structured data: `.json` `.xml` `.yaml`
- Mail: `.msg` (Outlook format; only `.eml` is supported)
- E-books: `.epub`
- Audio / video: `.mp3` `.wav` `.m4a` `.mp4` `.mov` and so on
- Some images: `.tif` `.tiff` `.bmp` `.svg`
- Some archives: `.7z` `.rar` `.tar` `.gz` (only `.zip` is supported)

Other limitations:

- **Zip nesting is only one level deep.** A zip inside a zip is not opened
  (the extraction step in `rag.py` skips entries whose extension is `.zip`).
- **Image files cannot be read (currently under development).** You cannot search by what is inside a photo or screenshot. There is no OCR (optical character recognition) mechanism.
- If a PDF was produced as an image (merely scanned), not a single character can be extracted.
  There is no OCR (optical character recognition) mechanism.
- Encrypted PDFs and corrupted documents are skipped. They appear in the ingest result as
  "読めない/空: N件".

---

## 3. Speaking to it by voice

- The voice feature has been removed. This package has no speech-to-text.
- The legacy path `/api/transcribe` is **no longer connected**.
  `include_router` has been removed in `server.py` (it was a hole through which a
  transcription would come back unmasked, so it was deliberately removed).

---

## 4. There is no endpoint for uploading documents

The endpoint for pushing files in from the screen or the API has been **removed**
(the top of `routers/sources.py` states that "アップロード保存先 `_uploads_root` と
`/api/sources/upload` を撤去した。取り込みは取り込みフォルダ経由に一本化する").

Documents are **placed in a predetermined ingest folder** and then selected on screen.
There is no longer any place inside the application that makes a copy of a document.

---

## 5. Conditions under which sending to the outside is stopped

These are less "things it cannot do" than "things deliberately stopped".
When a determination cannot be made, it always falls to the stopping side. As a result,
features can look like they are not working.

- **CRAG pre-reading.** The step that has the LLM pre-read whether the search results are
  sufficient for the question is not executed when the destination is not inside the local
  machine, and **when the destination cannot be determined** (`rag.py`). When it is not
  executed, it falls back to "adopt the search results as they are".
  The screen shows `[CRAG] 非ローカル宛のため下読みをスキップします`.
- **Conversation summarisation and extraction of hints from an answer.** Both use the same
  determination, and for external destinations (including undeterminable ones) they send
  nothing and return empty (`routers/chat.py`).
- **Sending original text based on role.** If the destination is external, only masked content
  is sent, even for an administrator (the `_effective_send_tier` described above).
- **If masking fails, processing stops.** For both the question text and the answer, if the
  masking step fails with an exception, a 503 is returned and processing is aborted.
  Pre-masking content is never returned instead (`routers/chat.py`).
- **The combination of unmasked ingest and external embedding is rejected.**
  Collections created by an older version as "unmasked" cannot be published while external
  embedding is enabled (`rag.py`).

---

## 6. Constraints when used concurrently

- **Publish is limited to 2 at a time.** A third waits 5 seconds and, if no slot opens, is
  returned as a failure (`server.py`; the screen shows
  "他のPublishが多すぎます。少し待ってから再試行してください。").
- **LLM concurrency is 3 by default** (`llm.max_concurrent` in `cynovela.yaml`;
  `server.py` builds a semaphore from this value). A fourth waits until a previous call
  finishes.
- **Storage is a single SQLite file** (WAL mode). Where writes overlap, waiting occurs.
  A usage pattern with dozens of people running ingest at the same time is not assumed.
- The vector index (ChromaDB) is also a file on the same machine.
  Do not rewrite the same index from multiple processes.

---

## 7. Constraints on replacing models

Detailed steps are in [operations.md](operations.md). Only the key points are written here.

- **The embedding model must match down to the version (snapshot).**
  The snapshot version of `BAAI/bge-m3` must be aligned.
  **If the version differs the vector values change, they mix with the index built on this machine, and the
  search ranking breaks.**
  If the version differs, a warning appears at startup and at publish time. When a warning
  appears, either align the version or rebuild the whole index.
- **Neither the package edition nor the source edition bundles the AI models.**
  If you run the startup script without placing the models, the first startup asks whether to
  fetch them from the internet.
  If you decline, **it stops before starting**.
- **`host.containers.internal` cannot be resolved outside a container.**
  If you start directly on the host, rewrite it to `127.0.0.1`
  (the container package rewrites this one word automatically.
  If you write a different host name or IP it is not rewritten and is used exactly as written).
- **The image endpoint of the external accelerator is unimplemented.** Calling it returns 501.
- **The reranker is set to an external accelerator that no distributable carries.**
  In the `cynovela.yaml` that ships, `reranker.device` is `external` and
  `reranker.base_url` is `http://localhost:18850`, but nothing that answers on that
  address is included in any of the downloads. Every search therefore tries that
  address, fails, and falls back — to reranking inside the process when the reranker
  weights are in place (they are, in the `models` download), and to no reranking at
  all when they are not. One log line is written each time it falls back, and the
  settings screen shows the state. Answers are still produced. What selects the
  accelerator is `reranker.device`; the shipped `reranker.provider` is already
  `cross_encoder`, so on an edition whose `cynovela.yaml` you can edit, emptying
  `device` makes the in-process path the first choice instead of the fallback.
- **Some values of `--mode` at startup do not actually switch anything.**
  This is written directly in the description text of `--mode`.
  `lite` and `lite-en` have no wiring to a lightweight model, and currently run on the same
  `bge-m3` as the default `text`. `minimal` has no TF-IDF integration, so it too requires
  `bge-m3` (in an environment without the models placed, ingest is not possible).
  **Whichever mode you choose, the size of the required models does not change.**

---

## 8. Features that are only a skeleton with nothing inside

These raise `NotImplementedError` when called, or are only abstract declarations.
(Line numbers are not written, because they shift immediately. They are indicated by file name
and class / method name.)

| File | Class / method | State |
|---------|----------------|------|
| `providers/classifier.py` | `ClassifierProvider.classify` | Abstract (a slot for replacement) |
| `providers/embedding.py` | `EmbeddingProvider.embed` / `.test_connection` | Abstract |
| `providers/embedding.py` | `MLXEmbeddingProvider.embed` | Unimplemented (future) |
| `providers/reranker.py` | `RerankerProvider.rerank` / `.test_connection` | Abstract |
| `providers/reranker.py` | `MLXReranker.rerank` | Unimplemented (future) |
| `providers/vector_store.py` | `VectorStoreProvider.add` / `.search` / `.delete_collection` / `.export` / `.import_data` / `.test_connection` | Abstract |
| `providers/vector_store.py` | `QdrantVectorStore.add` / `.search` / `.delete_collection` / `.export` / `.import_data` | Unimplemented (skeleton only) |
| `providers/vector_store.py` | The LanceDB backend | Initialization only; the substance is not implemented, and it is rejected when the package is not installed |
| `services/rag_strategies.py` | `GraphRAGStrategy.retrieve` / `.build_graph` / `.traverse_with_acl` | Unimplemented (future) |
| `services/agent_runtime.py` | `AgentRuntime.run` / `.call_tool` / `.available_tools` | Abstract declarations only. There is not a single implementing class |

In other words:

- **You cannot switch the vector storage to Qdrant.** Only ChromaDB works.
- **The MLX path for Apple Silicon is unusable.** Both embedding and reranking are
  unimplemented.
  (If you want to use the Apple Silicon GPU, it goes through the external accelerator.
  See [operations.md](operations.md).)
- **You cannot switch the vector storage to LanceDB either.** Only the initialization exists.
- **Graph-based search (GraphRAG) is unusable.**
- **You cannot have an agent do work.** Only the type declarations exist.

---

## 9. The Kubernetes set does not work as-is

- **The container package does not include `deploy/k8s/20-deployment.yaml`.**
  `tools/build-dist.sh`, which builds the package, drops this file right before making the
  `tar`. With only the remaining 3 (namespace / pvc / service), not a single application
  container comes up.
- **The direct-host-startup package has no `deploy/` at all.**

If you want to run on Kubernetes, you need to write the Deployment definition yourself.

---

## 10. Other limitations and notes

### Startup forms and where data lives

- With `--demo`, it starts with the demo database (`store/db/demo.db` and
  `store/vector/demo/chroma`). At the first `--demo` startup, the server ingests the
  bundled `dummy-corpus/` on the spot and builds the database and the index on this
  machine; later startups do not re-ingest.
- With nothing added it is production, and starts with an **empty database**
  (`store/db/cynovela.db` and `store/vector/default/chroma`).
- **Neither is erased by a restart.** They are not initialised on every startup.
  If you want to erase them, delete the files yourself.
- The package does not ship a database, an index, or key files. They are created on this
  machine: the keys at the first startup, the demo database and index at the first `--demo`
  startup, **only from the `dummy-corpus/` inside the package**. Not a single working
  document from the builder's side is included. See `BUNDLED-DATA.md` in the package.
- **Where `store/` itself sits depends on the edition.** In every edition that is a folder
  you unpack, it is `store/` inside that folder. In the app edition — in preparation, not
  part of this release — the installed bundle is read-only, so the launcher sets
  `CYNOVELA_DATA_ROOT` and the same paths are taken relative to
  `~/Library/Application Support/Cynovela/` instead.
- **The first sign-in name and password are printed on screen at the first startup —
  in both forms (`--demo` and production).** The startup script decides "this is a
  first run" by asking whether the database file already exists, and neither database
  ships in the package, so the first startup prints them either way. If you missed
  that screen, the same value can be read from the `cynovela.yaml` next to the
  startup script, on the `admin_initial_password:` line under `auth:`
  (`grep admin_initial_password cynovela.yaml`). You are asked to change the password at
  the first sign-in either way.

### Cross-collection search

The MCP tools include `search_across_collections` (search spanning multiple collections), but
**the screen (GUI) has no entry point for cross-collection search.**
From the screen you select one workspace and search it.

### Workspace separation

- **The separation of a workspace in ChromaDB is a logical boundary (the collection name);
  a physical boundary (a separate directory and the like) is not implemented.**
  One Chroma store directory holds every collection, and what divides them is the collection
  name, `{collection_id}__raw` and `{collection_id}__masked` (`providers/vector_store.py`).
- When a `workspace_id` is passed to a search, a `where` condition on the metadata narrows the
  result further, but that is a filter applied inside the same store; the place where the data
  is kept is not divided.
- The BM25 index is held in memory in a dictionary keyed by `(workspace_id, tier)`, so that
  path is divided by the key, not by a directory either (`rag.py`).

### MCP

- `mcp_server.py` provides 25 tools (22 visible by default; 3 admin tools appear only when CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 is set).
- The MCP server is built to query Cynovela's REST API internally, with authentication.
  In other words, **if the main body is not running, MCP does not work either.**
- The Python executable that runs MCP can be specified with the environment variable
  `CYNOVELA_MCP_PYTHON`. If not specified, the currently running Python is used as-is
  (`routers/mcp.py`).

### How answers are built

- **Structured answers cannot be returned.** Answers are free-form (Markdown where needed).
  Responses in JSON or with fixed tags are not provided.
  Citation of sources (in the `[1][2]` form) is implemented.
- **There is no automatic switching when confidence is low.**
  `cynovela.yaml` has `confidence_threshold` (default `0.4`), but no behaviour that
  automatically switches to a general-knowledge mode when it falls below is built in.
  The value is defined as a setting, and the processing that switches to
  `GENERAL_KNOWLEDGE_SYSTEM_PROMPT` when there are 0 search results is not integrated;
  the exclusion logic in the search pipeline is only **partly integrated**.
- **Self-evaluation of an answer is a simple rule.** `evaluate_answer_quality()` in
  `adaptive_rag.py` decides sufficiency from "the answer is empty", "under 60 characters with
  few hits", and "contains a negative phrasing". It does not have an LLM evaluate it.

### Removed features

| Feature | State |
|------|------|
| `--mock` startup | Removed. It does not exist among the startup options. Startup without models is also impossible |
| `/chat-popup` | Returns 410 Gone. Migrated to the full-screen chat |
| Login with `user_id` only | Removed. `username` and `password` are required |
| Unauthenticated access to `/api/auth/users` | Removed. Administrator authentication is always required |
| The `--pii-mode` startup option | Abolished. Specify it with `pii_mode` in `cynovela.yaml` |
| Legacy `/api/transcribe` | Removed. There is no voice feature |
| `/api/sources/upload` | Removed. Unified on going through the ingest folder |

### The pass (login token)

The pass is a JWT issued by `POST /api/auth/login`. The signing key is
**not included in the package**. The receiving side auto-generates it from cryptographic
random numbers at first startup and saves it to `store/db/jwt/secret.key`
(`_load_or_create_jwt_signing_key` in `config.py`). This key is always dropped when the package
is built (because if it were shared, a pass issued elsewhere would be accepted).

If saving the key fails, the key is valid only for that one run.
In that case, restarting invalidates any issued passes (logging in again works).

**Since 1.0.7 the pass does not expire unless the caller asks it to.** Before,
every pass stopped working 8 hours after it was issued. Now `POST /api/auth/login`
issues a pass with no expiry unless you pass `expires_in_hours` or
`expires_in_seconds`. Two consequences you should know about:

- **Signing out does not make the pass stop working.** `POST /api/auth/logout`
  removes the refresh token and the in-memory session, but the pass itself is
  checked by its signature alone, so a copy of it keeps working. Previously the
  8-hour limit put a floor under this; now there is none. If a pass leaks, the
  only way to invalidate it is to delete `store/db/jwt/secret.key` and restart,
  which invalidates **every** pass.
- Pass `expires_in_hours` when you hand a pass to something you do not control.

### Pitfalls

- ChromaDB's `PersistentClient` does not error even when you pass it the wrong path.
  It silently creates an empty database. **When a search returns 0 results,
  first suspect whether the index location is correct.**
- Do not pass `max_tokens` to the LM Studio API.
  With a reasoning-type model, it will use up the tokens it needs for thinking.
- **The screen asks for `/api/settings/embedding` before anyone has signed in, and keeps
  asking after they have.** The banner that reports the state of the embedding path polls
  that endpoint every 5 seconds for the first five minutes and every 60 seconds after that,
  and the polling starts when the page loads rather than when a sign-in succeeds. Before a
  sign-in, and for a viewer, the endpoint answers 401 or 403; the banner swallows that and
  shows nothing, but the request is made and logged all the same. It is noise in the log,
  not a leak — the endpoint rejects the request, it does not answer.


## 11. Things recorded in 1.0.7

These were measured while preparing 1.0.7. They are written here because they
will bite you if you do not know them, not because they are about to change.

### 11.1 Restoring a backup through the API does not reliably give you the backup

`POST /api/admin/backups/{name}/restore` copies the saved `cynovela.db` over the
live database file **while the server is still running**. SQLite is in WAL mode,
so the running process still holds `cynovela.db-wal` and `cynovela.db-shm` from
before the copy, and those companions can write the old content back over the
file you just restored. The endpoint answers `{"ok": true}` either way.

**The route that works:** stop the server (`bash stop.sh`), put the files back by
hand, then start it again.

```
bash stop.sh
cd store/db
mv cynovela.db     cynovela.db.aside
mv cynovela.db-wal cynovela.db-wal.aside   # if it exists
mv cynovela.db-shm cynovela.db-shm.aside   # if it exists
cp ../backups/<the backup>/cynovela.db .
rm -rf ../vector/default/chroma
cp -R ../backups/<the backup>/chroma ../vector/default/chroma
cd ../..
./launch.sh
```

**Move the `-wal` and `-shm` companions aside together with the database.** If
you move only `cynovela.db`, SQLite finds a WAL that does not belong to the file
next to it, and the result is neither the old data nor the new.

### 11.2 A backup holds data, not settings

`_create_backup` copies exactly two things: the database (`cynovela.db`) and the
search index (`chroma`). It does **not** copy:

- `cynovela.yaml` — every setting that lives in the file, including the LLM
  endpoint, the masking mode and the paths
- `store/db/jwt/secret.key` — the key that signs the pass

So restoring gives you your documents, users and index back. It does not give
you your configuration back, and every pass issued before is still valid because
the key never moved. Copy `cynovela.yaml` yourself if you want it kept.

### 11.3 The "dimension" written into an export is a fixed number

`_meta.json` inside a full export carries `"embedding_dim": 1024`. That number is
written into `routers/chat.py` directly; nothing measures the vectors. It is
correct for BGE-M3, which is what ships. If you replace the embedding model with
one of a different width, the file will say 1024 and be wrong. The model **name**
in the same file is read from the running configuration and is correct.

### 11.4 With Ollama, the context length is whatever Ollama defaults to

Cynovela never sends `num_ctx` to Ollama. The parameters it does send are
`top_p`, `top_k`, `max_tokens`, `repeat_penalty`, `seed` and `think`. Ollama
therefore uses its own default context window and **silently drops** whatever
does not fit — you get an answer that ignores the passages that were cut. Set the
context length on the Ollama side (a Modelfile with `PARAMETER num_ctx`, or
`OLLAMA_CONTEXT_LENGTH`) to match the material you feed it.

### 11.5 An imported workspace searches by vector only

`POST /api/workspaces/import` restores the vectors, and since 1.0.7 it also
rewrites the ids inside them so the imported workspace answers without being
published again. What it does **not** restore is the `chunks` table, from which
the BM25 keyword index is built. So an imported workspace is searched by vector
similarity and reranking only; the keyword half of the hybrid search contributes
nothing (you can see this as `bm25_score: 0.0` on every hit). Publish the
collection again if you want the keyword half back.

### 11.6 Not measured: the package edition on a Mac without conda

The package edition is meant to need neither Python nor conda. That it starts
from its bundled environment was measured on the build machine — but that machine
has conda installed, so this run cannot tell you that a Mac with **no** conda at
all behaves the same. Treat "no conda required" as designed-for and checked on a
machine that happens to have conda, not as measured on a machine without it.

### 11.7 Fixed in chewie, not in falcon

The following were repaired in chewie and deliberately **not** carried into the
container build (falcon) at 1.0.7, because falcon's code differs at those places
and that release did not rewrite falcon to match:

| What | Why not |
|---|---|
| The generation-timeout wording | falcon has no `_timeout_answer`; the old sentence sits inline in two places |
| Citation numbers carried through to MCP | falcon's MCP server is an older build (11 tools against 25) |
| The CLI, including `login` / `logout` | falcon ships no `cynovela-cli.py`. Its own, older `cynovela_cli.py` has neither `login` nor `logout` |

**One of them has since been carried over.** "Two scans of one folder cannot run
at once" was ported into falcon on 2026-08-26. `_do_scan` in `falcon/server.py` is
now a thin guarded entry point — a module-level lock plus a set of source ids,
added before the work and discarded in a `finally` — wrapped around the previous
body, which was renamed `_do_scan_body`. All eight call sites into the scan are
covered by it. falcon still has no `scan_jobs` table, so the write-back to a job
row that chewie does inside its own guard has no counterpart there; the guard
itself is the same.

---

## 12. Authentication, authorization and communication

- **Authentication is a JWT.** It is issued by `POST /api/auth/login`, and it is required even
  with a `--demo` startup. The old fixed token in the form `Bearer demo-token-<user_id>` was
  abolished on 2026-07-29. How the signing key is created and where it lives is in §10,
  "The pass (login token)".
- **Scope of the RBAC implementation.** An authorization check is present in 34 of the 36
  router files under `routers/`. Authentication itself is enforced regardless of the startup
  form, and it is not loosened with a `--demo` startup.
- **There is no API key management feature.** Issuing and revoking a per-user API key is not
  implemented.
- **HTTPS is not supported.** The main body listens over HTTP only. TLS termination has to be
  delegated to a reverse proxy (nginx and the like).
- **The communication with the LLM is plain text too.** The connection to LM Studio / Ollama
  is plain HTTP as well. Publishing outside the LAN is not recommended.
- **The Embedding / Reranker settings are not persisted.** A change made at runtime (through
  the UI) is not written back to the YAML, and returns to the default on restart.

---

## 13. Linkages that are defined but not integrated

- **DataSyncService is not connected to publish.** The hash-based differential sync only
  writes logs; the actual call into `rag.publish` is a noop.
- **The difference detection is per path.** Addition and deletion over the set of paths are
  detected (at a 60 second interval by default), but comparison by `content_hash` is not
  implemented and the comparison method is not fixed, so a change to the *content* of a file
  is not detected this way.
- **The exclusion logic of `confidence_threshold` is only partly integrated** into the search
  pipeline. What this means in practice is in §10, "How answers are built".
- **A structured answer template is not implemented.** Fixing the LLM's answer into a
  structured format such as JSON or an `<answer>` tag is not supported; a free-form answer is
  the standard. Whether such a feature will be introduced is not decided.
- **Some elements of the i18n switch are fixed.** A few elements whose display is controlled by
  the language switch (Japanese / English) do not follow it.
- **Some UI elements are hidden until the tab is initialised.** They stay `display:none` until
  the JavaScript initialisation finishes.

---

## 14. Areas skipped in the tests

- **Demo mode related.** 4 authentication boundary tests remain `@pytest.mark.skip`
  (lines 11 / 51 / 56 / 157 of `tests/test_auth_boundary.py`). The reason text states
  "`--demo` モードでは認証バイパスが仕様", but because it was changed on 2026-07-29 into a
  form that enforces authentication even with a `--demo` startup, this reason no longer
  matches the implementation.
- **Sources API.** Because of the path registration form, 2 tests are skipped.
- **Publish Semaphore.** Because mock injection at module scope is difficult, 1 xfail.

---

## 15. Items that are not complete

The following are recorded as unfinished in [reference/changelog.md](reference/changelog.md).
They are written here as the state of the current build, not as a schedule.

| Item | Current state |
|---|---|
| Bugs recorded as HIGH priority | The reversed DB → Chroma order in `import_workspace`, the race condition in `admin_cleanup_chromadb_orphans`, the physical boundary of workspace isolation (see §10, "Workspace separation"), the workspace-A → workspace-B cross-boundary check, and others |
| Indirect prompt injection detection | A detection mechanism aimed at attacks that come through ingested documents is not implemented |
| Reranker testing with a real model | Verification with CrossEncoder and others is not done |
| KnowledgeCatalog | Metadata search in the Chunks viewer and citation tracking are not implemented |

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 企業・製品の公式見解を一切代表しません。

この文書は、Cynovela に **できないこと**、および気をつけることを書いたものです。
できることの説明は [getting-started.md](getting-started.md) と
[concept.md](concept.md) にあります。ここには、期待すると外れることだけを書きます。

版は `1.2.0` です（`core/version.py` の `APP_VERSION` が唯一の入手元で、
`GET /api/health` と `/docs` はここを読みます）。

---

**目次**

- [1. マスキング（マスキング）でできないこと](#1-マスキングマスキングでできないこと)
  - [1.1 決まった形をした 13 種類しか、規則では取れない](#11-決まった形をした-13-種類しか規則では取れない)
  - [1.2 氏名と住所は言語解析まかせ。`lite` にすると一切マスキングされない](#12-氏名と住所は言語解析まかせlite-にすると一切マスキングされない)
  - [1.3 組織名と地名は、名前だけあって中身がない](#13-組織名と地名は名前だけあって中身がない)
  - [1.4 言語モデルが入っていないと、`standard` でも規則だけに退行する](#14-言語モデルが入っていないとstandard-でも規則だけに退行する)
  - [1.5 パスワードと API キーは、空白・日本語・改行で切れる](#15-パスワードと-api-キーは空白日本語改行で切れる)
  - [1.6 PDF から取り出した文字に空白が入り、電子メールがマスキングを逃れることがある](#16-pdf-から取り出した文字に空白が入り電子メールがマスキングを逃れることがある)
  - [1.7 管理者が原文を見られるかどうかは、暗号鍵と宛先しだい](#17-管理者が原文を見られるかどうかは暗号鍵と宛先しだい)
- [2. 読み込めない資料の形式](#2-読み込めない資料の形式)
- [3. 音声で話しかけること](#3-音声で話しかけること)
- [4. 資料をアップロードする受け口はない](#4-資料をアップロードする受け口はない)
- [5. 外部への送出が止まる条件](#5-外部への送出が止まる条件)
- [6. 同時に使うときの制約](#6-同時に使うときの制約)
- [7. モデルの差し替えの制約](#7-モデルの差し替えの制約)
- [8. 骨組みだけで中身がない機能](#8-骨組みだけで中身がない機能)
- [9. Kubernetes 一式は、そのままでは動かない](#9-kubernetes-一式はそのままでは動かない)
- [10. その他の制限と注意](#10-その他の制限と注意)
  - [起動の形態とデータの場所](#起動の形態とデータの場所)
  - [横断検索](#横断検索)
  - [workspace の分離](#workspace-の分離)
  - [MCP](#mcp-1)
  - [回答の作り](#回答の作り)
  - [廃止した機能](#廃止した機能)
  - [通行証（ログイン用のトークン）](#通行証ログイン用のトークン)
  - [落とし穴](#落とし穴)
- [11. 1.0.7 で分かったこと](#11-107-で分かったこと)
  - [11.1 API から控えに戻しても、控えの中身になるとはかぎらない](#111-api-から控えに戻しても控えの中身になるとはかぎらない)
  - [11.2 控えに入るのはデータであって、設定ではない](#112-控えに入るのはデータであって設定ではない)
  - [11.3 書き出しに書かれる「次元」は、決め打ちの数である](#113-書き出しに書かれる次元は決め打ちの数である)
  - [11.4 Ollama を使うと、文脈の長さは Ollama の既定のままになる](#114-ollama-を使うと文脈の長さは-ollama-の既定のままになる)
  - [11.5 取り込んだ作業場所は、ベクターだけで探される](#115-取り込んだ作業場所はベクターだけで探される)
  - [11.6 測っていないこと: conda の入っていない Mac でのパッケージ版](#116-測っていないこと-conda-の入っていない-mac-でのパッケージ版)
  - [11.7 chewie では直し、falcon では直していないもの](#117-chewie-では直しfalcon-では直していないもの)
- [12. 認証・認可と通信](#12-認証認可と通信)
- [13. 定義はあるが統合されていない連携](#13-定義はあるが統合されていない連携)
- [14. テストでスキップされている領域](#14-テストでスキップされている領域)
- [15. 完了していない事項](#15-完了していない事項)

## 1. マスキング（マスキング）でできないこと

**この節がいちばん重い節です。** マスキングは「個人情報を隠す仕組み」ですが、隠せる範囲には
はっきりした限界があります。**マスキングが当たったからといって、資料の中の個人情報が
すべて消えたわけではありません。** 隠しきれないものが必ず残ります。

### 1.1 決まった形をした 13 種類しか、規則では取れない

`guardrail.py` の `PII_PATTERNS` に書かれている種別は、次の 13 種類だけです。

| 種別 | 何を指すか |
|------|-----------|
| `URL` | http / https で始まるアドレス |
| `EMAIL` | 電子メールアドレス |
| `PHONE_JP` | 携帯電話番号（070 / 080 / 090） |
| `PHONE_LAND` | 固定電話番号 |
| `CREDIT` | クレジットカード番号 |
| `MYNUMBER` | マイナンバー（個人番号） |
| `PASSPORT` | 旅券番号（英字 2 + 数字 7） |
| `IPV4` | IPv4 アドレス |
| `PASSWORD` | 「パスワード: ○○」のようなラベル付きの値 |
| `APIKEY` | API キー・アクセストークン |
| `PRIVATEKEY` | 秘密鍵のブロック（`-----BEGIN ... PRIVATE KEY-----`） |
| `SSN` | 米国の社会保障番号（3-2-4 の形） |
| `IBAN` | 国際銀行口座番号 |

これ以外のものは、規則では 1 件もマスキングされません。たとえば社員番号・顧客番号・
契約番号・口座番号（IBAN 以外）・車両番号・保険証番号などは、対象外です。

規則は「形」で当てています。形が崩れていれば当たりません。逆に、形が偶然一致した
無関係な数字はマスキングされます（12 桁ちょうどの数値がマイナンバーとしてマスキングされるのは
その例で、漏れを防ぐほうを優先した結果として意図的にそうしてあります）。

### 1.2 氏名と住所は言語解析まかせ。`lite` にすると一切マスキングされない

氏名と住所は、上の 13 種類には入っていません。形が決まっていないので規則では取れず、
言語解析（NER）の側で扱っています。

- 設定は `cynovela.yaml` の `pii_mode` です。既定は `standard` です。
- `standard` のときだけ、`PERSON_JP`（氏名）と `ADDRESS_JP`（住所）が働きます。
- **`pii_mode` を `lite` にすると、氏名も住所も一切マスキングされません。**
  `lite` は正規表現だけで判定する道へ切り替わり、氏名・住所の認識器は
  そもそも組み立てられません（`utils/metadata/pii.py` の `get_active_recognizers()`
  と `detect_pii()` を参照）。

氏名の判定は、姓名として登録のある語しか当たりません。珍しい姓名、外国人名の
カタカナ表記、あだ名、役職と一体になった書き方などは取りこぼします。
住所も、都道府県から始まる書き方と郵便番号の形しか見ておらず、
「本社ビル 3 階」「◯◯支店」のような書き方は住所として扱いません。

### 1.3 組織名と地名は、名前だけあって中身がない

`get_active_recognizers()` は `ORG_JP`（組織名）と `LOC_JP`（地名）も返します。
名前は返りますが、**それを供給する認識器は 1 つも登録されていません**（ツリー全体で、
この 2 つの語はこの 1 行にしか出てきません）。

つまり **組織名も地名もマスキングされません。** 一覧に名前があるからといって、
働いていると思わないでください。

### 1.4 言語モデルが入っていないと、`standard` でも規則だけに退行する

氏名・住所の判定には spaCy / GiNZA の言語モデルが要ります。これが入っていない環境では、
`pii_mode` が `standard` のままでも、判定は正規表現だけに退行します。

起動時に `launch.sh` が存在を確かめ、無ければ次の警告を出します。

```
⚠️  spaCy モデル '...' が未導入です (standard PII が regex フォールバックします)。'pip install -r requirements.txt' を実行してください。
```

**この警告が出ているときは、氏名も住所もマスキングされていません。** 起動は止まらないので、
警告を読み飛ばすと、マスキングが効いているつもりのまま使ってしまいます。

### 1.5 パスワードと API キーは、空白・日本語・改行で切れる

`PASSWORD` と `APIKEY` の規則は、値の部分を ASCII の図形文字だけで拾います
（`guardrail.py` の該当ブロックに「値は ASCII 図形文字 `[!-~]` のみ（空白・CJK で必ず切れる）」
と明記してあります）。このため、次のものは取れません。

- 値の途中に空白が入っているもの（`パスワード: abc def`）→ `abc` までで切れます
- 値の途中に日本語が入っているもの
- 改行をまたぐ値（ラベルと値の間の空白は タブと空白だけに限られ、改行はまたぎません）

また、ラベルと値の間に区切り（`:` `：` `=` `＝` または「は」）が無いものは
対象外です。`password protection` のような一般的な語を巻き込まないための設計で、
その代償として「パスワード　abcdefgh」のような空白区切りは取れません。

### 1.6 PDF から取り出した文字に空白が入り、電子メールがマスキングを逃れることがある

PDF は文字の並びではなく、文字を置く位置の情報として組まれています。そこから文字を
取り出すとき、元の見た目には無かった空白が語の途中に入ることがあります。

マスキングの規則は文字の並びを見ているので、空白が 1 個入るだけで当たらなくなります。
電子メールアドレスの場合、次のようになります。

- `taro.yamada@example.co.jp` → マスキングされる
- `taro.yamada @example.co.jp` → **マスキングされない**（`@` の前で切れる）
- `taro.yamada@ example.co.jp` → **マスキングされない**（`@` の後ろで切れる）
- `taro. yamada@example.co.jp` → `yamada@example.co.jp` の部分だけがマスキングされ、
  `taro.` は残る

同じことは電話番号・カード番号など、他の種別でも起こり得ます。
**PDF を取り込んだときは、マスキングが当たっているかどうかを目で確かめてください。**
取り込み後のチャンク一覧から実際の本文を見られます。

### 1.7 管理者が原文を見られるかどうかは、暗号鍵と宛先しだい

役割が `admin` のときは、マスキング前の原文を見られる設計です（`rag.py` の `tier_for_role`）。
ただし、次の 3 つの場合は管理者でもマスキング済みのものしか出ません。

1. **回答用 LLM の宛先が外部を向いているとき。**
   `routers/chat.py` の `_effective_send_tier` は、送り先が自マシン内・
   コンテナのホスト側・私設アドレス帯のいずれでもない場合、役割によらずマスキング済みへ
   落とします。宛先を判定できないときもマスキング済みに倒します。
2. **暗号化された保管の暗号鍵（`store/secret.key`）が合わないとき。**
   原文は暗号化して保管してあり、`rag.py` の `_vault_substitute_raw` が復号します。
   復号できない行はマスキング済みの本文をそのまま使います
   （画面に暗号文を出さないため、あえてそうしてあります）。
   配布物を受け取ったあとで暗号鍵を入れ替えると、それ以前に取り込んだ資料は
   管理者でも原文を読めなくなります。
3. **質問文そのもの。**
   質問文へのマスキングは役割で分けていません。管理者が質問文に IP アドレスを書いても、
   その IP はマスキングされてから検索と LLM へ渡ります。

以前の版のこの文書には「管理者でも IP がマスキングされる（調査中）」と書いてありましたが、
上の 3 つが理由です。不具合ではありません。

---

## 2. 読み込めない資料の形式

取り込める形式は `rag.py` の `SUPPORTED_EXTENSIONS` に書いてあるものだけです。

| 種類 | 拡張子 |
|------|--------|
| 文書 | `.txt` `.md` `.csv` `.pdf` `.docx` |
| 表計算・プレゼン | `.xlsx` `.xls` `.pptx` |
| ウェブ・メール | `.html` `.htm` `.eml` |
| 書庫 | `.zip` |
| 画像 | `.jpg` `.jpeg` `.png` `.heic` `.webp` `.gif` |

これ以外は取り込みの対象から外れます。よく持ち込まれるもので、**扱えない**ものを
挙げます。

- 古い Office 形式: `.doc` `.ppt`（`.xls` だけは扱えます）、`.rtf`
- OpenDocument 系: `.odt` `.ods` `.odp`
- 構造化データ: `.json` `.xml` `.yaml`
- メール: `.msg`（Outlook 形式。`.eml` のみ対応）
- 電子書籍: `.epub`
- 音声・動画: `.mp3` `.wav` `.m4a` `.mp4` `.mov` など
- 画像の一部: `.tif` `.tiff` `.bmp` `.svg`
- 書庫の一部: `.7z` `.rar` `.tar` `.gz`（`.zip` のみ対応）

そのほかの制限:

- **zip の入れ子は 1 段だけです。** zip の中の zip は開きません
  （`rag.py` の取り出し処理が、中身の拡張子が `.zip` のものを飛ばします）。
- **画像ファイルは読めません（現在開発中）。**写真やスクリーンショットの中身で探すことはできません。文字起こし（OCR）の仕組みは入っていません。
- PDF が画像として作られている（スキャンしただけの）場合、文字が 1 つも取れません。
  文字認識（OCR）の仕組みは入っていません。
- 暗号化された PDF や壊れた文書は飛ばされます。取り込み結果に
  「読めない/空: ○件」として出ます。

---

## 3. 音声で話しかけること

- 音声の機能は撤去済みです。この配布物に音声からの文字起こしはありません。
- 旧来の経路 `/api/transcribe` は**もう繋がっていません**。
  `server.py` で `include_router` を外してあります（マスキング前の文字起こしがそのまま
  返る穴だったため、あえて外したものです）。

---

## 4. 資料をアップロードする受け口はない

画面やAPIからファイルを送りつける受け口は**撤去済み**です
（`routers/sources.py` の冒頭に「アップロード保存先 `_uploads_root` と
`/api/sources/upload` を撤去した。取り込みは取り込みフォルダ経由に一本化する」と
あります）。

資料は、あらかじめ決めた**取り込みフォルダに置いてから**画面で選びます。
アプリの中に資料のコピーを作る場所はもうありません。

---

## 5. 外部への送出が止まる条件

これは「できないこと」というより「あえて止めていること」です。
判定できないときは必ず止める側に倒します。そのぶん、機能が働かないように見えます。

- **CRAG の下読み。** 検索結果が質問に足りているかを LLM に下読みさせる処理は、
  宛先が自マシン内でないとき、および**宛先を判定できないとき**は実行しません
  （`rag.py`）。実行しない場合は「検索結果をそのまま採用」に落ちます。
  画面には `[CRAG] 非ローカル宛のため下読みをスキップします` と出ます。
- **会話の要約と、回答からの手がかり抽出。** どちらも同じ判定を使い、
  外部宛（判定不能を含む）では送らずに空を返します（`routers/chat.py`）。
- **役割による原文送出。** 宛先が外部なら、管理者であってもマスキング済みのものだけを送ります
  （前述の `_effective_send_tier`）。
- **マスキングが失敗したら止まる。** 質問文・回答のいずれも、
  マスキング処理が例外で落ちた場合は 503 を返して処理を打ち切ります。
  マスキング前のものを代わりに返すことはしません（`routers/chat.py`）。
- **マスキングなし取り込みと外部埋め込みの組み合わせは拒否します。**
  古い版で作られた「マスキングなし」のコレクションは、外部の埋め込みを有効にしている間は
  公開（publish）できません（`rag.py`）。

---

## 6. 同時に使うときの制約

- **公開（Publish）は同時に 2 件までです。** 3 件目は 5 秒待って空きが出なければ
  失敗として返します（`server.py`。画面には
  「他のPublishが多すぎます。少し待ってから再試行してください。」と出ます）。
- **LLM の同時実行は既定で 3 件までです**（`cynovela.yaml` の `llm.max_concurrent`。
  `server.py` がこの値でセマフォを作ります）。4 件目は前の呼び出しが終わるまで待ちます。
- **保管は単一の SQLite ファイルです**（WAL 方式）。書き込みが重なる場面では
  待ちが発生します。何十人も同時に取り込みを回す使い方は想定していません。
- ベクターインデックス（ChromaDB）も同じマシンのファイルです。
  複数のプロセスから同じインデックスを書き換えないでください。

---

## 7. モデルの差し替えの制約

詳しい手順は [operations.md](operations.md) にあります。要点だけ書きます。

- **埋め込みモデルは、版（snapshot）まで一致していなければなりません。**
  `BAAI/bge-m3` の snapshot 版まで揃える必要があります。
  **版が違うとベクトルの数値が変わり、この機材で作られたインデックスと混ざって検索順位が壊れます。**
  版が違う場合は起動時と公開時に警告が出ます。警告が出たら、版を揃えるか
  インデックスを全部作り直してください。
- **パッケージ版もソース版も、AIモデルを同梱していません。** モデルを置かないまま起動用スクリプトを
  実行すると、初回の起動でインターネットから取得するかどうかの確認が出ます。
  取得しない場合は、**起動する前に止まります**。
- **`host.containers.internal` はコンテナの外では名前解決できません。**
  ホスト側で直接起動する場合は `127.0.0.1` に書き換えてください
  （コンテナ版の配布物は、この 1 語だけは自動で読み替えます。
  別のホスト名や IP を書いた場合は読み替えず、書いたとおりに使います）。
- **外部アクセラレータの画像の受け口は未実装です。** 呼ぶと 501 を返します。
- **再ランクの宛先は、どの配布物にも入っていない外部アクセラレータになっています。**
  同梱の `cynovela.yaml` は `reranker.device` が `external`、`reranker.base_url` が
  `http://localhost:18850` ですが、その番地で答えるものは、どのダウンロードしたファイルにも
  入っていません。∴ 検索のたびにその番地へ当たりに行って失敗し、退避します。再ランクの
  重みが置かれていれば本体の中で再ランクし（`models` のダウンロードしたファイルに入っています）、
  置かれていなければ再ランクなしで素通しします。退避のたびにログが 1 行出て、
  設定の画面にも状態が出ます。答えそのものは返ります。外部を選んでいるのは
  `reranker.device` で、同梱の `reranker.provider` はすでに `cross_encoder` です。
  ∴ `cynovela.yaml` を書き換えられる形態では、`device` を空にすれば本体の中で
  再ランクする道が退避ではなく最初の選択になります。
- **起動時の `--mode` は、実際には切り替わらないものがあります。**
  `--mode` の説明文にそのまま書いてあります。
  `lite` と `lite-en` は軽量モデルへの切り替えが未配線で、現状は既定の `text` と
  同じ `bge-m3` で動きます。`minimal` は TF-IDF が未統合で、こちらも `bge-m3` が要ります
  （モデルを置いていない環境では取り込みができません）。
  **どのモードを選んでも、必要なモデルの大きさは変わりません。**

---

## 8. 骨組みだけで中身がない機能

呼ぶと `NotImplementedError` になるもの、または抽象宣言だけのものです。
（行番号は書きません。すぐにずれるためです。ファイル名とクラス・メソッド名で示します。）

| ファイル | クラス・メソッド | 状態 |
|---------|----------------|------|
| `providers/classifier.py` | `ClassifierProvider.classify` | 抽象（差し替え用の口） |
| `providers/embedding.py` | `EmbeddingProvider.embed` / `.test_connection` | 抽象 |
| `providers/embedding.py` | `MLXEmbeddingProvider.embed` | 未実装（将来） |
| `providers/reranker.py` | `RerankerProvider.rerank` / `.test_connection` | 抽象 |
| `providers/reranker.py` | `MLXReranker.rerank` | 未実装（将来） |
| `providers/vector_store.py` | `VectorStoreProvider.add` / `.search` / `.delete_collection` / `.export` / `.import_data` / `.test_connection` | 抽象 |
| `providers/vector_store.py` | `QdrantVectorStore.add` / `.search` / `.delete_collection` / `.export` / `.import_data` | 未実装（骨格のみ） |
| `providers/vector_store.py` | LanceDB バックエンド | 初期化のみで実体は未実装。パッケージ未導入時は拒否されます |
| `services/rag_strategies.py` | `GraphRAGStrategy.retrieve` / `.build_graph` / `.traverse_with_acl` | 未実装（将来） |
| `services/agent_runtime.py` | `AgentRuntime.run` / `.call_tool` / `.available_tools` | 抽象宣言のみ。実装したクラスは 1 つもありません |

つまり:

- **ベクターの保管先を Qdrant に替えることはできません。** 動くのは ChromaDB だけです。
- **Apple Silicon 向けの MLX 経路は使えません。** 埋め込みも再ランクも未実装です。
  （Apple Silicon の GPU を使いたい場合は、外部アクセラレータ経由になります。
  [operations.md](operations.md) を参照してください。）
- **ベクターの保管先を LanceDB に替えることもできません。** 初期化しかありません。
- **グラフを使った検索（GraphRAG）は使えません。**
- **エージェントに作業をさせることはできません。** 型の宣言だけがあります。

---

## 9. Kubernetes 一式は、そのままでは動かない

- **コンテナ版の配布物には `deploy/k8s/20-deployment.yaml` が入っていません。**
  配布物を作る `tools/build-dist.sh` が、`tar` を作る直前にこのファイルを落としています。
  残りの 3 つ（namespace / pvc / service）だけでは、アプリのコンテナが 1 つも立ちません。
- **ホスト直起動版には `deploy/` そのものがありません。**

Kubernetes で動かしたい場合は、Deployment の定義を自分で書く必要があります。

---

## 10. その他の制限と注意

### 起動の形態とデータの場所

- `--demo` を付けると、デモのデータベースで起動します（`store/db/demo.db` と
  `store/vector/demo/chroma`）。`--demo` の初回起動時に、サーバが同梱の
  `dummy-corpus/` をその場で取り込み、データベースとインデックスをこの機材の上で
  作ります。2 回目以降の起動では取り込み直しません。
- 何も付けなければ本番で、**空のデータベース**で起動します
  （`store/db/cynovela.db` と `store/vector/default/chroma`）。
- **どちらも再起動で消えません。** 起動のたびに初期化されることはありません。
  消したい場合は自分でファイルを消してください。
- 配布物にはデータベース・インデックス・鍵ファイルは入っていません。この機材の上で
  作られます: 鍵は初回起動時、デモのデータベースとインデックスは `--demo` の初回起動時に、
  **配布物の中の `dummy-corpus/` だけ**から作られます。作った側の作業用の資料は
  1 件も入っていません。詳しくは配布物の `BUNDLED-DATA.md` を見てください。
- **`store/` 自体の場所は形態で違います。** 展開して使うフォルダの形では、そのフォルダの
  中の `store/` です。アプリ版（準備中。この版には入っていません）は入れたあとの包みが
  読み取り専用のため、入口が `CYNOVELA_DATA_ROOT` を与え、上の道筋は
  `~/Library/Application Support/Cynovela/` からの相対として扱われます。
- **最初のユーザー名とパスワードは、初回起動時に画面へ出ます（`--demo` でも本番でも
  初回に出ます）。** 起動用スクリプトはデータベースのファイルがすでに在るかどうかで
  「初回である」と判定します。配布物にはどちらのデータベースも入っていないため、
  どちらの形でも初回起動でちゃんと出ます。この表示を見逃した場合は、起動用スクリプトと
  同じ場所にある `cynovela.yaml` の `auth:` の下、`admin_initial_password:` の行から
  読めます（`grep admin_initial_password cynovela.yaml`）。どちらの道でも、最初の
  ログインで変更を求められる点は同じです。

### 横断検索

MCP のツールには `search_across_collections`（複数のコレクションをまたぐ検索）が
ありますが、**画面（GUI）には横断検索の入口がありません。**
画面からはワークスペースを 1 つ選んで検索します。

### workspace の分離

- **ChromaDB 上の workspace の分離は論理境界（collection 名）であり、物理境界（別ディレクトリ等）は
  実装されていません。** 1 つの Chroma の保管先ディレクトリにすべての collection が入り、
  分けているのは `{collection_id}__raw` と `{collection_id}__masked` という collection 名です
  （`providers/vector_store.py`）。
- 検索に `workspace_id` を渡すと、メタデータの `where` 条件でさらに絞り込みますが、これは同じ保管先の
  中での絞り込みであって、置き場所を分けているわけではありません。
- BM25 のインデックスは `(workspace_id, tier)` をキーにした辞書としてメモリに持つため、こちらも
  ディレクトリではなくキーで分けています（`rag.py`）。

### MCP

- `mcp_server.py` は 25 個の道具（既定で見えるのは 22 個。管理系の 3 個は CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を設定したときだけ現れます）を提供します。
- MCP サーバーは、内部で Cynovela の REST API に認証付きで問い合わせる作りです。
  つまり **本体が動いていないと MCP も動きません。**
- MCP を動かす Python の実行ファイルは、環境変数 `CYNOVELA_MCP_PYTHON` で指定できます。
  指定が無ければ、いま動いている Python をそのまま使います（`routers/mcp.py`）。

### 回答の作り

- **構造化された回答は返せません。** 回答は自由形式（必要に応じて Markdown）です。
  JSON や決まったタグでの応答は用意していません。
  出典の引用（`[1][2]` の形）は実装済みです。
- **信頼度の低いときの自動切り替えはありません。**
  `cynovela.yaml` に `confidence_threshold`（既定 `0.4`）がありますが、
  下回ったときに一般知識モードへ自動で切り替えるような動きは組み込まれていません。
  値は設定としては定義済みですが、検索結果が 0 件のときに
  `GENERAL_KNOWLEDGE_SYSTEM_PROMPT` へ自動切替する処理は未統合で、
  検索パイプラインからの除外ロジックも **部分統合** に留まります。
- **回答の自己評価は単純な規則です。** `adaptive_rag.py` の
  `evaluate_answer_quality()` は「回答が空」「60 文字未満でヒットも少ない」
  「否定的な言い回しを含む」で足りているかを決めます。LLM に評価させてはいません。

### 廃止した機能

| 機能 | 状態 |
|------|------|
| `--mock` 起動 | 撤去済み。起動の選択肢に存在しません。モデル不要の起動もできません |
| `/chat-popup` | 410 Gone を返します。全画面のチャットへ移行しました |
| `user_id` だけのログイン | 撤去済み。`username` と `password` が必要です |
| `/api/auth/users` の未認証許可 | 撤去済み。常に管理者の認証が要ります |
| `--pii-mode` の起動指定 | 廃止。`cynovela.yaml` の `pii_mode` で指定します |
| 旧 `/api/transcribe` | 撤去済み。音声の機能はありません |
| `/api/sources/upload` | 撤去済み。取り込みフォルダ経由に一本化しました |

### 通行証（ログイン用のトークン）

通行証は `POST /api/auth/login` が発行する JWT です。署名鍵は
**配布物には入っていません**。受け取った側で初回起動時に暗号乱数から自動生成し、
`store/db/jwt/secret.key` に保存します（`config.py` の
`_load_or_create_jwt_signing_key`）。配布物を作るときに、この鍵は必ず落とします
（共有すると、よそで発行された通行証が通ってしまうためです）。

鍵の保存に失敗した場合は、その起動のあいだだけ有効な鍵になります。
この場合、再起動すると発行済みの通行証は無効になります（再ログインで通ります）。

**1.0.7 から、通行証は呼ぶ側が頼まないかぎり期限を持ちません。** 従来は発行から
8時間で必ず使えなくなっていました。いまは `POST /api/auth/login` に
`expires_in_hours` か `expires_in_seconds` を渡さないかぎり、期限の入っていない
通行証が出ます。承知しておくべきことが2つあります。

- **ログアウトしても、その通行証は使えなくなりません。** `POST /api/auth/logout` は
  リフレッシュトークンと記憶の中の入室記録を消しますが、通行証そのものは署名だけで
  確かめられるので、写しを持っている側は使い続けられます。従来は8時間という下限が
  ありましたが、いまはありません。漏れた通行証を無効にする道は、
  `store/db/jwt/secret.key` を消して起動し直すことだけで、そのときは**すべての**
  通行証が無効になります。
- 自分の手の届かないところへ通行証を渡すときは、`expires_in_hours` を渡してください。

### 落とし穴

- ChromaDB の `PersistentClient` は、間違ったパスを渡してもエラーになりません。
  空のデータベースを黙って作ります。**検索が 0 件になったときは、
  まずインデックスの場所が合っているかを疑ってください。**
- LM Studio の API に `max_tokens` を渡さないでください。
  思考する型のモデルで、考えるためのトークンを使い切ってしまいます。
- **画面は、誰もログインしていないうちから `/api/settings/embedding` を叩き、
  ログインした後も叩き続けます。** 埋め込み経路の状態を出す帯が、最初の5分は5秒ごと、
  その後は60秒ごとにこの受け口を見に行きます。見に行き始めるのはページを開いた
  ときであって、ログインが通ったときではありません。ログイン前と閲覧者では受け口は
  401 か 403 を返し、帯はそれを飲み込んで何も出しませんが、要求そのものは飛び、
  記録にも残ります。漏れではありません（受け口は断っており、答えてはいません）。
  記録が賑やかになるだけです。

---

## 11. 1.0.7 で分かったこと

1.0.7 を用意する過程で実際に測ったものです。近く変わるからではなく、知らないと
つまずくのでここに書いてあります。

### 11.1 API から控えに戻しても、控えの中身になるとはかぎらない

`POST /api/admin/backups/{name}/restore` は、保存してある `cynovela.db` を、
**サーバが動いたまま**、いまのデータベースのファイルへ上書きします。SQLite は
WAL の形で動いているので、動いているプロセスは上書きの前から
`cynovela.db-wal` と `cynovela.db-shm` を握ったままです。∴ その相方が、戻した
ばかりの中身の上へ古い中身を書き戻すことがあります。口はどちらの場合も
`{"ok": true}` を返します。

**通る道:** サーバを止め（`bash stop.sh`）、ファイルを手で置き直してから起こし直します。

```
bash stop.sh
cd store/db
mv cynovela.db     cynovela.db.aside
mv cynovela.db-wal cynovela.db-wal.aside   # 在れば
mv cynovela.db-shm cynovela.db-shm.aside   # 在れば
cp ../backups/<控えの名前>/cynovela.db .
rm -rf ../vector/default/chroma
cp -R ../backups/<控えの名前>/chroma ../vector/default/chroma
cd ../..
./launch.sh
```

**`-wal` と `-shm` の相方も、データベースと一緒に退けてください。** `cynovela.db`
だけを退けると、SQLite は隣にあるファイルのものではない WAL を見つけることになり、
出来上がりは古い中身でも新しい中身でもなくなります。

### 11.2 控えに入るのはデータであって、設定ではない

`_create_backup` が写すのはちょうど2つ、データベース（`cynovela.db`）と索引
（`chroma`）だけです。次は**写しません**。

- `cynovela.yaml` — ファイルに書いてある設定の全部。LLM の宛先、伏字の強さ、
  置き場所の指定を含みます
- `store/db/jwt/secret.key` — 通行証に署名する鍵

∴ 戻して返ってくるのは、資料・利用者・索引です。設定は戻りません。鍵が動いていない
ので、前に発行した通行証も全部そのまま通ります。設定も残したいなら
`cynovela.yaml` は自分で写してください。

### 11.3 書き出しに書かれる「次元」は、決め打ちの数である

フルエクスポートの `_meta.json` には `"embedding_dim": 1024` が入ります。この数は
`routers/chat.py` に直に書かれていて、ベクターを測ってはいません。同梱の BGE-M3 に
対しては正しい値です。幅の違う埋め込みモデルに差し替えると、この行は 1024 のまま
事実と食い違います。同じファイルのモデルの**名前**のほうは、動いている設定から
読んでいるので正しい値です。

### 11.4 Ollama を使うと、文脈の長さは Ollama の既定のままになる

Cynovela は `num_ctx` を Ollama へ送りません。送っているのは `top_p`・`top_k`・
`max_tokens`・`repeat_penalty`・`seed`・`think` です。∴ Ollama は自分の既定の
文脈の窓を使い、入りきらなかったぶんを**黙って捨てます**。捨てられた断片を無視した
答えが返ってきます。渡す材料に見合う長さを Ollama 側で決めてください
（Modelfile の `PARAMETER num_ctx`、または `OLLAMA_CONTEXT_LENGTH`）。

### 11.5 取り込んだ作業場所は、ベクターだけで探される

`POST /api/workspaces/import` はベクターを戻します。1.0.7 からは、その中の番号も
書き換えるので、取り込んだ作業場所は再度の公開なしで答えられます。戻**さない**のは
`chunks` の表で、BM25 のキーワード索引はここから作られます。∴ 取り込んだ作業場所は、
ベクターの近さと再並べ替えだけで探されます。合わせ技のうちキーワード側は効いていません
（当たりの `bm25_score` が全て `0.0` になることで見えます）。キーワード側も効かせたい
ときは、そのまとまりをもう一度公開してください。

### 11.6 測っていないこと: conda の入っていない Mac でのパッケージ版

パッケージ版は Python も conda も要らない形として作られています。同梱の環境から
起き上がることは作った機械の上で測りましたが、その機械には conda が入っています。
∴ conda が**まったく**入っていない Mac で同じになるかは、この走行では言えません。
「conda 不要」は、そう作られていて、conda の在る機械で確かめた、という意味に
とどめてください。conda の無い機械で測った、ではありません。

### 11.7 chewie では直し、falcon では直していないもの

次は chewie で直し、コンテナ版（falcon）へは 1.0.7 の時点では**わざと**当てていません。
falcon はその箇所のコードが違っており、その版では falcon を書き換えて合わせることを
していないためです。

| 何 | 当てなかった理由 |
|---|---|
| 時間切れの文言 | falcon に `_timeout_answer` が無く、古い文が本文中の2か所に置かれている |
| 出典の番号を MCP まで通すこと | falcon の MCP サーバは版が古い（道具 11件・chewie は 25件） |
| `login` / `logout` を含む CLI | falcon に `cynovela-cli.py` は無い。falcon 自身の古い `cynovela_cli.py` には `login` も `logout` も無い |

**このうち1件は、その後 falcon へも当てました。**「同じフォルダの走査を2本同時に
始められない件」は 2026-08-26 に falcon へ移してあります。`falcon/server.py` の
`_do_scan` は、モジュール階層の錠と source の id の集合で守る薄い入口になり
（始める前に足し、`finally` で外す）、元の本体は `_do_scan_body` へ改名されました。
走査を呼ぶ 8 か所すべてがこの入口を通ります。falcon には今も `scan_jobs` の表が
無いため、chewie が同じ錠の中で行っている job の行への書き戻しに当たるものは
falcon にはありません。錠そのものは同じです。


---

## 12. 認証・認可と通信

- **認証は JWT です。** `POST /api/auth/login` が発行し、`--demo` 起動でも必要です。
  旧 `Bearer demo-token-<user_id>` 形式の固定トークンは 2026-07-29 に廃止済みです。
  署名鍵の作られ方と置き場所は §10「通行証（ログイン用のトークン）」にあります。
- **RBAC の実装範囲。** `routers/` 配下の 36 ファイルのうち 34 ファイルに認可チェックが
  入っています。認証そのものは起動形態によらず強制され、`--demo` 起動でも緩みません。
- **API キー管理機能はありません。** ユーザー単位の API キー発行・失効機能は未実装です。
- **HTTPS 化は未対応です。** 本体は HTTP のみで待ち受けます。TLS 終端はリバースプロキシ
  （nginx 等）に委譲する必要があります。
- **LLM との通信も平文です。** LM Studio / Ollama への接続も HTTP 平文です。
  LAN 外への公開は推奨しません。
- **Embedding / Reranker の設定は永続化されません。** 実行時変更（UI 経由）は YAML に
  書き戻されず、再起動で既定値に戻ります。

---

## 13. 定義はあるが統合されていない連携

- **DataSyncService は publish につながっていません。** ハッシュ差分同期はログ出力のみで、
  実際の `rag.publish` への接続は noop です。
- **差分検出はパス単位です。** パスの集合に対する追加・削除は検出します（既定 60 秒間隔）が、
  `content_hash` 比較は実装されておらず比較方式も確定していないため、ファイルの*内容*の
  変更はこの経路では検出されません。
- **`confidence_threshold` の除外ロジックは検索パイプラインへ部分統合に留まります。**
  実際の挙動は §10「回答の作り」にあります。
- **構造化回答テンプレートは未実装です。** LLM の回答を JSON や `<answer>` タグなどの
  構造化フォーマットで固定する機能はありません。自由形式の回答が標準です。
  導入するかどうかは決まっていません。
- **i18n 切替の一部要素は固定です。** 言語切替（日本語 / 英語）で表示制御される要素の一部が
  切替に追随しません。
- **タブ初期化前に隠れている UI 要素があります。** JavaScript の初期化が終わるまで
  `display:none` のままです。

---

## 14. テストでスキップされている領域

- **デモモード関連。** 認証境界テスト 4 件が `@pytest.mark.skip` のままです
  （`tests/test_auth_boundary.py` の 11 / 51 / 56 / 157 行）。理由文には
  「`--demo` モードでは認証バイパスが仕様」と書かれていますが、2026-07-29 に `--demo` 起動でも
  認証を強制する形へ変えたため、この理由はすでに実装と合っていません。
- **Sources API。** path 登録形式のため一部テスト 2 件をスキップしています。
- **Publish Semaphore。** モジュールスコープでのモック注入困難により xfail 1 件です。

---

## 15. 完了していない事項

以下は [reference/changelog.md](reference/changelog.md) に未完了として記録されている事項です。
予定ではなく、現在の作りの状態として書きます。

| 項目 | 現在の状態 |
|---|---|
| HIGH 優先度として記録されているバグ | `import_workspace` の DB → Chroma 順序逆転、`admin_cleanup_chromadb_orphans` の競合状態、workspace 分離の物理境界（§10「workspace の分離」参照）、workspace-A → workspace-B の越境チェックなど |
| 間接プロンプトインジェクション検出 | 取り込んだ文書を経由する攻撃を対象とした検出機構は未実装です |
| Reranker の実モデルでの試験 | CrossEncoder などでの検証を行っていません |
| KnowledgeCatalog | Chunks ビューアのメタデータ検索と出典追跡は未実装です |

---
