# メタデータエンジン（Smart Ingestion）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual to understand
> the concepts of AI infrastructure tools hands-on. It is not a commercial product or an official implementation.
> The implementation is entirely original and consists of an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela's Smart Ingestion is a mechanism that **automatically classifies** ingested documents and organizes them as collections (units of file groups) under a workspace (a management unit). It reproduces the metadata engine concept of the AI infrastructure tool it refers to, on a local OSS stack, for personal learning purposes.

---

## 1. The concept of Smart Ingestion

Smart Ingestion works in the following 3 steps.

1. **Ingestion**: Files are discovered recursively from a Source (the ingest origin), and text is extracted.
2. **Classification**: The file name and the beginning of the body text are examined, and the file is assigned to one of the predefined categories.
3. **Collection**: Files are grouped into a collection, and at the Publish stage, chunk splitting, embedding, PII detection, and insertion into Chroma are performed.

---

## 2. The 14 category definitions (all of them)

The **CATEGORIES** that the classifier assigns are the following 14 kinds (`utils/metadata/classification.py`).

| ID | Display name |
|---|---|
| `governance_policy` | Governance / policy document |
| `incident_report` | Incident report |
| `technical_guide` | Technical guide / manual |
| `case_study` | Case study |
| `meeting_minutes` | Meeting minutes |
| `audit_report` | Audit / assessment report |
| `poc_report` | POC assessment report |
| `faq` | FAQ / frequently asked questions |
| `whitepaper` | Whitepaper |
| `checklist` | Checklist |
| `proposal_rfp` | Proposal / RFP |
| `newsletter` | Newsletter / technical information |
| `reference` | Reference / glossary |
| `other` | Other |

### Supplement: document types (5 kinds)

As `DOCUMENT_TYPE_RULES`, the following 5 kinds are defined for auxiliary classification.

| ID | Display name |
|---|---|
| `contract` | Contract |
| `technical_spec` | Technical specification |
| `email` | Email |
| `report` | Report |
| `manual` | Manual |

These are labels given in parallel with the 14 categories, and they supplement the **format aspect** of a document.

---

## 3. The 3-stage classification engine

`utils/metadata/classification.py` implements 3 kinds of classifier. They are switched with the factory function `get_classifier(engine)`.

### 3.1 LightweightClassifier (lightweight, rule based)

```python
class LightweightClassifier(ClassificationEngine):
    """ファイル名と本文先頭 500 文字のキーワードマッチで分類"""
```

- Extremely small CPU load, stateless
- Confidence: **0.85** for a file name match, **0.65** for a body text match
- `FILENAME_RULES`: the 10 patterns incident / minutes / audit / poc / faq / whitepaper / checklist / rfp / newsletter / glossary
- `CONTENT_RULES`: the 3 patterns policy / guideline / case_study

### 3.2 LLMClassifier (uses a local LLM)

```python
class LLMClassifier(ClassificationEngine):
    """ローカル LLM（Ollama）を使ったゼロショット分類"""
```

- Example endpoint when using Ollama: `http://localhost:11434`, model: `llama3` (the bundled default is not Ollama but LM Studio)
- JSON output is enforced (it must return `category`, `confidence`, `reason`)
- Timeout: 30 seconds
- If Ollama is not running, it returns `confidence=0.0` to prompt a fallback
- It supports all 14 categories

### 3.3 HybridClassifier (recommended)

```python
class HybridClassifier(ClassificationEngine):
    """Lightweight を優先、信頼度が低い時のみ LLM フォールバック"""
```

- `LLM_FALLBACK_THRESHOLD = 0.65`
- Lightweight confidence of 0.65 or higher → adopted as is
- Less than 0.65 → the LLM classifier is asked
- If the LLM confidence is also less than 0.65, the Lightweight result is adopted

### 3.4 Supplement: the classifier on the providers/ side (PII only)

`providers/classifier.py` separately contains a Provider abstraction for PII classification.

| Class | Overview |
|---|---|
| `RuleBasedClassifier` | Rule based, targeting EMAIL / PHONE / MYNUMBER |
| `APIClassifier` | POSTs to an external HTTP API to classify (authorized with `Bearer {api_key}`) |

