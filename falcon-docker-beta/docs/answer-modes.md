> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# 回答モード（Answer Modes）

Cynovela の RAG（検索拡張生成）回答は、用途に応じて **モード** と **プリセット** の組み合わせで挙動が変わります。本ドキュメントでは、Alpha GA 時点で確認できるモードを実装根拠とあわせて整理します。

---

## 1. 厳格度モード（2 種類）

`rag.py` には、2 種類のシステムプロンプトが定義されています。これが「厳格度モード」相当の切替軸になります。

### 1.1 DEFAULT_SYSTEM_PROMPT（既定 / RAG 有効）

- 取り込んだドキュメント（コンテキスト）を根拠に回答するよう指示
- 引用番号 `[1][2]` の埋め込みを推奨

### 1.2 GENERAL_KNOWLEDGE_SYSTEM_PROMPT（一般知識モード / RAG 無効）

`rag.py:204-213` の定義（抜粋）:

```python
GENERAL_KNOWLEDGE_SYSTEM_PROMPT = """あなたは優秀なアシスタントです。
ユーザーの質問にあなたの一般知識のみを根拠として回答してください。

【ルール】
- このモードではコンテキストや社内資料は提供されません。
- 知らないことは「分かりません」と素直に伝えること。事実を捏造しないこと。
- 回答はMarkdown形式で返してよい（見出し・�条書き使用可）。
- 質問の意図を理解し、簡潔で正確な説明を心がけること。
```

### 1.3 切替

- 既定: `DEFAULT_SYSTEM_PROMPT`（RAG 有効、検索結果に基づく回答）
- 一般知識モード: `GENERAL_KNOWLEDGE_SYSTEM_PROMPT`（RAG 無効、LLM の一般知識のみで回答）

MCP（外部ツール）からは `rag_general` ツールを呼ぶことで、RAG なしの直接回答を要求できます。

---

## 2. RAG プリセット（全 5 件）

`routers/pipeline_config.py` に 5 つの組み込みプリセットが定義されています。

| ID | 名前 | 説明 | チャンキング | RAG モード | ガードレール | 画像処理 |
|---|---|---|---|---|---|---|
| `tech_doc` | 📄 技術文書 | マニュアル向け | tech_doc | standard | default | — |
| `confidential` | 🔒 機密文書 | PII を含む社内文書 | general | standard | mask | — |
| `personal_memo` | 📝 個人メモ | 議事録・メモ | email_minutes | lite | log_only | — |
| `multimedia` | 🖼️ マルチメディア | 画像・Office 混在 | tech_doc | standard | default | caption |
| `quickstart` | ⚡ クイックスタート | 初心者向け全自動 | tech_doc | standard | default | — |

### 2.1 プリセット構造

```json
{
  "id": "tech_doc",
  "name": "📄 技術文書",
  "description": "...",
  "config_json": "{\"chunking\": \"tech_doc\", \"rag_mode\": \"standard\", \"guardrail\": \"default\"}",
  "is_builtin": 1
}
```

### 2.2 RAG モードの 3 種類

プリセットの `rag_mode` には次の 3 種類があります。

| モード | 概要 |
|---|---|
| `lite` | 最小限の RAG（1 回検索、オプション処理を省略） |
| `standard` | 標準的な RAG（BM25 ハイブリッド、Reranker はオプション） |
| `hq` | 高品質 RAG（CRAG、Multi-Query、HyDE を有効化） |

---

## 3. 構造化回答テンプレート

### 3.1 現状: 未実装

`grep -rn "structured.*answer\|answer.*template\|template.*answer" --include="*.py"` の検索結果は **0 件** で、次のいずれの実装も確認できませんでした。

- `ChunkHit` / `RetrievalResult` dataclass に構造化フィールドなし
- システムプロンプトに「JSON 形式で返す」「`<answer>XXX</answer>` タグで返す」等の指示なし

そのため、Alpha GA 時点では **自由形式の回答が標準** です。

### 3.2 引用機能は実装済み

構造化回答テンプレートとは別に、**引用（citation）機能** は実装済みです（`rag.py:238-288` の `build_citations()` / `build_context_with_citations()`）。回答中に `[1][2]` 形式の引用番号を埋め込み、後段で出典マッピングを返します。

- 設定: `config.rag.citation_enabled = true`（既定）

### 3.3 Beta GA 予定

構造化回答テンプレートの導入可否は未確定です。
<!-- BACKLOG: 構造化回答テンプレート（JSON 出力固定、タグ強制など）の仕様は未定 -->

---

## 4. 信頼度閾値の調整

### 4.1 設定値（既定）

```yaml
# config.py の defaults
rag:
  confidence_threshold: 0.50
```

- スケール: コサイン類似度（0〜1）
- BGE-M3 のノイズフロア: 0.35〜0.45（無関係なクエリでもこの程度のスコアが出る）
- 実存クエリの典型範囲: 0.55〜0.75
- 判定方針: 0.50 以下を「低品質」とみなすフォールバック候補

### 4.2 判定指標は vector cosine

過去の教訓として、**Abstention（回答抑制）判定に RRF スコアを使うのは誤り** です。RRF は順位の逆数和（最大 ≈ 0.033）であり、コサイン類似度（0〜1）と桁が違います。判定指標は必ず **vector cosine** を使ってください。

### 4.3 パイプライン統合状況

`config.rag.confidence_threshold` は値としては定義済みですが、検索パイプライン（`rag_retrieve`）の中で **明示的な除外ロジックには部分統合** に留まります。

- 検索結果の 0 件処理 → `GENERAL_KNOWLEDGE_SYSTEM_PROMPT` への自動切替は未実装
- 最高スコア < threshold での別処理フローは未実装
<!-- BACKLOG: confidence_threshold を踏まえた Abstention フォールバックの完全統合は未実装 -->

### 4.4 調整の方針

`cynovela.yaml` の `rag.confidence_threshold` を編集することで閾値を変えられます。ハードコードは禁止されており、設定ファイル経由のみで変更します。

---

## 5. 関連する高度機能

回答モードと組み合わせて使う高度な RAG 機能は次のとおりです。詳細は `docs/spec-overview.md` を参照してください。

| 機能 | 関連設定 | 用途 |
|---|---|---|
| MMR 再選別 | `rag.mmr_enabled`, `mmr_lambda` | 関連性と多様性のバランス調整 |
| Parent-Child チャンキング | `rag.parent_child_enabled` | 子で検索、親に置換 |
| Multi-Query 展開 | `rag.multi_query_enabled`, `multi_query_count` | クエリを LLM で複数バリアントに展開 |
| CRAG（自己評価式再検索） | `rag.crag_enabled`, `crag_max_loops` | 検索結果の質を LLM が評価 |
| HyDE（仮想文書埋め込み） | `rag.hyde_enabled` | 仮想回答を生成して、その埋め込みで検索 |
| Adaptive RAG | `rag.adaptive_enabled`, `adaptive_threshold` | クエリ複雑度で basic / agentic を自動切替 |
| Reranker | `reranker.provider` | 既定は無効、CrossEncoder などに切替可能 |

---

## 6. ロール別 回答スタイル

`rag.py` のロール接頭辞で、回答のトーンも切り替わります。

| ロール | 接頭辞の方針 |
|---|---|
| admin | 技術的な詳細・設定値・内部構造を含む完全な情報を提供 |
| reader | 要点を絞ったわかりやすい説明、専門用語は避ける |

詳細は `docs/rbac.md` を参照してください。

---

最終更新: 2026-05-26 / Alpha GA 対応版
