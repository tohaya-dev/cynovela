# 変更履歴（Changelog）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool built by an individual to
> understand the concepts of AI platform tools hands-on. It is not a commercial
> product nor an official implementation.
> The implementation is entirely original, built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

This records the main changes to Cynovela in chronological order.

---

## v1.1.3 (2026-08-31)

- **`./launch.sh --help` now names the real place of the first password**: this
  package's own `cynovela.yaml`, key `auth.admin_initial_password` (the
  viewer's is `auth.viewer_initial_password`), printed on the screen once on
  the ordinary first start and never on `--demo`. The wording is the one the
  documents have carried since 1.1.2; only the terminal output was behind.
- **`--follow` / `--pro` are refused at the entry point, with a reason, when no
  terminal is connected.** They are wrapper-only flags; on a call without a
  terminal the wrapper used to hand them to the body, which rejected them as
  unknown. With a terminal connected they behave as before.
- **The distributables no longer carry the `.app` build materials**
  (`macos-app/`, `tools/build-macos-app.sh`, `tools/split-pkg.sh`), and the
  publishing gate now fails the build if an internal work number appears in
  the packaged product (previously it only counted them).
- **`docs/html/` regenerated from the current `.md` files.**

## v1.1.2 (2026-08-30)

- **An app edition (`.pkg`) is in preparation.** It is not part of this release.
  The code below that was written for it is in this version, and changes nothing
  for the editions that do ship.
- **The data root can now be moved out of the tree.** An installed app is
  read-only, so the database, index, logs, backups and keys cannot live inside it.
  When `CYNOVELA_DATA_ROOT` is set — which only the app's launcher does — those go
  under `~/Library/Application Support/Cynovela/` instead. When it is unset, which
  is every other edition, the behaviour is byte-for-byte what it was.
- **`launch.sh` skips clearing extended attributes when its own folder is not
  writable.** A package-installed app is owned by root, and the recursive
  `xattr -rc` printed a warning line per entry on every launch. Every folder-based
  edition has a writable root, so the guard is never taken there.

## v1.1.0 (2026-08-25)

- **The distributables for this version were rebuilt and replaced on 2026-08-25.** The
  ones published first carried an older copy of the bundled documents. The behaviour of
  the tool is unchanged; only the documents inside the package differ. If you downloaded
  before that date, download again.
- **The package edition's bundled environment now has its own name, separate from the
  venv the source edition creates.** Both used to share the name `.venv-cynovela` and the
  internal label `FORM_SEL="venv"`, even though they are technically different things: the
  package edition ships a pre-built `conda-pack` environment, while the source edition's
  choice 2 creates a real `venv` from scratch with `python -m venv`. The bundled
  `conda-pack` environment is now named `.condapack-cynovela` (`FORM_SEL="condapack"`)
  everywhere — `launch.sh`'s auto-detection (which skips the selection screen when a
  working bundled environment is already there), `tools/conf.sh`'s Python search order,
  `tools/check-cli-mcp.sh`, `uninstall.sh`'s inventory and confirmation screens, and the
  published documents. The source edition's real `venv` keeps its existing name
  `.venv-cynovela` and `FORM_SEL="venv"` unchanged — nothing about how it is built or
  where it lives has changed.
- **Compatibility note (why this is a minor version, not a patch):** `START-HERE.md` and
  the MCP document (`docs/mcp-guide.md` then, `docs/reference/mcp.md` now) used to show
  the package edition's own Python as a direct path —
  `./.venv-cynovela/bin/python3 cynovela-cli.py doctor`, or
  `export CYNOVELA_MCP_PYTHON=/path/to/.venv-cynovela/bin/python3`. Anyone who copied one
  of those commands into a script or shell alias will find it points at a path that no
  longer exists; the package edition's Python is now at `.condapack-cynovela/bin/python3`.
  The documents have been corrected to the new path.

## v1.0.7 (2026-08-22)

