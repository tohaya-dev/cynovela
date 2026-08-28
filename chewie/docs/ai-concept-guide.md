# AI コンセプトガイド

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built so that an individual
> could understand the concepts of an AI platform tool by working with their own hands.
> It is not a commercial product and not an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

This is an explanation of the concepts around RAG, written so that you can understand them by running Cynovela. It is based only on public information and on the implementation in this repository.

## 1. The Concept of RAG

RAG (Retrieval-Augmented Generation) is a method in which external documents are searched for a user's question, and the search results are passed to the LLM as context before the answer is generated. It is used when you want the LLM to answer with in-house information that the LLM alone does not know (regulations, procedures, meeting minutes).

In Cynovela, `rag_retrieve()` in `rag.py` is the main search function, and it runs the following pipeline (A-3 §10).

1. **Vector Search**: The question is turned into an embedding (dense vector) with BGE-M3, and chunks that are close by cosine similarity are retrieved from ChromaDB.
2. **BM25 Search**: Lexically close chunks are retrieved from the in-memory BM25Okapi index (tokenized with fugashi/MeCab).
3. **Hybrid Integration**: By default both are integrated with RRF (Reciprocal Rank Fusion, k=60). The `weighted` method (Vector 0.7 + BM25 0.3) can also be chosen.
4. **Parent-Child Resolution**: Child chunks that were hit by the search are replaced with their parent chunks (A-3 PHASE A-3, `rag.py:2251-2281`).
5. **Reranker** (optional): If a reranker provider is configured, the top results are reordered with a CrossEncoder or similar.
6. **Final Ranking**: The top `n_results` items are returned.

The search results are assembled into a context string with citation numbers (`build_context_with_citations`, A-3 line 291) and placed at the end of the LLM prompt (the CLAUDE.md principle "the system prompt comes after retrieved_content").

As applied features, Multi-Query RAG (A-5 §3), CRAG (Corrective RAG: self-evaluation of search results, then re-search, A-6), HyDE (Hypothetical Document Embeddings: generate a hypothetical text, then search with its embedding, A-7), and Adaptive RAG (an agentic loop that follows query complexity, `adaptive_rag.py`) are all implemented.

## 2. Why Data Cannot Be Sent to the Cloud (Data Sovereignty)

The typical reasons why in-house documents cannot be sent to an external API are listed below.

- **Data sovereignty**: The principle of not taking documents outside national or organizational borders.
- **Audit requirements**: You want to preserve "when, who, which document, with which query" as an internal audit log. In Cynovela, `_log_audit(conn, action, target, detail)` is always called for important operations (Source creation and deletion, Publish, Chat, PII detection, prompt injection blocking) (CLAUDE.md, A-2 §1).
- **PII / confidential information**: You do not want documents containing personal information or trade secrets mixed into external training data.
- **Reproducibility**: With an external LLM, the model version changes at the operator's convenience. There are cases in internal verification where you want to keep using the same model.

To meet these requirements, Cynovela adopts an IP allowlist middleware that can narrow down where access comes from (A-5 §4, it works when `--allow-subnet` and similar are passed), vault encryption with Fernet (A-2 §8), and connection to a local LLM (an OpenAI-compatible /v1 API such as LM Studio).

## 3. PII Protection

PII (Personally Identifiable Information) protection has two stages (A-2 §6, §7).

**Tier1: Masking at ingest time**

At Publish time, `_mtws_publish` (`guardrail.mask_text_with_spans`) runs on every chunk and produces both a `raw` and a `masked` line. Rows with a `__masked` suffix are created in the SQLite `chunks` table, and two collections, `{collection_id}__raw` and `{collection_id}__masked`, are created in ChromaDB.

**Tier2: Masking at answer time**

`_mask_for_viewer(text, user)` is called at four points on the chat response path (normal response / compare A / compare B / SSE streaming). By the decision in `tier_for_role(role)`, only `admin` passes through; everything else (`curator` / `viewer` / unset) always gets the exit masking applied.

