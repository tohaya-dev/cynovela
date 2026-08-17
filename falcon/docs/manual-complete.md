> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# Cynovela 完全マニュアル

本マニュアルは、Cynovela のすべての機能を一冊にまとめた統合ドキュメントです。個別ドキュメントを横断したい場合に参照してください。

---

## 目次

1. 概要
2. AI ガバナンスのコンセプト
3. インストール・起動
4. 基本操作
5. 設計詳細
6. 外部連携
7. 既知制限
8. FAQ

---

# 1. 概要

## 1-1. Cynovela とは

Cynovela は、AI 基盤ツールのコンセプトを個人が手を動かして理解するために作った、完全非公式の学習用ツールです。

参照元の AI 基盤ツールが提供する以下のような機能について、「実際に作るとどうなるか」を体験するために設計されています。

- データガバナンス（ガードレール、PII 検出、監査ログ）
- データ取り込み（自動分類、メタデータ抽出、差分同期）
- RAG（検索拡張生成）パイプライン
- ロールベースアクセス制御（RBAC）
- MCP（Model Context Protocol）連携

## 1-2. 設計コンセプト

Cynovela は「読むだけで終わらせず、自分で動かして学ぶ」ことを最優先に設計されています。

- **コア機能を欠かさない**: ガードレール / PII / RAG / RBAC / 監査ログ といった本質的機能は省略せず、簡素化したかたちで実装する。
- **OSS のみで構成**: FastAPI、SQLite、ChromaDB、BAAI/bge-m3、cryptography（Fernet）など、すべて入手しやすい OSS を使用。
- **ローカル完結**: 既定では LM Studio / Ollama などローカル LLM ランナーへの接続が前提。クラウド依存なし。
- **冪等で破壊的でない**: スキーマ変更は `CREATE TABLE IF NOT EXISTS` と `try/except` で囲んだ `ALTER TABLE`、データ更新は `INSERT ... ON CONFLICT DO UPDATE` を徹底。

## 1-3. プロジェクトの位置付け

Cynovela は商用製品ではありません。参照元のいかなる会社・製品の公式見解も代表しません。実装はすべてオリジナルで、参照元のソースコード・商標・公式ドキュメントは一切含みません。

---

# 2. AI ガバナンスのコンセプト

AI 基盤ツールに共通するガバナンス機能を、Cynovela がどのように再現しているかを 8 つの観点で整理します。

## 2-1. データの分類とラベリング

文書ごとに「何の種類か」を機械的に判断し、ラベルを付与する仕組みです。Cynovela は 14 種類のカテゴリを定義しています。

- ガバナンス・ポリシー文書
- インシデントレポート
- 技術ガイド・マニュアル
- 導入事例
- 会議議事録
- 監査・評価報告書
- POC 評価報告書
- FAQ・よくある質問
- ホワイトペーパー
- チェックリスト
- 提案書・RFP
- ニュースレター・技術情報
- リファレンス・用語集
- その他

加えて 5 種のドキュメント形式分類（契約書、技術仕様書、メール、レポート、マニュアル）も補助的に行います。

## 2-2. 機密性の検出

機密情報（PII、個人情報）を検出してマスクする仕組みです。Cynovela は 2 系統の検出器を備えています。

**一次（正規表現ベース、`guardrail.py`）**:
- URL、EMAIL、PHONE_JP（携帯）、PHONE_LAND（固定電話）、CREDIT（クレジットカード）、MYNUMBER（マイナンバー）、PASSPORT、IPV4

**二次（Presidio + GiNZA NER フォールバック、`utils/metadata/pii.py`）**:
- PERSON_JP、ORG_JP、LOC_JP、ADDRESS_JP、EMAIL_ADDRESS、PHONE_NUMBER、DATE_TIME、INTERNAL_URL

## 2-3. アクセス制御（RBAC）

ユーザーのロールに応じて、見られる情報と実行できる操作を制限する仕組みです。

| ロール | 説明 |
|---|---|
| `admin` | フル管理権限 |
| `viewer` | 閲覧のみ |

> `curator` / `data-scientist` 等の名称は後方互換の値として受理されますが、現行実装では `viewer` に正規化され、固有権限はありません（実効ロールは `admin` / `viewer` の 2 値）。

RBAC は 33 のルーター（242 箇所）でチェックされ、4 種のヘルパー関数（`_require_admin`、`_require_authenticated`、`_require_role`、`_require_admin_or_self`）に集約されています。

## 2-4. 監査ログ

