# Cynovela ガードレール

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built so that an individual
> could understand the concepts of an AI platform tool by working with their own hands.
> It is not a commercial product and not an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

## 1. How the Guardrail Works

A guardrail (a mechanism that detects and stops inappropriate input and output on the LLM path) works in Cynovela for the following 3 purposes.

1. **Ingest phase**: At Publish time, PII (personal information) contained in the body text of each chunk is detected, and depending on the policy one of "mask it", "exclude it from the vector DB", "only leave a log", or "let it through" is chosen.
2. **Query acceptance phase**: If there is a sign of prompt injection (an attack that overwrites the instructions) in the user's query, it is blocked immediately with a 400.
3. **Answer generation phase**: The LLM's response text is inspected for wording that would take confidential information out, and it is recorded when detected.

> **Abolished: ingest without masking (`collections.raw_only = 1`)**: Ingest that bypasses masking (Raw mode) was abolished on 2026-07-24. If you specify it now, it is rejected with HTTP 400 (measured 2026-08-02). Only collections created in the past can remain in a state without a masked layer (for details see pii-masking.md §1 / metadata-engine.md §6).

### 1.1 Entry Points

Guardrail settings are managed through the following 3 paths.

| Path | Setting target | Operation API |
|------|----------|----------|
| Workspace policy | Defines classification x action in a policy tied to a Workspace | `/api/policies/*` (admin only) |
| Blocked topics | block / warn on strings contained in the query | `/api/guardrails/blocked-topics` (admin only) |
| Prompt injection inspection | 14 English/Japanese patterns built into the code + 4 output patterns | Fixed in the code (`routers/chat.py:55-91`) |

### 1.2 The Triple of Policy x Classification x Action

One policy (for example `pol-pii` = "PII protection policy") is expressed as JSON that defines an action per classification class (PII / Financial / HR and so on).

```json
[
  {"classifier": "PII", "action": "mask"},
  {"classifier": "Financial", "action": "exclude_from_rag"}
]
```

A policy is tied to a Workspace (the `workspace_policies` table), and is applied to Publish operations under that Workspace.

---

## 2. Categories (Classification Classes)

The classification classes that can be confirmed from the seed data at `db.py:855 / 861 / 867` are 3 items.

| Classification name | Meaning | Example of how it is used |
|--------|------|---------------|
| `PII` | Personal information in general (name, contact details, account number, and so on) | Targeted by all 3 seed policies `pol-pii`, `pol-strict`, `pol-log` |
| `Financial` | Financial and transaction information (credit card numbers, and so on) | Same as above |
| `HR` | Human resources information | Targeted only by `pol-strict` (`exclude_from_rag`) |

The old `classifier.py` also has definitions of 8 categories, PII / Financial / HR / Legal / Healthcare / Sales / Technical / Marketing, but that is a separate system from Smart Ingestion (document type classification at ingest time), and the seeds actually used on the guardrail side are the 3 items above.

<!-- BACKLOG: Legal / Healthcare / Sales / Technical / Marketing の 5 カテゴリは旧 classifier.py に定義はあるが、現行のガードレールシードでは使われていない。GA 時点でこれらを有効化するのか・分類エンジンとの接続をどうするかは spec-raw に確認情報なし -->

---

## 3. Initial Policies (Seeds)

3 initial policies are seeded at `db.py:851-870`.

| Policy ID | Display name | Definition |
|-------------|--------|------|
| `pol-pii` | PII protection policy | PII: mask, Financial: exclude_from_rag |
| `pol-strict` | Strict management policy | PII: mask, Financial: exclude_from_rag, HR: exclude_from_rag |
| `pol-log` | Log-only policy | PII: log_only, Financial: log_only |

By default they are not tied to any workspace. You assign one when you create a workspace.

---

## 4. Action Types

The `valid_actions` at `routers/policies.py:201` is the authoritative definition.

```python
valid_actions = {"mask", "exclude_from_rag", "log_only", "allow"}
```

