# セキュリティ設計

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual to
> understand the concepts of AI infrastructure tools hands-on. It is not a
> commercial product or an official implementation.
> The implementation is entirely original, and consists of an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela implements the **guardrails (protection rules)** and **access control** that are required when handling internal documents with RAG (Retrieval-Augmented Generation), split across several layers. This document summarizes the design principles, the implementation status, and the known limitations.

---

## 1. Three principles of the security design

The security design of Cynovela rests on the following 3 principles.

1. **Double-defense PII (personal information) masking**
   At ingest time both raw and masked are stored, and at answer time an exit mask per role is also applied. Even if one of the two stops working, the other covers it.

2. **Encrypted originals (vault)**
   The original body text is passed through Fernet encryption immediately before it is stored into SQLite and Chroma. The `enc:` prefix makes it idempotent and prevents double encryption.

3. **Three-layer prompt injection countermeasures**
   Checks are made in 3 stages: input inspection, post-retrieval inspection, and output inspection. On detection it is recorded in the audit log and blocked with HTTP 400.

---

## 2. Technical guarantees of workspace separation

### 2.1 Separation layers per workspace

| Layer | Separation method |
|---|---|
| User assignment | `workspace_users (workspace_id, user_id)` |
| Guardrail policy | `workspace_policies (workspace_id, policy_id)` |
| Source binding | `workspace_sources (workspace_id, source_id)` |
| Collection | References `workspaces.id` with an FK; deleted together via `ON DELETE CASCADE` |

### 2.2 Separation in ChromaDB (vector search)

At Publish time, 2 kinds of vector collections, `{cid}__raw` and `{cid}__masked`, are created per collection. When searching from chat, the destination that is read is switched according to the role of the user.

### 2.3 ACL (access control list) filter

The ACL filter operates inside the search pipeline (`rag_retrieve`) of `rag.py`.

```python
# Vector 経路での ACL
if user_role and _acl_filter_enabled():
    allowed_roles = metadata.get("allowed_roles")
    if allowed_roles and user_role not in allowed_roles:
        continue  # 除外
```

On the BM25 path as well, the metadata is completed first and then the ACL check is performed. Setting `features.acl_filter` to `false` allows it to be skipped, but the default is `true`.

### 2.4 Known limitations

- ChromaDB is separated by a logical boundary (collection name), but a **physical boundary (a separate directory, etc.) is not implemented**. An improvement is planned toward Beta GA.
- The cross-boundary check for session information of WS-A being diverted into a chat of WS-B has a known gap, and is planned to be addressed in Phase 3.

---

## 3. PII detection and masking

### 3.1 Two PII detection systems

PII detection in Cynovela has 2 systems.

#### Primary: regular expression based (`guardrail.py`)

It detects 8 kinds of entities.

| entity_type | Mask token | Pattern example |
|---|---|---|
| URL | `[MASKED:URL]` | `https?://...` |
| EMAIL | `[MASKED:EMAIL]` | `\b[\w.+-]+@[\w.-]+\.\w+\b` |
| PHONE_JP | `[MASKED:PHONE]` | Mobile phone number |
| PHONE_LAND | `[MASKED:PHONE]` | Landline phone number |
| CREDIT | `[MASKED:CREDIT]` | Credit card number |
| MYNUMBER | `[MASKED:MYNUM]` | My Number (12 digits) |
| PASSPORT | `[MASKED:PASSPORT]` | Passport number |
| IPV4 | `[MASKED:IP]` | IPv4 address |

#### Secondary: named entity recognition + fallback (`utils/metadata/pii.py`)

presidio (a personal information detection library) is used if available, and if not, a regular expression fallback is used. Both Japanese and English are supported.

- presidio side: `PERSON_JP`, `ORG_JP`, `LOC_JP`, `ADDRESS_JP`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `DATE_TIME`, and others
- Fallback: `EMAIL`, `PHONE_JP`, `PHONE_INTL`, `IP_ADDRESS`, `MY_NUMBER`, `CREDIT_CARD`, `INTERNAL_URL`

The targets of the policy matrix (`routers/policies.py`) are 6 kinds: EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / IPV4.

### 3.2 PII detection modes

Switched with `pii_mode` in `cynovela.yaml` (abolished as a CLI argument).

| Value | Detection method | Speed |
|---|---|---|
| `lite` | Regular expressions only | Lightweight and fast |
| `standard` (default) | Regular expressions + GiNZA NER | Middle ground |
| `quality` | Regular expressions + GiNZA NER + detailed filtering | High accuracy, slow |