重要操作（Source / Workspace 作成・削除、Publish、Chat、PII 検出、認証失敗 など）を改ざんできない形で記録します。Cynovela は `audit_logs` テーブルへの API 経由の変更・削除を禁止しています。

## 2-5. ガードレール

検出した情報や入力クエリに対して、どう対処するかを定義する仕組みです。Cynovela のアクションは 4 種類です。

| アクション | 動作 |
|---|---|
| `mask` | 該当箇所をマスクトークン（`[MASKED:EMAIL]` 等）に置換 |
| `exclude_from_rag` | RAG 検索対象から除外 |
| `log_only` | 検出のみ記録、アクションは取らない |
| `allow` | 許可（明示的にホワイトリスト化） |

ポリシーは複数の分類クラス（PII、Financial、HR）と組み合わせて Workspace に紐付きます。シードデータでは `pol-pii`、`pol-strict`、`pol-log` の 3 種が用意されています。

## 2-6. 暗号化

機密度の高い raw 本文（マスク前データ）は Fernet（対称鍵暗号）で暗号化されて保存されます。

- **鍵管理**: `CYNOVELA_SECRET_KEY` 環境変数（無指定時は自動生成、本番運用では明示推奨）
- **対象**: SQLite の `chunks` / `parent_chunks` テーブルおよび ChromaDB の `*__raw` コレクション
- **形式**: `enc:` プレフィックス + base64 文字列（冪等、二重暗号化なし）

## 2-7. プロンプトインジェクション対策

LLM への悪意ある指示注入を防ぐため、3 層防御を実装しています。

1. **入力検査**: クエリに 14 種の英日インジェクションパターン（`ignore previous instructions`、`これまでの指示を無視` 等）が含まれていれば HTTP 400 で即遮断。
2. **Retrieval 後検査**: 検索結果のチャンクからインジェクション文言を含むものを除外。
3. **出力検査**: LLM 応答に `HACKED` / `PWNED` / `SECRET-ALPHA-TOKEN` / `[SYSTEM OVERRIDE]` が含まれていないか確認。

検出時は `audit_logs` に `PROMPT_INJECTION_BLOCKED` を記録します。

## 2-8. データ最小化（Dual-Tier 保管）

同じ文書について、raw（生本文）と masked（マスク済み本文）を別々のレコード・別々のベクターコレクションに保存することで、ロールに応じて参照先を切り替えます。

- **admin ロール**: raw コレクション（`{cid}__raw`、Fernet 暗号化）を参照
- **その他のロール**: masked コレクション（`{cid}__masked`）を参照

加えて、LLM 出力にも `_mask_for_viewer` を適用して二重防御を実現しています。

---

# 3. インストール・起動

## 3-1. 推奨環境

- macOS（Apple Silicon 推奨）、Linux、Windows
- Python 3.10 以上
- conda 環境（推奨環境名: `cynovela`）

## 3-2. 起動コマンド

### デモモード（最も簡単）

```bash
python server.py --demo
```

ブラウザで `http://127.0.0.1:8765` を開きます。

### 実 LLM モード

LM Studio または Ollama を別途起動した状態で次を実行します。

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

## 3-3. 起動モード（`--mode`）

| mode | 説明 | 必要モデル | 推奨環境 |
|---|---|---|---|
| `text` | テキスト RAG 全機能（既定） | BAAI/bge-m3 | GPU 不要 |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — |

## 3-4. CLI 引数一覧

| フラグ | 説明 |
|---|---|
| `--demo` | デモのデータベース `store/db/demo.db` で起動（付けなければ本番＝`store/db/cynovela.db`。どちらも再起動では消えません） |
| `--lmstudio-url` | LM Studio ベース URL（既定: `http://localhost:1234`） |
| `--mode` | 起動モード（text / lite / lite-en） |
| `--host` | バインドアドレス（既定: `0.0.0.0`。絞るのは `--local-only`） |
| `--port` | ポート番号（既定: `8765`） |
| `--lan` | LAN 公開（`host=0.0.0.0`） |
| `--allow-tailscale` | Tailscale サブネット（`100.64.0.0/10`）を許可 |
| `--allow-subnet` | カスタムサブネットを追加（複数指定可） |
| `--local-only` | 自マシン内だけに絞る（`host=127.0.0.1`） |
| `--reset-admin` | 管理者パスワードをリセットして表示し終了（デモを直すときは `--demo` を併記） |

## 3-5. PII 検出モード

`cynovela.yaml` の `pii_mode` キーで指定します。