| Action | Behavior | Use case |
|------------|------|--------------|
| `mask` | Replaces the relevant part with a `[MASKED:XXX]` token before storing | You want to make use of most of the document body while hiding only the personal information |
| `exclude_from_rag` | Does not put the relevant chunk into the vector DB | A classification that "you do not want included in the search target in the first place" |
| `log_only` | Detects but neither masks nor excludes; records only in `audit_logs` | For learning and statistics collection |
| `allow` | Does nothing | A classification you want to let through as an exception |

The actual dispatch is done at `guardrail.py:31-90` (the `exclude_from_rag` / `mask` branch).

### 4.1 Actions on the Blocked Topic Side

Blocked topics added with `/api/guardrails/blocked-topics` take a separate set of actions.

```python
if act not in ("block", "warn"):
    raise api_error("BAD_REQUEST", "action must be 'block' or 'warn'", status=400)
```

| Action | Behavior |
|------------|------|
| `block` | Blocks queries that contain the relevant pattern |
| `warn` | Lets it through but records it as a warning |

Registration as a regular expression is also possible (`is_regex=true`); if there is an error at compile time, a 400 is returned with `INVALID_REGEX`.

---

## 5. Prompt Injection Countermeasures (3-Layer Defense)

The following 3 stages of inspection are implemented in `routers/chat.py`.

### 5.1 Input Inspection (`detect_prompt_injection`)

`routers/chat.py:55-91`. If the query contains any of the following 14 English/Japanese patterns, it is blocked immediately with a 400 and `PROMPT_INJECTION_BLOCKED` is recorded in `audit_logs`.

```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|prior)\s+instructions?",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+",
    r"new\s+instructions?:",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[\s*system\s+override\s*\]",
    r"jailbreak",
    r"pretend\s+you\s+are",
    r"act\s+as\s+(?:if\s+)?(?:you\s+(?:have\s+no|are\s+without))",
    r"reveal\s+(all|your|the)\s+(documents?|data|instructions?|prompt)",
    r"ignore\s+(safety|security|guardrail)",
    r"これまでの指示を(無視|忘れて)",
    r"(全ての|すべての)(ドキュメント|文書|データ)を(教えて|表示)",
]
```

### 5.2 Retrieved Result Inspection (`filter_poisoned_chunks`)

`routers/chat.py:94-111`. The same pattern inspection is also performed on the body text of chunks retrieved as search results, and the relevant chunks are excluded before the context is assembled (`routers/chat.py:1268`). This is a countermeasure against "an indirect attack in which injection wording is planted in the document body".

### 5.3 Output Inspection (`detect_output_exfiltration`)

`routers/chat.py:114-125`. The LLM's response text is inspected for the following 4 patterns, and it is recorded when detected.

```python
EXFILTRATION_PATTERNS = [
    r"\bHACKED\b",
    r"\bPWNED\b",
    r"SECRET-ALPHA-TOKEN",
    r"\[\s*SYSTEM\s+OVERRIDE\s*\]",
]
```

### 5.4 Security Verification

Verified based on international AI security evaluation criteria, including countermeasures against indirect attacks through documents.

### 5.5 Auxiliary Means: LLM Judge

A mechanism is also provided at `llm_judge_pi(text)` in `utils/metadata/pii.py:263` that makes an additional decision based on an LLM judge for patterns that regular expressions cannot fully catch (introduced in Stage R7 C-5).

---

## 6. Placement of the System Prompt

As an important design principle, the system prompt (the pre-specified operating instructions for the LLM) is placed "after" the retrieved content (the body text of the retrieved documents). If it is placed before, a path is created where it can be overwritten by wording such as `[SYSTEM OVERRIDE]` written inside the document body.

---

## 7. Audit Logs (audit_logs)

Events where a guardrail fired are recorded in the `audit_logs` table. In `_AUDIT_CATEGORY_MAP` at `core/audit.py:15`, `PROMPT_INJECTION_BLOCKED` and `pii_detected` are mapped to the `security` category.

`audit_logs` cannot be deleted or modified through the API, and tamper prevention is built into the design.

There are the following 2 aggregation endpoints (both admin only):

- `/api/guardrails/pii-detections` (GET): aggregates PII detections from `audit_logs`
- `/api/pii-detections` (GET): aggregates per document from the `chunks` table

---

