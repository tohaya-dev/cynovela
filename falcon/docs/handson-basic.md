# ハンズオン（基礎編）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual to
> understand the concepts of AI infrastructure tools hands-on. It is not a
> commercial product or an official implementation.
> The implementation is entirely original, and consists of an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

In this hands-on, you go through 5 steps, from creating a workspace to RAG (Retrieval-Augmented Generation) queries, checking the audit log, and experiencing the guardrails.

As a precondition, it is assumed that Cynovela has already been started according to the quickstart.

---

## Step 1: Create a workspace

### Why it is needed

A workspace is the management unit that groups users, guardrail policies, and collections (sets of files). By splitting them per business area or per information sensitivity, it becomes easier to apply the access control and the guardrails in the later stages.

### Operation

Open the "workspace management" screen in the GUI and press the "create new" button.

Input items:

| Item | Content |
|------|------|
| Name | Workspace name (unique) |
| Guardrail policy | Select 1 policy to apply |

In demo mode, the following 3 kinds of guardrail policies are prepared in advance.

| Policy ID | Name | Content |
|-----------|------|------|
| `pol-pii` | PII protection policy | PII is `mask`, Financial is `exclude_from_rag` |
| `pol-strict` | Strict management policy | PII is `mask`, Financial and HR are `exclude_from_rag` |
| `pol-log` | Log only policy | PII and Financial are `log_only` (recorded only, not masked) |

There are 4 kinds of guardrail actions (`mask` / `exclude_from_rag` / `log_only` / `allow`).

---

## Step 2: Ingest files and check the classification

### Why it is needed

Cynovela automatically classifies each ingested document with a metadata assignment mechanism called "Smart Ingestion". This is so that, in the later RAG search and reports, you can grasp "how many documents of which kind there are".

### Classification categories (14 kinds)

| Category ID | Description |
|-----------|------|
| governance_policy | Governance and policy documents |
| incident_report | Incident report |
| technical_guide | Technical guide and manual |
| case_study | Case study |
| meeting_minutes | Meeting minutes |
| audit_report | Audit and assessment report |
| poc_report | POC evaluation report |
| faq | FAQ, frequently asked questions |
| whitepaper | Whitepaper |
| checklist | Checklist |
| proposal_rfp | Proposal, RFP |
| newsletter | Newsletter, technical information |
| reference | Reference, glossary |
| other | Other |

### Choosing the classification engine

Cynovela can switch between 3 kinds of classification engines.

| Engine | Mechanism | Characteristics |
|---------|------|------|
| Lightweight | Keyword match on the file name and the first 500 characters | Very small CPU, stateless, fast |
| LLM | Zero-shot classification with a local LLM (Ollama) | Strong on context, requires the LLM to be running |
| Hybrid | Falls back to the LLM if the Lightweight confidence is below the threshold (0.65) | The default combination |

### Operation

1. Select a workspace and run "create collection"
2. Upload files (PDF / DOCX / TXT / images, and so on)
3. Start the ingest with the "Publish" button

After Publish, a category and a confidence are assigned to each file, and you can check them in the GUI.

---

## Step 3: RAG queries and how to read the scores

### Why it is needed

RAG is a "hybrid search" that combines vector search (semantic similarity) and BM25 search (keyword match). Once you can read the scores, it becomes easier to judge and tune the answer quality.

### Composition of the hybrid search

Cynovela integrates the following 2 systems.

| Search system | Mechanism | Default weight |
|---------|------|----------|
| Vector search | Computes cosine similarity with an Embedding (default: BGE-M3) | 70% (when weighted) |
| BM25 search | Keyword match based on morphological analysis | 30% (when weighted) |

Two integration methods can be selected.

- `weighted`: weighted addition of the scores (vector × 0.7 + bm25 × 0.3)
- `rrf` (Reciprocal Rank Fusion, default): adds the reciprocals of the ranks (smoothed with k=60)

### Rough guide to the scores (vector cosine similarity)

For BGE-M3, the Embedding model used in the AI infrastructure tool that this refers to, the rough guide is as follows.