---

## 4. The relationship between Workspace and Collection

### 4.1 Workspace

A workspace is "a management unit that bundles users, a guardrail policy, and multiple collections".

```sql
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    guardrail_policy_id TEXT REFERENCES guardrail_policies(id),
    created_at TEXT DEFAULT (datetime('now'))
);
```

Intermediate tables:

| Table | Purpose |
|---|---|
| `workspace_sources` | Association between a workspace and a Source |
| `workspace_policies` | Association between a workspace and a guardrail policy |
| `workspace_users` | Association between a workspace and a user |

### 4.2 Collection

A collection is "a unit of a file group together with its chunk strategy and access control".

```sql
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft','ingested','publishing','ready','failed')),
    access_level TEXT DEFAULT 'public' CHECK(access_level IN ('public','internal','confidential')),
    chunk_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

Additional columns (added with ALTER TABLE):

| Column | Purpose |
|---|---|
| `allowed_roles_json` | List of allowed roles |
| `rag_strategy` | Default `hybrid_bm25`; also `simple` / `contextual` |
| `chunk_size` / `chunk_overlap` | Chunk splitting parameters |
| `rag_mode` | Mode switch such as `'raw'` |
| `acl_roles` | Role set for ACL |
| `last_published_at` | Time of the last Publish |

### 4.3 State transitions

```
draft → ingested → ready
draft → publishing → ready / failed
publishing → stopped
failed → draft
ready → draft
```

---

## 5. Hash based differential sync (DataSyncService)

`services/data_sync.py` implements an **automatic polling sync service**.

### 5.1 Behavior specification

- Default polling interval: **60 seconds**
- Minimum value: **10 seconds** (`max(10, int(poll_interval_sec))`)
- Monitored targets: rows of the `sources` table with `status != 'failed'`
- Compared against: the `files` table records under each Source

### 5.2 Difference detection logic

```python
discovered_paths = {d.source_path for d in discovered}
existing_paths   = {r["path"] for r in db_files}
new_paths     = discovered_paths - existing_paths
deleted_paths = existing_paths - discovered_paths
```

A rescan is done with `FileSystemDataSource.discover()`, and the set of file paths is divided into the 2 sets of new / deleted.

### 5.3 Lifecycle

| Method | Role |
|---|---|
| `start()` | Creates an `asyncio.Task` and starts polling |
| `stop()` | Stops with `Task.cancel()` |
| `run()` | Repeatedly runs `_sync_all_sources()` at the polling interval (exceptions are recorded with `logger.exception`) |

### 5.4 Known limitations

- **Difference detection works per path.** Strict difference detection by `content_hash` is not implemented yet.
<!-- BACKLOG: content_hash 比較ベースの差分同期は仕様未確定 -->
- There is no integrated path that **automatically links the detected changes to Publish**. Only logging after detection is implemented.

---

## 6. Ingestion without masking (raw_only) and the old raw mode

The names are similar, but the following 2 are **separate mechanisms**. Do not confuse them.

### 6.1 Abolished: `raw_only` (ingesting without masking = Raw mode)

**This feature was abolished on 2026-07-24.** If you now specify `raw_only` when creating a collection, it is rejected with HTTP 400 "raw_only (マスキングなし取り込み) は廃止されました" (measured 2026-08-02: `routers/collections.py`). The index holds only the single masked set.

- The column `collections.raw_only` remains for the preservation of past data, but for new creations it is always the default value 0.
- Collections created in the past with `raw_only = 1` do not have a masked layer (`{cid}__masked`).

```sql
ALTER TABLE collections ADD COLUMN raw_only INTEGER NOT NULL DEFAULT 0;
```

### 6.2 Old specification (for reference): `raw_mode` / `rag_mode='raw'`

> The following is an **old concept** (the rag mode that was explained as a yellow frame with no Guardrail applied). The current ingestion without masking is done with the `raw_only` column in 6.1 above. The old `raw_mode` is a separate mechanism that only stores `'raw'` in the `collections.rag_mode` column, and it does not control whether a masked layer is generated.

```sql
ALTER TABLE collections ADD COLUMN rag_mode TEXT;   -- 旧: raw_mode の保存先
```

---

## 7. Chunk splitting strategy

### 7.1 Basic (split_chunks)

```python
def split_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]
```

- Default: a sliding window of **500 characters / 50 characters of overlap**
- `chunk_size` / `chunk_overlap` can be overridden per collection

### 7.2 Contextual Chunking (Phase 2)

`chunker.py` implements **rule based Contextual Retrieval without an LLM**. A context sentence like the following is prepended to the beginning of a chunk.

```
[コンテキスト] 文書: filename.pdf | 種別: technical_guide | 感度: confidential | 部門: Engineering | 位置: 3/10番目のセクション | タグ: API, design, patterns
```

Priority order for enabling it:

1. DB `settings` table: `chunking.contextual` = `1` / `true` (highest priority)
2. YAML setting: `chunking.contextual`
3. Function argument `default` (default `False`)

### 7.3 RAG strategies

```python
RAG_STRATEGIES = {"simple", "hybrid_bm25", "contextual"}
```

| Strategy | Overview |
|---|---|
| `simple` | Simple vector search |
| `hybrid_bm25` | Hybrid of vector + BM25 (default) |
| `contextual` | Used together with Contextual Chunking |

---

## 8. Compatibility with the old classification

The old `classifier.py` defines the 8 categories PII / Financial / HR / Legal / Healthcare / Sales / Technical / Marketing, but this is **deprecated**. The new implementation is unified on the 14 categories in `utils/metadata/classification.py`.

---

Last updated: 2026-05-26 / Alpha GA edition

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela の Smart Ingestion（賢い取り込み）は、取り込んだドキュメントを **自動分類** し、ワークスペース（管理単位）配下のコレクション（ファイル群の単位）として整理する仕組みです。参照元の AI 基盤ツールにおけるメタデータエンジン構想を、個人学習用にローカル OSS スタックで再現しています。

---

## 1. Smart Ingestion の概念

Smart Ingestion は次の 3 ステップで動作します。

1. **取り込み（Ingestion）**: Source（取り込み元）から再帰的にファイルを発見し、テキストを抽出します。
2. **分類（Classification）**: ファイル名と本文先頭の特徴を見て、定義済みカテゴリのいずれかに割り当てます。
3. **コレクション編成（Collection）**: ファイル群をコレクションにまとめ、Publish（公開）の段階でチャンク分割・Embedding・PII 検出・Chroma 投入を行います。

---

## 2. 14 カテゴリ定義（全件）

分類器が割り当てる **CATEGORIES** は次の 14 種類です（`utils/metadata/classification.py`）。

| ID | 表示名 |
|---|---|
| `governance_policy` | ガバナンス・ポリシー文書 |
| `incident_report` | インシデントレポート |
| `technical_guide` | 技術ガイド・マニュアル |
| `case_study` | 導入事例 |
| `meeting_minutes` | 会議議事録 |
| `audit_report` | 監査・評価報告書 |
| `poc_report` | POC評価報告書 |
| `faq` | FAQ・よくある質問 |
| `whitepaper` | ホワイトペーパー |
| `checklist` | チェックリスト |
| `proposal_rfp` | 提案書・RFP |
| `newsletter` | ニュースレター・技術情報 |
| `reference` | リファレンス・用語集 |
| `other` | その他 |

### 補足: ドキュメントタイプ（5 種）

`DOCUMENT_TYPE_RULES` として、補助分類用に次の 5 種類が定義されています。

| ID | 表示名 |
|---|---|
| `contract` | 契約書 |
| `technical_spec` | 技術仕様書 |
| `email` | メール |
| `report` | レポート |
| `manual` | マニュアル |

これは 14 カテゴリと並列に付与されるラベルで、文書の **形式面** を補足します。

---

## 3. 分類エンジン 3 段構え

`utils/metadata/classification.py` には 3 種類の Classifier（分類器）が実装されています。ファクトリ関数 `get_classifier(engine)` で切り替えます。

### 3.1 LightweightClassifier（軽量・ルールベース）

```python
class LightweightClassifier(ClassificationEngine):
    """ファイル名と本文先頭 500 文字のキーワードマッチで分類"""