### 3.3 Masking at ingest time (Tier1)

At Publish time, 2 lines, raw and masked, are generated from each chunk and stored in parallel into both SQLite and Chroma.

```python
_meta_raw["tier"]    = "raw"
_meta_masked["tier"] = "masked"
all_docs_masked.append(_masked_chunk or "")
```

### 3.4 Masking at answer time (Tier2)

An exit mask is applied to the LLM output according to the role of the user.

```python
def tier_for_role(role: str) -> str:
    return "raw" if (role or "").strip() == "admin" else "masked"
```

It is called on all 4 paths of `routers/chat.py`: normal response / comparison A / comparison B / SSE. For anything other than admin, the exit mask is applied by force.

For details, see `docs/guardrails.md` (provided separately) or `docs/rbac.md`.

---

## 4. Fernet encryption (vault)

### 4.1 Design policy

- **Target**: the original body text (raw tier only). The masked tier passes through as-is (double defense is unnecessary, and this keeps search performance)
- **Interface**: goes through `enc_raw()` / `dec_raw()` of `vault_enc.py`
- **Idempotency**: the `enc:` prefix is used as a marker to prevent double encryption
- **Key**: uses the Fernet key in the environment variable `CYNOVELA_SECRET_KEY`

### 4.2 Where it is implemented

Fernet is initialized at `config.py:62`.

```python
_fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)
```

The interface functions of `vault_enc.py`:

```python
ENC_PREFIX = "enc:"

def enc_raw(text):
    """raw 本文を暗号化形式に揃える (冪等)"""

def dec_raw(text):
    """暗号化形式なら復号、それ以外はそのまま素通し (冪等)"""
```

Where it is applied:

| Location | Code |
|---|---|
| SQLite `chunks` | `rag.py:1131` |
| Insert into Chroma | `rag.py:1285` |
| SQLite `parent_chunks` | `rag.py:1393` |

`tools/vault_enc_migrate.py` also provides a bulk encryption migration for existing data.

---

## 5. RAG poisoning countermeasures (3-layer defense)

### 5.1 Input inspection

Prompt injection wording contained in the query itself is detected with 14 patterns (both English and Japanese).

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

On detection, `PROMPT_INJECTION_BLOCKED` is recorded in the audit log and it is blocked immediately with HTTP 400.

### 5.2 Post-retrieval inspection

The same set of patterns is applied to the chunks in the search results as well, and contaminated chunks are excluded **before** the context is built.

```python
filtered_chunks, _pi_filtered_count = filter_poisoned_chunks(filtered_chunks)
```

### 5.3 Output inspection

It checks whether the response of the LLM contains exfiltration (information leakage) keywords.

```python
EXFILTRATION_PATTERNS = [
    r"\bHACKED\b",
    r"\bPWNED\b",
    r"SECRET-ALPHA-TOKEN",
    r"\[\s*SYSTEM\s+OVERRIDE\s*\]",
]
```

In addition, an extra **LLM judge based** decision is also provided by `llm_judge_pi` in `utils/metadata/pii.py` (Stage R7 C-5).

### 5.4 Indirect attacks through documents (known limitation)

Prompt injection wording that slipped into an ingested document is guarded once by the post-retrieval inspection, but a **detection mechanism dedicated to indirect prompt injection** is listed as one of the HIGH priority bugs to be added in Phase 3.

---

## 6. Authentication and authorization

For details, see `docs/rbac.md`. Only the key points are described here.

- Roles: 3 kinds, `admin` / `curator` / `viewer` (fixed by a CHECK constraint in the DB)
- Role check helpers: `_require_admin`, `_require_authenticated`, `_require_role`, `_require_admin_or_self`
- Calls to the role checks are spread over about 242 places under the routers
- One-click entry has been removed (username / password are required)

---

## 7. Audit log

- Important operations (creation and deletion of Source / Workspace, Publish, Chat, authentication failure, PII detection, prompt injection blocking, and so on) are recorded with `_log_audit(conn, action, target, detail)`.
- **Deletion and modification through the API are forbidden** (tamper prevention).
- They are classified into `security` / `data` / `system` and so on by the category map (`_AUDIT_CATEGORY_MAP` of `core/audit.py`).

---

## 8. Network control

### 8.1 IP allow list

In the middleware of `server.py`, the client IP is checked against the allow list.