| Score band | Interpretation |
|---------|------|
| 0.35 to 0.45 | Noise floor. Appears even for unrelated queries |
| 0.50 | The default value of the confidence threshold (`confidence_threshold`) |
| 0.55 to 0.75 | Typical hit range for a real query |
| 0.75 and above | Extremely highly relevant |

### Reranker

The Reranker is a mechanism that "re-evaluates the top N search results with a more precise model and reorders them". The default is `NoReranker` (not applied), but it can be switched in the settings to a provider such as `cross_encoder` / `flashrank`.

### Advanced RAG features (those enabled by default)

| Feature | Role |
|------|------|
| MMR (Maximal Marginal Relevance) | Balances relevance and diversity. Controlled with `mmr_lambda` |
| Parent-Child chunking | Searches with the small child chunks, and swaps in the text of the parent chunk for the answer |
| Multi-Query | Expands the query into N-1 similar queries with the LLM and integrates them with RRF |
| CRAG (Corrective RAG) | The LLM evaluates whether the search results are sufficient, and searches again if necessary |
| HyDE (OFF by default) | Generates a hypothetical answer first and searches with its embedding |
| Adaptive RAG | Switches between basic / agentic according to the complexity of the query |

### Operation

1. Enter a query on the RAG Chat screen
2. An answer and citation numbers `[1][2]` are returned
3. If you switch the detail display mode to `developer`, you can see the vector score / BM25 score / hybrid score / Reranker score of each chunk

---

## Step 4: Check the audit log

### Why it is needed

Cynovela records all important operations in the "audit_logs" table. It is a mechanism that lets you verify afterwards who did what and when, and how many PII (personal information) items were detected.

### Main recording targets

- Creation and deletion of workspaces, collections, and sources
- Execution and completion of Publish
- Chat (question and answer)
- PII detection (`PII_DETECTED` / `pii_detected`)
- Prompt injection detection (`PROMPT_INJECTION_BLOCKED`)
- Authentication failure

### Operation

Browse it from the "audit log" screen of the GUI (admin only). The following filters are available.

- Action type
- Target (workspace ID / collection ID)
- Date and time range

### Through the API

- `GET /api/guardrails/pii-detections` — aggregates PII detections from `audit_logs` (admin required)
- `GET /api/pii-detections` — aggregates per document from the `chunks` table (admin required)

> **Important**: `audit_logs` cannot be deleted or modified through the API (tamper prevention).

---

## Step 5: Experience the guardrails

### Why it is needed

The guardrails work in two stages, "detection → action", and prevent the leakage of PII and sensitive information. They operate as a double defense of Tier1 (masking at ingest time) and Tier2 (masking at answer time).

### Tier1: masking at ingest time

At the timing of Publish, 2 systems, "raw (the original body text)" and "masked", are generated from each chunk, and both are stored into the 2 collections of ChromaDB (`{cid}__raw` / `{cid}__masked`) and into the `chunks` table of SQLite.

### Tier2: masking at answer time

An exit mask is applied to the output of the LLM according to the role.

| Role | Vault searched | Exit mask |
|--------|-------------|----------|
| `admin` | raw (the original body text) | None |
| `curator` / `viewer` | masked | Yes |

### PII types that are detected

The types handled by the regular expression base (primary detection) are as follows.

| Type | Mask token | Example |
|------|-------------|-----|
| URL | `[MASKED:URL]` | `https://example.com/...` |
| EMAIL | `[MASKED:EMAIL]` | `taro@example.co.jp` |
| PHONE_JP | `[MASKED:PHONE]` | `090-1234-5678` |
| PHONE_LAND | `[MASKED:PHONE]` | `03-1234-5678` |
| CREDIT | `[MASKED:CREDIT]` | Card number format |
| MYNUMBER | `[MASKED:MYNUM]` | My Number format |
| PASSPORT | `[MASKED:PASSPORT]` | Passport number format |
| IPV4 | `[MASKED:IP]` | IPv4 address |

In addition to these, the secondary system (presidio + GiNZA NER) detects named entities such as `ADDRESS_JP` / `PERSON_JP` / `ORG_JP` / `LOC_JP`.

### Detection modes

You can switch among 3 levels with the `pii_mode` key of `cynovela.yaml` (the default is `standard`).