- **A single API call could stop the whole server. It cannot any more.** Registering an
  ingest folder whose name could not be assigned raised `SystemExit`, which took the
  server down — one ordinary `POST /api/ingest-roots` was enough. Names are now assigned
  so that the disambiguating suffix always survives the 32-character limit, and the
  exhausted case answers 409 instead of exiting.
- **A `confidential` collection was listed to a viewer.** The collection list now hides
  `confidential` collections from non-administrators, and a search restricted to given
  `collection_ids` no longer lets the BM25 half reach outside that set.
- **The pass no longer expires after 8 hours.** `POST /api/auth/login` issues a pass with
  no expiry unless the caller passes `expires_in_hours` or `expires_in_seconds`; the same
  applies to `POST /api/auth/refresh`. See `limits.md` §11 for what that means
  for a leaked pass.
- **`cynovela-cli login` and `logout`.** `login` takes the password from standard input or
  from the terminal (never from the command line by default), stores the pass in
  `~/.cynovela_cli.env` readable only by you, and never prints it. `logout` removes it.
- **Full Export could produce an empty `files.json`.** When a collection held files from a
  folder that was not linked to the workspace, the export listed the file ids but not the
  files, and the import then produced a collection with nothing in it — while reporting
  success. Both halves are fixed, and an import that ends up hollow now says so.
- **An imported workspace can be asked questions without publishing it again.** The import
  now rewrites the ids stored inside the restored vectors, which retrieval filters on.
- **A user can be removed for good**, not only switched off:
  `DELETE /api/admin/users/{id}?purge=true`, `cynovela-cli users delete --purge`,
  MCP `manage_users` with `purge: true`. Audit log entries are kept.
- **The same folder can no longer be registered twice** under two names.
- **Two scans of one folder can no longer run at once.** The guard used to sit on one
  endpoint; it now sits in the scan itself, so every way in is covered.
- **The generation-timeout message says what actually happened** — the wait is 120 seconds
  per call and cannot be configured — instead of suggesting a document count that has no
  setting anywhere.
- **Citation numbers match the answer.** The `[N]` in the text and the numbers printed
  beside the sources are now the same numbers in the CLI and in MCP, as they already were
  on the screen.
- **Documents**: new `docs/cli-reference.md` (every command and argument), `docs/mcp-reference.md`
  (all 25 tools), `docs/first-run.md` (from the download to the first answer, for someone who
  has never opened Terminal), `docs/restart.md`, `docs/editions.md` (which of the four
  downloads to take). `docs/api-reference.md` was replaced by a list of all 186 endpoints
  read out of the code. `docs/known-limitations.md` gained section 11.
  (Those are the file names as they were at 1.0.7. The documents were reorganised
  afterwards — `known-limitations.md` is now `limits.md`, `first-run.md` is now
  `getting-started.md`, and the four reference documents moved under `docs/reference/`.
  `docs/INDEX.md` lists what exists now.)
- The same repairs were carried into falcon wherever its code is identical; where it is not,
  `limits.md` §11.7 says so.

## v1.0.6 (2026-08-20)

- **The CLI now covers the same work as the screen.** Added: `sources` / `audit-logs` / `chat` /
  `ingest` (register a folder and start scanning in one line) / `scan start·status·cancel` /
  `publish start·status·stop·recover` / `collections create·link` / `workspaces create·update·archive·unarchive` /
  `delete` / `users` / `backup`. Dangerous operations show what would happen and never run without `--yes`.
- **MCP now has 25 tools (22 visible by default).** Added `server_status`, `ingest_source`,
  `get_job_status`, `cancel_scan`, `create_collection`, `publish_control`; the three admin tools
  (`delete_item` / `manage_users` / `manage_backups`) are closed by default and appear only when
  `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` is set. `publish_collection` now starts the publish and
  returns a `job_id` immediately instead of blocking.
