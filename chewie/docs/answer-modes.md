# 回答モード（Answer Modes）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool built by an individual to
> understand the concepts of AI infrastructure tools by working on them by hand.
> It is not a commercial product or an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela's RAG (Retrieval-Augmented Generation) answers change their behavior according to the combination of a **mode** and a **preset**, depending on the use case. This document organizes the modes that can be confirmed at present, together with their implementation evidence.

---

## 1. Strictness Modes (2 Kinds)

Two system prompts are defined in `rag.py`. These are the switching axis that corresponds to the "strictness mode."

### 1.1 DEFAULT_SYSTEM_PROMPT (Default / RAG Enabled)

- Instructs the model to answer based on the ingested documents (context)
- Recommends embedding the citation numbers `[1][2]`

### 1.2 GENERAL_KNOWLEDGE_SYSTEM_PROMPT (General Knowledge Mode / RAG Disabled)

The definition at `rag.py:204-213` (excerpt):

```python
GENERAL_KNOWLEDGE_SYSTEM_PROMPT = """あなたは優秀なアシスタントです。
ユーザーの質問にあなたの一般知識のみを根拠として回答してください。

【ルール】
- このモードではコンテキストや社内資料は提供されません。
- 知らないことは「分かりません」と素直に伝えること。事実を捏造しないこと。
- 回答はMarkdown形式で返してよい（見出し・�条書き使用可）。
- 質問の意図を理解し、簡潔で正確な説明を心がけること。
```

### 1.3 Switching