| Startup flag | Effect |
|---|---|
| Default | No restriction (everything passes when `--allow-subnet` / `--allow-tailscale` are not specified) |
| `--lan` | LAN exposure (`host=0.0.0.0`) |
| `--allow-tailscale` | Adds the Tailscale subnet (`100.64.0.0/10`) |
| `--allow-subnet` | Adds a custom subnet (can be specified multiple times) |

Access from an IP that is not allowed returns **HTTP 403 Forbidden**.

### 8.2 Restriction on the LM Studio URL

`llm_endpoint` is validated on the settings API side so that it cannot be changed to a value that points to the internal network.

---

## 9. Placement order of the system prompt

When composing the LLM prompt, the design is that the **system prompt is placed "after" retrieved_content**. This is because, if it is placed first, it can be overwritten by the body text of an ingested document.

---

## 10.  known limitations

| Item | Status |
|---|---|
| Forced authentication | Resolved (2026-07-29). Only the JWT of `/api/auth/login` is accepted, and authentication is forced even on a `--demo` startup |
| WS physical boundary | A physical boundary at the ChromaDB level is not implemented. Planned for Phase 3 |
| WS-A → WS-B cross-boundary check | There is a gap. Planned for Phase 3 |
| Indirect prompt injection detection | No dedicated mechanism. Planned to be added in Phase 3 |
| DB → Chroma order inversion in `import_workspace` | Known bug. Planned to be fixed in Phase 3 |
| Race condition in `admin_cleanup_chromadb_orphans` | Known bug. Planned to be fixed in Phase 3 |
| Persistence of Embedding / Reranker settings | Kept in memory only. Returns to the default on restart |

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela は、社内ドキュメントを RAG（検索拡張生成）で扱う際に必要となる **ガードレール（保護ルール）** と **アクセス制御** を、複数層に分けて実装しています。本ドキュメントでは、その設計原則・実装状況・既知制限をまとめます。

---

## 1. セキュリティ設計 3 原則

Cynovela のセキュリティ設計は、次の 3 原則に立脚しています。

1. **二重防御の PII（個人情報）マスキング**
   取込時に raw / masked を両方保存し、回答時にロール別の出口マスクも適用します。どちらか一方が機能不全になっても、もう一方で覆える構造です。

2. **暗号化された原本（vault）**
   原本本文は SQLite と Chroma に保存する直前で Fernet 暗号化を通します。`enc:` プレフィックスで冪等にし、二重暗号化を防ぎます。

3. **3 層のプロンプトインジェクション対策**
   入力検査 → retrieval 後検査 → 出力検査の 3 段階でチェックします。検出時は監査ログに記録し、HTTP 400 で遮断します。

---

## 2. ワークスペース分離の技術的保証

### 2.1 ワークスペース単位の分離レイヤー

| レイヤー | 分離方式 |
|---|---|
| ユーザー割り当て | `workspace_users (workspace_id, user_id)` |
| ガードレールポリシー | `workspace_policies (workspace_id, policy_id)` |
| Source 紐付け | `workspace_sources (workspace_id, source_id)` |
| Collection | `workspaces.id` を FK で参照、`ON DELETE CASCADE` で連動削除 |

### 2.2 ChromaDB（ベクター検索）の分離

Publish 時にコレクション単位で `{cid}__raw` と `{cid}__masked` の 2 種類のベクターコレクションを作ります。チャットの検索時には、利用者のロールに応じて読みに行く先を切り替えます。

### 2.3 ACL（アクセス制御リスト）フィルター

`rag.py` の検索パイプライン（`rag_retrieve`）の中で ACL フィルターが動作します。

```python
# Vector 経路での ACL
if user_role and _acl_filter_enabled():
    allowed_roles = metadata.get("allowed_roles")
    if allowed_roles and user_role not in allowed_roles:
        continue  # 除外
```

BM25 経路でも同様にメタデータを補完してから ACL チェックを行います。`features.acl_filter` を `false` にするとスキップ可能ですが、既定は `true` です。

### 2.4 既知制限

- ChromaDB は論理境界（コレクション名）で分離していますが、**物理境界（別ディレクトリ等）は未実装** です。Beta GA に向けて改善が予定されています。
- WS-A のセッション情報が WS-B のチャットに流用される越境チェックには既知の漏れがあり、Phase 3 で対応予定です。
<!-- BACKLOG: WS 分離の物理境界化、越境チェックの強化は Phase 3 対応 -->