- **Scans run in the background.** New `POST /api/sources/{id}/scan/async` returns a `job_id`
  immediately; progress via `GET /api/jobs/{job_id}` (same shape as publish). The screen's rescan
  uses this, a "Reload sources" button was added above the source list, and the server scans the
  registered sources once at every startup (files that have not changed are not re-read).
- **`launch.sh`**: drops the quarantine marks inside the package by itself at start; warns before
  starting when the folder sits under cloud sync (iCloud Drive / Dropbox / OneDrive / Google Drive);
  and skips the base-selection screen when the bundled `.venv-cynovela` is present and working.
- **`uninstall.sh`** now reports the reason and the next step when the move to the Trash fails.
- Removed the old, unreferenced `cynovela_cli.py` (underscore name). The CLI is `cynovela-cli.py`.
- Documents: added download-and-assembly guidance, updated tool counts and command lists, fixed the
  model overlay destination to `store/models/`, and aligned stale version numbers.

## Public repository and package form (2026-08-12)

- In the public GitHub repository (cynovela), two forms were placed side by side:
  falcon (the form that runs inside a container) and chewie (the form that runs directly on a Mac).
- There are now four package forms: falcon all-in-one, falcon lightweight, chewie all-in-one, and chewie lightweight.
- The all-in-one form (the form that bundles the models) is too large to fit in a single file, so it is
  distributed **split into multiple files**. `HOW-TO-ASSEMBLE.md` and `SHA256SUMS` are placed in the same location as the split files;
  assemble them and verify the SHA256 before use.
- The lightweight form (the form that does not bundle the models) is distributed as **a single file**. At first startup you can choose to
  download the models (no communication starts until you choose).

## The first working milestone (before the public repository)

This is the milestone for "a state in which the core flows work end to end as a personal learning tool". After going through Stage 0 to Stage 6, the main features of guardrails, PII detection, RAG, and MCP integration became operational.

### Stage 0: Startup foundation

- Organizing the CLI argument definitions with argparse
- Introducing the 5 values of `--mode` (full / text / lite / lite-en / minimal)
- Startup preflight (checking that the required models exist, and offering download or an alternative mode when they are not obtained)
- Skipping the dialog during script execution with `CYNOVELA_NONINTERACTIVE=1`
- Centralizing configuration with `cynovela.yaml`, plus environment variable overrides

### Stage 1: Data persistence and FK integrity

- Setting up the SQLite schema (`workspaces`, `collections`, `sources`, `files`, `chunks`, `audit_logs`, etc.)
- Applying `PRAGMA foreign_keys = ON` to all connections
- The `_purge_chunks_for_*()` family of helpers that clean up both SQLite and ChromaDB on deletion
- Introducing `_stable_fid(path)` for `file_id` stability after a rescan
- Thorough use of the audit recording helper `_log_audit(conn, action, target, detail)`

### Stage 2: Guardrails and PII

- 4 guardrail actions (`mask` / `exclude_from_rag` / `log_only` / `allow`)
- Detection of 8 kinds of PII patterns (URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4)
- Generation of dual-tier storage (raw / masked) at publish time
- Protection of the raw body text by Fernet encryption (`vault_enc.py`)
- 3-layer prompt injection countermeasures (input inspection, post-retrieval inspection, output inspection)

### Stage 3: RAG pipeline

- Hybrid fusion of BM25 and vector search (default: RRF, k=60)
- BAAI/bge-m3 vector embeddings
- Replaceable Reranker (CrossEncoder, FlashRank, Ollama, HTTP)
- Advanced search features (MMR, Parent-Child chunking, Multi-Query, CRAG, HyDE, Adaptive RAG)
- Adoption of a confidence threshold (cosine similarity 0.40)

### Stage 4: Smart Ingestion

- Automatic classification into 14 document categories
- 3 kinds of classification engines (lightweight, LLM, hybrid)
- Hash-based differential sync per path by DataSyncService (default interval 60 seconds)
- Contextual Chunking (prepending metadata to the beginning of a chunk)