| 値 | 検出方式 |
|---|---|
| `lite` | 正規表現のみ |
| `standard`（既定） | 正規表現 + GiNZA NER |
| `quality` | 正規表現 + GiNZA NER + 詳細フィルタリング |

実行時に変更する場合は `/api/settings/pii-mode` を PUT します。

## 3-6. Preflight チェック

起動時に必要モデルの存在確認を行い、未取得モデルがある場合は次の選択肢が提示されます。

1. 今すぐダウンロードして起動する（HuggingFace から `~/.cynovela/models/` 配下に保存）
2. 代替モードで起動する（full → text → lite → lite-en → mock）
3. キャンセル

スクリプト実行時は `CYNOVELA_NONINTERACTIVE=1` でこのプロンプトをスキップ（モデル不在時は exit）できます。

---

# 4. 基本操作

## 4-1. コアフロー

Cynovela の主要操作は以下のフローに沿って進みます。

```
Source 登録 → Scan → Workspace 作成 → Collection 作成 → Publish → RAG Chat
```

### Step 1: Source 登録

データの取得元（ローカルフォルダ）を登録します。`/api/sources` にパスを POST するか、UI から「Source 追加」ボタンで登録します。

### Step 2: Scan

登録した Source 配下のファイルを走査し、`files` テーブルにレコードを作成します。各ファイルにはパス由来の決定論的 ID（`_stable_fid(path)`）が振られます。

### Step 3: Workspace 作成

Workspace は「複数の Collection をまとめる単位」かつ「ガードレールポリシーとユーザーを紐付ける単位」です。

### Step 4: Collection 作成

Collection は「ファイル群 + 分類・チャンク戦略」の単位です。状態は `draft → ingested → publishing → ready` と遷移します。

主な設定:
- `rag_strategy`: `simple` / `hybrid_bm25`（既定）/ `contextual`
- `chunk_size`、`chunk_overlap`
- `access_level`: `public` / `internal` / `confidential`
- `allowed_roles_json`: ACL（アクセス制御リスト）

### Step 5: Publish

Collection 内のファイルをチャンク化・ベクター化して ChromaDB に投入します。Publish 時には次が同時に行われます。

- raw / masked 両 tier のチャンク生成
- PII 検出と Fernet 暗号化（raw 側のみ）
- BM25 インデックス構築
- `publish_history` への記録（doc_count、chunk_count、pii_count、excluded_count、elapsed_seconds など）

### Step 6: RAG Chat

ユーザーが質問を入力すると、検索 → Reranker → LLM 生成 → ガードレール適用 → 回答返却、というパイプラインが実行されます。

## 4-2. RAG プリセット

UI から選べる 5 種類のプリセットがあります。

| ID | 名前 | 用途 |
|---|---|---|
| `tech_doc` | 技術文書 | マニュアル向け |
| `confidential` | 機密文書 | PII を含む社内文書 |
| `personal_memo` | 個人メモ | 議事録・メモ |
| `multimedia` | マルチメディア | 画像・Office 混在 |
| `quickstart` | クイックスタート | 初心者向け全自動 |

各プリセットは `chunking`、`rag_mode`、`guardrail` の組み合わせを定義しています。

## 4-3. 回答モード

RAG モードは 3 種類です。

| RAG Mode | 内容 |
|---|---|
| `lite` | 最小限の RAG（1 回検索、オプション省略） |
| `standard` | 標準（BM25 ハイブリッド、Reranker オプション） |
| `hq` | 高品質（CRAG / Multi-Query / HyDE 有効） |

加えて、ロール別に回答スタイルを切り替える機能があります。

- `admin`: 技術詳細・設定値・内部構造を含む完全な情報
- `reader`: 専門用語を避けた要点重視の説明

## 4-4. ユーザー管理

SQL CHECK 制約は後方互換のため `admin` / `curator` / `viewer` の 3 値を許容しますが、現行実装では `curator` は `viewer` に正規化され、実効ロールは `admin` / `viewer` の 2 値です。初回起動時は `CYNOVELA_ADMIN_USERNAME` と `CYNOVELA_ADMIN_INITIAL_PASSWORD` 環境変数で admin ユーザーを作成できます。

---

# 5. 設計詳細

## 5-1. RAG パイプライン

メイン関数 `rag_retrieve()` は次のフローを実行します。

```
1. Vector Search (ChromaDB)
   ├ MMR（多様性確保）
   └ ACL フィルタリング
2. BM25 Search（メモリ内インデックス）
   ├ トークン化（日本語: fugashi、英語: 空白区切り）
   └ ACL フィルタリング
3. Hybrid Integration
   └ RRF（k=60、既定）または重み付け（vector 0.7 + bm25 0.3）
4. Parent-Child 解決
   └ child hit を parent テキストに置換
5. Reranker 適用
   └ CrossEncoder / BGE-Reranker など
6. Final Ranking
   └ Top n_results 件を返却
```