```

- CPU 負荷が極小・ステートレス
- 信頼度（confidence）: ファイル名マッチで **0.85**、本文マッチで **0.65**
- `FILENAME_RULES`: incident / minutes / audit / poc / faq / whitepaper / checklist / rfp / newsletter / glossary の 10 パターン
- `CONTENT_RULES`: policy / guideline / case_study の 3 パターン

### 3.2 LLMClassifier（ローカル LLM 利用）

```python
class LLMClassifier(ClassificationEngine):
    """ローカル LLM（Ollama）を使ったゼロショット分類"""
```

- Ollama を使う場合の接続先の例: `http://localhost:11434`、モデル: `llama3`（同梱の既定は Ollama ではなく LM Studio です）
- JSON 出力を強制（`category`, `confidence`, `reason` を返させる）
- タイムアウト: 30 秒
- Ollama が起動していない場合は `confidence=0.0` を返してフォールバックを促す
- 14 カテゴリ全てに対応

### 3.3 HybridClassifier（推奨）

```python
class HybridClassifier(ClassificationEngine):
    """Lightweight を優先、信頼度が低い時のみ LLM フォールバック"""
```

- `LLM_FALLBACK_THRESHOLD = 0.65`
- Lightweight の confidence が 0.65 以上 → そのまま採用
- 0.65 未満 → LLM 分類器に問い合わせ
- LLM の信頼度も 0.65 未満なら Lightweight の結果を採用