### Stage 5: RBAC and auditing

- Applying a SQL CHECK constraint for the 3 roles (admin / curator / viewer)
- Setting up the 4 RBAC helper functions (`_require_admin`, `_require_authenticated`, `_require_role`, `_require_admin_or_self`)
- Applying RBAC checks to 33 routers (242 places)
- Prohibiting modification and deletion of audit_logs via the API

### Stage 6: External integration

- Publishing an MCP server (11 tools at that time; 25 as of v1.0.6)
- LM Studio / Ollama / OpenAI-compatible API connections
- Setting up the flags for LAN sharing and Tailscale sharing (`--lan` / `--allow-tailscale` / `--allow-subnet`)
- IP allowlist middleware

---

## History of main fixes

### Security hardening

- **Complete removal of user_id-only login**: The legacy path was deleted and username/password became mandatory.
- **Making `/api/auth/users` admin-only**: The unauthenticated allowance in demo mode was abolished.
- **Restricting the PII detection history to admin**: `/api/guardrails/pii-detections` was changed to admin only.
- **Abolishing the chat popup route**: `/chat-popup` was changed to 410 Gone.

### Bug fixes

- **Strengthening path validation of `/api/sources`**: Prevents references to system paths.
- **Validation of `llm_endpoint`**: Restricts changes that reference the internal network.
- **Fixing the placement order of the system prompt**: Placed after retrieved_content (preventing overwriting by documents).
- **Eliminating `INSERT OR REPLACE`**: Unified to `ON CONFLICT DO UPDATE` to prevent FK CASCADE from firing by mistake.
- **Testability of `_publish_semaphore`**: Changed from module scope to dependency injection (carried over from Stage-3).

### Quality improvements

- Reduced pyright errors from 16 to 0
- Protecting all contracts of the dependency constraints with import-linter
- Expanded the pytest suite to 14 PHASEs / more than 405 assertions
- Maintained 0 console errors

---

## Items that are not complete

The following are recorded as unfinished. They describe the state of the current build, not a schedule.

### Authentication and authorization

- Full JWT authentication (RBAC enforcement in all modes)
- Per-user API key issuing

### RAG quality

- Reranker substance testing (quality verification of CrossEncoder and others)
- Adjustment of the chunking strategy (whether Contextual Chunking becomes the default)
- Structured answer templates

### Stability

- YAML persistence of the Embedding / Reranker settings (currently memory only)
- Hardening of the error recovery paths
- Integration of DataSyncService with publish (currently a noop)

### Integration expansion

- Expansion of the tools published by the MCP server
- Expansion of the Chunks viewer of KnowledgeCatalog (metadata search, citation tracking)

### Backend diversification

- Vector store support for Qdrant / LanceDB (currently a skeleton only)
- MLX Embedding / Reranker implementation (Apple Silicon optimization)

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela の主要な変更内容を時系列で記録します。

---

## v1.1.3（2026-08-31）

- **`./launch.sh --help` が、最初のパスワードの本当の在りかを言う**: この配布物
  自身の `cynovela.yaml` の `auth.admin_initial_password`（閲覧者のぶんは
  `auth.viewer_initial_password`）に在り、普通の初回起動では画面にも1回出て、
  `--demo` では出ない。文言は 1.1.2 から文書が載せているものと同じで、端末の
  出力だけが遅れていた。
- **端末が繋がっていない呼び出しでは、`--follow` / `--pro` を入口が理由つきで
  断る。** これらは包みだけが読む指定で、端末なしの呼び出しでは従来、これらを
  知らない本体へ渡って「知らない指定です」で落ちていた。端末が繋がっていれば
  従来どおり動く。
- **配布物から `.app` の組み立て材料を外した**（`macos-app/`・
  `tools/build-macos-app.sh`・`tools/split-pkg.sh`）。あわせて、内部の作業番号が
  配布物に現れたら組み立てを止める関門を足した（従来は数えるだけだった）。