| Mode | Method | Characteristics |
|--------|------|------|
| `lite` | Regular expressions only | Lightweight and fast |
| `standard` | Regular expressions + GiNZA NER | Middle ground, recommended |
| `quality` | Regular expressions + GiNZA NER + detailed filter | High accuracy, slow |

### Steps to try it

1. Publish a text file that contains PII (for example: "連絡先は taro@example.com、電話は 090-1234-5678")
2. Ask "連絡先を教えて" in RAG Chat with the `viewer` role → `[MASKED:EMAIL]` and `[MASKED:PHONE]` appear in the output
3. Ask the same question with the `admin` role → the raw email address and phone number appear
4. Check `pii_detected` in the audit log

### Encryption

The body text in the raw side vault is stored encrypted with Fernet (symmetric key encryption). The encryption key is specified with the `CYNOVELA_SECRET_KEY` environment variable (recommended for production).

---

## What you have experienced so far

| Element | Content |
|------|------|
| Workspace management | Name + guardrail policy |
| Smart Ingestion | Automatic classification into 14 categories + 3 kinds of classification engines |
| Hybrid search | Integration of Vector + BM25 with RRF or weighted |
| Audit log | Complete tracking of important operations and PII detections |
| Guardrails | Tier1 masking at ingest time + Tier2 masking at answer time + Fernet encryption |

The next step is "hands-on (advanced)", which goes on to workspace separation, MCP (Model Context Protocol) integration, and so on.

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

このハンズオンでは、ワークスペースの作成から RAG（Retrieval-Augmented Generation：検索拡張生成）クエリ、監査ログ確認、ガードレール体験までを 5 ステップで進めます。

前提として、クイックスタートに沿って Cynovela が起動済みであることを想定します。

---

## ステップ 1: ワークスペースを作成する

### なぜ必要か

ワークスペース（Workspace）は、ユーザー・ガードレールポリシー・コレクション（ファイル群）をまとめる管理単位です。業務領域や情報感度ごとに分けることで、後段のアクセス制御とガードレールを適用しやすくなります。

### 操作

GUI で「ワークスペース管理」画面を開き、「新規作成」ボタンを押します。

入力項目:

| 項目 | 内容 |
|------|------|
| 名前 | ワークスペース名（一意） |
| ガードレールポリシー | 適用するポリシーを 1 件選択 |

デモモードでは以下の 3 種類のガードレールポリシーがあらかじめ用意されています。

| ポリシー ID | 名前 | 内容 |
|-----------|------|------|
| `pol-pii` | PII保護ポリシー | PII を `mask`、Financial を `exclude_from_rag` |
| `pol-strict` | 厳格管理ポリシー | PII を `mask`、Financial と HR を `exclude_from_rag` |
| `pol-log` | ログのみポリシー | PII と Financial を `log_only`（マスクせず記録のみ） |

ガードレールのアクションは 4 種類です（`mask` / `exclude_from_rag` / `log_only` / `allow`）。

---

## ステップ 2: ファイルを取り込んで分類を確認する

### なぜ必要か

Cynovela は取り込んだ各ドキュメントを「Smart Ingestion」というメタデータ付与の仕組みで自動分類します。後段の RAG 検索やレポートで「どの種別の文書が何件あるか」を把握できるようにするためです。

### 分類カテゴリ（14 種）

| カテゴリ ID | 説明 |
|-----------|------|
| governance_policy | ガバナンス・ポリシー文書 |
| incident_report | インシデントレポート |
| technical_guide | 技術ガイド・マニュアル |
| case_study | 導入事例 |
| meeting_minutes | 会議議事録 |
| audit_report | 監査・評価報告書 |
| poc_report | POC 評価報告書 |
| faq | FAQ・よくある質問 |
| whitepaper | ホワイトペーパー |
| checklist | チェックリスト |
| proposal_rfp | 提案書・RFP |
| newsletter | ニュースレター・技術情報 |
| reference | リファレンス・用語集 |
| other | その他 |

### 分類エンジンの選択

Cynovela は 3 種類の分類エンジンを切り替えられます。