**Detection methods and detected types**

The primary system (`guardrail.py`, regular expressions) detects 8 types — URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4 — and replaces each with a token such as `[MASKED:URL]` or `[MASKED:EMAIL]`. The secondary system (`utils/metadata/pii.py`, presidio + GiNZA fallback) additionally detects PERSON_JP / ORG_JP / LOC_JP / ADDRESS_JP / DATE_TIME and others.

The PII detection mode can be chosen with the `pii_mode` key in `cynovela.yaml` from `lite` (regular expressions only) / `standard` (default) / `quality` (all features) (A-1 §3).

**Vault encryption**

The body text of the `raw` tier goes through `vault_enc.enc_raw()` and is stored Fernet-encrypted with an `enc:` prefix. The `masked` side is not encrypted (search performance is preserved, and the double defense is achieved on the raw side). The key is read from the `CYNOVELA_SECRET_KEY` environment variable (A-2 §8).

## 4. What the Scores Mean (Cosine Similarity, Reranker)

Several scores with different scales appear in Cynovela's search. It is important not to confuse them.

**Vector Score (cosine similarity)**: A 0 to 1 scale. BGE-M3 turns a sentence into a vector, and the ChromaDB distance is converted into a similarity with `_dist_to_sim()` (A-3 §11, `rag.py:3204`). The noise floor of BGE-M3 is 0.35 to 0.45, and real queries (ones whose answer is in a published file) typically land around 0.55 to 0.75. The low-confidence fallback threshold `confidence_threshold` is 0.40 by default (`config.py:181-185`).

**BM25 Score**: A lexical score based on word occurrence frequency. It is normalized to `[0, 1]` before integration.

**RRF Score**: The score of reciprocal rank fusion. It is a method that sums `1 / (k + rank)` for each rank (k=60 by default), and the maximum value is a small number of roughly 0.033. **You must not perform a cosine similarity threshold decision with an RRF score** (CLAUDE.md lesson 2; because the order of magnitude differs, there was a past case where abstention misfired on every query).

**Rerank Score**: The score that a reranker provider assigns after evaluating a pair of the query and a candidate chunk. It is held as `rerank_score: float = 0.0` at `pipeline_types.py:71`, and 0 means it was not applied. The default is `NoReranker` (disabled); you enable it by choosing `yaml.reranker.provider` from `cross_encoder` / `flashrank` / `ollama` / `cohere` / `jina` / `voyage` / `openai_compat` (A-1).

## 5. RBAC (Role-Based Access Control)

There are 3 roles (A-5 §2, the CHECK constraint at line 18 of `db.py`).

| Role | Function |
|--------|------|
| `admin` | Full administrative rights. User management, system setting changes, viewing PII detection history. The only role that can see the raw body text (raw tier). |
| `viewer` | Viewing only. RAG search and report viewing. |

> Names such as `curator` / `data-scientist` are accepted as backward-compatible values, but in the current implementation they are normalized to `viewer` and have no rights of their own (the effective roles are the 2 values `admin` / `viewer`).

On the API side, authorization is done with the 4 helpers in `core/auth.py` (A-5 §2).

- `_require_admin(request)`: requires `role == 'admin'`
- `_require_authenticated(request)`: any role, as long as it is authenticated
- `_require_role(request, allowed)`: requires a role in the given set
- `_require_admin_or_self(request, user_id)`: the administrator or the person themselves

There are 242 RBAC checks under routers/, and 13 routers apply `_require_admin` (A-5 §2).

There is also an ACL (Access Control List) filter inside the search pipeline: on both the vector and BM25 paths of `rag_retrieve()`, chunks whose `metadata.allowed_roles` does not contain `user_role` are excluded (A-3 §10, `rag.py:1958` `_filter_hits_by_role`). It is skipped when `features.acl_filter=False`.