- **`docs/html/` を、いまの `.md` から作り直した。**

## v1.1.2（2026-08-30）

- **アプリ版（`.pkg`）は準備中である。** この版には入っていない。
  そのために書いた下記のコードはこの版に入っており、配布している形の動きは
  何も変えない。
- **保存先の根を、木の外へ移せるようにした。** 入れたあとのアプリは読み取り専用のため、
  データベース・索引・記録・控え・鍵をその中に置けない。`CYNOVELA_DATA_ROOT` が
  与えられたとき（与えるのはアプリ版の入口だけである）、それらは
  `~/Library/Application Support/Cynovela/` の下へ行く。与えられないとき ＝ ほかの
  すべての形では、振る舞いは 1 バイトも変わらない。
- **`launch.sh` は、自分の置き場に書けないときは拡張属性を落とす処理を行わない。**
  `.pkg` で入れた包みは root の持ち物であり、再帰的な `xattr -rc` が 1 つにつき 1 行の
  警告を毎回出していた。フォルダで配る形はどれも根が書けるため、そちらでこの判定に
  当たることはない。

## v1.1.0（2026-08-25）

- **この版の配布物は 2026-08-25 に作り直して差し替えた。** 最初に公開した配布物には、
  同梱の文書が古いまま入っていた。道具の動きは変わっていない。違うのは配布物の中の
  文書だけである。その日より前に落とされた方は、落とし直してください。
- **パッケージ版に同梱の環境が、ソース版が作る venv とは別の名前を持つようになった。**
  それまでは技術的に別物であるにもかかわらず、両方とも `.venv-cynovela` という名前・
  `FORM_SEL="venv"` という内部の呼び名を共有していた: パッケージ版は `conda-pack` で
  固めた既製の環境を同梱しているのに対し、ソース版の選択肢2は `python -m venv` で
  その場から新規に本物の `venv` を作る。同梱の `conda-pack` 済み環境は、`launch.sh` の
  自動検出（同梱の環境が既に動くときは選択画面を出さない仕組み）・`tools/conf.sh` の
  Python 探索順・`tools/check-cli-mcp.sh`・`uninstall.sh` の一覧と確認画面・公開文書の
  すべてで、新しい名前 `.condapack-cynovela`（`FORM_SEL="condapack"`）に統一した。
  ソース版が作る本物の `venv` の名前 `.venv-cynovela`・`FORM_SEL="venv"` は変えていない。
  作り方も置き場所も、これまでどおりである。
- **互換性についての注記（パッチ版ではなくマイナー版へ上げた理由）：** `START-HERE.md` と
  MCP の文書（当時は `docs/mcp-guide.md`・いまは `docs/reference/mcp.md`）は、
  パッケージ版が用意した Python を、直書きのパスとして
  `./.venv-cynovela/bin/python3 cynovela-cli.py doctor` や
  `export CYNOVELA_MCP_PYTHON=/path/to/.venv-cynovela/bin/python3` の形で示していた。
  このコマンドをスクリプトやシェルのエイリアスへそのまま写した方は、指す先が
  無くなっていることに気づくはずである。パッケージ版の Python は、いまは
  `.condapack-cynovela/bin/python3` に在る。文書は新しいパスへ直してある。

## v1.0.7（2026-08-22）

- **API を1回叩くだけでサーバー全体が止まることがあった。もう止まらない。** 取り込み元の
  フォルダを登録するとき、名前を割り当てられないと `SystemExit` が投げられ、サーバーごと
  落ちていた。ふつうの `POST /api/ingest-roots` 1回で足りた。名前の付け方を改め、
  避けるための印が32文字の枠から必ず落ちないようにし、探し尽くしたときは終了ではなく
  409 で断るようにした。
- **`confidential` のまとまりが閲覧者の一覧に出ていた。** まとまりの一覧は管理者以外へ
  `confidential` を出さないようにし、`collection_ids` で絞った検索でも BM25 側だけが
  その外へ届いてしまう経路を塞いだ。
