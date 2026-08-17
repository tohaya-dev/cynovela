# このツールにできないこと（既知の制限）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual in order to
> understand the concepts of AI infrastructure tools hands-on. It is not a commercial
> product and not an official implementation.
> The implementation is entirely original, and is made of an OSS stack:
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

This document describes what Cynovela **cannot** do. An explanation of what it can do is
in `README.md` and `QUICKSTART.md`. Here we only write the things that will not meet your expectations.

The version is `` (`APP_VERSION` in `core/version.py` is the only source of this
value, and `GET /api/health` and `/docs` read it from there).

---

## 1. What masking cannot do

**This is the most important section.** Masking is a mechanism for hiding personal information,
but there is a clear limit to what it can hide. **Even when masking has been applied, it does
not mean that all of the personal information in a document has been removed.** Something that
cannot be hidden always remains.

### 1.1 The rules can only catch the 13 types that have a fixed shape

The types written in `PII_PATTERNS` in `guardrail.py` are only the following 13.

| Type | What it means |
|------|-----------|
| `URL` | An address starting with http / https |
| `EMAIL` | Email address |
| `PHONE_JP` | Mobile phone number (070 / 080 / 090) |
| `PHONE_LAND` | Landline phone number |
| `CREDIT` | Credit card number |
| `MYNUMBER` | My Number (Japanese individual number) |
| `PASSPORT` | Passport number (2 letters + 7 digits) |
| `IPV4` | IPv4 address |
| `PASSWORD` | A labeled value such as "パスワード: xxxx" |
| `APIKEY` | API key / access token |
| `PRIVATEKEY` | A private key block (`-----BEGIN ... PRIVATE KEY-----`) |
| `SSN` | US Social Security Number (3-2-4 shape) |
| `IBAN` | International Bank Account Number |

Nothing other than these is masked by the rules, not even once. For example, employee numbers,
customer numbers, contract numbers, bank account numbers (other than IBAN), vehicle numbers and
insurance card numbers are out of scope.

The rules match on "shape". If the shape is broken, they do not match. Conversely, an unrelated
number that happens to match the shape is masked (a number of exactly 12 digits being masked as
a My Number is an example of this; it is intentional, as the result of giving priority to
preventing leaks).

### 1.2 Names and addresses are left to language analysis. With `lite` they are not masked at all

Names and addresses are not in the 13 types above. Their shape is not fixed, so the rules cannot
catch them, and they are handled on the language analysis (NER) side.

- The setting is `pii_mode` in `cynovela.yaml`. The default is `standard`.
- Only when it is `standard` do `PERSON_JP` (name) and `ADDRESS_JP` (address) work.
- **If you set `pii_mode` to `lite`, neither names nor addresses are masked at all.**
  `lite` switches to a path that judges with regular expressions only, and the recognizers for
  names and addresses are not assembled in the first place (see `get_active_recognizers()` and
  `detect_pii()` in `utils/metadata/pii.py`).

Name detection only matches words that are registered as family names or given names. Rare names,
katakana spellings of foreign names, nicknames, and writings that are fused with a job title are
missed. Addresses are also only looked at in the form that starts from a prefecture and in the
shape of a postal code, so writings such as "本社ビル 3 階" or "◯◯支店" are not treated as addresses.

### 1.3 Organization names and place names have a name but no substance

`get_active_recognizers()` also returns `ORG_JP` (organization name) and `LOC_JP` (place name).
The names are returned, but **not a single recognizer that supplies them is registered** (in the
whole tree, these two words appear only on this one line).

In other words, **neither organization names nor place names are masked.** Do not assume that
they are working just because their names are in the list.

### 1.4 Without a language model, even `standard` falls back to rules only

Detecting names and addresses requires the spaCy / GiNZA language models. In an environment where
these are not installed, detection falls back to regular expressions only, even while `pii_mode`
is still `standard`.

At startup, `launch.sh` checks whether they exist, and if not it prints the following warning.