---

## 3. PII 検出とマスキング

### 3.1 PII 検出 2 系統

Cynovela の PII 検出には 2 系統あります。

#### 一次：正規表現ベース（`guardrail.py`）

8 種類のエンティティを検出します。

| entity_type | マスクトークン | パターン例 |
|---|---|---|
| URL | `[MASKED:URL]` | `https?://...` |
| EMAIL | `[MASKED:EMAIL]` | `\b[\w.+-]+@[\w.-]+\.\w+\b` |
| PHONE_JP | `[MASKED:PHONE]` | 携帯電話番号 |
| PHONE_LAND | `[MASKED:PHONE]` | 固定電話番号 |
| CREDIT | `[MASKED:CREDIT]` | クレジットカード番号 |
| MYNUMBER | `[MASKED:MYNUM]` | マイナンバー（12 桁） |
| PASSPORT | `[MASKED:PASSPORT]` | パスポート番号 |
| IPV4 | `[MASKED:IP]` | IPv4 アドレス |

#### 二次：固有表現抽出 + フォールバック（`utils/metadata/pii.py`）

presidio（個人情報検出ライブラリ）が使えれば使い、使えなければ正規表現フォールバック。日本語・英語両対応。

- presidio 系: `PERSON_JP`, `ORG_JP`, `LOC_JP`, `ADDRESS_JP`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `DATE_TIME` ほか
- フォールバック: `EMAIL`, `PHONE_JP`, `PHONE_INTL`, `IP_ADDRESS`, `MY_NUMBER`, `CREDIT_CARD`, `INTERNAL_URL`

ポリシーマトリクス（`routers/policies.py`）の対象は 6 種類: EMAIL / PHONE_JP / PHONE_LAND / CREDIT / MYNUMBER / IPV4。

### 3.2 PII 検出モード

`cynovela.yaml` の `pii_mode` で切り替えます（CLI 引数では廃止）。

| 値 | 検出方式 | 速度 |
|---|---|---|
| `lite` | 正規表現のみ | 軽量・高速 |
| `standard`（既定） | 正規表現 + GiNZA NER | 中庸 |
| `quality` | 正規表現 + GiNZA NER + 詳細フィルタリング | 高精度・低速 |

### 3.3 取込時マスキング（Tier1）

Publish 時に各チャンクから raw / masked の 2 行を生成し、SQLite と Chroma の両方に並列保存します。

```python
_meta_raw["tier"]    = "raw"
_meta_masked["tier"] = "masked"
all_docs_masked.append(_masked_chunk or "")
```

### 3.4 回答時マスキング（Tier2）

LLM 出力に対して、利用者のロールに応じて出口マスクを適用します。

```python
def tier_for_role(role: str) -> str:
    return "raw" if (role or "").strip() == "admin" else "masked"
```

`routers/chat.py` の通常応答 / 比較 A / 比較 B / SSE の 4 経路すべてで呼ばれます。admin 以外は強制的に出口マスクが適用されます。

詳細は `docs/guardrails.md`（別途）または `docs/rbac.md` を参照してください。
<!-- BACKLOG: docs/guardrails.md の存在は B-3 フェーズで生成予定 -->

---

## 4. Fernet 暗号化（vault）

### 4.1 設計方針

- **対象**: 原本本文（raw tier のみ）。masked tier は素通し（二重防御不要、検索パフォーマンス確保のため）
- **インターフェース**: `vault_enc.py` の `enc_raw()` / `dec_raw()` を介す
- **冪等性**: `enc:` プレフィックスをマーカーにして二重暗号化を防ぐ
- **鍵**: 環境変数 `CYNOVELA_SECRET_KEY` の Fernet 鍵を使用

### 4.2 実装箇所

`config.py:62` で Fernet が初期化されます。

```python
_fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)
```

`vault_enc.py` のインターフェース関数:

```python
ENC_PREFIX = "enc:"

def enc_raw(text):
    """raw 本文を暗号化形式に揃える (冪等)"""

def dec_raw(text):
    """暗号化形式なら復号、それ以外はそのまま素通し (冪等)"""
```

適用箇所:

| 箇所 | コード |
|---|---|
| SQLite `chunks` | `rag.py:1131` |
| Chroma 投入 | `rag.py:1285` |
| SQLite `parent_chunks` | `rag.py:1393` |

`tools/vault_enc_migrate.py` で、既存データの一括暗号化マイグレーションも提供されています。

---