### 3.4 補助: providers/ 側の Classifier（PII 専用）

`providers/classifier.py` には PII 分類用の Provider 抽象が別に存在します。

| クラス | 概要 |
|---|---|
| `RuleBasedClassifier` | EMAIL / PHONE / MYNUMBER を対象としたルールベース |
| `APIClassifier` | 外部 HTTP API に POST して分類（`Bearer {api_key}` で認可） |

---

## 4. Workspace と Collection の関係

### 4.1 Workspace

ワークスペースは「ユーザー・ガードレールポリシー・複数 Collection を束ねる管理単位」です。

```sql
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    guardrail_policy_id TEXT REFERENCES guardrail_policies(id),
    created_at TEXT DEFAULT (datetime('now'))
);
```

中間テーブル:

| テーブル | 用途 |
|---|---|
| `workspace_sources` | ワークスペースと Source の紐付け |
| `workspace_policies` | ワークスペースとガードレールポリシーの紐付け |
| `workspace_users` | ワークスペースとユーザーの紐付け |

### 4.2 Collection

コレクションは「ファイル群と、それに対するチャンク戦略・アクセス制御の単位」です。

```sql
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft','ingested','publishing','ready','failed')),
    access_level TEXT DEFAULT 'public' CHECK(access_level IN ('public','internal','confidential')),
    chunk_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

追加カラム（ALTER TABLE で追加）:

| カラム | 用途 |
|---|---|
| `allowed_roles_json` | ロール許可リスト |
| `rag_strategy` | 既定 `hybrid_bm25`、他に `simple` / `contextual` |
| `chunk_size` / `chunk_overlap` | チャンク分割パラメータ |
| `rag_mode` | `'raw'` などのモード切替 |
| `acl_roles` | ACL 用ロール集合 |
| `last_published_at` | 最終 Publish 日時 |

### 4.3 状態遷移

```
draft → ingested → ready
draft → publishing → ready / failed
publishing → stopped
failed → draft
ready → draft
```

---

## 5. ハッシュ差分同期（DataSyncService）

`services/data_sync.py` に **自動ポーリング型の同期サービス** が実装されています。

### 5.1 動作仕様

- 既定ポーリング間隔: **60 秒**
- 最小値: **10 秒**（`max(10, int(poll_interval_sec))`）
- 監視対象: `sources` テーブルのうち `status != 'failed'` のもの
- 比較対象: 各 Source 配下の `files` テーブルレコード

### 5.2 差分検出ロジック

```python
discovered_paths = {d.source_path for d in discovered}
existing_paths   = {r["path"] for r in db_files}
new_paths     = discovered_paths - existing_paths
deleted_paths = existing_paths - discovered_paths
```

`FileSystemDataSource.discover()` で再スキャンを行い、ファイルパスの集合を新規 / 削除の 2 集合に分けます。

### 5.3 ライフサイクル

| メソッド | 役割 |
|---|---|
| `start()` | `asyncio.Task` を生成し、ポーリング開始 |
| `stop()` | `Task.cancel()` で停止 |
| `run()` | `_sync_all_sources()` をポーリング間隔で繰り返し実行（例外は `logger.exception` で記録） |

### 5.4 既知制限

- **差分検出はパス単位** で動作します。`content_hash` による厳密な差分検出はまだ実装されていません。
<!-- BACKLOG: content_hash 比較ベースの差分同期は仕様未確定 -->
- 検出した変更を **Publish に自動連携** する経路は未統合です。検出後のログ出力までは実装済み。

---

## 6. マスキングなし取り込み（raw_only）と旧 raw モード

名前が似ていますが、以下の 2 つは **別機構** です。混同しないでください。

### 6.1 廃止済み: `raw_only`（マスキングなしで取り込む＝Raw モード）

**この機能は 2026-07-24 に廃止しました。** いまコレクション作成時に `raw_only` を指定すると HTTP 400「raw_only (マスキングなし取り込み) は廃止されました」で拒否されます（2026-08-02 実測: `routers/collections.py`）。インデックスはマスキング済みの一組だけを持ちます。

- 列 `collections.raw_only` は過去データ保全のため残っていますが、新規作成では常に既定値 0 です。
- 過去に `raw_only = 1` で作られたコレクションは masked 層（`{cid}__masked`）を持ちません。

```sql
ALTER TABLE collections ADD COLUMN raw_only INTEGER NOT NULL DEFAULT 0;
```

### 6.2 旧仕様（参考）: `raw_mode` / `rag_mode='raw'`

> 以下は **旧概念**（黄色枠・Guardrail 非適用として説明されていた rag モード）です。現行のマスキングなし取り込みは上記 6.1 の `raw_only` 列で行います。旧 `raw_mode` は `collections.rag_mode` 列に `'raw'` を保存するだけの別機構で、masked 層の生成有無を制御するものではありません。

```sql
ALTER TABLE collections ADD COLUMN rag_mode TEXT;   -- 旧: raw_mode の保存先
```

---

## 7. チャンク分割戦略

### 7.1 基本（split_chunks）

```python
def split_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]
```

- 既定: **500 文字 / 50 文字オーバーラップ** のスライディングウィンドウ
- コレクションごとに `chunk_size` / `chunk_overlap` を上書き可能

### 7.2 Contextual Chunking（Phase 2）

`chunker.py` で **LLM 不使用のルールベース Contextual Retrieval** を実装しています。チャンク冒頭に下記のようなコンテキスト文を付加します。

```
[コンテキスト] 文書: filename.pdf | 種別: technical_guide | 感度: confidential | 部門: Engineering | 位置: 3/10番目のセクション | タグ: API, design, patterns
```

有効化の優先順位:

1. DB `settings` テーブル: `chunking.contextual` = `1` / `true`（最優先）
2. YAML 設定: `chunking.contextual`
3. 関数引数 `default`（既定 `False`）

### 7.3 RAG 戦略

```python
RAG_STRATEGIES = {"simple", "hybrid_bm25", "contextual"}
```

| 戦略 | 概要 |
|---|---|
| `simple` | 単純なベクター検索 |
| `hybrid_bm25` | ベクター + BM25 のハイブリッド（既定） |
| `contextual` | Contextual Chunking と合わせて使用 |

---

## 8. 旧分類との互換性

旧 `classifier.py` には PII / Financial / HR / Legal / Healthcare / Sales / Technical / Marketing の 8 カテゴリが定義されていますが、これは **非推奨** です。新実装は `utils/metadata/classification.py` の 14 カテゴリに統一されています。

---

最終更新: 2026-05-26 / Alpha GA 対応版