## 8. How to Add a Custom Detector

### 8.1 Adding a PII Regular Expression

Add a tuple of `(entity_type, re.compile(pattern), mask_token)` to the list at `guardrail.py:137-153`.

```python
("CUSTOM_ID", re.compile(r"\bCUST-\d{6}\b"), "[MASKED:CUSTOMID]"),
```

The detection counts are aggregated into audit_logs and can be checked from `/api/guardrails/pii-detections`.

### 8.2 Adding a Guardrail Category

If you want to add a new classification class, include the new classification name in the policy JSON and POST it to `/api/policies`.

```json
{
  "id": "pol-custom",
  "name": "カスタムポリシー",
  "rules": [
    {"classifier": "PII", "action": "mask"},
    {"classifier": "CustomConfidential", "action": "exclude_from_rag"}
  ],
  "status": "active"
}
```

On top of that, either extend the implementation of `providers/classifier.py` so that the classifier (Classifier Provider) side returns `CustomConfidential`, or connect an external API classifier (`APIClassifier`) with `classifier.provider: api` in `cynovela.yaml`.

### 8.3 Adding a Blocked Topic

Post to `/api/guardrails/blocked-topics` (POST, admin only) with a pattern string, an action (`block` / `warn`), and if needed `is_regex=true`.

```json
{
  "pattern": "社外秘プロジェクトX",
  "action": "block",
  "is_regex": false
}
```

If you register it as a regular expression, it is compiled beforehand with the equivalent of `re.compile()`, and if it is invalid a 400 is returned with `INVALID_REGEX`.

### 8.4 Adding a Prompt Injection Pattern

Add a regular expression to the `INJECTION_PATTERNS` / `EXFILTRATION_PATTERNS` lists at `routers/chat.py:55-91`. Because they are built into the code, a restart is required after adding.

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

## 1. ガードレールの仕組み

ガードレール（guardrail：LLM 経路で不適切な入力・出力を検出して止める仕組み）は、Cynovela において次の 3 つの目的で機能します。

1. **取込フェーズ**: Publish のときに各 chunk の本文に含まれる PII（個人情報）を検出し、ポリシーに応じて「マスクする」「ベクター DB から除外する」「ログだけ残す」「通す」のいずれかを選びます。
2. **クエリ受付フェーズ**: ユーザのクエリにプロンプトインジェクション（指示の上書き攻撃）の兆候があれば即座に 400 で遮断します。
3. **回答生成フェーズ**: LLM の応答テキストから機密情報持ち出し文言を検査し、検出時には記録します。

> **廃止済み: マスキングなし取り込み（`collections.raw_only = 1`）**: マスキングを迂回する取り込み（Raw モード）は 2026-07-24 に廃止しました。いま指定すると HTTP 400 で拒否されます（2026-08-02 実測）。過去に作られたコレクションだけが masked 層を持たない状態で残り得ます（詳細は pii-masking.md §1 / metadata-engine.md §6）。

### 1.1 入口

ガードレールの設定は次の 3 経路で管理されます。

| 経路 | 設定対象 | 操作 API |
|------|----------|----------|
| Workspace ポリシー | Workspace に紐付くポリシーで分類×アクションを定義 | `/api/policies/*`（admin 限定） |
| 禁止トピック | クエリに含まれた文字列を block / warn | `/api/guardrails/blocked-topics`（admin 限定） |
| プロンプトインジェクション検査 | コード組み込みの英日 14 パターン + 出力 4 パターン | コード固定（`routers/chat.py:55-91`） |

### 1.2 ポリシー × 分類 × アクションの三項

1 つのポリシー（例: `pol-pii` = 「PII 保護ポリシー」）は、分類クラス（PII / Financial / HR など）ごとにアクションを定めた JSON で表現されます。

```json
[
  {"classifier": "PII", "action": "mask"},
  {"classifier": "Financial", "action": "exclude_from_rag"}
]
```

ポリシーは Workspace に紐付き（`workspace_policies` テーブル）、その Workspace 配下の Publish に対して適用されます。

---

## 2. カテゴリ（分類クラス）

`db.py:855 / 861 / 867` のシードデータから確認できる分類クラスは 3 件です。