## 6. Audit Logs

Audit logs are recorded in the `audit_logs` table, and deletion or modification through the API is prohibited (CLAUDE.md, Security). The recorded targets are important operations such as the following.

- Creation and deletion of Source / Workspace / Collection
- Start and completion of Publish
- Chat (the query and referenced sources, and firing of the low-confidence fallback)
- PII detection (`PII_DETECTED` / `pii_detected`, A-2 §1)
- Prompt injection blocking (`PROMPT_INJECTION_BLOCKED`, A-2 §9)
- Authentication failure (`user_id_only_login_removed` and so on, A-6 §2)

The PII detection history can be obtained from `/api/guardrails/pii-detections`, and `_require_admin` is applied to it (A-2 §2, restricted to admin in FIX-026).

In `_AUDIT_CATEGORY_MAP` of `core/audit.py`, each action is classified into a category (such as `security`).

## 7. Smart Ingestion

Smart Ingestion is a mechanism that automatically classifies documents into 14 categories (A-4 §1, `utils/metadata/classification.py`).

**Categories**: the 14 kinds `governance_policy` / `incident_report` / `technical_guide` / `case_study` / `meeting_minutes` / `audit_report` / `poc_report` / `faq` / `whitepaper` / `checklist` / `proposal_rfp` / `newsletter` / `reference` / `other`.

As a separate system, there is also classification of the document type (the 5 kinds `contract` / `technical_spec` / `email` / `report` / `manual`).

There are 3 **classification engines** (A-4 §2).

| Engine | Mechanism | Confidence |
|---------|-------|--------|
| `LightweightClassifier` | Keyword match on the file name + the first 500 characters | 0.85 (file name) / 0.65 (content) |
| `LLMClassifier` | Zero-shot classification with local Ollama, JSON output enforced | LLM output |
| `HybridClassifier` | Lightweight first, LLM fallback when the confidence is below 0.65 | Integrated |

In addition, a PII-only `RuleBasedClassifier` (EMAIL / PHONE / MYNUMBER) and an externally delegated `APIClassifier` are in `providers/classifier.py`.

The **chunk splitting strategy** (A-4 §6) is the sliding window method by default (`chunk_size=500`, `overlap=50`, `split_chunks()`). If you set `chunking.contextual=true`, contextual chunking runs, which prepends metadata (file name, type, sensitivity, department, position, tags) to the head of the chunk as [context] (`chunker.py`, `build_context_prefix`). There are 3 RAG strategies: `simple` / `hybrid_bm25` / `contextual`.

Five **RAG presets** (A-3 §4) are also provided: technical documents / confidential documents / personal notes / multimedia / quick start.

## 8. Relationship with the Referenced Tool

Cynovela is a re-implementation, using only OSS and for an individual's learning purposes, of the concept that the referenced AI platform tool tries to solve (a RAG platform that safely connects in-house documents to a local LLM).

- **The implementation is entirely original**: There is no compatibility with the referenced tool in the source code, the API specification, or the data model. It is assembled from OSS parts: FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
- **It does not represent an official position**: The design decisions, trade-offs, and implementation content are all the responsibility of an individual, and do not represent any official specification or position of the referenced AI platform tool or its affiliated companies.
- **Purpose**: To understand the concept "by working with your own hands". Commercial use and production operation are not assumed.

For the formal specification and features of the referenced AI platform tool, please refer to the official documentation of its provider.

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela を動かして理解するための、RAG 周辺概念の解説です。公開情報と本リポジトリの実装のみを根拠としています。

## 1. RAG の概念

RAG（Retrieval-Augmented Generation: 検索拡張生成）は、ユーザーの質問に対して外部の文書を検索し、検索結果を文脈として LLM に渡してから回答を生成する方式です。LLM 単体が知らない社内固有の情報（規程・手順・議事録）に答えさせる際に使います。

