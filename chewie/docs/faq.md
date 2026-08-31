# よくある質問（FAQ）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built so that an individual
> could understand the concepts of an AI platform tool by working with their own hands.
> It is not a commercial product and not an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any organization or product.

If you are starting from nothing, read [getting-started.md](getting-started.md) first.
What Cynovela is and what it is for is in [concept.md](concept.md); what it cannot do is in
[limits.md](limits.md).

**Contents**

- [Q1. What is the difference from the referenced AI platform tool](#q1-what-is-the-difference-from-the-referenced-ai-platform-tool)
- [Q2. What does it mean that the data does not go outside](#q2-what-does-it-mean-that-the-data-does-not-go-outside)
- [Q3. What file types can be used](#q3-what-file-types-can-be-used)
- [Q4. How much spec is required](#q4-how-much-spec-is-required)
- [Q5. How are documents containing personal information handled](#q5-how-are-documents-containing-personal-information-handled)
- [Q6. Are there features that do not work](#q6-are-there-features-that-do-not-work)
- [Q7. Where do I look next](#q7-where-do-i-look-next)

## Q1. What is the difference from the referenced AI platform tool

Cynovela is a learning project that re-implements, using only OSS and so that an individual could understand it by working with their own hands, the concept that the referenced AI platform tool tries to solve (a RAG platform that safely connects internal documents to a local LLM). The implementation is entirely original, and there is no compatibility with the referenced tool in the source code, the API specification, or the data model. Commercial features, support, and an SLA are not provided.

See [concept.md](concept.md) for the comparison in detail.

## Q2. What does it mean that the data does not go outside

In the default configuration of Cynovela, all of the following are completed in the local environment.

- **Document body text**: Stored in SQLite (`~/.cynovela/db/cynovela.db` and so on) and ChromaDB (`~/.cynovela/vector/default/chroma` and so on).
- **Embedding generation**: In the default mode, BGE-M3 is run locally.
- **LLM inference**: Sent with the OpenAI-compatible /v1 API to the local LLM specified by `--lmstudio-url` (default `http://localhost:1234`).

External transmission can occur only in the following cases, and all of them require an explicit setting.

- When you allow access from other hosts with `--lan` / `--allow-tailscale` / `--allow-subnet`.
- When you set `reranker.provider` to an external API such as `cohere` / `jina` / `voyage`.
- When you set `execution.llm_provider` to `openrouter` / `claude_api`.

**Note about the listening address.** The server listens on `0.0.0.0` by default, so other terminals on the same network can reach it. Add `--local-only` to narrow it to your own machine. The IP allowlist middleware works only when `--allow-subnet` / `--allow-tailscale` is passed; when it is not passed, it does not restrict anything.

The cases where sending to the outside is deliberately stopped, and the cases where a feature therefore looks like it is not working, are listed in [limits.md](limits.md).

## Q3. What file types can be used

`extract_text()` in `rag.py` is in charge of text extraction. The formats that can be ingested are the ones listed in `SUPPORTED_EXTENSIONS` — documents (`.txt` `.md` `.csv` `.pdf` `.docx`), spreadsheets and presentations (`.xlsx` `.xls` `.pptx`), web and mail (`.html` `.htm` `.eml`), archives (`.zip`), and images (`.jpg` `.jpeg` `.png` `.heic` `.webp` `.gif`). The exhaustive list, together with the commonly brought-in formats that **cannot** be handled, is in [limits.md](limits.md).

**About images.** The default behaviour is `filename_only`, which puts only the file name into the index; text inside an image is not read, and there is no OCR (optical character recognition) mechanism. There are settings that generate a description (`caption` / `lm_studio`), but the bundled `cynovela.yaml` has no `image:` entry, so the default stays in place. A PDF that was produced as an image (merely scanned) yields not a single character.

## Q4. How much spec is required

In every startup mode (`--mode`), the required models are the same (the switch is not wired).

| Mode | Embedding model | Size | Recommended environment |
|--------|----------------|-------|----------|
| `text` (default) | BAAI/bge-m3 | About 2.3GB | No GPU needed, general purpose |
| `lite` | The switch is **not wired** = it is actually BAAI/bge-m3 (the behavior is the same as text; only the display name changes) | — | — |
| `lite-en` | The switch is **not wired** = it is actually BAAI/bge-m3 (the behavior is the same as text; only the display name changes) | — | — |
| `minimal` | Nominally TF-IDF, but there is no TF-IDF integration, so BAAI/bge-m3 is required here too | — | — |

**Whichever mode you choose, the size of the required models does not change.**

The requirements on the LLM side are needed separately (the `--mock` option that used to exist, meaning to run without calling an LLM, has been removed). The verification of this repository is done on a MacBook Pro M4 Max 128GB.

## Q5. How are documents containing personal information handled

Cynovela handles PII (Personally Identifiable Information) in two stages.

**Tier1 (masking at ingest time)**: At publish time, `_mtws_publish` (= `guardrail.mask_text_with_spans`) in `rag.py` runs and produces both `tier="raw"` (the raw body text) and `tier="masked"` (masked) from each chunk. Two collections, `{cid}__raw` / `{cid}__masked`, are also created in ChromaDB, and both are stored in the SQLite `chunks` table as well, with a `__masked` suffix.

**Tier2 (masking at answer time)**: `_mask_for_viewer` runs on the chat answer's LLM output, and for roles other than `admin` masking is forcibly applied (`routers/chat.py`). The collection the search draws from is also switched by role with `tier_for_role(role)` (`rag.py`).

**PII types that are detected**: The primary system (regular expressions) has 8 types: URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4. The secondary system (presidio + GiNZA) additionally detects PERSON_JP / ORG_JP / LOC_JP / ADDRESS_JP / DATE_TIME and others.

**Vault encryption**: The body text of the `raw` tier goes through `vault_enc.enc_raw()` and is encrypted with Fernet before being stored in SQLite / ChromaDB. The `masked` side is not encrypted, for search performance (double defense is unnecessary).

**PII detection mode**: With the `pii_mode` key in `cynovela.yaml` you can choose from `lite` (regular expressions only) / `standard` (default, Regex + GiNZA NER) / `quality` (all features).

**Read this before you rely on it.** The fact that masking matched does not mean all personal information in a document has been removed. The rules catch only 13 types that have a fixed shape; personal names and addresses depend on language analysis and are not masked at all under `lite`; organisation names and place names have no recognizer behind them; and whitespace inserted while extracting text from a PDF can let an email address escape. Every one of these limits is written out in [limits.md](limits.md).

## Q6. Are there features that do not work

Written honestly. Skeleton features (interface only, whose substance throws `NotImplementedError`) exist as follows.

| Feature | File | State |
|------|---------|------|
| MLX Embedding | `providers/embedding.py` | Not implemented |
| MLX Reranker | `providers/reranker.py` | Not implemented |
| Qdrant VectorStore | `providers/vector_store.py` | Skeleton only (add / search / delete / export / import are all unimplemented) |
| LanceDB backend | `providers/vector_store.py` | Initialization only; rejected when the package is not installed |
| GraphRAG strategy | `services/rag_strategies.py` | Not implemented |

Features that were explicitly abolished:

- The `/chat-popup` route (returns 410 Gone)
- Login with `user_id` alone (returns 401, changed to require `username/password`)
- The unauthenticated allowance in demo mode for `/api/auth/users` (changed to require `admin` authentication)
- The `--mock` startup option, the legacy `/api/transcribe` path, and `/api/sources/upload`

Features that are defined as settings but whose integration into the search pipeline is partial:

- `confidence_threshold` (default 0.40) is defined in config, but the logic to exclude low-confidence results is only partly integrated.
- Structured answer templates (JSON format, forced tags, and so on) are unimplemented. Answers are free-form.

Authentication is enforced even on a `--demo` start. The `@pytest.mark.skip` that remains in the authentication boundary tests is a leftover from when `--demo` bypassed authentication, and the reason text no longer matches the implementation.

The full list, including the limits of masking, the formats that cannot be read, the constraints when used concurrently, and the items that are not complete, is in [limits.md](limits.md).

## Q7. Where do I look next

- **To get it running**: [getting-started.md](getting-started.md)
- **What it is and what it is for**: [concept.md](concept.md)
- **How the pieces fit together, and how to read the scores**: [architecture.md](architecture.md)
- **To try it with your own documents, step by step**: [handson.md](handson.md)
- **To install it, keep it running, back it up and restore it**: [operations.md](operations.md)
- **Disclaimers, ways of use that are not recommended, and recommended configurations**: [security.md](security.md)
- **What it cannot do, and what to watch out for**: [limits.md](limits.md)
- **The API, the CLI, MCP, and what changed in each version**: [reference/api.md](reference/api.md) / [reference/cli.md](reference/cli.md) / [reference/mcp.md](reference/mcp.md) / [reference/changelog.md](reference/changelog.md)

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 企業・製品の公式見解を一切代表しません。

まだ何も始めていない場合は、まず [getting-started.md](getting-started.md) を読んでください。
Cynovela が何であり何のためのものかは [concept.md](concept.md) に、
できないことは [limits.md](limits.md) にあります。

**目次**

- [Q1. 参照元の AI 基盤ツールとの違いは何ですか](#q1-参照元の-ai-基盤ツールとの違いは何ですか)
- [Q2. データが外に出ないとはどういう意味ですか](#q2-データが外に出ないとはどういう意味ですか)
- [Q3. 使えるファイル種別は何ですか](#q3-使えるファイル種別は何ですか)
- [Q4. スペック要件はどれくらい必要ですか](#q4-スペック要件はどれくらい必要ですか)
- [Q5. 個人情報が入った文書はどう扱われますか](#q5-個人情報が入った文書はどう扱われますか)
- [Q6. 動かない機能はありますか](#q6-動かない機能はありますか)
- [Q7. 次はどこを見ればよいですか](#q7-次はどこを見ればよいですか)

## Q1. 参照元の AI 基盤ツールとの違いは何ですか

Cynovela は、参照元の AI 基盤ツールが解こうとしているコンセプト（組織内ドキュメントを安全にローカル LLM へつなぐ RAG 基盤）を、個人が手を動かして理解するために OSS だけで再実装した学習用プロジェクトです。実装はすべてオリジナルで、ソースコード・API 仕様・データモデルに参照元との互換性はありません。商用機能・サポート・SLA は提供しません。

詳しい対比は [concept.md](concept.md) にあります。

## Q2. データが外に出ないとはどういう意味ですか

Cynovela の既定構成では、以下のすべてがローカル環境で完結します。

- **文書本文**: SQLite（`~/.cynovela/db/cynovela.db` 等）と ChromaDB（`~/.cynovela/vector/default/chroma` 等）に保存。
- **Embedding 生成**: 既定モードでは BGE-M3 をローカルで実行。
- **LLM 推論**: `--lmstudio-url`（既定 `http://localhost:1234`）で指定したローカル LLM に対して OpenAI 互換 /v1 API で送信。

外部送信が発生し得るのは以下の場合のみで、いずれも明示的な設定が必要です。

- `--lan` / `--allow-tailscale` / `--allow-subnet` で他ホストからのアクセスを許可した場合。
- `reranker.provider` を `cohere` / `jina` / `voyage` などの外部 API に設定した場合。
- `execution.llm_provider` を `openrouter` / `claude_api` に設定した場合。

**待ち受けアドレスについて。** サーバーは既定で `0.0.0.0` を待ち受けるため、同じネットワークの他の端末から到達できます。自マシン内に絞るには `--local-only` を付けます。IP アローリストミドルウェアは `--allow-subnet` / `--allow-tailscale` を渡したときだけ働き、渡さないときは何も制限しません。

外部への送出をわざと止めている条件、およびその結果として機能が動いていないように見える場合は [limits.md](limits.md) に列挙してあります。

## Q3. 使えるファイル種別は何ですか

`rag.py` の `extract_text()` がテキスト抽出を担当します。取り込めるのは `SUPPORTED_EXTENSIONS` に書かれた形式——文書（`.txt` `.md` `.csv` `.pdf` `.docx`）、表計算・プレゼン（`.xlsx` `.xls` `.pptx`）、Web・メール（`.html` `.htm` `.eml`）、書庫（`.zip`）、画像（`.jpg` `.jpeg` `.png` `.heic` `.webp` `.gif`）——です。網羅的な一覧と、よく持ち込まれるのに**扱えない**形式は [limits.md](limits.md) にあります。

**画像について。** 既定の動作は `filename_only` で、索引にはファイル名だけが入ります。画像の中の文字は読みません。OCR（光学文字認識）の仕組みはありません。説明文を生成する設定（`caption` / `lm_studio`）はありますが、同梱の `cynovela.yaml` に `image:` の項目が無いため既定のままです。画像として作られた PDF（単に読み取っただけのもの）からは一文字も取り出せません。

## Q4. スペック要件はどれくらい必要ですか

どの起動モード（`--mode`）でも、必要なモデルは同じです（切替は未配線）。

| モード | Embedding モデル | サイズ | 推奨環境 |
|--------|----------------|-------|----------|
| `text`（既定） | BAAI/bge-m3 | 約 2.3GB | GPU 不要・汎用 |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — |
| `minimal` | 名目上は TF-IDF ですが TF-IDF の統合が無く、ここでも BAAI/bge-m3 が要ります | — | — |

**どのモードを選んでも、必要なモデルの大きさは変わりません。**

LLM 側の要件は別途必要です（以前あった `--mock`＝LLM を呼ばずに動かす指定は撤去済みです）。本リポジトリの検証は MacBook Pro M4 Max 128GB で行っています。

## Q5. 個人情報が入った文書はどう扱われますか

Cynovela は二段構えで PII（Personally Identifiable Information: 個人情報）を扱います。

**Tier1（取込時マスキング）**: publish のタイミングで `rag.py` の `_mtws_publish`（= `guardrail.mask_text_with_spans`）が走り、各チャンクから `tier="raw"`（生本文）と `tier="masked"`（マスク済み）の両系統を生成します。ChromaDB にも `{cid}__raw` / `{cid}__masked` の 2 つの collection が作られ、SQLite の `chunks` テーブルにも `__masked` サフィックス付きで両方保存されます。

**Tier2（回答時マスキング）**: チャットの回答 LLM 出力に対して `_mask_for_viewer` が動き、`admin` 以外のロールでは強制的にマスクを適用します（`routers/chat.py`）。検索の引き先 collection も `tier_for_role(role)` でロール別に切り替わります（`rag.py`）。

**検出される PII 種別**: 一次系（正規表現）は URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4 の 8 種類。二次系（presidio + GiNZA）でさらに PERSON_JP / ORG_JP / LOC_JP / ADDRESS_JP / DATE_TIME などを追加検出します。

**保管庫暗号化**: `raw` tier の本文は `vault_enc.enc_raw()` を経由して Fernet で暗号化されてから SQLite / ChromaDB に保存されます。`masked` 側は検索性能のため暗号化しません（二重防御不要）。

**PII 検出モード**: `cynovela.yaml` の `pii_mode` キーで `lite`（正規表現のみ）/ `standard`（既定、Regex + GiNZA NER）/ `quality`（全機能）から選べます。

**頼る前に読んでください。** マスキングが当たったからといって、資料の中の個人情報がすべて消えたわけではありません。規則で取れるのは決まった形をした 13 種類だけで、氏名と住所は言語解析まかせのため `lite` にすると一切マスキングされず、組織名と地名は名前だけあって実体の認識器がありません。PDF からの文字取り出しで入る空白により、電子メールがマスキングを逃れることもあります。これらの限界はすべて [limits.md](limits.md) に書き出してあります。

## Q6. 動かない機能はありますか

正直に書きます。スケルトン（インターフェイスのみで実体は `NotImplementedError` を投げる）の機能が以下に存在します。

| 機能 | ファイル | 状態 |
|------|---------|------|
| MLX Embedding | `providers/embedding.py` | 未実装 |
| MLX Reranker | `providers/reranker.py` | 未実装 |
| Qdrant VectorStore | `providers/vector_store.py` | 骨格のみ（add / search / delete / export / import すべて未実装） |
| LanceDB バックエンド | `providers/vector_store.py` | 初期化のみ。パッケージ未導入時は拒否 |
| GraphRAG 戦略 | `services/rag_strategies.py` | 未実装 |

明示的に廃止された機能:

- `/chat-popup` ルート（410 Gone を返却）
- `user_id` 単独ログイン（401 を返却、`username/password` 必須に変更）
- `/api/auth/users` のデモモード未認証許可（`admin` 認証必須に変更）
- `--mock` 起動指定、旧 `/api/transcribe` 経路、`/api/sources/upload`

設定としては定義されているが、検索パイプラインへの統合が部分的な機能:

- `confidence_threshold`（既定 0.40）は config に定義済みだが、低信頼度結果の除外ロジックは部分統合に留まります。
- 構造化回答テンプレート（JSON 形式・タグ強制など）は未実装。回答は自由形式。

`--demo` 起動でも認証は強制されます。認証境界テストに残っている `@pytest.mark.skip` は、`--demo` が認証をバイパスしていた頃の名残で、理由文はすでに実装と合っていません。

マスキングの限界・読み込めない形式・同時に使うときの制約・完了していない事項を含む全一覧は [limits.md](limits.md) にあります。

## Q7. 次はどこを見ればよいですか

- **とにかく動かす**: [getting-started.md](getting-started.md)
- **何であり何のためのものか**: [concept.md](concept.md)
- **部品の組み合わせ方とスコアの読み方**: [architecture.md](architecture.md)
- **自分の資料で順を追って試す**: [handson.md](handson.md)
- **入れる・動かし続ける・控えを取って戻す**: [operations.md](operations.md)
- **免責・推奨しない使用方法・推奨運用構成**: [security.md](security.md)
- **できないこと・気をつけること**: [limits.md](limits.md)
- **API・CLI・MCP・版ごとの変更**: [reference/api.md](reference/api.md) / [reference/cli.md](reference/cli.md) / [reference/mcp.md](reference/mcp.md) / [reference/changelog.md](reference/changelog.md)

---