```
⚠️  spaCy モデル '...' が未導入です (standard PII が regex フォールバックします)。'pip install -r requirements.txt' を実行してください。
```

**While this warning is shown, neither names nor addresses are being masked.** Startup does not
stop, so if you skip past the warning you will keep using the tool while believing that masking
is in effect.

### 1.5 Passwords and API keys are cut off by spaces, Japanese characters and line breaks

The rules for `PASSWORD` and `APIKEY` pick up the value part using ASCII graphic characters only
(the corresponding block in `guardrail.py` states explicitly that "値は ASCII 図形文字 `[!-~]` のみ
（空白・CJK で必ず切れる）"). Because of this, the following cannot be caught.

- A value with a space in the middle (`パスワード: abc def`) → it is cut off after `abc`
- A value with Japanese characters in the middle
- A value that spans a line break (the whitespace between the label and the value is limited to
  tabs and spaces, and it does not cross a line break)

Also, anything without a separator (`:` `：` `=` `＝` or "は") between the label and the value is
out of scope. This is a design choice to avoid catching common phrases such as `password
protection`, and the price paid for it is that a space-separated form such as "パスワード　abcdefgh"
cannot be caught.

### 1.6 Text extracted from a PDF can contain spaces, letting an email address escape masking

A PDF is composed not as a sequence of characters but as information about where to place each
character. When text is extracted from it, spaces that were not in the original appearance can be
inserted in the middle of a word.

The masking rules look at the sequence of characters, so a single inserted space is enough to stop
them from matching. For an email address, this looks as follows.

- `taro.yamada@example.co.jp` → masked
- `taro.yamada @example.co.jp` → **not masked** (cut off before the `@`)
- `taro.yamada@ example.co.jp` → **not masked** (cut off after the `@`)
- `taro. yamada@example.co.jp` → only the `yamada@example.co.jp` part is masked, and
  `taro.` remains

The same thing can happen with other types, such as phone numbers and card numbers.
**When you have ingested a PDF, check with your own eyes whether masking has been applied.**
You can see the actual text from the chunk list after ingest.

### 1.7 Whether an administrator can see the original text depends on the key and the destination

When the role is `admin`, the design is that the original text before masking can be seen
(`tier_for_role` in `rag.py`). However, in the following 3 cases, even an administrator only gets
the masked version.

1. **When the destination of the answering LLM points outside.**
   `_effective_send_tier` in `routers/chat.py` drops to masked regardless of role when the
   destination is none of: inside the same machine, the container's host side, or a private
   address range. It also falls back to masked when the destination cannot be determined.
2. **When the key of the vault (encrypted storage) does not match.**
   The original text is stored encrypted, and `_vault_substitute_raw` in `rag.py` decrypts it.
   For rows that cannot be decrypted, the masked text is used as-is
   (this is deliberate, so that ciphertext is not shown on the screen).
   If you replace the key after receiving the package, the documents ingested before that point
   can no longer be read as original text, even by an administrator.
3. **The question text itself.**
   Masking of the question text is not divided by role. Even if an administrator writes an IP
   address in the question, that IP is masked before it is passed to search and to the LLM.

An earlier version of this document said "even an administrator has IPs masked (under
investigation)", and the 3 items above are the reason. It is not a defect.

---

## 2. Document formats that cannot be read

Only the formats written in `SUPPORTED_EXTENSIONS` in `rag.py` can be ingested.

| Kind | Extension |
|------|--------|
| Documents | `.txt` `.md` `.csv` `.pdf` `.docx` |
| Spreadsheets / presentations | `.xlsx` `.xls` `.pptx` |
| Web / mail | `.html` `.htm` `.eml` |
| Archives | `.zip` |
| Images | `.jpg` `.jpeg` `.png` `.heic` `.webp` `.gif` |

Anything else is excluded from ingest. Here are the ones that are often brought in but
**cannot be handled**.