| 分類名 | 意味 | 使われ方の例 |
|--------|------|---------------|
| `PII` | 個人情報全般（氏名・連絡先・口座番号など） | `pol-pii`・`pol-strict`・`pol-log` の全 3 シードポリシーで対象 |
| `Financial` | 財務・取引情報（クレジットカード番号等） | 同上 |
| `HR` | 人事情報 | `pol-strict` のみで対象（`exclude_from_rag`） |

旧 `classifier.py` には PII / Financial / HR / Legal / Healthcare / Sales / Technical / Marketing の 8 カテゴリ定義もありますが、これは Smart Ingestion（取込時の文書種別分類）とは別系統で、ガードレール側で実際に使われているシードは上記 3 件です。

<!-- BACKLOG: Legal / Healthcare / Sales / Technical / Marketing の 5 カテゴリは旧 classifier.py に定義はあるが、現行のガードレールシードでは使われていない。GA 時点でこれらを有効化するのか・分類エンジンとの接続をどうするかは spec-raw に確認情報なし -->

---

## 3. 初期ポリシー（シード）

`db.py:851-870` で 3 件の初期ポリシーがシードされます。

| ポリシー ID | 表示名 | 定義 |
|-------------|--------|------|
| `pol-pii` | PII 保護ポリシー | PII: mask, Financial: exclude_from_rag |
| `pol-strict` | 厳格管理ポリシー | PII: mask, Financial: exclude_from_rag, HR: exclude_from_rag |
| `pol-log` | ログのみポリシー | PII: log_only, Financial: log_only |

既定ではどのワークスペースにも紐付いていません。ワークスペースを作成するときに割り当てて使います。

---

## 4. アクション種別

`routers/policies.py:201` の `valid_actions` が権威定義です。

```python
valid_actions = {"mask", "exclude_from_rag", "log_only", "allow"}
```

| アクション | 動作 | ユースケース |
|------------|------|--------------|
| `mask` | 該当箇所を `[MASKED:XXX]` トークンに置換してから保管 | 文書本文の大半を活かしつつ、個人情報だけ伏せたい |
| `exclude_from_rag` | 該当 chunk をベクター DB に投入しない | 「そもそも検索対象に含めたくない」分類 |
| `log_only` | 検出するがマスクも除外もしない、`audit_logs` にだけ記録 | 学習・統計収集目的 |
| `allow` | 何もしない | 例外的に通したい分類 |

実際の振り分けは `guardrail.py:31-90` で行われます（`exclude_from_rag` / `mask` 分岐）。

### 4.1 禁止トピック側のアクション

`/api/guardrails/blocked-topics` で追加する禁止トピックは別系統のアクションを取ります。

```python
if act not in ("block", "warn"):
    raise api_error("BAD_REQUEST", "action must be 'block' or 'warn'", status=400)
```

| アクション | 動作 |
|------------|------|
| `block` | 該当パターンを含むクエリを遮断 |
| `warn` | 通すが警告として記録 |

正規表現での登録も可能（`is_regex=true`）で、コンパイル時にエラーがあると `INVALID_REGEX` で 400 を返します。

---

## 5. プロンプトインジェクション対策（3 層防御）

`routers/chat.py` には次の 3 段階の検査が実装されています。

### 5.1 入力検査（`detect_prompt_injection`）

`routers/chat.py:55-91`。クエリに次の英日 14 パターンが含まれていれば即時 400 で遮断し、`audit_logs` に `PROMPT_INJECTION_BLOCKED` を記録します。

```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|prior)\s+instructions?",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+",
    r"new\s+instructions?:",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[\s*system\s+override\s*\]",
    r"jailbreak",
    r"pretend\s+you\s+are",
    r"act\s+as\s+(?:if\s+)?(?:you\s+(?:have\s+no|are\s+without))",
    r"reveal\s+(all|your|the)\s+(documents?|data|instructions?|prompt)",
    r"ignore\s+(safety|security|guardrail)",
    r"これまでの指示を(無視|忘れて)",
    r"(全ての|すべての)(ドキュメント|文書|データ)を(教えて|表示)",
]
```