Cynovela では `rag.py` の `rag_retrieve()` がメインの検索関数で、以下のパイプラインを実行します（A-3 §10）。

1. **Vector Search**: 質問を BGE-M3 で Embedding（密ベクトル）化し、ChromaDB に対してコサイン類似度で近いチャンクを取得。
2. **BM25 Search**: メモリ上の BM25Okapi インデックス（fugashi/MeCab トークナイズ）で語彙的に近いチャンクを取得。
3. **Hybrid Integration**: 既定では RRF（Reciprocal Rank Fusion: 相互順位融合、k=60）で両系統を統合。`weighted` 方式（Vector 0.7 + BM25 0.3）も選べます。
4. **Parent-Child Resolution**: 検索でヒットした子チャンクを親チャンクに差し替え（A-3 PHASE A-3、`rag.py:2251-2281`）。
5. **Reranker**（オプション）: Reranker プロバイダーが設定されていれば、上位を CrossEncoder 等で再順序付け。
6. **Final Ranking**: 上位 `n_results` 件を返却。

検索結果は引用番号付きでコンテキスト文字列に組み立てられ（`build_context_with_citations`、A-3 行 291）、LLM プロンプトの末尾に配置されます（CLAUDE.md 「retrieved_content の後にシステムプロンプト」原則）。

応用機能として Multi-Query RAG（A-5 §3）、CRAG（Corrective RAG: 検索結果の自己評価 → 再検索、A-6）、HyDE（Hypothetical Document Embeddings: 仮想文章生成 → その Embedding で検索、A-7）、Adaptive RAG（クエリ複雑度に応じた agentic ループ、`adaptive_rag.py`）がすべて実装済みです。

## 2. クラウドに送信できない理由（データ主権）

社内ドキュメントを外部 API に送信できない代表的な理由を列挙します。

- **データ主権**: 文書を国境・組織境界の外に持ち出さない原則。
- **監査要件**: 「いつ・誰が・どの文書を・どのクエリで参照したか」を内部監査ログとして保全したい。Cynovela では `_log_audit(conn, action, target, detail)` を重要操作（Source 作成・削除、Publish、Chat、PII 検出、プロンプトインジェクション遮断）で必ず呼びます（CLAUDE.md、A-2 §1）。
- **PII / 機密情報**: 個人情報や営業秘密を含む文書を外部学習データに混ぜたくない。
- **再現性**: 外部 LLM はモデルバージョンが運営者都合で変わります。社内検証では同一モデルを使い続けたいケースがあります。

Cynovela はこれらの要請に応えるため、アクセス元を絞れる IP アローリストミドルウェア（A-5 §4・`--allow-subnet` 等を渡したときに働く）、Fernet による保管庫暗号化（A-2 §8）、ローカル LLM（LM Studio などの OpenAI 互換 /v1 API）への接続を採用しています。

## 3. PII 保護

PII（Personally Identifiable Information: 個人情報）保護は二段構えです（A-2 §6, §7）。

**Tier1: 取込時マスキング**

Publish の際、各チャンクに対して `_mtws_publish`（`guardrail.mask_text_with_spans`）が動き、`raw` と `masked` の両系統を生成します。SQLite の `chunks` テーブルには `__masked` サフィックス付きの行が、ChromaDB には `{collection_id}__raw` と `{collection_id}__masked` の 2 つの Collection が作られます。

**Tier2: 回答時マスキング**

チャット応答経路 4 箇所（通常応答 / compare A / compare B / SSE ストリーミング）で `_mask_for_viewer(text, user)` が呼ばれます。`tier_for_role(role)` の判定で `admin` のみ素通し、それ以外（`curator` / `viewer` / 未設定）は出口マスクを必ず適用します。

**検出方式と検出種別**

