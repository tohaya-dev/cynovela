> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# メタデータエンジン（Smart Ingestion）

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

## 6. 伏字なし取り込み（raw_only）と旧 raw モード

名前が似ていますが、以下の 2 つは **別機構** です。混同しないでください。

### 6.1 廃止済み: `raw_only`（伏字なしで取り込む＝Raw モード）

**この機能は 2026-07-24 に廃止しました。** いまコレクション作成時に `raw_only` を指定すると HTTP 400「raw_only (伏字なし取り込み) は廃止されました」で拒否されます（2026-08-02 実測: `routers/collections.py`）。索引は伏字済みの一組だけを持ちます。

- 列 `collections.raw_only` は過去データ保全のため残っていますが、新規作成では常に既定値 0 です。
- 過去に `raw_only = 1` で作られたコレクションは masked 層（`{cid}__masked`）を持ちません。

```sql
ALTER TABLE collections ADD COLUMN raw_only INTEGER NOT NULL DEFAULT 0;
```

### 6.2 旧仕様（参考）: `raw_mode` / `rag_mode='raw'`

> 以下は **旧概念**（黄色枠・Guardrail 非適用として説明されていた rag モード）です。現行の伏字なし取り込みは上記 6.1 の `raw_only` 列で行います。旧 `raw_mode` は `collections.rag_mode` 列に `'raw'` を保存するだけの別機構で、masked 層の生成有無を制御するものではありません。

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