- Default: `DEFAULT_SYSTEM_PROMPT` (RAG enabled, answers based on search results)
- General knowledge mode: `GENERAL_KNOWLEDGE_SYSTEM_PROMPT` (RAG disabled, answers from the LLM's general knowledge only)

From MCP (an external tool), you can request a direct answer without RAG by calling the `rag_general` tool.

---

## 2. RAG Presets (5 in Total)

Five built-in presets are defined in `routers/pipeline_config.py`.

| ID | Name | Description | Chunking | RAG mode | Guardrail | Image processing |
|---|---|---|---|---|---|---|
| `tech_doc` | 📄 技術文書 | For manuals | tech_doc | standard | default | — |
| `confidential` | 🔒 機密文書 | In-house documents containing PII | general | standard | mask | — |
| `personal_memo` | 📝 個人メモ | Meeting minutes and memos | email_minutes | lite | log_only | — |
| `multimedia` | 🖼️ マルチメディア | Mixed images and Office files | tech_doc | standard | default | caption |
| `quickstart` | ⚡ クイックスタート | Fully automatic, for beginners | tech_doc | standard | default | — |

### 2.1 Preset Structure

```json
{
  "id": "tech_doc",
  "name": "📄 技術文書",
  "description": "...",
  "config_json": "{\"chunking\": \"tech_doc\", \"rag_mode\": \"standard\", \"guardrail\": \"default\"}",
  "is_builtin": 1
}
```

### 2.2 The 3 Kinds of RAG Mode

A preset's `rag_mode` has the following three kinds.

| Mode | Outline |
|---|---|
| `lite` | Minimal RAG (one search, optional processing omitted) |
| `standard` | Standard RAG (BM25 hybrid, Reranker is optional) |
| `hq` | High-quality RAG (enables CRAG, Multi-Query, and HyDE) |

---

## 3. Structured Answer Template

### 3.1 Current State: Unimplemented

The search `grep -rn "structured.*answer\|answer.*template\|template.*answer" --include="*.py"` returns **0 hits**, and none of the following implementations could be confirmed.

- No structured fields in the `ChunkHit` / `RetrievalResult` dataclasses
- No instruction in the system prompt such as "return in JSON format" or "return with `<answer>XXX</answer>` tags"

Therefore, at present a **free-form answer is the standard**.

### 3.2 The Citation Feature Is Implemented

Separately from the structured answer template, the **citation feature** is implemented (`build_citations()` / `build_context_with_citations()` at `rag.py:479-523`). It embeds citation numbers in the form `[1][2]` in the answer, and returns the citation mapping downstream.

- Setting: `config.rag.citation_enabled = true` (default)

### 3.3 Not decided

Whether to introduce a structured answer template has not been decided, and neither is the shape it would take (fixed JSON output, forced tags, and so on).

---

## 4. Adjusting the Confidence Threshold

### 4.1 Setting Value (Default)

```yaml
# config.py の defaults
rag:
  confidence_threshold: 0.40
```

- Scale: cosine similarity (0 to 1)
- BGE-M3's noise floor: 0.35 to 0.45 (roughly this score appears even for unrelated queries)
- Typical range for real queries: 0.55 to 0.75
- Judgment policy: a highest `vector_score` below 0.40 is treated as low confidence and becomes a fallback candidate

### 4.2 The Judgment Metric Is the Vector Cosine

As a lesson from the past, **using the RRF score for the abstention judgment is wrong**. RRF is a sum of reciprocal ranks (max ≈ 0.033) and differs by orders of magnitude from cosine similarity (0 to 1). Always use the **vector cosine** as the judgment metric.

### 4.3 Where the Threshold Is Applied

`config.rag.confidence_threshold` is read at the chat entry point (`routers/chat.py`), not inside `rag_retrieve`. The current build works as follows.

- When there is at least one hit and the highest `vector_score` is below the threshold, the LLM is not called. A `LOW_CONFIDENCE_FALLBACK` audit entry is written, and the reply carries `low_confidence`, `max_score`, `threshold` and up to 3 suggested questions built from the hits. The SSE path applies the same rule.
- When there are 0 hits, there is no automatic switch to `GENERAL_KNOWLEDGE_SYSTEM_PROMPT`. General knowledge mode is used only when it is asked for explicitly.

### 4.4 Policy for Adjustment

You can change the threshold by editing `rag.confidence_threshold` in `cynovela.yaml`. Hard-coding is prohibited; change it only through the configuration file. Note that a `confidence_threshold` row in the SQLite `settings` table takes priority over the configuration file (see `docs/rag-pipeline.md` §6.4).

---

## 5. Related Advanced Features

The advanced RAG features used in combination with the answer modes are as follows. For details, see `docs/spec-overview.md`.

| Feature | Related setting | Use |
|---|---|---|
| MMR re-selection | `rag.mmr_enabled`, `mmr_lambda` | Balances relevance and diversity |
| Parent-Child chunking | `rag.parent_child_enabled` | Search on the child, replace with the parent |
| Multi-Query expansion | `rag.multi_query_enabled`, `multi_query_count` | Expands the query into several variants with the LLM |
| CRAG (self-evaluating re-search) | `rag.crag_enabled`, `crag_max_loops` | The LLM evaluates the quality of the search results |
| HyDE (hypothetical document embedding) | `rag.hyde_enabled` | Generates a hypothetical answer and searches with its embedding |
| Adaptive RAG | `rag.adaptive_enabled`, `adaptive_threshold` | Switches automatically between basic / agentic by query complexity |
| Reranker | `reranker.provider` | Disabled by default, can be switched to CrossEncoder and so on |

---

## 6. Answer Style by Role

The role prefix in `rag.py` also switches the tone of the answer.

| Role | Policy of the prefix |
|---|---|
| admin | Provides complete information including technical details, setting values, and internal structure |
| reader | A focused, easy-to-understand explanation that avoids technical jargon |

For details, see `docs/rbac.md`.

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela の RAG（検索拡張生成）回答は、用途に応じて **モード** と **プリセット** の組み合わせで挙動が変わります。本ドキュメントでは、現時点で確認できるモードを実装根拠とあわせて整理します。

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

そのため、現時点では **自由形式の回答が標準** です。

### 3.2 引用機能は実装済み

構造化回答テンプレートとは別に、**引用（citation）機能** は実装済みです（`rag.py:479-523` の `build_citations()` / `build_context_with_citations()`）。回答中に `[1][2]` 形式の引用番号を埋め込み、後段で出典マッピングを返します。

- 設定: `config.rag.citation_enabled = true`（既定）

### 3.3 未確定の事項

構造化回答テンプレートの導入可否は未確定で、その仕様（JSON 出力固定、タグ強制など）も未定です。

---

## 4. 信頼度閾値の調整

### 4.1 設定値（既定）

```yaml
# config.py の defaults
rag:
  confidence_threshold: 0.40
```

- スケール: コサイン類似度（0〜1）
- BGE-M3 のノイズフロア: 0.35〜0.45（無関係なクエリでもこの程度のスコアが出る）
- 実存クエリの典型範囲: 0.55〜0.75
- 判定方針: 最高 `vector_score` が 0.40 を下回るものを低信頼度とみなすフォールバック候補

### 4.2 判定指標は vector cosine

過去の教訓として、**Abstention（回答抑制）判定に RRF スコアを使うのは誤り** です。RRF は順位の逆数和（最大 ≈ 0.033）であり、コサイン類似度（0〜1）と桁が違います。判定指標は必ず **vector cosine** を使ってください。

### 4.3 しきい値が効く場所

`config.rag.confidence_threshold` は `rag_retrieve` の中ではなく、chat の入口（`routers/chat.py`）で読まれます。現在の作りは次のとおりです。

- hits が 1 件以上あり、その最高 `vector_score` がしきい値を下回るとき、LLM は呼ばれません。`LOW_CONFIDENCE_FALLBACK` の監査記録が書かれ、応答には `low_confidence`・`max_score`・`threshold` と、hits から作った推奨質問（最大 3 件）が入ります。SSE 経路も同じ規則です。
- hits が 0 件のときに `GENERAL_KNOWLEDGE_SYSTEM_PROMPT` へ自動で切り替わることはありません。一般知識モードは明示的に指定されたときだけ使われます。

### 4.4 調整の方針

`cynovela.yaml` の `rag.confidence_threshold` を編集することで閾値を変えられます。ハードコードは禁止されており、設定ファイル経由のみで変更します。なお SQLite の `settings` テーブルに `confidence_threshold` 行があるときは、そちらが設定ファイルより優先されます（`docs/rag-pipeline.md` §6.4）。

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