一次系（`guardrail.py`、正規表現）で URL / EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / PASSPORT / IPV4 の 8 種類を検出し、それぞれ `[MASKED:URL]` `[MASKED:EMAIL]` などのトークンに置換します。二次系（`utils/metadata/pii.py`、presidio + GiNZA フォールバック）で PERSON_JP / ORG_JP / LOC_JP / ADDRESS_JP / DATE_TIME などを追加検出します。

PII 検出モードは `cynovela.yaml` の `pii_mode` キーで `lite`（正規表現のみ）/ `standard`（既定）/ `quality`（全機能）から選択できます（A-1 §3）。

**保管庫暗号化**

`raw` tier の本文は `vault_enc.enc_raw()` を通り、`enc:` プレフィックス付きで Fernet 暗号化されて保存されます。`masked` 側は暗号化しません（検索性能を確保し、二重防御は raw 側で達成）。鍵は `CYNOVELA_SECRET_KEY` 環境変数から読み込みます（A-2 §8）。

## 4. スコアの意味（コサイン類似度・Reranker）

Cynovela の検索ではスケールの異なる複数のスコアが登場します。混同しないことが重要です。

**Vector Score（コサイン類似度）**: 0〜1 のスケール。BGE-M3 が文をベクトル化し、ChromaDB の距離（distance）を `_dist_to_sim()` で類似度に変換した値（A-3 §11、`rag.py:3204`）。BGE-M3 のノイズフロアは 0.35〜0.45 で、実存クエリ（publish 済みの file に答えがあるもの）は典型的に 0.55〜0.75 程度になります。低信頼度フォールバックの閾値 `confidence_threshold` は既定 0.40 です（`config.py:181-185`）。

**BM25 Score**: 単語の出現頻度に基づく語彙的スコア。`[0, 1]` に正規化してから統合されます。

**RRF Score**: 相互順位融合のスコア。各順位（rank）に対して `1 / (k + rank)`（k=60 既定）を足し合わせる方式で、最大値はおおむね 0.033 程度の小さな値になります。**RRF スコアでコサイン類似度の閾値判定を行ってはいけません**（CLAUDE.md 教訓 2、桁が違うため全クエリで Abstention が誤発火した過去あり）。

**Rerank Score**: Reranker プロバイダーがクエリと候補チャンクのペアを評価して付与するスコア。`pipeline_types.py:71` で `rerank_score: float = 0.0` として保持され、0 なら未適用を意味します。既定は `NoReranker`（無効）で、`yaml.reranker.provider` を `cross_encoder` / `flashrank` / `ollama` / `cohere` / `jina` / `voyage` / `openai_compat` から選んで有効化します（A-1）。

## 5. RBAC（ロールベースアクセス制御）

ロールは 3 種類です（A-5 §2、`db.py` 行 18 の CHECK 制約）。

| ロール | 役割 |
|--------|------|
| `admin` | フル管理権限。ユーザー管理・システム設定変更・PII 検出履歴閲覧。生本文（raw tier）を見られる唯一のロール。 |
| `viewer` | 閲覧のみ。RAG 検索・レポート閲覧。 |

> `curator` / `data-scientist` 等の名称は後方互換の値として受理されますが、現行実装では `viewer` に正規化され、固有権限はありません（実効ロールは `admin` / `viewer` の 2 値）。

API 側では `core/auth.py` の 4 つのヘルパーで認可します（A-5 §2）。

- `_require_admin(request)`: `role == 'admin'` を要求
- `_require_authenticated(request)`: 認証済みであればロール不問
- `_require_role(request, allowed)`: 指定集合のロールを要求
- `_require_admin_or_self(request, user_id)`: 管理者または本人

RBAC チェックは routers/ 配下に 242 箇所、`_require_admin` 適用ルーターは 13 個あります（A-5 §2）。

検索パイプライン内部にも ACL（Access Control List）フィルターがあり、`rag_retrieve()` の Vector / BM25 両経路で `metadata.allowed_roles` に `user_role` が含まれないチャンクを除外します（A-3 §10、`rag.py:1958` `_filter_hits_by_role`）。`features.acl_filter=False` のときはスキップします。

