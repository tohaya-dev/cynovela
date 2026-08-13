> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# AI コンセプトガイド

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

**Vector Score（コサイン類似度）**: 0〜1 のスケール。BGE-M3 が文をベクトル化し、ChromaDB の距離（distance）を `_dist_to_sim()` で類似度に変換した値（A-3 §11、`rag.py:1701`）。BGE-M3 のノイズフロアは 0.35〜0.45 で、実存クエリ（資料に答えがあるもの）は典型的に 0.55〜0.75 程度になります。低信頼度フォールバックの閾値 `confidence_threshold` は既定 0.50 です（`config.py:131-135`）。

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
最終更新: 2026-05-26 / Alpha GA 対応版