## 5. RAG ポイズニング対策（3 層防御）

### 5.1 入力検査

クエリ自体に含まれるプロンプトインジェクション文言を 14 パターン（英日両対応）で検出します。

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

検出時は監査ログに `PROMPT_INJECTION_BLOCKED` を記録し、HTTP 400 で即遮断します。

### 5.2 retrieval 後検査

検索結果のチャンクにも同じパターン群を適用し、汚染されたチャンクを context 構築の **前** に除外します。

```python
filtered_chunks, _pi_filtered_count = filter_poisoned_chunks(filtered_chunks)
```

### 5.3 出力検査

LLM の応答に exfiltration（情報漏えい）系のキーワードが含まれていないかチェックします。

```python
EXFILTRATION_PATTERNS = [
    r"\bHACKED\b",
    r"\bPWNED\b",
    r"SECRET-ALPHA-TOKEN",
    r"\[\s*SYSTEM\s+OVERRIDE\s*\]",
]
```

加えて、`utils/metadata/pii.py` の `llm_judge_pi` で **LLM judge ベース** の追加判定も用意されています（Stage R7 C-5）。

### 5.4 ドキュメント経由の間接攻撃（既知制限）

取り込んだドキュメントに紛れ込んだプロンプトインジェクション文言は、retrieval 後検査で 1 段ガードしていますが、**間接プロンプトインジェクション専用の検出機構** は Phase 3 で追加予定の HIGH 優先度バグの 1 つに挙げられています。
<!-- BACKLOG: 間接プロンプトインジェクション専用検出の設計詳細は Phase 3 で確定 -->

---

## 6. 認証・認可

詳細は `docs/rbac.md` を参照してください。要点のみ記載します。

- ロール: `admin` / `curator` / `viewer` の 3 種類（DB の CHECK 制約で固定）
- ロール検査ヘルパー: `_require_admin`, `_require_authenticated`, `_require_role`, `_require_admin_or_self`
- ロール検査の呼び出しはルーター配下に約 242 箇所分散
- ワンクリック入室は撤去済み（username / password 必須）

---

## 7. 監査ログ

- 重要操作（Source / Workspace の作成・削除、Publish、Chat、認証失敗、PII 検出、プロンプトインジェクション遮断など）は `_log_audit(conn, action, target, detail)` で記録されます。
- **API 経由での削除・変更は禁止** されています（改ざん防止）。
- カテゴリマップ（`core/audit.py` の `_AUDIT_CATEGORY_MAP`）で `security` / `data` / `system` などに分類されます。

---

## 8. ネットワーク制御

### 8.1 IP アローリスト

`server.py` のミドルウェアで、クライアント IP を許可リストと照合します。

| 起動フラグ | 効果 |
|---|---|
| 既定 | 制限なし（`--allow-subnet` / `--allow-tailscale` 未指定時は全通過） |
| `--lan` | LAN 公開（`host=0.0.0.0`） |
| `--allow-tailscale` | Tailscale サブネット（`100.64.0.0/10`）を追加 |
| `--allow-subnet` | カスタムサブネットを追加（複数指定可） |

許可外 IP からのアクセスは **HTTP 403 Forbidden** を返します。

### 8.2 LM Studio URL の制限

`llm_endpoint` は内部ネットワークを指す値に変更できないように、設定 API 側でバリデーションされます。

---

## 9. システムプロンプトの配置順

LLM プロンプトを構成する際、**システムプロンプトは retrieved_content の「後」に配置** する設計です。前置きすると、取り込んだドキュメント本文で上書きされ得るためです。

---

## 10. 既知の制限

| 項目 | 状態 |
|---|---|
| 認証強制 | 解消済み（2026-07-29）。`/api/auth/login` の JWT のみを受け付け、`--demo` 起動でも認証は強制されます |
| WS 物理境界 | ChromaDB レベルの物理境界は未実装。Phase 3 で対応予定 |
| WS-A → WS-B 越境チェック | 漏れあり。Phase 3 で対応予定 |
| 間接プロンプトインジェクション検出 | 専用機構なし。Phase 3 で追加予定 |
| `import_workspace` の DB → Chroma 順序逆転 | 既知バグ。Phase 3 で修正予定 |
| `admin_cleanup_chromadb_orphans` の競合状態 | 既知バグ。Phase 3 で修正予定 |
| Embedding / Reranker 設定の永続化 | メモリ保持のみ。再起動でデフォルトに戻る |

---