### 5.2 取得結果検査（`filter_poisoned_chunks`）

`routers/chat.py:94-111`。検索結果として取得した chunk 本文に対しても同じパターン検査を行い、context を組み立てる前に該当 chunk を除外します（`routers/chat.py:1268`）。これは「ドキュメント本文に注入文言を仕込まれる間接攻撃」への対策です。

### 5.3 出力検査（`detect_output_exfiltration`）

`routers/chat.py:114-125`。LLM の応答テキストから次の 4 パターンを検査し、検出時に記録します。

```python
EXFILTRATION_PATTERNS = [
    r"\bHACKED\b",
    r"\bPWNED\b",
    r"SECRET-ALPHA-TOKEN",
    r"\[\s*SYSTEM\s+OVERRIDE\s*\]",
]
```

### 5.4 セキュリティ検証

国際的な AI セキュリティ評価指標に基づき検証済み、ドキュメント経由の間接攻撃対策を含みます。

### 5.5 補助手段：LLM judge

`utils/metadata/pii.py:263` の `llm_judge_pi(text)` で、正規表現では拾いきれないパターンを LLM judge ベースで追加判定する機構も用意されています（Stage R7 C-5 で導入）。

---

## 6. システムプロンプトの配置

設計上の重要原則として、システムプロンプト（事前指定された LLM の動作指示）は retrieved content（取得した文書本文）の「後」に配置します。前に置くとドキュメント本文の中に書かれた `[SYSTEM OVERRIDE]` などの文言で上書きされる経路ができてしまうためです。

---

## 7. 監査ログ（audit_logs）

ガードレールが発火したイベントは `audit_logs` テーブルに記録されます。`core/audit.py:15` の `_AUDIT_CATEGORY_MAP` で `PROMPT_INJECTION_BLOCKED` と `pii_detected` は `security` カテゴリにマップされます。

`audit_logs` は API 経由での削除・変更ができないようになっており、改ざん防止が設計に組み込まれています。

集計エンドポイントは次の 2 系統です（いずれも admin 限定）：

- `/api/guardrails/pii-detections`（GET）: `audit_logs` から PII 検出を集計
- `/api/pii-detections`（GET）: `chunks` テーブルからドキュメント単位で集計

---

## 8. カスタム検出器の追加方法

### 8.1 PII 正規表現の追加

`guardrail.py:137-153` のリストに `(entity_type, re.compile(pattern), mask_token)` のタプルを追加します。

```python
("CUSTOM_ID", re.compile(r"\bCUST-\d{6}\b"), "[MASKED:CUSTOMID]"),
```

検出件数は audit_logs に集計され、`/api/guardrails/pii-detections` から確認できます。

### 8.2 ガードレールカテゴリの追加

新しい分類クラスを追加したい場合は、ポリシー JSON に新規分類名を含めて `/api/policies` に POST します。

```json
{
  "id": "pol-custom",
  "name": "カスタムポリシー",
  "rules": [
    {"classifier": "PII", "action": "mask"},
    {"classifier": "CustomConfidential", "action": "exclude_from_rag"}
  ],
  "status": "active"
}
```

そのうえで、分類器（Classifier Provider）側で `CustomConfidential` を返すように `providers/classifier.py` の実装を拡張するか、外部 API Classifier（`APIClassifier`）を `cynovela.yaml` の `classifier.provider: api` で接続します。

### 8.3 禁止トピックの追加

`/api/guardrails/blocked-topics`（POST、admin 限定）にパターン文字列とアクション（`block` / `warn`）、必要なら `is_regex=true` を付けて投げます。

```json
{
  "pattern": "社外秘プロジェクトX",
  "action": "block",
  "is_regex": false
}
```

正規表現として登録する場合は事前に `re.compile()` 相当でコンパイルされ、無効なら `INVALID_REGEX` で 400 が返ります。

### 8.4 プロンプトインジェクションパターンの追加

`routers/chat.py:55-91` の `INJECTION_PATTERNS` / `EXFILTRATION_PATTERNS` リストに正規表現を追加します。コード組み込みのため、追加後は再起動が必要です。

---

最終更新: 2026-05-26 / Alpha GA 対応版