- Old Office formats: `.doc` `.ppt` (only `.xls` can be handled), `.rtf`
- OpenDocument family: `.odt` `.ods` `.odp`
- Structured data: `.json` `.xml` `.yaml`
- Mail: `.msg` (Outlook format; only `.eml` is supported)
- E-books: `.epub`
- Audio and video: `.mp3` `.wav` `.m4a` `.mp4` `.mov` and so on
- Some images: `.tif` `.tiff` `.bmp` `.svg`
- Some archives: `.7z` `.rar` `.tar` `.gz` (only `.zip` is supported)

Other limits:

- **Nesting of zip is only one level.** A zip inside a zip is not opened
  (the extraction step in `rag.py` skips entries whose extension is `.zip`).
- **By default, the contents of images are not read.** The default behavior is `filename_only`,
  which puts only the file name into the index (`_extract_image_text` in `rag.py`). Characters
  inside an image are not read. There are settings that generate a caption
  (`caption` / `lm_studio`), but the bundled `cynovela.yaml` has no `image:` entry, so the default
  is kept.
- If a PDF was made as an image (merely scanned), not a single character can be extracted.
  There is no OCR mechanism.
- Encrypted PDFs and broken documents are skipped. They appear in the ingest result as
  "読めない/空: N件".

---

## 3. Speaking to it by voice

- The voice feature has been removed. This package has no transcription from audio.
- The old path `/api/transcribe` is **no longer connected**.
  `include_router` has been removed in `server.py` (it was a hole that returned the transcription
  as-is, before masking, so it was removed deliberately).

---

## 4. There is no endpoint for uploading documents