主要パラメータ（`cynovela.yaml` の `rag` セクション）:

- `strategy`: `hybrid_bm25`（既定）
- `default_n_results`: 5
- `confidence_threshold`: 0.40（パラメータ定義値、cosine スケール）
- `vector_weight`: 0.7、`bm25_weight`: 0.3
- `hybrid_method`: `rrf`（既定）/ `weighted`
- `rrf_k`: 60
- `mmr_enabled`: true、`mmr_lambda`: 0.7、`mmr_fetch_k`: 20
- `parent_child_enabled`: true、`child_chunk_size`: 256、`parent_chunk_size`: 1000
- `multi_query_enabled`: true、`multi_query_count`: 3
- `crag_enabled`: true、`crag_max_loops`: 1
- `hyde_enabled`: false
- `adaptive_enabled`: true、`adaptive_threshold`: 2.0

## 5-2. Advanced RAG（PHASE A シリーズ）

| 名称 | 機能 |
|---|---|
| MMR | 関連性 vs 多様性のバランス調整 |
| Parent-Child | 検索ヒットの周辺コンテキストを拡張 |
| Hybrid Search | BM25 + Vector を RRF または重み付けで統合 |
| Multi-Query | LLM でクエリを N 個に展開して並列検索 |
| CRAG（Corrective RAG） | LLM が検索結果の質を評価し、不十分なら再検索 |
| HyDE | 仮想文章生成 → その埋め込みで検索 |
| Adaptive RAG | 質問の複雑度を判定して Agentic ループを起動 |

## 5-3. Smart Ingestion・Collection

### 分類エンジン

| エンジン | 動作 |
|---|---|
| `LightweightClassifier` | ルールベース（ファイル名 + 先頭 500 文字のキーワード） |
| `LLMClassifier` | Ollama 等のローカル LLM でゼロショット分類 |
| `HybridClassifier` | 軽量を優先、信頼度 0.65 未満で LLM フォールバック |

### Collection の状態遷移

```
draft → ingested → ready
draft → publishing → ready / failed
publishing → stopped
failed → draft
```

### ハッシュ差分同期

`DataSyncService` が `sources` テーブルを定期的に走査します。

- 既定間隔: 60 秒（最小 10 秒）
- 比較対象: `files` テーブルの (source_id, path) レコード
- 差分検出: パス集合の追加 / 削除

publish 連携は未統合で、現状はログ出力のみ。

### チャンク分割

- 既定: スライディングウィンドウ 500 文字 × 50 文字 overlap
- Contextual Chunking 有効時: メタデータ（ファイル名、種別、感度、部門、位置、タグ）をチャンク冒頭に付加

## 5-4. ガードレール・PII（再掲）

### Tier1（取込時マスキング）

Publish 時に各チャンクから raw / masked の dual-row を生成。ChromaDB には `{cid}__raw` と `{cid}__masked` の 2 コレクションを作成。SQLite `chunks` にも `tier='raw'` / `tier='masked'` の 2 行を保存。

### Tier2（回答時マスキング）

`_mask_for_viewer` が chat 経路 4 箇所（通常 / compare A / compare B / SSE）で LLM 出力に適用される。admin 以外は強制マスク。

### Fernet 暗号化

`vault_enc.py` の `enc_raw` / `dec_raw` インターフェース（`enc:` プレフィックス、冪等）。raw tier のみ暗号化、masked tier は素通し。

---

# 6. 外部連携

## 6-1. LLM 接続

Cynovela は OpenAI 互換 `/v1/chat/completions` を持つ任意のサービスに接続できます。

### LM Studio

```bash
python server.py --lmstudio-url http://localhost:1234
```

### Ollama

```bash
python server.py --lmstudio-url http://localhost:11434
```

### OpenAI 互換（汎用）

`cynovela.yaml` で設定:

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:8000
  model: meta-llama/Llama-3-8B-Instruct