## 6. 監査ログ

監査ログは `audit_logs` テーブルに記録され、API 経由での削除・変更は禁止されています（CLAUDE.md セキュリティ）。記録対象は以下のような重要操作です。

- Source / Workspace / Collection の作成・削除
- Publish の開始・完了
- Chat（クエリと参照ソース、低信頼度フォールバックの発火）
- PII 検出（`PII_DETECTED` / `pii_detected`、A-2 §1）
- プロンプトインジェクション遮断（`PROMPT_INJECTION_BLOCKED`、A-2 §9）
- 認証失敗（`user_id_only_login_removed` など、A-6 §2）

PII 検出履歴は `/api/guardrails/pii-detections` から取得可能で、`_require_admin` が掛かっています（A-2 §2、FIX-026 で admin 限定化）。

`core/audit.py` の `_AUDIT_CATEGORY_MAP` で各 action がカテゴリ（`security` 等）に分類されています。

## 7. Smart Ingestion（賢い取り込み）

Smart Ingestion は文書を 14 のカテゴリに自動分類する仕組みです（A-4 §1、`utils/metadata/classification.py`）。

**カテゴリ**: `governance_policy` / `incident_report` / `technical_guide` / `case_study` / `meeting_minutes` / `audit_report` / `poc_report` / `faq` / `whitepaper` / `checklist` / `proposal_rfp` / `newsletter` / `reference` / `other` の 14 種類。

別系統で文書タイプ（`contract` / `technical_spec` / `email` / `report` / `manual` の 5 種類）の分類もあります。

**分類エンジン**は 3 種類（A-4 §2）。

| エンジン | 仕組み | 信頼度 |
|---------|-------|--------|
| `LightweightClassifier` | ファイル名 + 先頭 500 文字のキーワードマッチ | 0.85（ファイル名）/ 0.65（コンテンツ） |
| `LLMClassifier` | ローカル Ollama でゼロショット分類、JSON 出力強制 | LLM 出力 |
| `HybridClassifier` | Lightweight 優先、信頼度 0.65 未満で LLM フォールバック | 統合 |

加えて PII 専用の `RuleBasedClassifier`（EMAIL / PHONE / MYNUMBER）と外部委譲 `APIClassifier` が `providers/classifier.py` にあります。

**チャンク分割戦略**（A-4 §6）は既定でスライディングウィンドウ方式（`chunk_size=500`、`overlap=50`、`split_chunks()`）。`chunking.contextual=true` を設定すると、チャンク冒頭にメタデータ（ファイル名・種別・感度・部門・位置・タグ）を [コンテキスト] として付加する Contextual Chunking が走ります（`chunker.py`、`build_context_prefix`）。RAG 戦略は `simple` / `hybrid_bm25` / `contextual` の 3 種類です。

**RAG プリセット**（A-3 §4）も 5 つ用意されています: 技術文書 / 機密文書 / 個人メモ / マルチメディア / クイックスタート。

## 8. 参照元との関係

Cynovela は、参照元の AI 基盤ツールが解こうとしているコンセプト（社内ドキュメントを安全にローカル LLM につなぐ RAG 基盤）を、個人の学習目的で OSS だけで再実装したものです。

- **実装はすべてオリジナル**: ソースコード・API 仕様・データモデルに参照元との互換性はありません。FastAPI / SQLite / ChromaDB / BGE-M3 / ローカル LLM の OSS 部品で組み立てています。
- **公式見解を代表しない**: 設計判断・トレードオフ・実装内容はすべて個人の責任で、参照元の AI 基盤ツール・関連会社の公式な仕様や見解を一切代表しません。
- **目的**: コンセプトを「手を動かして」理解すること。商用利用・本番運用は想定していません。

参照元の AI 基盤ツールの正式な仕様や機能については、その提供元の公式ドキュメントを参照してください。

---