| エンジン | 仕組み | 特徴 |
|---------|------|------|
| Lightweight | ファイル名・先頭 500 文字のキーワードマッチ | CPU 極小・ステートレス・高速 |
| LLM | ローカル LLM（Ollama）でゼロショット分類 | 文脈に強い・要 LLM 起動 |
| Hybrid | Lightweight の信頼度が閾値（0.65）未満なら LLM フォールバック | 既定の組み合わせ |

### 操作

1. ワークスペースを選び、「コレクション作成」を実行
2. ファイル（PDF / DOCX / TXT / 画像など）をアップロード
3. 「Publish（公開）」ボタンで取り込みを開始

Publish 後、各ファイルにカテゴリと信頼度（confidence）が付与され、GUI 上で確認できます。

---

## ステップ 3: RAG クエリとスコアの読み方

### なぜ必要か

RAG はベクター検索（意味的類似度）と BM25 検索（キーワード一致）を組み合わせた「ハイブリッド検索」です。スコアを読めるようになると、回答品質の判断と調整がしやすくなります。

### ハイブリッド検索の構成

Cynovela は次の 2 系統を統合します。

| 検索系統 | 仕組み | 既定の重み |
|---------|------|----------|
| ベクター検索 | Embedding（既定: BGE-M3）でコサイン類似度を計算 | 70%（weighted 時） |
| BM25 検索 | 形態素解析ベースのキーワード一致 | 30%（weighted 時） |

統合方式は 2 種類選択できます。

- `weighted`: スコアを重み付き加算（vector × 0.7 + bm25 × 0.3）
- `rrf`（Reciprocal Rank Fusion、既定）: 順位の逆数を加算（k=60 で平滑化）

### スコアの目安（ベクター・コサイン類似度）

参照元の AI 基盤ツールで使われている Embedding モデル BGE-M3 の場合、おおまかな目安は次のとおりです。

| スコア帯 | 解釈 |
|---------|------|
| 0.35 ～ 0.45 | ノイズフロア。無関係なクエリでも出現します |
| 0.50 | 信頼度しきい値（`confidence_threshold`）の既定値 |
| 0.55 ～ 0.75 | 実存クエリの典型的なヒット範囲 |
| 0.75 以上 | きわめて関連性が高い |

### Reranker（再順位付け）

Reranker は「上位 N 件の検索結果を、より精緻なモデルで再評価して並べ替える」機構です。既定は `NoReranker`（適用なし）ですが、設定で `cross_encoder` / `flashrank` などのプロバイダーに切り替えられます。

### Advanced RAG 機能（既定で有効化されているもの）

| 機能 | 役割 |
|------|------|
| MMR（Maximal Marginal Relevance） | 関連性と多様性のバランス調整。`mmr_lambda` で制御 |
| Parent-Child チャンキング | 検索は小さい子チャンクで、回答用には親チャンクのテキストに差し替え |
| Multi-Query | LLM で類似クエリに N-1 件展開し、RRF で統合 |
| CRAG（Corrective RAG） | 検索結果が十分かを LLM が評価し、必要なら再検索 |
| HyDE（既定 OFF） | 仮想回答を先に生成し、その埋め込みで検索 |
| Adaptive RAG | クエリの複雑度に応じて basic / agentic を切り替え |

### 操作

1. RAG Chat 画面でクエリを入力
2. 回答と引用番号 `[1][2]` が返る
3. 詳細表示モードを `developer` に切り替えると、各チャンクのベクタースコア / BM25 スコア / ハイブリッドスコア / Reranker スコアが見えます

---

## ステップ 4: 監査ログを確認する

### なぜ必要か

Cynovela は重要操作をすべて「audit_logs」テーブルに記録します。誰がいつ何をしたか、PII（個人情報）が何件検出されたかを後から検証できる仕組みです。

### 主な記録対象

- ワークスペース・コレクション・ソースの作成と削除
- Publish の実行と完了
- チャット（質問・回答）
- PII 検出（`PII_DETECTED` / `pii_detected`）
- プロンプトインジェクション検出（`PROMPT_INJECTION_BLOCKED`）
- 認証失敗

### 操作