- **通行証が8時間で切れなくなった。** `POST /api/auth/login` は、呼ぶ側が
  `expires_in_hours` か `expires_in_seconds` を渡さないかぎり期限の無い通行証を出す。
  `POST /api/auth/refresh` も同じ。漏れたときにどうなるかは `limits.md` の
  §11 に書いた。
- **`cynovela-cli login` と `logout` を足した。** `login` は合言葉を標準入力かターミナルから
  受け取り（既定では命令の行に書かせない）、通行証を自分だけが読める形で
  `~/.cynovela_cli.env` へ書く。通行証そのものは画面に出さない。`logout` はそれを消す。
- **フルエクスポートの `files.json` が空になることがあった。** まとまりが持つ資料の出どころの
  フォルダが作業場所に結ばれていないと、書き出しには資料の番号だけが並んで資料そのものが
  入らず、取り込むと中身の空のまとまりができた。しかも成功と表示していた。書き出す側と
  取り込む側の両方を直し、中身が空になった取り込みはそう言うようにした。
- **取り込んだ作業場所は、再度の公開なしで質問できる。** 取り込みのときに、戻したベクターの
  中に残っている番号を書き換えるようにした。探す側はその番号で絞っているためである。
- **利用者を完全に消せるようにした。** 使えなくするだけでなく、行そのものを消す道:
  `DELETE /api/admin/users/{id}?purge=true`・`cynovela-cli users delete --purge`・
  MCP の `manage_users` に `purge: true`。監査の記録は残る。
- **同じフォルダを、名前を変えて二重に登録できなくなった。**
- **同じフォルダの走査が2本同時に走らなくなった。** これまで断っていたのは1つの口だけだった。
  走査の本体側で締めたので、どの入口から来ても効く。
- **時間切れの文言が実態を言うようになった。** 待ち時間は1回の呼び出しにつき 120秒 で、
  設定から変えられない。従来はどこにも設定の無い「参照ドキュメント数」を減らせと言っていた。
- **出典の番号が本文と対応するようになった。** 本文の `[N]` と、出典の並びに付く番号が、
  CLI でも MCP でも同じ番号になった（画面では前から同じだった）。
- **文書**: `docs/cli-reference.md`（全ての命令と引数）・`docs/mcp-reference.md`（道具25件）・
  `docs/first-run.md`（ターミナルを開いたことが無い方向けに、落とすところから最初の答えまで）・
  `docs/restart.md`・`docs/editions.md`（4つのうちどれを落とすか）を新設。
  `docs/api-reference.md` は、コードから起こした全186件の口の一覧に差し替えた。
  `docs/known-limitations.md` に第11節を足した。
  （これらは 1.0.7 当時のファイル名である。文書はその後に組み替えており、
  `known-limitations.md` は `limits.md`、`first-run.md` は `getting-started.md` に、
  引くための4本は `docs/reference/` の下へ移った。いま在るものは `docs/INDEX.md` に
  並んでいる。）
- 同じ直しは、コードが同じ箇所であれば falcon へも当てた。当てていない箇所は
  `limits.md` の §11.7 に書いた。

## v1.0.6（2026-08-20）

- **CLI が画面と同じ作業を覆うようになった。** 追加: `sources` / `audit-logs` / `chat` /
  `ingest`（フォルダの登録と走査の開始を1行で）/ `scan start·status·cancel` /
  `publish start·status·stop·recover` / `collections create·link` / `workspaces create·update·archive·unarchive` /
  `delete` / `users` / `backup`。危険な操作は「何が起きるか」を見せ、`--yes` なしには実行しない。