The endpoint for sending files from the screen or the API has been **removed**
(the top of `routers/sources.py` says that "アップロード保存先 `_uploads_root` と
`/api/sources/upload` を撤去した。取り込みは取り込みフォルダ経由に一本化する").

Documents are **placed in the ingest folder decided in advance**, and then selected on the screen.
There is no longer any place inside the application where a copy of a document is made.

---

## 5. Conditions under which sending to the outside stops

Rather than "what it cannot do", this is "what is deliberately stopped".
When it cannot be determined, it always falls to the side that stops. As a result, features can
look as if they are not working.

- **CRAG pre-reading.** The step that has the LLM pre-read whether the search results are
  sufficient for the question is not run when the destination is not inside the same machine, and
  **also when the destination cannot be determined** (`rag.py`). When it is not run, it falls back
  to "adopt the search results as they are". The screen shows
  `[CRAG] 非ローカル宛のため下読みをスキップします`.
- **Conversation summarization and extraction of hints from the answer.** Both use the same
  judgment, and for an external destination (including "cannot be determined") they send nothing
  and return empty (`routers/chat.py`).
- **Sending original text based on role.** If the destination is outside, only the masked version
  is sent, even for an administrator (the `_effective_send_tier` described above).
- **If masking fails, it stops.** For both the question text and the answer, if the masking step
  fails with an exception, 503 is returned and processing is aborted. It never returns the version
  before masking instead (`routers/chat.py`).
- **The combination of ingest without masking and external embedding is refused.**
  A collection created "without masking" by an older version cannot be published while external
  embedding is enabled (`rag.py`).

---

## 6. Constraints when used concurrently

- **Publish is limited to 2 at a time.** The 3rd one waits 5 seconds and is returned as a failure
  if no slot opens (`server.py`; the screen shows
  "他のPublishが多すぎます。少し待ってから再試行してください。").
- **Concurrent LLM execution is limited to 3 by default** (`llm.max_concurrent` in
  `cynovela.yaml`; `server.py` creates a semaphore with this value). The 4th waits until a previous
  call finishes.
- **Storage is a single SQLite file** (WAL mode). Waiting occurs in situations where writes
  overlap. A usage where dozens of people run ingest at the same time is not assumed.
- The vector index (ChromaDB) is also a file on the same machine.
  Do not rewrite the same index from multiple processes.

---

## 7. Constraints on replacing models

The detailed procedure is in `SETUP-ACCELERATOR.md`. Only the key points are written here.

- **The embedding model must match down to the version (snapshot).**
  You need to match `BAAI/bge-m3` down to the snapshot version.
  **If the version differs, the vector values change, they mix with the bundled index, and the
  search ranking breaks.**
  If the version differs, a warning is shown at startup and at publish. When the warning appears,
  either match the version or rebuild the whole index.
- **The lightweight package (it does not contain AI models; about 2.4 MB) does not bundle models.**
  If you run the startup script without placing the models, on the first startup you are asked
  whether to fetch them from the internet. If you choose not to fetch them, **it stops before
  starting**.
- **`host.containers.internal` cannot be resolved outside a container.**
  When starting directly on the host, rewrite it to `127.0.0.1`
  (the container package automatically substitutes this one word only.
  If you write a different host name or IP, it is not substituted and is used exactly as written).
- **The image endpoint of the external accelerator is not implemented.** Calling it returns 501.
- **Some values of `--mode` at startup do not actually switch anything.**
  This is written as-is in the description of `--mode`.
  For `lite` and `lite-en`, switching to a lightweight model is not wired up, and at present they
  run on the same `bge-m3` as the default `text`. For `minimal`, TF-IDF is not integrated, and it
  too requires `bge-m3` (in an environment where the models are not placed, ingest cannot be done).
  **Whichever mode you choose, the size of the required models does not change.**

---

## 8. Features that are only a skeleton with no substance

These raise `NotImplementedError` when called, or are only an abstract declaration.
(Line numbers are not written, because they go out of date immediately. They are indicated by file
name and class / method name.)

| File | Class / method | State |
|---------|----------------|------|
| `providers/classifier.py` | `ClassifierProvider.classify` | Abstract (a slot for replacement) |
| `providers/embedding.py` | `EmbeddingProvider.embed` / `.test_connection` | Abstract |
| `providers/embedding.py` | `MLXEmbeddingProvider.embed` | Not implemented (future) |
| `providers/reranker.py` | `RerankerProvider.rerank` / `.test_connection` | Abstract |
| `providers/reranker.py` | `MLXReranker.rerank` | Not implemented (future) |
| `providers/vector_store.py` | `VectorStoreProvider.add` / `.search` / `.delete_collection` / `.export` / `.import_data` / `.test_connection` | Abstract |
| `providers/vector_store.py` | `QdrantVectorStore.add` / `.search` / `.delete_collection` / `.export` / `.import_data` | Not implemented (skeleton only) |
| `services/rag_strategies.py` | `GraphRAGStrategy.retrieve` / `.build_graph` / `.traverse_with_acl` | Not implemented (future) |
| `services/agent_runtime.py` | `AgentRuntime.run` / `.call_tool` / `.available_tools` | Abstract declaration only. There is not a single class that implements it |

In other words:

- **You cannot switch the vector storage to Qdrant.** Only ChromaDB works.
- **The MLX path for Apple Silicon cannot be used.** Neither embedding nor reranking is
  implemented. (If you want to use the GPU of Apple Silicon, it goes through the external
  accelerator. See `SETUP-ACCELERATOR.md`.)
- **Search using a graph (GraphRAG) cannot be used.**
- **You cannot make an agent do work.** Only the type declarations exist.

---

## 9. The Kubernetes set does not work as-is

- **The container package does not include `deploy/k8s/20-deployment.yaml`.**
  `tools/build-dist.sh`, which builds the package, drops this file right before making the `tar`.
  With only the remaining 3 (namespace / pvc / service), not a single application container comes up.
- **The host-direct package does not have `deploy/` at all.**

If you want to run it on Kubernetes, you need to write the Deployment definition yourself.

---

## 10. Other limits and notes

### Startup forms and where the data is

- With `--demo`, it starts with the demo database loaded with the bundled dummy documents
  (`store/db/demo.db` and `store/vector/demo/chroma`).
- With nothing attached it is production, and it starts with an **empty database**
  (`store/db/cynovela.db` and `store/vector/default/chroma`).
- **Neither one disappears on restart.** They are not initialized every time it starts.
  If you want to delete them, delete the files yourself.
- The bundled index and database are built **only from `dummy-corpus/` inside the package** when
  the package is made. Not a single working document of the person who made it is included.
  What is actually inside, and how many items, is written out in `BUNDLED-DATA.md` in the package.

### Cross-collection search

The MCP tools include `search_across_collections` (search across multiple collections), but
**the screen (GUI) has no entry point for cross-collection search.**
From the screen you select one workspace and search.

### MCP

- `mcp_server.py` provides 11 tools.
- The MCP server is built to query Cynovela's REST API internally, with authentication.
  In other words, **if the main body is not running, MCP does not work either.**
- The Python executable that runs MCP can be specified with the environment variable
  `CYNOVELA_MCP_PYTHON`. If it is not specified, the currently running Python is used as-is
  (`routers/mcp.py`).

### How the answer is made

- **Structured answers cannot be returned.** The answer is free-form (Markdown where needed).
  There is no response in JSON or in fixed tags.
  Citations (in the `[1][2]` form) are implemented.
- **There is no automatic switching when confidence is low.**
  `cynovela.yaml` has `confidence_threshold` (default `0.4`), but no behavior that automatically
  switches to general-knowledge mode when it falls below is built in.
- **Self-evaluation of the answer is a simple rule.** `evaluate_answer_quality()` in
  `adaptive_rag.py` decides sufficiency from "the answer is empty", "fewer than 60 characters and
  few hits", and "contains a negative expression". It does not have the LLM evaluate it.

### Removed features

| Feature | State |
|------|------|
| `--mock` startup | Removed. It does not exist among the startup options. Starting without models is also not possible |
| `/chat-popup` | Returns 410 Gone. Moved to the full-screen chat |
| Login with `user_id` only | Removed. `username` and `password` are required |
| Unauthenticated access to `/api/auth/users` | Removed. Administrator authentication is always required |
| The `--pii-mode` startup option | Abolished. It is specified with `pii_mode` in `cynovela.yaml` |
| The old `/api/transcribe` | Removed. There is no voice feature |
| `/api/sources/upload` | Removed. Unified to go through the ingest folder |

### The pass (login token)

The pass is a JWT issued by `POST /api/auth/login`. The signing key is
**not included in the package**. The receiving side generates it automatically from cryptographic
random numbers on the first startup and saves it to `store/db/jwt/secret.key`
(`_load_or_create_jwt_signing_key` in `config.py`). When the package is built, this key is always
dropped (because if it were shared, a pass issued elsewhere would be accepted).

If saving the key fails, the key is valid only for that one run. In that case, passes already
issued become invalid after a restart (logging in again works).

### Pitfalls

- ChromaDB's `PersistentClient` does not raise an error even if you pass the wrong path.
  It silently creates an empty database. **When search returns 0 results, first suspect that the
  location of the index is wrong.**
- Do not pass `max_tokens` to the LM Studio API.
  With a thinking-type model, it uses up the tokens needed for thinking.

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

この文書は、Cynovela に **できないこと** を書いたものです。できることの説明は
`README.md` と `QUICKSTART.md` にあります。ここには、期待すると外れることだけを書きます。

版は `` です（`core/version.py` の `APP_VERSION` が唯一の入手元で、
`GET /api/health` と `/docs` はここを読みます）。

---

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

### 1.7 管理者が原文を見られるかどうかは、鍵と宛先しだい

役割が `admin` のときは、マスキング前の原文を見られる設計です（`rag.py` の `tier_for_role`）。
ただし、次の 3 つの場合は管理者でもマスキング済みのものしか出ません。

1. **回答用 LLM の宛先が外部を向いているとき。**
   `routers/chat.py` の `_effective_send_tier` は、送り先が自マシン内・
   コンテナのホスト側・私設アドレス帯のいずれでもない場合、役割によらずマスキング済みへ
   落とします。宛先を判定できないときもマスキング済みに倒します。
2. **金庫（暗号化された保管）の鍵が合わないとき。**
   原文は暗号化して保管してあり、`rag.py` の `_vault_substitute_raw` が復号します。
   復号できない行はマスキング済みの本文をそのまま使います
   （画面に暗号文を出さないため、あえてそうしてあります）。
   配布物を受け取ったあとで鍵を入れ替えると、それ以前に取り込んだ資料は
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
- **画像は既定では本文を読みません。** 既定の動作はファイル名だけをインデックスに入れる
  `filename_only` です（`rag.py` の `_extract_image_text`）。画像の中の文字は読みません。
  説明文を作らせる設定（`caption` / `lm_studio`）もありますが、
  同梱の `cynovela.yaml` には `image:` の項目がなく、既定のままです。
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

詳しい手順は `SETUP-ACCELERATOR.md` にあります。要点だけ書きます。

- **埋め込みモデルは、版（snapshot）まで一致していなければなりません。**
  `BAAI/bge-m3` の snapshot 版まで揃える必要があります。
  **版が違うとベクトルの数値が変わり、同梱済みのインデックスと混ざって検索順位が壊れます。**
  版が違う場合は起動時と公開時に警告が出ます。警告が出たら、版を揃えるか
  インデックスを全部作り直してください。
- **軽量版（AIモデルを含みません。約 2.4 MB）はモデルを同梱していません。** モデルを置かないまま起動用スクリプトを
  実行すると、初回の起動でインターネットから取得するかどうかの確認が出ます。
  取得しない場合は、**起動する前に止まります**。
- **`host.containers.internal` はコンテナの外では名前解決できません。**
  ホスト側で直接起動する場合は `127.0.0.1` に書き換えてください
  （コンテナ版の配布物は、この 1 語だけは自動で読み替えます。
  別のホスト名や IP を書いた場合は読み替えず、書いたとおりに使います）。
- **外部アクセラレータの画像の受け口は未実装です。** 呼ぶと 501 を返します。
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
| `services/rag_strategies.py` | `GraphRAGStrategy.retrieve` / `.build_graph` / `.traverse_with_acl` | 未実装（将来） |
| `services/agent_runtime.py` | `AgentRuntime.run` / `.call_tool` / `.available_tools` | 抽象宣言のみ。実装したクラスは 1 つもありません |

つまり:

- **ベクターの保管先を Qdrant に替えることはできません。** 動くのは ChromaDB だけです。
- **Apple Silicon 向けの MLX 経路は使えません。** 埋め込みも再ランクも未実装です。
  （Apple Silicon の GPU を使いたい場合は、外部アクセラレータ経由になります。
  `SETUP-ACCELERATOR.md` を参照してください。）
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

- `--demo` を付けると、同梱のダミー資料が載ったデモのデータベースで起動します
  （`store/db/demo.db` と `store/vector/demo/chroma`）。
- 何も付けなければ本番で、**空のデータベース**で起動します
  （`store/db/cynovela.db` と `store/vector/default/chroma`）。
- **どちらも再起動で消えません。** 起動のたびに初期化されることはありません。
  消したい場合は自分でファイルを消してください。
- 同梱のインデックスとデータベースは、配布物を作るときに**配布物の中の `dummy-corpus/` だけ**から
  作っています。作った側の作業用の資料は 1 件も入っていません。
  実際に何が何件入っているかは、配布物の `BUNDLED-DATA.md` に書き出してあります。

### 横断検索

MCP のツールには `search_across_collections`（複数のコレクションをまたぐ検索）が
ありますが、**画面（GUI）には横断検索の入口がありません。**
画面からはワークスペースを 1 つ選んで検索します。

### MCP

- `mcp_server.py` は 11 個のツールを提供します。
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

### 落とし穴

- ChromaDB の `PersistentClient` は、間違ったパスを渡してもエラーになりません。
  空のデータベースを黙って作ります。**検索が 0 件になったときは、
  まずインデックスの場所が合っているかを疑ってください。**
- LM Studio の API に `max_tokens` を渡さないでください。
  思考する型のモデルで、考えるためのトークンを使い切ってしまいます。

---