GUI の「監査ログ」画面（admin 専用）から閲覧します。フィルタは以下が利用できます。

- アクション種別
- 対象（ワークスペース ID / コレクション ID）
- 日時範囲

### API 経由

- `GET /api/guardrails/pii-detections` — `audit_logs` から PII 検出を集計（admin 必須）
- `GET /api/pii-detections` — `chunks` テーブルからドキュメント単位で集計（admin 必須）

> **重要**: `audit_logs` は API 経由での削除・変更ができません（改ざん防止）。

---

## ステップ 5: ガードレールを体験する

### なぜ必要か

ガードレールは「検出 → アクション」の二段構えで、PII やセンシティブ情報の流出を防ぎます。Tier1（取込時マスキング）と Tier2（回答時マスキング）の二重防御で動作します。

### Tier1: 取込時マスキング

Publish のタイミングで、各チャンクから「raw（生本文）」と「masked（マスク済み）」の 2 系統を生成し、ChromaDB の 2 つのコレクション（`{cid}__raw` / `{cid}__masked`）と SQLite の `chunks` テーブルに両方保存します。

### Tier2: 回答時マスキング

LLM の出力に対し、ロールに応じて出口マスクを適用します。

| ロール | 検索対象保管庫 | 出口マスク |
|--------|-------------|----------|
| `admin` | raw（生本文） | なし |
| `curator` / `viewer` | masked（マスク済み） | あり |

### 検出対象の PII 種別

正規表現ベース（一次検出）で扱う種別は以下です。

| 種別 | マスクトークン | 例 |
|------|-------------|-----|
| URL | `[MASKED:URL]` | `https://example.com/...` |
| EMAIL | `[MASKED:EMAIL]` | `taro@example.co.jp` |
| PHONE_JP | `[MASKED:PHONE]` | `090-1234-5678` |
| PHONE_LAND | `[MASKED:PHONE]` | `03-1234-5678` |
| CREDIT | `[MASKED:CREDIT]` | カード番号形式 |
| MYNUMBER | `[MASKED:MYNUM]` | マイナンバー形式 |
| PASSPORT | `[MASKED:PASSPORT]` | パスポート番号形式 |
| IPV4 | `[MASKED:IP]` | IPv4 アドレス |

これに加え、二次系（presidio + GiNZA NER）が `ADDRESS_JP` / `PERSON_JP` / `ORG_JP` / `LOC_JP` などの固有表現を検出します。

### 検出モード

`cynovela.yaml` の `pii_mode` キーで 3 段階を切り替えられます（既定は `standard`）。

| モード | 方式 | 特徴 |
|--------|------|------|
| `lite` | 正規表現のみ | 軽量・高速 |
| `standard` | 正規表現 + GiNZA NER | 中庸・推奨 |
| `quality` | 正規表現 + GiNZA NER + 詳細フィルタ | 高精度・低速 |

### 体験手順

1. PII を含むテキストファイル（例: 「連絡先は taro@example.com、電話は 090-1234-5678」）を Publish
2. `viewer` ロールで RAG Chat に「連絡先を教えて」と質問 → 出力に `[MASKED:EMAIL]` と `[MASKED:PHONE]` が現れる
3. `admin` ロールで同じ質問 → 生のメールと電話番号が出る
4. 監査ログで `pii_detected` を確認

### 暗号化

raw 側保管庫の本文は Fernet（対称鍵暗号）で暗号化されて保存されます。暗号化鍵は `CYNOVELA_SECRET_KEY` 環境変数で指定します（本番推奨）。

---

## ここまでで体験できた要素

| 要素 | 内容 |
|------|------|
| ワークスペース管理 | 名前 + ガードレールポリシー |
| Smart Ingestion | 14 カテゴリ自動分類 + 3 種の分類エンジン |
| ハイブリッド検索 | Vector + BM25 を RRF or weighted で統合 |
| 監査ログ | 重要操作と PII 検出の完全な追跡 |
| ガードレール | Tier1 取込時マスキング + Tier2 回答時マスキング + Fernet 暗号化 |

次のステップは「ハンズオン（応用編）」で、ワークスペース分離・MCP（Model Context Protocol）連携などに進みます。

---