- **MCP の道具が 25 個になった（既定で見えるのは 22 個）。** `server_status`・`ingest_source`・
  `get_job_status`・`cancel_scan`・`create_collection`・`publish_control` を追加。管理系の 3 個
  （`delete_item` / `manage_users` / `manage_backups`）は既定で閉じており、
  `CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1` を設定したときだけ現れる。`publish_collection` は
  公開を始めて `job_id` を即返す形になった（終わるまで待たない）。
- **走査が背景で走るようになった。** `POST /api/sources/{id}/scan/async` が `job_id` を即返し、
  進み具合は `GET /api/jobs/{job_id}`（公開と同じ形）。画面の再スキャンはこの形を使い、
  資料一覧の上に「すべて読み込み直す」を新設。サーバは起動のたびに登録済みの取り込み元を
  1回走査する（変わっていないファイルは読み直さない）。
- **`launch.sh`**: 起動の最初に配布物の中の印（quarantine を含む拡張属性）を自分で全部落とす。
  クラウド同期（iCloud Drive / Dropbox / OneDrive / Google Drive）の下に置かれているときは
  起動前に注意を出す。同梱の `.venv-cynovela` が在って動くときは土台の選択画面を出さない。
- **`uninstall.sh`** は、ゴミ箱へ入れられなかったときに理由と次の一手を出すようになった。
- 参照されていなかった旧 `cynovela_cli.py`（下線の名前）を撤去した。CLI は `cynovela-cli.py`。
- 文書: 落とし方と結合の案内を追加。道具の数と命令の一覧を実体へ更新。モデルを重ねる宛先を
  `store/models/` に統一。古い版番号の表記を揃えた。

## 公開のリポジトリと配る形（2026-08-12）

- 公開の GitHub リポジトリ（cynovela）に、falcon（コンテナの中で動く形）と
  chewie（Mac の上で直に動く形）の2つの形を並べた。
- 配る形は4つになった。falcon 全部入り・falcon 軽量版・chewie 全部入り・chewie 軽量版。
- 全部入り（モデルを同梱する形）は、1つのファイルに収まらない大きさのため、
  **分割ファイルに分けて**配る。分割ファイルと同じ場所に `HOW-TO-ASSEMBLE.md` と `SHA256SUMS` を置き、
  組み立てと SHA256 の確認をしてから使う。
- 軽量版（モデルを同梱しない形）は **1つのファイル**で配る。初回の起動でモデルの
  ダウンロードを選べる（選ぶまで通信は始まらない）。

## 最初に一通り動いた節目（公開リポジトリより前）

これは「個人学習用ツールとして一通りのコアフローが動く状態」のマイルストーンです。Stage 0 〜 Stage 6 を経て、ガードレール・PII 検出・RAG・MCP 連携の主要機能が稼働するに至りました。

### Stage 0: 起動基盤

- argparse による CLI 引数定義の整理
- `--mode`（full / text / lite / lite-en / minimal）の 5 種を導入
- 起動時 preflight（必要モデルの存在確認、未取得時のダウンロード or 代替モード提案）
- `CYNOVELA_NONINTERACTIVE=1` でスクリプト実行時の対話スキップ
- `cynovela.yaml` による設定の一元化と環境変数オーバーライド

### Stage 1: データ永続化と FK 整合性

- SQLite スキーマの整備（`workspaces`、`collections`、`sources`、`files`、`chunks`、`audit_logs` 等）
- `PRAGMA foreign_keys = ON` の全接続適用
- 削除時に SQLite と ChromaDB の両方をクリーンアップする `_purge_chunks_for_*()` 系ヘルパー
- 再スキャン後の `file_id` 安定性のための `_stable_fid(path)` 導入
- 監査記録ヘルパー `_log_audit(conn, action, target, detail)` の徹底

### Stage 2: ガードレール・PII

- 4 種のガードレールアクション（`mask` / `exclude_from_rag` / `log_only` / `allow`）
- 8 種類の PII パターン検出（URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4）
- Dual-tier 保管（raw / masked）の Publish 時生成
- Fernet 暗号化による raw 本文保護（`vault_enc.py`）
- 3 層プロンプトインジェクション対策（入力検査・retrieval 後検査・出力検査）