```

### モック

```bash
python server.py --demo
```

## 6-2. MCP 連携

Cynovela は MCP サーバーとして 11 ツールを公開しています。

| カテゴリ | ツール |
|---|---|
| RAG 検索系（4） | `search_collection`、`search_across_collections`、`rag_with_role`、`rag_general` |
| 情報取得系（4） | `list_workspaces`、`get_workspace_info`、`get_collection_info`、`get_audit_logs` |
| 管理系（3） | `list_sources`、`publish_collection`、`create_workspace` |

LM Studio などの MCP クライアントから接続できます。conda 環境固有の制限として、`CYNOVELA_MCP_PYTHON` 環境変数で Python 実行ファイルパスを指定する必要があります。

詳細は `mcp-guide.md` を参照してください。

## 6-3. LAN・Tailscale 共有

### LAN 共有

```bash
python server.py --lan --allow-subnet 192.168.1.0/24
```

### Tailscale 共有

```bash
python server.py --lan --allow-tailscale
```

`tailscale ip -4` で Tailscale IP を自動検出し、`100.64.0.0/10` サブネットを許可リストに追加します。

詳細は `lan-sharing.md` を参照してください。

---

# 7. 既知制限

## 7-1. 認証・認可

- 認証は JWT（`POST /api/auth/login` が発行・`--demo` でも必要）。旧 `Bearer demo-token-<user_id>` 形式は廃止済み
- ユーザー単位の API キー発行機能なし

## 7-2. 通信暗号化

- HTTPS 化未対応（リバースプロキシで TLS 終端する必要あり）
- LLM 通信も HTTP 平文

## 7-3. 永続化されない設定

- Embedding / Reranker 設定の実行時変更は YAML に永続化されない（再起動でデフォルトに戻る）

## 7-4. 骨格のみの機能

- Qdrant VectorStore（`add` / `search` 等が `NotImplementedError`）
- MLX Embedding / Reranker（`NotImplementedError`）
- LanceDB バックエンド
- GraphRAG 戦略

## 7-5. DataSyncService

- publish 連携未統合（ログ出力のみ）
- content_hash 比較なし（パス単位の差分のみ）

## 7-6. RAG パイプライン

- 構造化回答テンプレート未実装（自由形式回答が標準）
- 低信頼度フォールバック部分実装

## 7-7. UI

- 一部 UI 要素は JavaScript 初期化まで `display:none`
- 言語切替（日本語 / 英語）で一部要素は固定

詳細は `security-policy.md` を参照してください。

---

# 8. FAQ

## Q1. ChromaDB と SQLite の使い分けは？

- **SQLite**: メタデータ（Workspace、Collection、Source、File、User、AuditLog、PublishHistory など構造化情報）
- **ChromaDB**: ベクター埋め込みとチャンク本文（検索用途）

両者は `_purge_chunks_for_*()` ヘルパーで同期削除されます。

## Q2. Fernet 鍵を紛失するとどうなりますか？

raw 本文（Fernet 暗号化されているもの）は復号できなくなります。masked 本文は素通しのため引き続き読めますが、admin ロールでも raw 本文の参照は不可能になります。`CYNOVELA_SECRET_KEY` は安全に保管してください。

## Q3. 全テストを実行するには？

```bash
bash scripts/run_all_tests.sh
```

14 PHASE / 405 アサーション以上が実行されます。

## Q4. LLM を使わずに品質確認はできますか？

できません。以前あった `--mock`（LLM を呼ばずに動かす指定）は撤去済みで、いま指定するとエラーで止まります。品質確認は実 LLM 環境で行ってください。

## Q5. PII 検出が日本語の住所を拾わないのですが？

PII 検出モードを確認してください。`lite` は正規表現のみのため、住所などの自然言語 PII は検出されません。`standard` または `quality` に変更すると GiNZA NER による住所・人名・組織名の検出が有効になります。

## Q6. MCP クライアントから接続できません

以下を確認してください。
- Cynovela 本体（`server.py`）が `http://127.0.0.1:8765` で起動済みか
- `CYNOVELA_TOKEN` 環境変数の値、トークンの有効性
- `CYNOVELA_MCP_PYTHON` で conda 環境の Python パスを指定済みか
- 対象 Collection が `ready` ステータスに到達済みか

## Q7. インターネットに公開しても良いですか？

絶対に推奨しません。HTTPS 化されておらず、JWT 認証も未実装、ファイルアップロード制限も緩いため、インターネット直接公開は重大なリスクがあります。

## Q8. データを完全に削除するには？

UI から Source / Workspace / Collection を削除すれば、SQLite と ChromaDB の両方が `_purge_chunks_for_*()` 系ヘルパー経由でクリーンアップされます。完全初期化したい場合は `~/.cynovela/` ディレクトリ全体を削除してください（バックアップは事前に取得してください）。

---

最終更新: 2026-05-26 / Alpha GA 対応版