### Stage 3: RAG パイプライン

- BM25 + ベクター検索のハイブリッド統合（既定: RRF、k=60）
- BAAI/bge-m3 ベクター埋め込み
- Reranker の差し替え（CrossEncoder、FlashRank、Ollama、HTTP）
- 高度な検索機能（MMR、Parent-Child チャンキング、Multi-Query、CRAG、HyDE、Adaptive RAG）
- 信頼度閾値（cosine similarity 0.40）を採用

### Stage 4: Smart Ingestion

- 14 種類のドキュメントカテゴリ自動分類
- 3 種類の分類エンジン（軽量、LLM、ハイブリッド）
- DataSyncService によるパス単位のハッシュ差分同期（既定 60 秒間隔）
- Contextual Chunking（メタデータをチャンク冒頭に付加）

### Stage 5: RBAC・監査

- 3 ロール（admin / curator / viewer）の SQL CHECK 制約適用
- RBAC ヘルパー関数 4 種の整備（`_require_admin`、`_require_authenticated`、`_require_role`、`_require_admin_or_self`）
- 33 ルーター（242 箇所）への RBAC チェック適用
- audit_logs の API 経由変更・削除を禁止

### Stage 6: 外部連携

- MCP サーバー（当時 11 ツール。v1.0.6 時点では 25 ツール）の公開
- LM Studio / Ollama / OpenAI 互換 API 接続
- LAN 共有・Tailscale 共有のフラグ整備（`--lan` / `--allow-tailscale` / `--allow-subnet`）
- IP アローリストミドルウェア

---

## 主要修正履歴

### セキュリティ強化

- **user_id 単独ログインの完全撤去**: レガシーパスを削除し、username/password 必須化。
- **`/api/auth/users` の admin 必須化**: デモモードでの未認証許可を撤廃。
- **PII 検出履歴の admin 限定化**: `/api/guardrails/pii-detections` を admin 専用に変更。
- **Chat popup ルートの廃止**: `/chat-popup` を 410 Gone に変更。

### バグ修正

- **`/api/sources` の path バリデーション強化**: システムパスへの参照を防止。
- **`llm_endpoint` のバリデーション**: 内部ネットワーク参照変更の制限。
- **システムプロンプト配置順序の修正**: retrieved_content の後に配置（文書による上書き防止）。
- **`INSERT OR REPLACE` の排除**: FK CASCADE 誤発火を防ぐため `ON CONFLICT DO UPDATE` に統一。
- **`_publish_semaphore` のテスト容易性**: モジュールスコープから依存注入化（Stage-3 引き継ぎ）。

### 品質改善

- pyright エラーを 16 件から 0 件に削減
- import-linter による依存関係制約の全 contracts 保護
- pytest スイートを 14 PHASE / 405 アサーション以上に拡充
- console エラー 0 件を維持

---

## 完了していない事項

以下は未完了として記録されている事項です。予定ではなく、現在の作りの状態として書きます。

### 認証・認可

- JWT 認証の本格導入（全モードでの RBAC 強制）
- ユーザー単位の API キー発行

### RAG 品質

- Reranker 実体テスト（CrossEncoder などでの品質検証）
- chunk 戦略の調整（Contextual Chunking を既定にするかどうか）
- 構造化回答テンプレート

### 安定性

- Embedding / Reranker 設定の YAML 永続化（現状はメモリのみ）
- エラー回復経路の堅牢化
- DataSyncService の publish 連携統合（現状は noop）

### 連携拡張

- MCP サーバーの公開ツール拡充
- KnowledgeCatalog の Chunks ビューア拡張（メタデータ検索、出典追跡）

### バックエンド多様化

- Qdrant / LanceDB のベクターストア対応（現状は骨格のみ）
- MLX Embedding / Reranker の実装（Apple Silicon 最適化）

---

