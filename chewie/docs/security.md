# セキュリティ

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual to
> understand the concepts of AI infrastructure tools hands-on. It is not a
> commercial product or an official implementation.
> The implementation is entirely original, and consists of an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela implements the **guardrails (protection rules)** and **access control** that are required when handling internal documents with RAG (Retrieval-Augmented Generation), split across several layers. This document describes how the current construction works, so that the person who sets Cynovela up can judge what is covered by it and what is not.

Cynovela is a learning tool, and it does not meet the security requirements of production operation. The known limitations of Cynovela as a whole are collected in `docs/limits.md`.

---

**Contents**

- [1. Disclaimers (4 points)](#1-disclaimers-4-points)
  - [1-1. Learning purpose, unofficial implementation](#1-1-learning-purpose-unofficial-implementation)
  - [1-2. Absence of any official position](#1-2-absence-of-any-official-position)
  - [1-3. Production operation is out of scope](#1-3-production-operation-is-out-of-scope)
  - [1-4. Possibility of specification changes](#1-4-possibility-of-specification-changes)
- [2. Overall construction](#2-overall-construction)
  - [2.1 Three principles of the security design](#21-three-principles-of-the-security-design)
  - [2.2 Separation layers per workspace](#22-separation-layers-per-workspace)
  - [2.3 Separation in ChromaDB (vector search)](#23-separation-in-chromadb-vector-search)
  - [2.4 ACL (access control list) filter](#24-acl-access-control-list-filter)
  - [2.5 Known limitations of the separation](#25-known-limitations-of-the-separation)
  - [2.6 Audit log](#26-audit-log)
  - [2.7 Network control: IP allow list](#27-network-control-ip-allow-list)
  - [2.8 Network control: restriction on the LM Studio URL](#28-network-control-restriction-on-the-lm-studio-url)
  - [2.9 Known limitations of the current construction](#29-known-limitations-of-the-current-construction)
- [3. Roles and permissions (RBAC)](#3-roles-and-permissions-rbac)
  - [3.1 Role definitions (3 roles)](#31-role-definitions-3-roles)
  - [3.2 Role check helpers](#32-role-check-helpers)
  - [3.3 Main endpoints by role (admin only)](#33-main-endpoints-by-role-admin-only)
  - [3.4 Access control per workspace](#34-access-control-per-workspace)
  - [3.5 Differences in answer style by role](#35-differences-in-answer-style-by-role)
  - [3.6 Limitations of the role implementation](#36-limitations-of-the-role-implementation)
- [4. Guardrails](#4-guardrails)
  - [4.1 How the guardrail works](#41-how-the-guardrail-works)
  - [4.2 Entry points](#42-entry-points)
  - [4.3 The triple of policy x classification x action](#43-the-triple-of-policy-x-classification-x-action)
  - [4.4 Categories (classification classes)](#44-categories-classification-classes)
  - [4.5 Initial policies (seeds)](#45-initial-policies-seeds)
  - [4.6 Action types](#46-action-types)
  - [4.7 Prompt injection countermeasures (3-layer defense)](#47-prompt-injection-countermeasures-3-layer-defense)
  - [4.8 Placement of the system prompt](#48-placement-of-the-system-prompt)
  - [4.9 Audit logs of guardrail events (audit_logs)](#49-audit-logs-of-guardrail-events-audit_logs)
  - [4.10 How to add a custom detector](#410-how-to-add-a-custom-detector)
- [5. PII detection and masking](#5-pii-detection-and-masking)
  - [5.1 Design principle: put only masked text into the vector DB](#51-design-principle-put-only-masked-text-into-the-vector-db)
  - [5.2 Tier1: masking at ingest time](#52-tier1-masking-at-ingest-time)
  - [5.3 Tier2: masking at answer time](#53-tier2-masking-at-answer-time)
  - [5.4 Dispatch by role](#54-dispatch-by-role)
  - [5.5 How it looks by role](#55-how-it-looks-by-role)
  - [5.6 Fernet encryption (vault)](#56-fernet-encryption-vault)
  - [5.7 All PII categories](#57-all-pii-categories)
  - [5.8 Differences between `pii_mode` values](#58-differences-between-pii_mode-values)
  - [5.9 Aggregation of detection counts](#59-aggregation-of-detection-counts)
  - [5.10 Migration from the old implementation](#510-migration-from-the-old-implementation)
- [6. Ways of use that are not recommended](#6-ways-of-use-that-are-not-recommended)
  - [6-1. Publishing directly to the internet](#6-1-publishing-directly-to-the-internet)
  - [6-2. Production operation with confidential documents](#6-2-production-operation-with-confidential-documents)
  - [6-3. LAN sharing with users you cannot trust](#6-3-lan-sharing-with-users-you-cannot-trust)
  - [6-4. Editing the audit log directly in the DB](#6-4-editing-the-audit-log-directly-in-the-db)
  - [6-5. Forcing multiple simultaneous Publishes](#6-5-forcing-multiple-simultaneous-publishes)
  - [6-6. Checking quality in mock mode](#6-6-checking-quality-in-mock-mode)
  - [6-7. Adding new `INSERT OR REPLACE` statements](#6-7-adding-new-insert-or-replace-statements)
- [7. Recommended operation configurations](#7-recommended-operation-configurations)
  - [7-1. Fully local operation (the narrowest exposure)](#7-1-fully-local-operation-the-narrowest-exposure)
  - [7-2. Local LLM operation](#7-2-local-llm-operation)
  - [7-3. Operation via a personal VPN](#7-3-operation-via-a-personal-vpn)
- [8. Vulnerability reports](#8-vulnerability-reports)

## 1. Disclaimers (4 points)

### 1-1. Learning purpose, unofficial implementation

Cynovela is a learning tool for an individual to understand the concepts of AI infrastructure tools hands-on. It is not a commercial product, and it contains no source code or official implementation of what it refers to.

### 1-2. Absence of any official position

The behavior, implementation and documentation of Cynovela do not represent the official position of any company or product it refers to. Interpretations of specifications and design decisions are based on personal understanding, and may contain errors.

### 1-3. Production operation is out of scope

Business use and production operation are not assumed. No guarantee whatsoever is provided even if events such as data loss, information leakage or service outage occur.

### 1-4. Possibility of specification changes

The behavior of features, API signatures, the database schema and setting keys may change without notice.

---

## 2. Overall construction

### 2.1 Three principles of the security design

The security design of Cynovela rests on the following 3 principles.

1. **Double-defense PII (personal information) masking**
   At ingest time both raw and masked are stored, and at answer time an exit mask per role is also applied. The construction is such that if one of the two stops working, the other one still applies. See §5.

2. **Encrypted originals (vault)**
   The original body text is passed through Fernet encryption immediately before it is stored into SQLite and Chroma. The `enc:` prefix makes it idempotent and prevents double encryption. See §5.6.

3. **Three-layer prompt injection countermeasures**
   Checks are made in 3 stages: input inspection, post-retrieval inspection, and output inspection. On detection it is recorded in the audit log and blocked with HTTP 400. See §4.7.

### 2.2 Separation layers per workspace

| Layer | Separation method |
|---|---|
| User assignment | `workspace_users (workspace_id, user_id)` |
| Guardrail policy | `workspace_policies (workspace_id, policy_id)` |
| Source binding | `workspace_sources (workspace_id, source_id)` |
| Collection | References `workspaces.id` with an FK; deleted together via `ON DELETE CASCADE` |

### 2.3 Separation in ChromaDB (vector search)

At Publish time, 2 kinds of vector collections, `{cid}__raw` and `{cid}__masked`, are created per collection. When searching from chat, the destination that is read is switched according to the role of the user.

### 2.4 ACL (access control list) filter

The ACL filter operates inside the search pipeline (`rag_retrieve`) of `rag.py`.

```python
# Vector 経路での ACL
if user_role and _acl_filter_enabled():
    allowed_roles = metadata.get("allowed_roles")
    if allowed_roles and user_role not in allowed_roles:
        continue  # 除外
```

On the BM25 path as well, the metadata is completed first and then the ACL check is performed. If the role of the user is not included in `allowed_roles`, the item is excluded from the search results. Setting `features.acl_filter` to `false` allows it to be skipped, but the default is `true`.

The metadata columns that the ACL filter reads are listed in §3.4.

### 2.5 Known limitations of the separation

- ChromaDB is separated by a logical boundary (collection name), but a **physical boundary (a separate directory, etc.) is not implemented**. All collections are held in one Chroma store directory (`providers/vector_store.py`).
- The cross-boundary check for session information of workspace-A being diverted into a chat of workspace-B has a known gap.

### 2.6 Audit log

- Important operations (creation and deletion of Source / Workspace, Publish, Chat, authentication failure, PII detection, prompt injection blocking, and so on) are recorded with `_log_audit(conn, action, target, detail)`.
- **Deletion and modification through the API are forbidden** (tamper prevention). Note that this applies to the API path only; direct access to the DB file is outside what this covers (see §6-2 and §6-4).
- They are classified into `security` / `data` / `system` and so on by the category map (`_AUDIT_CATEGORY_MAP` of `core/audit.py`).

The audit log entries that a guardrail writes are described in §4.9.

### 2.7 Network control: IP allow list

In the middleware of `server.py`, the client IP is checked against the allow list.

| Startup flag | Effect |
|---|---|
| Default | No restriction (everything passes when `--allow-subnet` / `--allow-tailscale` are not specified) |
| `--lan` | LAN exposure (`host=0.0.0.0`) |
| `--allow-tailscale` | Adds the Tailscale subnet (`100.64.0.0/10`) |
| `--allow-subnet` | Adds a custom subnet (can be specified multiple times) |

Access from an IP that is not allowed returns **HTTP 403 Forbidden**.

### 2.8 Network control: restriction on the LM Studio URL

`llm_endpoint` is validated on the settings API side so that it cannot be changed to a value that points to the internal network.

### 2.9 Known limitations of the current construction

The limitations are collected in [limits.md](limits.md), so that there is one place to read them. The ones that bear on security are these, and each is written out there:

- The physical boundary of the workspace separation (§10 "Workspace separation")
- The cross-boundary check from workspace-A to workspace-B (§10)
- Detection of indirect prompt injection (§15)
- The two bugs recorded as HIGH priority — the reversed DB → Chroma order in `import_workspace`, and the race condition in `admin_cleanup_chromadb_orphans` (§10)
- Persistence of the Embedding / Reranker settings (§10)

---

## 3. Roles and permissions (RBAC)

Cynovela manages the permissions of API requests on a **role** basis. What each user can do is decided by a role, and the implementation calls a role check helper at the beginning of each API endpoint.

### 3.1 Role definitions (3 roles)

The following CHECK constraint is applied on the database side, so only these three roles can be registered.

```sql
role TEXT NOT NULL CHECK(role IN ('admin', 'curator', 'viewer'))
```

| Role | Assumed user | Main permissions |
|---|---|---|
| **admin** | System administrator | All API endpoints. User management, changing system settings, viewing audit logs, viewing the original PII (personal information) text |
| **viewer** | General user | Read operations such as RAG (Retrieval-Augmented Generation) queries and report viewing |

> The DB CHECK constraint allows `role IN ('admin', 'curator', 'viewer')` for backward compatibility, but in the current implementation `curator` (and `data-scientist` and so on) is normalized to `viewer` and has no permissions of its own. The effective roles are the two values `admin` / `viewer`.

Authentication is by username and password. One-click entry (unauthenticated login from a user card) has been completely removed. The initial password of the first user has to be changed on the first sign-in.

### 3.2 Role check helpers

`core/auth.py` provides four role check functions, and each endpoint in the router layer calls them to perform authorization (permission checking).

| Function name | What it checks | Behavior when it fails |
|---|---|---|
| `_require_admin()` | Whether the role is admin | Raises an exception (insufficient permission) |
| `_require_authenticated()` | Whether the request is authenticated (any role) | Raises an exception |
| `_require_role(roles)` | Whether the role matches one of the given roles | Raises an exception |
| `_require_admin_or_self()` | Whether the user is admin, or is the user_id in question | Raises an exception |

The role check calls are spread over **about 242 places** under the routers.

### 3.3 Main endpoints by role (admin only)

An excerpt of the routers on which `_require_admin` is applied is as follows. **13 routers** contain admin-only endpoints.

| Router | Admin-only targets | Role |
|---|---|---|
| `routers/alerts.py` | Alert operations | Management of notifications |
| `routers/auth.py` | Creating, deleting and listing users | Account management |
| `routers/files.py` | File deletion, bulk operations, changing limits | Upload management |
| `routers/catalog.py` | Catalog editing | Data catalog management |
| `routers/archived.py` | Archive lookup and restore | Organizing stored items |
| `routers/models.py` | Model settings | Selecting the LLM / embedding model |
| `routers/compliance.py` | Compliance operations | Audit and policy area |
| `routers/health.py` | Part of the health checks | Reading internal state |
| `routers/sessions.py` | Session management | Management of chat history |
| `routers/llm.py` | LLM connection settings | Switching providers |
| `routers/feedback.py` | Getting and editing feedback | Lookup of 👍👎 totals |
| `routers/guardrails.py` | PII detection history, editing forbidden topics | Management of protection rules |
| `routers/policies.py` | Editing guardrail policies | Policy matrix |

In addition, `/api/guardrails/pii-detections`, which returns the PII detection history, is fixed to **admin only** (the implementation calls `_require_admin(request)` at the beginning in `routers/guardrails.py`).

### 3.4 Access control per workspace

A workspace (Workspace, the unit in which data is stored) has an intermediate table `workspace_users (workspace_id, user_id)` for assigning users to it. This makes it possible to limit the workspaces a user can access.

In addition, a collection (Collection, the unit of a group of files) carries the following metadata.

| Column | Purpose |
|---|---|
| `access_level` | Three levels: `public` / `internal` / `confidential` |
| `allowed_roles_json` | The list of roles allowed per collection (JSON) |
| `acl_roles` | The set of roles equivalent to an ACL (access control list) |

These columns are what the ACL filter in §2.4 reads.

### 3.5 Differences in answer style by role

The role prefix in `rag.py` also switches the tone of the answer.

| Role | Policy of the prefix |
|---|---|
| admin | Provides complete information including technical details, setting values and internal structure |
| reader | An easy-to-understand explanation focused on the main points, avoiding technical terms |

How the PII in an answer differs by role is described in §5.5.

### 3.6 Limitations of the role implementation

- Authentication is only the JWT (JSON Web Token) issued by `/api/auth/login`. The simple token of the form `Bearer demo-token-{user_id}` was abolished on 2026-07-29, and is rejected with 401 even when started with `--demo`.
- Because the implementation of the role checks is **spread over about 242 places**, unifying it (for example, consolidating it into a FastAPI Depends base) is a candidate for future cleanup.
- One-click entry (unauthenticated login from a user card) has been completely removed. Entering `username` and `password` is now required.

---

## 4. Guardrails

### 4.1 How the guardrail works

A guardrail (a mechanism that detects and stops inappropriate input and output on the LLM path) works in Cynovela for the following 3 purposes.

1. **Ingest phase**: At Publish time, PII (personal information) contained in the body text of each chunk is detected, and depending on the policy one of "mask it", "exclude it from the vector DB", "only leave a log", or "let it through" is chosen.
2. **Query acceptance phase**: If there is a sign of prompt injection (an attack that overwrites the instructions) in the user's query, it is blocked immediately with a 400.
3. **Answer generation phase**: The LLM's response text is inspected for wording that would take confidential information out, and it is recorded when detected.

### 4.2 Entry points

Guardrail settings are managed through the following 3 paths.

| Path | Setting target | Operation API |
|------|----------|----------|
| Workspace policy | Defines classification x action in a policy tied to a Workspace | `/api/policies/*` (admin only) |
| Blocked topics | block / warn on strings contained in the query | `/api/guardrails/blocked-topics` (admin only) |
| Prompt injection inspection | 14 English/Japanese patterns built into the code + 4 output patterns | Fixed in the code (`routers/chat.py:55-91`) |

### 4.3 The triple of policy x classification x action

One policy (for example `pol-pii` = "PII protection policy") is expressed as JSON that defines an action per classification class (PII / Financial / HR and so on).

```json
[
  {"classifier": "PII", "action": "mask"},
  {"classifier": "Financial", "action": "exclude_from_rag"}
]
```

A policy is tied to a Workspace (the `workspace_policies` table), and is applied to Publish operations under that Workspace.

### 4.4 Categories (classification classes)

The classification classes that can be confirmed from the seed data at `db.py:855 / 861 / 867` are 3 items.

| Classification name | Meaning | Example of how it is used |
|--------|------|---------------|
| `PII` | Personal information in general (name, contact details, account number, and so on) | Targeted by all 3 seed policies `pol-pii`, `pol-strict`, `pol-log` |
| `Financial` | Financial and transaction information (credit card numbers, and so on) | Same as above |
| `HR` | Human resources information | Targeted only by `pol-strict` (`exclude_from_rag`) |

The old `classifier.py` also has definitions of 8 categories, PII / Financial / HR / Legal / Healthcare / Sales / Technical / Marketing, but that is a separate system from Smart Ingestion (document type classification at ingest time), and the seeds actually used on the guardrail side are the 3 items above.

### 4.5 Initial policies (seeds)

3 initial policies are seeded at `db.py:851-870`.

| Policy ID | Display name | Definition |
|-------------|--------|------|
| `pol-pii` | PII protection policy | PII: mask, Financial: exclude_from_rag |
| `pol-strict` | Strict management policy | PII: mask, Financial: exclude_from_rag, HR: exclude_from_rag |
| `pol-log` | Log-only policy | PII: log_only, Financial: log_only |

By default they are not tied to any workspace. You assign one when you create a workspace.

### 4.6 Action types

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

### 4.7 Prompt injection countermeasures (3-layer defense)

The following 3 stages of inspection are implemented in `routers/chat.py`.

#### 4.7.1 Input inspection (`detect_prompt_injection`)

`routers/chat.py:55-91`. Prompt injection wording contained in the query itself is detected with the following 14 English/Japanese patterns. On detection, `PROMPT_INJECTION_BLOCKED` is recorded in `audit_logs` and it is blocked immediately with HTTP 400.

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

#### 4.7.2 Retrieved result inspection (`filter_poisoned_chunks`)

`routers/chat.py:94-111`. The same pattern inspection is also performed on the body text of chunks retrieved as search results, and the relevant chunks are excluded **before** the context is assembled (`routers/chat.py:1268`).

```python
filtered_chunks, _pi_filtered_count = filter_poisoned_chunks(filtered_chunks)
```

#### 4.7.3 Output inspection (`detect_output_exfiltration`)

`routers/chat.py:114-125`. The LLM's response text is inspected for the following 4 exfiltration (information leakage) patterns, and it is recorded when detected.

```python
EXFILTRATION_PATTERNS = [
    r"\bHACKED\b",
    r"\bPWNED\b",
    r"SECRET-ALPHA-TOKEN",
    r"\[\s*SYSTEM\s+OVERRIDE\s*\]",
]
```

#### 4.7.4 Indirect attacks through documents (known limitation)

Prompt injection wording that slipped into an ingested document is inspected once by the retrieved result inspection of §4.7.2, but a **detection mechanism dedicated to indirect prompt injection** is not implemented.

#### 4.7.5 Auxiliary means: LLM judge

A mechanism is also provided at `llm_judge_pi(text)` in `utils/metadata/pii.py:263` that makes an additional decision based on an LLM judge for patterns that regular expressions cannot fully catch.

### 4.8 Placement of the system prompt

As an important design principle, the system prompt (the pre-specified operating instructions for the LLM) is placed **"after"** the retrieved content (the body text of the retrieved documents). If it is placed before, a path is created where it can be overwritten by wording such as `[SYSTEM OVERRIDE]` written inside the document body.

### 4.9 Audit logs of guardrail events (audit_logs)

Events where a guardrail fired are recorded in the `audit_logs` table. In `_AUDIT_CATEGORY_MAP` at `core/audit.py:15`, `PROMPT_INJECTION_BLOCKED` and `pii_detected` are mapped to the `security` category.

`audit_logs` cannot be deleted or modified through the API (see §2.6).

There are the following 2 aggregation endpoints (both admin only):

- `/api/guardrails/pii-detections` (GET): aggregates PII detections from `audit_logs`
- `/api/pii-detections` (GET): aggregates per document from the `chunks` table

### 4.10 How to add a custom detector

#### 4.10.1 Adding a PII regular expression

Add a tuple of `(entity_type, re.compile(pattern), mask_token)` to the list at `guardrail.py:137-153`.

```python
("CUSTOM_ID", re.compile(r"\bCUST-\d{6}\b"), "[MASKED:CUSTOMID]"),
```

The detection counts are aggregated into audit_logs and can be checked from `/api/guardrails/pii-detections`.

#### 4.10.2 Adding a guardrail category

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

#### 4.10.3 Adding a blocked topic

Post to `/api/guardrails/blocked-topics` (POST, admin only) with a pattern string, an action (`block` / `warn`), and if needed `is_regex=true`.

```json
{
  "pattern": "社外秘プロジェクトX",
  "action": "block",
  "is_regex": false
}
```

If you register it as a regular expression, it is compiled beforehand with the equivalent of `re.compile()`, and if it is invalid a 400 is returned with `INVALID_REGEX`.

#### 4.10.4 Adding a prompt injection pattern

Add a regular expression to the `INJECTION_PATTERNS` / `EXFILTRATION_PATTERNS` lists at `routers/chat.py:55-91`. Because they are built into the code, a restart is required after adding.

---

## 5. PII detection and masking

### 5.1 Design principle: put only masked text into the vector DB

The basic policy against PII (Personally Identifiable Information: personal information and confidential internal information) is that "the vector DB (ChromaDB), which is broadly exposed as a search target, in principle holds only masked text." The raw text is stored encrypted in a separate line, and can be pulled out only by the administrator role.

With this construction, the leakage paths are narrowed in situations such as the following.

- The path where a search hit gets mixed into the LLM prompt → only masked text is passed
- The path where the ChromaDB data is dumped or copied as is → masked only
- The path where the DB file is physically carried away → the raw side is already encrypted with Fernet

To achieve this, Cynovela adopts a double defense of masking at ingest time (Tier1) and masking at answer time (Tier2).

> **Abolished: ingest without masking (`collections.raw_only = 1`)** — the ingest that bypasses masking (Raw mode) was abolished on 2026-07-24. If you specify it now, it is rejected with HTTP 400 (measured 2026-08-02). Only collections created in the past with `raw_only = 1` can remain in a state without a masked layer (for details see [architecture.md](architecture.md) §3.5.1 "Abolished: `raw_only`").

### 5.2 Tier1: masking at ingest time

#### 5.2.1 Role

In the middle of Publish (the processing that loads a collection into ChromaDB), a dual-row of "raw text" and "masked text" is generated for each chunk. Both are saved in the `chunks` table in SQLite and in both ChromaDB collections.

#### 5.2.2 Implementation location

`rag.py:984-1075` (excerpt):

```python
pii_flag = 1 if pii_pat.search(chunk or "") else 0
# §段1b: マスク済本文を生成 (context prefix 付き全文を対象)
try:
    _masked_chunk, _mask_spans = _mtws_publish(chunk or "")
except Exception as _me:
    _log.warning(f"§段1b mask 失敗 doc_id={doc_id}: {_me}")
    _masked_chunk, _mask_spans = (chunk or ""), []
# 項目④: 検出種別 × 件数のみを集計（値は捨てる）
...
_masked_doc_id = f"{doc_id}__masked"
# §段1b: masked 本文に対する PII 再評価 (マスクが十分なら 0)
_masked_pii_flag = 1 if pii_pat.search(_masked_chunk or "") else 0
...
_meta_raw["tier"] = "raw"
...
_meta_masked["tier"] = "masked"
all_docs_masked.append(_masked_chunk or "")
```

`_mtws_publish` is an alias of `guardrail.mask_text_with_spans`, and applies a regular-expression-based mask to each chunk.

#### 5.2.3 Storage destinations

| Storage destination | raw tier | masked tier |
|--------|----------|-------------|
| SQLite `chunks` table | The `doc_id` row (`tier='raw'`) | The `doc_id + '__masked'` row (`tier='masked'`) |
| ChromaDB | The `{collection_id}__raw` collection | The `{collection_id}__masked` collection |
| Encryption | Encrypted with Fernet (`enc:` prefix) | No encryption (to secure search performance) |

#### 5.2.4 Behavior on failure

Even if an exception occurs in the mask processing, Publish is not stopped: it is written to the log with `_log.warning`, and then the raw text is saved on the masked side as well. This is a design choice to avoid the risk that "if ingest stops, the business stops."

### 5.3 Tier2: masking at answer time

#### 5.3.1 Role

An additional exit mask is applied to the answer text generated by the LLM, according to the user's role. This way, if raw text gets mixed into the context for some reason, the exit mask is still applied for users other than admin.

#### 5.3.2 Implementation location

`routers/chat.py:128-162`:

```python
def _mask_for_viewer(text: str, user: dict | None) -> str:
    """M1 (設計正本準拠): 利用者の保管庫 tier (raw/masked) に応じて
    LLM 生成出力に出口マスクを適用する。

    判定は rag.tier_for_role() に一元化:
      - tier_for_role(role) == "raw"    → 素通し (= admin・素側保管庫の利用者)
      - tier_for_role(role) == "masked" → マスク (= curator/viewer/legacy/未設定・伏せ側保管庫)
    """
    if not text or not user:
        return text
    try:
        from rag import tier_for_role
        if tier_for_role(user.get("role") or "") == "raw":
            return text
    except Exception:
        pass
    try:
        from guardrail import mask_text_with_spans
        masked, _spans = mask_text_with_spans(text)
        return masked
    except Exception:
        return text
```

`_mask_for_viewer` is called at 4 places in the chat path (normal response / Compare A / Compare B / SSE path) (`routers/chat.py:653 / 655 / 681 / 1814`). For anything other than admin, the exit mask is applied by force.

### 5.4 Dispatch by role

`rag.py:1726-1737`:

```python
def tier_for_role(role: str) -> str:
    """§段2: ロールに応じて保管庫の tier を決める。
    admin → 'raw'   (生本文を保管する管理者保管庫を引く)
    その他 → 'masked' (マスク済本文の一般保管庫を引く)
    """
    return "raw" if (role or "").strip() == "admin" else "masked"
```

`tier_for_role` decides both which ChromaDB collection is queried (`{cid}__raw` or `{cid}__masked`) and whether the output goes through the exit mask or passes through, so it works as a double defense.

- **admin** → refers to the collection on the `raw` side, and the exit masking is passed through in the answer display (the original text is shown as it is)
- **viewer / not specified** (`curator` and so on are normalized to viewer) → refers to the collection on the `masked` side, and the exit masking is also applied (the text stays masked when displayed)

> However, when an external (non-local) LLM is used, crag-egress-guard prevents the preliminary reading of raw (context_preview) from being sent outside even for admin (CRAG is skipped). The admin pass-through described above assumes "answer display with a local LLM"; it does not mean "admin = the original text is always passed to an external LLM".

### 5.5 How it looks by role

| Role | Vault queried | Exit mask | What is visible as a result |
|--------|--------------|------------|----------------------|
| `admin` | raw tier (raw text with the encryption decrypted) | Pass through | Raw text |
| `curator` | masked tier | Applied | Masked text |
| `viewer` | masked tier | Applied | Masked text |
| Unauthenticated / unset | masked tier | Applied | Masked text |

Because of this, even if the role ends up empty due to a configuration mistake, the dispatch falls to the masked tier.

### 5.6 Fernet encryption (vault)

#### 5.6.1 Role and design policy

Immediately before saving the raw tier text into SQLite and ChromaDB, it is encrypted with Fernet (one of the symmetric-key encryption schemes, authenticated AES-128-CBC + HMAC) and saved with the prefix `enc:`. The implementation is idempotent (a string that already starts with `enc:` is not re-encrypted), which avoids double encryption.

- **Target**: the original body text (raw tier only). The masked tier passes through as-is (double defense is unnecessary, and this keeps search performance)
- **Interface**: goes through `enc_raw()` / `dec_raw()` of `vault_enc.py`
- **Idempotency**: the `enc:` prefix is used as a marker to prevent double encryption
- **Key**: uses the Fernet key in the environment variable `CYNOVELA_SECRET_KEY`

#### 5.6.2 Implementation

- **Key management**: `Fernet(_KEY)` is initialized at `config.py:62`. The key is passed with the `CYNOVELA_SECRET_KEY` environment variable. Setting this environment variable explicitly is recommended.

```python
_fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)
```

- **Interface**: `enc_raw(text)` / `dec_raw(text)` in `vault_enc.py` provide thin wrappers.

```python
ENC_PREFIX = "enc:"

def enc_raw(text: str | None) -> str:
    """raw 本文を暗号化形式に揃える (冪等)。
    - 既に "enc:" 始まり: 二重暗号化しない
    - それ以外: "enc:" + config.encrypt(text) を返す """

def dec_raw(text: str | None) -> str:
    """暗号化形式なら復号、それ以外 (masked / 旧平文) はそのまま素通し (冪等)。"""
```

#### 5.6.3 Where it is applied

| Path | Location | Target |
|------|----------|------|
| When loading into Chroma | `rag.py:1285` | Applies `enc_raw` in bulk to the `documents` array of the raw tier |
| When saving SQLite `chunks` | `rag.py:1393` | `enc_raw` on the `content` of the raw tier rows |
| When saving SQLite `parent_chunks` | `rag.py:1131` | `enc_raw` on the raw tier of the parent |

The masked tier is not encrypted. This is to secure search performance (embedding computation and full-text search). Because the raw tier goes into ChromaDB's `documents` as an encrypted byte string, it has to be decrypted with `dec_raw` when it is pulled out.

#### 5.6.4 Migration of existing data

`tools/vault_enc_migrate.py` is provided as a tool that converts existing SQLite / ChromaDB data to the `enc:` form in bulk.

### 5.7 All PII categories

There are 2 lines of PII detection.

#### 5.7.1 Primary line: `guardrail.py` (regular-expression based)

8 kinds are defined at `guardrail.py:137-153`.

| entity_type | Detection target | Token after masking |
|-------------|----------|------------------|
| `URL` | `https?://...` | `[MASKED:URL]` |
| `EMAIL` | Email address (`\b[\w.+-]+@[\w.-]+\.\w+\b`) | `[MASKED:EMAIL]` |
| `PHONE_JP` | Mobile number (070/080/090) | `[MASKED:PHONE]` |
| `PHONE_LAND` | Landline phone number | `[MASKED:PHONE]` |
| `CREDIT` | Credit card number (4-4-4-4 form) | `[MASKED:CREDIT]` |
| `MYNUMBER` | My Number (12 digits) | `[MASKED:MYNUM]` |
| `PASSPORT` | Passport number (2 letters + 7 digits) | `[MASKED:PASSPORT]` |
| `IPV4` | IPv4 address | `[MASKED:IP]` |

#### 5.7.2 Secondary line: `utils/metadata/pii.py` (presidio + GiNZA fallback)

If presidio (Microsoft Presidio: a PII detection and anonymization library) is available it is used; if not, it switches to the regular-expression fallback. Both Japanese and English are supported. Japanese NER is done with GiNZA (a spaCy-based Japanese NLP library) for named entity extraction.

Additional categories that are detected:

| entity_type | Description |
|-------------|------|
| `EMAIL` | Email address (regular expression) |
| `PHONE_JP` | Japanese phone number |
| `PHONE_INTL` | International phone number |
| `IP_ADDRESS` | IP address |
| `MY_NUMBER` | My Number |
| `CREDIT_CARD` | Credit card number |
| `INTERNAL_URL` | Internal URL |
| `EMAIL_ADDRESS` | Email detected by presidio |
| `PHONE_NUMBER` | Phone number detected by presidio |
| `DATE_TIME` | Date and time detected by presidio |
| `PERSON_JP` | Personal name detected by GiNZA (Japanese) |
| `ORG_JP` | Organization name detected by GiNZA (Japanese) |
| `LOC_JP` | Place name detected by GiNZA (Japanese) |
| `ADDRESS_JP` | Japanese address rule |

`{CREDIT_CARD, MY_NUMBER, SSN, PASSPORT, IBAN_CODE}` are defined as `HIGH_RISK_TYPES` and are weighted heavily in the calculation of the sensitivity score (0 to 100).

#### 5.7.3 Targets of the policy matrix

At `routers/policies.py:159`, the PII types selectable from a Workspace policy are narrowed to the following 6 kinds.

```python
pii_types = ["EMAIL", "PHONE_JP", "PHONE_LAND", "CREDIT", "MYNUMBER", "IPV4"]
```

URL and PASSPORT are detected, but are not among the choices in the policy UI.

### 5.8 Differences between `pii_mode` values

#### 5.8.1 How to set it

Set it with the `pii_mode` key in `cynovela.yaml`. The CLI argument (the old `--pii-mode`) has been abolished. If you want to change it at runtime, you can switch it with `/api/settings/pii-mode` (PUT) (admin only).

#### 5.8.2 Behavior of the 3 modes

| Value | Detection method | Speed | Accuracy | Main use |
|----|----------|------|------|--------|
| `lite` | Regular expressions only | Fast | Low to medium | Bulk ingest, lightweight environments |
| `standard` (default) | Regular expressions + GiNZA NER | Medium | Medium to high | The default value, recommended |
| `quality` | Regular expressions + GiNZA NER + detailed filtering | Slow | High | Research and development, close inspection of sensitive information |

If an invalid value is given, it is reset to `standard` (`server.py:3135-3137`).

A log like the following appears at startup:

```
[Cynovela] PII detection mode: standard (from cynovela.yaml)
```

### 5.9 Aggregation of detection counts

PII detections are aggregated through the following 2 lines.

- **`/api/guardrails/pii-detections` (GET)**: aggregates from the `audit_logs` table (admin only)
- **`/api/pii-detections` (GET)**: aggregates per document from the `chunks` table (admin only)

Both require the admin role, and `_require_admin(request)` is called at the head of the endpoint.

### 5.10 Migration from the old implementation

The old `utils/pii_detector.py` was deleted, and the implementation was consolidated into `utils/metadata/pii.py`. `llm_judge_pi(text)` in the new implementation is a function that performs an additional judgment based on an LLM judge.

---

## 6. Ways of use that are not recommended

The following ways of use are either not blocked by design or the blocking is incomplete, so do not do them.

### 6-1. Publishing directly to the internet

Opening the port directly to the internet side while bound to `0.0.0.0` with `--lan` is strictly forbidden. The reasons are as follows.

- It is not made HTTPS (plain text communication)
- The IP allow list places no restriction by default; everything passes when `--allow-subnet` / `--allow-tailscale` are not specified (§2.7)
- The role checks are spread over about 242 call sites under the routers and are not consolidated into one place (§3.6)
- File upload restrictions are loose

### 6-2. Production operation with confidential documents

Feeding in real confidential documents as they are is not recommended.

- Fernet encryption of the raw body text is in operation, but key management (`CYNOVELA_SECRET_KEY`) assumes personal operation
- Tamper prevention of audit_logs is only via the API, and direct DB access is out of scope of the protection
- Backup and restore are provided (`/api/admin/backup` and `/api/admin/backups/{name}/restore`, plus the manual procedure in `docs/operations.md`), but running them and managing where the copies are kept is left to the operator

### 6-3. LAN sharing with users you cannot trust

When sharing on a LAN, the premise is that all users on the network can be trusted. It is recommended to narrow the connection sources strictly with `--allow-subnet` and use it only among members you can trust.

### 6-4. Editing the audit log directly in the DB

Changing or deleting rows of the `audit_logs` table via the API is prohibited. Direct DB editing (with the `sqlite3` command etc.) also leads to breaking consistency, so avoid it.

### 6-5. Forcing multiple simultaneous Publishes

Running multiple Publishes for the same Collection at the same time is prevented with `collection_locks`, but forcibly releasing the DB lock and running them in parallel leads to breaking data consistency.

### 6-6. Checking quality in mock mode

Always run RAG quality check tests in an environment where a real LLM (such as LM Studio) is running. The `--mock` option that used to exist (a specification for running without calling an LLM) has been removed.

### 6-7. Adding new `INSERT OR REPLACE` statements

`INSERT OR REPLACE` fires the SQLite FK CASCADE against your intention, so it is forbidden in the codebase. For updating an existing row, use `INSERT ... ON CONFLICT(id) DO UPDATE SET ...`.

---

## 7. Recommended operation configurations

One of the following configurations is recommended.

### 7-1. Fully local operation (the narrowest exposure)

```bash
python server.py --demo --local-only
```

- Adding `--local-only` makes the bind `127.0.0.1` (the default is `0.0.0.0`)
- For verification, demos and tutorials

### 7-2. Local LLM operation

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

- Start LM Studio or Ollama on the same machine
- No network exposure
- For personal learning and experiments

### 7-3. Operation via a personal VPN

```bash
python server.py --lan --allow-tailscale
```

- Allows only via Tailscale
- Access only between personal devices you can trust
- For personal verification while away from home

---

## 8. Vulnerability reports

Cynovela is a personal project, and has no formal vulnerability report contact. If you report a problem you found on GitHub Issues or similar, handling it will be considered as far as possible.

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela は、社内ドキュメントを RAG（検索拡張生成）で扱う際に必要となる **ガードレール（保護ルール）** と **アクセス制御** を、複数層に分けて実装しています。本ドキュメントでは、導入する人が「いまの作りで何が扱われていて、何が扱われていないか」を判断できるように、現在の作りを記述します。

Cynovela は学習用ツールであり、本番運用のセキュリティ要件を満たすものではありません。Cynovela 全体の既知の制限は `docs/limits.md` にまとめています。

---

**目次**

- [1. 免責（4 点）](#1-免責4-点)
  - [1-1. 学習目的・非公式実装](#1-1-学習目的非公式実装)
  - [1-2. 公式見解の不在](#1-2-公式見解の不在)
  - [1-3. 本番運用は想定外](#1-3-本番運用は想定外)
  - [1-4. 仕様変更の可能性](#1-4-仕様変更の可能性)
- [2. 全体の作り](#2-全体の作り)
  - [2.1 セキュリティ設計 3 原則](#21-セキュリティ設計-3-原則)
  - [2.2 ワークスペース単位の分離レイヤー](#22-ワークスペース単位の分離レイヤー)
  - [2.3 ChromaDB（ベクター検索）の分離](#23-chromadbベクター検索の分離)
  - [2.4 ACL（アクセス制御リスト）フィルター](#24-aclアクセス制御リストフィルター)
  - [2.5 分離の既知制限](#25-分離の既知制限)
  - [2.6 監査ログ](#26-監査ログ)
  - [2.7 ネットワーク制御：IP アローリスト](#27-ネットワーク制御ip-アローリスト)
  - [2.8 ネットワーク制御：LM Studio URL の制限](#28-ネットワーク制御lm-studio-url-の制限)
  - [2.9 現在の作りの既知の制限](#29-現在の作りの既知の制限)
- [3. 役割と権限（RBAC）](#3-役割と権限rbac)
  - [3.1 ロール定義（3 ロール）](#31-ロール定義3-ロール)
  - [3.2 ロール検査ヘルパー](#32-ロール検査ヘルパー)
  - [3.3 ロール別 主要エンドポイント（admin 限定）](#33-ロール別-主要エンドポイントadmin-限定)
  - [3.4 ワークスペース単位のアクセス制御](#34-ワークスペース単位のアクセス制御)
  - [3.5 ロール別 回答スタイルの違い](#35-ロール別-回答スタイルの違い)
  - [3.6 ロール実装の制限](#36-ロール実装の制限)
- [4. ガードレール](#4-ガードレール)
  - [4.1 ガードレールの仕組み](#41-ガードレールの仕組み)
  - [4.2 入口](#42-入口)
  - [4.3 ポリシー × 分類 × アクションの三項](#43-ポリシー-分類-アクションの三項)
  - [4.4 カテゴリ（分類クラス）](#44-カテゴリ分類クラス)
  - [4.5 初期ポリシー（シード）](#45-初期ポリシーシード)
  - [4.6 アクション種別](#46-アクション種別)
  - [4.7 プロンプトインジェクション対策（3 層防御）](#47-プロンプトインジェクション対策3-層防御)
  - [4.8 システムプロンプトの配置](#48-システムプロンプトの配置)
  - [4.9 ガードレールの監査ログ（audit_logs）](#49-ガードレールの監査ログaudit_logs)
  - [4.10 カスタム検出器の追加方法](#410-カスタム検出器の追加方法)
- [5. PII の検出とマスキング](#5-pii-の検出とマスキング)
  - [5.1 設計思想：ベクター DB にはマスク済みのみ入れる](#51-設計思想ベクター-db-にはマスク済みのみ入れる)
  - [5.2 Tier1：取込時マスキング](#52-tier1取込時マスキング)
  - [5.3 Tier2：回答時マスキング](#53-tier2回答時マスキング)
  - [5.4 ロール別の振り分け](#54-ロール別の振り分け)
  - [5.5 ロール別の見え方](#55-ロール別の見え方)
  - [5.6 Fernet 暗号化（vault）](#56-fernet-暗号化vault)
  - [5.7 PII カテゴリ全件](#57-pii-カテゴリ全件)
  - [5.8 `pii_mode` の違い](#58-pii_mode-の違い)
  - [5.9 検出件数の集計](#59-検出件数の集計)
  - [5.10 旧実装からの移行](#510-旧実装からの移行)
- [6. 推奨しない使用方法](#6-推奨しない使用方法)
  - [6-1. インターネットへの直接公開](#6-1-インターネットへの直接公開)
  - [6-2. 機密文書での本番運用](#6-2-機密文書での本番運用)
  - [6-3. 信頼できないユーザーへの LAN 共有](#6-3-信頼できないユーザーへの-lan-共有)
  - [6-4. 監査ログの DB 直接編集](#6-4-監査ログの-db-直接編集)
  - [6-5. 同時複数 Publish の強制実行](#6-5-同時複数-publish-の強制実行)
  - [6-6. モックモードでの品質確認](#6-6-モックモードでの品質確認)
  - [6-7. `INSERT OR REPLACE` 文の新規追加](#6-7-insert-or-replace-文の新規追加)
- [7. 推奨運用構成](#7-推奨運用構成)
  - [7-1. 完全ローカル運用（露出が最も狭い構成）](#7-1-完全ローカル運用露出が最も狭い構成)
  - [7-2. ローカル LLM 運用](#7-2-ローカル-llm-運用)
  - [7-3. 個人 VPN 経由運用](#7-3-個人-vpn-経由運用)
- [8. 脆弱性報告](#8-脆弱性報告)

## 1. 免責（4 点）

### 1-1. 学習目的・非公式実装

Cynovela は個人が手を動かして AI 基盤ツールのコンセプトを理解するための学習用ツールです。商用製品ではなく、参照元のソースコード・公式実装も一切含みません。

### 1-2. 公式見解の不在

Cynovela の挙動・実装・ドキュメントは、参照元のいかなる会社・製品の公式見解も代表しません。仕様の解釈や設計判断は個人の理解に基づくものであり、誤りを含む可能性があります。

### 1-3. 本番運用は想定外

業務利用・本番運用は想定していません。データ損失・情報漏洩・サービス停止などの事象が発生してもいかなる保証も提供しません。

### 1-4. 仕様変更の可能性

機能の挙動・API シグネチャ・データベーススキーマ・設定キーは予告なく変更されることがあります。

---

## 2. 全体の作り

### 2.1 セキュリティ設計 3 原則

Cynovela のセキュリティ設計は、次の 3 原則に立脚しています。

1. **二重防御の PII（個人情報）マスキング**
   取込時に raw / masked を両方保存し、回答時にロール別の出口マスクも適用します。どちらか一方が機能しなくなっても、もう一方が掛かる作りです。§5 を参照してください。

2. **暗号化された原本（vault）**
   原本本文は SQLite と Chroma に保存する直前で Fernet 暗号化を通します。`enc:` プレフィックスで冪等にし、二重暗号化を防ぎます。§5.6 を参照してください。

3. **3 層のプロンプトインジェクション対策**
   入力検査 → retrieval 後検査 → 出力検査の 3 段階でチェックします。検出時は監査ログに記録し、HTTP 400 で遮断します。§4.7 を参照してください。

### 2.2 ワークスペース単位の分離レイヤー

| レイヤー | 分離方式 |
|---|---|
| ユーザー割り当て | `workspace_users (workspace_id, user_id)` |
| ガードレールポリシー | `workspace_policies (workspace_id, policy_id)` |
| Source 紐付け | `workspace_sources (workspace_id, source_id)` |
| Collection | `workspaces.id` を FK で参照、`ON DELETE CASCADE` で連動削除 |

### 2.3 ChromaDB（ベクター検索）の分離

Publish 時にコレクション単位で `{cid}__raw` と `{cid}__masked` の 2 種類のベクターコレクションを作ります。チャットの検索時には、利用者のロールに応じて読みに行く先を切り替えます。

### 2.4 ACL（アクセス制御リスト）フィルター

`rag.py` の検索パイプライン（`rag_retrieve`）の中で ACL フィルターが動作します。

```python
# Vector 経路での ACL
if user_role and _acl_filter_enabled():
    allowed_roles = metadata.get("allowed_roles")
    if allowed_roles and user_role not in allowed_roles:
        continue  # 除外
```

BM25 経路でも同様にメタデータを補完してから ACL チェックを行います。利用者のロールが `allowed_roles` に含まれない場合は検索結果から除外されます。`features.acl_filter` を `false` にするとスキップ可能ですが、既定は `true` です。

ACL フィルターが読むメタデータのカラムは §3.4 に記載しています。

### 2.5 分離の既知制限

- ChromaDB は論理境界（collection 名）で分離していますが、**物理境界（別ディレクトリ等）は未実装** です。すべての collection は 1 つの Chroma の保管先ディレクトリに入ります（`providers/vector_store.py`）。
- workspace-A のセッション情報が workspace-B のチャットに流用される越境チェックには既知の漏れがあります。

### 2.6 監査ログ

- 重要操作（Source / Workspace の作成・削除、Publish、Chat、認証失敗、PII 検出、プロンプトインジェクション遮断など）は `_log_audit(conn, action, target, detail)` で記録されます。
- **API 経由での削除・変更は禁止** されています（改ざん防止）。これは API 経路についての記述であり、DB ファイルへの直接アクセスは対象外です（§6-2・§6-4 を参照）。
- カテゴリマップ（`core/audit.py` の `_AUDIT_CATEGORY_MAP`）で `security` / `data` / `system` などに分類されます。

ガードレールが書く監査ログのエントリは §4.9 に記載しています。

### 2.7 ネットワーク制御：IP アローリスト

`server.py` のミドルウェアで、クライアント IP を許可リストと照合します。

| 起動フラグ | 効果 |
|---|---|
| 既定 | 制限なし（`--allow-subnet` / `--allow-tailscale` 未指定時は全通過） |
| `--lan` | LAN 公開（`host=0.0.0.0`） |
| `--allow-tailscale` | Tailscale サブネット（`100.64.0.0/10`）を追加 |
| `--allow-subnet` | カスタムサブネットを追加（複数指定可） |

許可外 IP からのアクセスは **HTTP 403 Forbidden** を返します。

### 2.8 ネットワーク制御：LM Studio URL の制限

`llm_endpoint` は内部ネットワークを指す値に変更できないように、設定 API 側でバリデーションされます。

### 2.9 現在の作りの既知の制限

制限は1か所で読めるように [limits.md](limits.md) へまとめてあります。セキュリティに関わるものは次のとおりで、それぞれ向こうに書き出してあります。

- workspace の分離の物理境界（§10「workspace の分離」）
- workspace-A から workspace-B への越境チェック（§10）
- 間接プロンプトインジェクションの検出（§15）
- HIGH 優先度として記録されている 2 つのバグ — `import_workspace` の DB → Chroma 順序逆転、`admin_cleanup_chromadb_orphans` の競合状態（§10）
- Embedding / Reranker 設定の永続化（§10）

---

## 3. 役割と権限（RBAC）

Cynovela は、API リクエストの権限管理を **ロール（役割）ベース** で行います。利用者ごとに「何ができるか」をロールで決め、各 API エンドポイントの先頭でロール検査ヘルパーを呼ぶ実装方式を取っています。

### 3.1 ロール定義（3 ロール）

データベース側で次の CHECK 制約が掛かっており、登録できるロールはこの 3 種類のみです。

```sql
role TEXT NOT NULL CHECK(role IN ('admin', 'curator', 'viewer'))
```

| ロール | 想定する利用者像 | 主な権限 |
|---|---|---|
| **admin** | システム管理者 | API 全エンドポイント。ユーザー管理、システム設定変更、監査ログ閲覧、PII（個人情報）原本の閲覧 |
| **viewer** | 一般利用者 | RAG（検索拡張生成）の問い合わせ、レポート閲覧などの読み取り操作 |

> DB の CHECK 制約は後方互換のため `role IN ('admin', 'curator', 'viewer')` を許容しますが、現行実装では `curator`（および `data-scientist` 等）は `viewer` に正規化され、固有の権限はありません。実効ロールは `admin` / `viewer` の 2 値です。

認証は username と password で行います。ワンクリック入室（ユーザーカードからの未認証ログイン）は完全撤去済みです。最初の利用者の初期パスワードは、初回のサインインで変更を求められます。

### 3.2 ロール検査ヘルパー

`core/auth.py` に 4 種類のロール検査関数を用意しており、ルーター層の各エンドポイントでこれらを呼び出して認可（権限チェック）を行います。

| 関数名 | 検査内容 | 不合格時の挙動 |
|---|---|---|
| `_require_admin()` | role が admin か | 例外送出（権限不足） |
| `_require_authenticated()` | 認証済みか（ロール不問） | 例外送出 |
| `_require_role(roles)` | 指定ロールのいずれかに合致するか | 例外送出 |
| `_require_admin_or_self()` | admin か、または当該 user_id 本人か | 例外送出 |

ロール検査の呼び出しはルーター配下に **約 242 箇所** 分散しています。

### 3.3 ロール別 主要エンドポイント（admin 限定）

`_require_admin` が掛けられているルーターを抜粋すると、次のとおりです。**13 個のルーター** に admin 限定のエンドポイントが含まれています。

| ルーター | admin 限定の対象 | 役割 |
|---|---|---|
| `routers/alerts.py` | アラート操作 | 通知系の管理 |
| `routers/auth.py` | ユーザー作成・削除・一覧 | アカウント管理 |
| `routers/files.py` | ファイル削除・一括操作・上限変更 | アップロード管理 |
| `routers/catalog.py` | カタログ編集系 | データカタログ管理 |
| `routers/archived.py` | アーカイブ照会・復元 | 保管対象の整理 |
| `routers/models.py` | モデル設定 | LLM / Embedding モデル選択 |
| `routers/compliance.py` | コンプライアンス操作 | 監査・ポリシー周辺 |
| `routers/health.py` | 一部の健全性確認 | 内部状態の参照 |
| `routers/sessions.py` | セッション管理 | チャット履歴の管理 |
| `routers/llm.py` | LLM 接続設定 | プロバイダー切替 |
| `routers/feedback.py` | フィードバック取得・編集 | 👍👎 集計の照会 |
| `routers/guardrails.py` | PII 検出履歴・禁止トピック編集 | 保護ルールの管理 |
| `routers/policies.py` | ガードレールポリシー編集 | ポリシーマトリクス |

加えて、PII 検出履歴を返す `/api/guardrails/pii-detections` は **admin 限定** に固定されています（`routers/guardrails.py` の `_require_admin(request)` を冒頭で呼ぶ実装）。

### 3.4 ワークスペース単位のアクセス制御

ワークスペース（Workspace、データの保管単位）には、利用者を割り当てるための中間テーブル `workspace_users (workspace_id, user_id)` が存在します。これにより、利用者がアクセスできるワークスペースを限定できます。

加えて、コレクション（Collection、ファイル群の単位）には次のメタデータが付きます。

| カラム | 用途 |
|---|---|
| `access_level` | `public` / `internal` / `confidential` の 3 段階 |
| `allowed_roles_json` | コレクション単位で許可するロールの一覧（JSON） |
| `acl_roles` | ACL（アクセス制御リスト）相当のロール集合 |

§2.4 の ACL フィルターが読むのは、これらのカラムです。

### 3.5 ロール別 回答スタイルの違い

`rag.py` のロール接頭辞で、回答のトーンも切り替えます。

| ロール | 接頭辞の方針 |
|---|---|
| admin | 技術的な詳細・設定値・内部構造を含む完全な情報を提供 |
| reader | 要点を絞ったわかりやすい説明、専門用語は避ける |

回答中の PII がロールでどう変わるかは §5.5 に記載しています。

### 3.6 ロール実装の制限

- 認証は `/api/auth/login` が発行する JWT（JSON Web Token）のみです。`Bearer demo-token-{user_id}` 形式の簡易トークンは 2026-07-29 に廃止し、`--demo` 起動でも 401 で拒否します。
- ロール検査の実装は **約 242 箇所に分散** しているため、共通化（例: FastAPI Depends ベースへの統合）は今後の整理候補です。
- ワンクリック入室（ユーザーカードからの未認証ログイン）は完全撤去済みです。`username` と `password` の入力が必須となっています。

---

## 4. ガードレール

### 4.1 ガードレールの仕組み

ガードレール（guardrail：LLM 経路で不適切な入力・出力を検出して止める仕組み）は、Cynovela において次の 3 つの目的で機能します。

1. **取込フェーズ**: Publish のときに各 chunk の本文に含まれる PII（個人情報）を検出し、ポリシーに応じて「マスクする」「ベクター DB から除外する」「ログだけ残す」「通す」のいずれかを選びます。
2. **クエリ受付フェーズ**: ユーザのクエリにプロンプトインジェクション（指示の上書き攻撃）の兆候があれば即座に 400 で遮断します。
3. **回答生成フェーズ**: LLM の応答テキストから機密情報持ち出し文言を検査し、検出時には記録します。

### 4.2 入口

ガードレールの設定は次の 3 経路で管理されます。

| 経路 | 設定対象 | 操作 API |
|------|----------|----------|
| Workspace ポリシー | Workspace に紐付くポリシーで分類×アクションを定義 | `/api/policies/*`（admin 限定） |
| 禁止トピック | クエリに含まれた文字列を block / warn | `/api/guardrails/blocked-topics`（admin 限定） |
| プロンプトインジェクション検査 | コード組み込みの英日 14 パターン + 出力 4 パターン | コード固定（`routers/chat.py:55-91`） |

### 4.3 ポリシー × 分類 × アクションの三項

1 つのポリシー（例: `pol-pii` = 「PII 保護ポリシー」）は、分類クラス（PII / Financial / HR など）ごとにアクションを定めた JSON で表現されます。

```json
[
  {"classifier": "PII", "action": "mask"},
  {"classifier": "Financial", "action": "exclude_from_rag"}
]
```

ポリシーは Workspace に紐付き（`workspace_policies` テーブル）、その Workspace 配下の Publish に対して適用されます。

### 4.4 カテゴリ（分類クラス）

`db.py:855 / 861 / 867` のシードデータから確認できる分類クラスは 3 件です。

| 分類名 | 意味 | 使われ方の例 |
|--------|------|---------------|
| `PII` | 個人情報全般（氏名・連絡先・口座番号など） | `pol-pii`・`pol-strict`・`pol-log` の全 3 シードポリシーで対象 |
| `Financial` | 財務・取引情報（クレジットカード番号等） | 同上 |
| `HR` | 人事情報 | `pol-strict` のみで対象（`exclude_from_rag`） |

旧 `classifier.py` には PII / Financial / HR / Legal / Healthcare / Sales / Technical / Marketing の 8 カテゴリ定義もありますが、これは Smart Ingestion（取込時の文書種別分類）とは別系統で、ガードレール側で実際に使われているシードは上記 3 件です。

### 4.5 初期ポリシー（シード）

`db.py:851-870` で 3 件の初期ポリシーがシードされます。

| ポリシー ID | 表示名 | 定義 |
|-------------|--------|------|
| `pol-pii` | PII 保護ポリシー | PII: mask, Financial: exclude_from_rag |
| `pol-strict` | 厳格管理ポリシー | PII: mask, Financial: exclude_from_rag, HR: exclude_from_rag |
| `pol-log` | ログのみポリシー | PII: log_only, Financial: log_only |

既定ではどのワークスペースにも紐付いていません。ワークスペースを作成するときに割り当てて使います。

### 4.6 アクション種別

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

### 4.7 プロンプトインジェクション対策（3 層防御）

`routers/chat.py` には次の 3 段階の検査が実装されています。

#### 4.7.1 入力検査（`detect_prompt_injection`）

`routers/chat.py:55-91`。クエリ自体に含まれるプロンプトインジェクション文言を次の英日 14 パターンで検出します。検出時は `audit_logs` に `PROMPT_INJECTION_BLOCKED` を記録し、HTTP 400 で即遮断します。

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

#### 4.7.2 取得結果検査（`filter_poisoned_chunks`）

`routers/chat.py:94-111`。検索結果として取得した chunk 本文に対しても同じパターン検査を行い、context を組み立てる **前** に該当 chunk を除外します（`routers/chat.py:1268`）。

```python
filtered_chunks, _pi_filtered_count = filter_poisoned_chunks(filtered_chunks)
```

#### 4.7.3 出力検査（`detect_output_exfiltration`）

`routers/chat.py:114-125`。LLM の応答テキストから次の exfiltration（情報漏えい）系 4 パターンを検査し、検出時に記録します。

```python
EXFILTRATION_PATTERNS = [
    r"\bHACKED\b",
    r"\bPWNED\b",
    r"SECRET-ALPHA-TOKEN",
    r"\[\s*SYSTEM\s+OVERRIDE\s*\]",
]
```

#### 4.7.4 ドキュメント経由の間接攻撃（既知制限）

取り込んだドキュメントに紛れ込んだプロンプトインジェクション文言は、§4.7.2 の取得結果検査で 1 段検査していますが、**間接プロンプトインジェクション専用の検出機構** はありません。

#### 4.7.5 補助手段：LLM judge

`utils/metadata/pii.py:263` の `llm_judge_pi(text)` で、正規表現では拾いきれないパターンを LLM judge ベースで追加判定する機構も用意されています。

### 4.8 システムプロンプトの配置

設計上の重要原則として、システムプロンプト（事前指定された LLM の動作指示）は retrieved content（取得した文書本文）の **「後」** に配置します。前に置くとドキュメント本文の中に書かれた `[SYSTEM OVERRIDE]` などの文言で上書きされる経路ができてしまうためです。

### 4.9 ガードレールの監査ログ（audit_logs）

ガードレールが発火したイベントは `audit_logs` テーブルに記録されます。`core/audit.py:15` の `_AUDIT_CATEGORY_MAP` で `PROMPT_INJECTION_BLOCKED` と `pii_detected` は `security` カテゴリにマップされます。

`audit_logs` は API 経由での削除・変更ができないようになっています（§2.6 を参照）。

集計エンドポイントは次の 2 系統です（いずれも admin 限定）：

- `/api/guardrails/pii-detections`（GET）: `audit_logs` から PII 検出を集計
- `/api/pii-detections`（GET）: `chunks` テーブルからドキュメント単位で集計

### 4.10 カスタム検出器の追加方法

#### 4.10.1 PII 正規表現の追加

`guardrail.py:137-153` のリストに `(entity_type, re.compile(pattern), mask_token)` のタプルを追加します。

```python
("CUSTOM_ID", re.compile(r"\bCUST-\d{6}\b"), "[MASKED:CUSTOMID]"),
```

検出件数は audit_logs に集計され、`/api/guardrails/pii-detections` から確認できます。

#### 4.10.2 ガードレールカテゴリの追加

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

#### 4.10.3 禁止トピックの追加

`/api/guardrails/blocked-topics`（POST、admin 限定）にパターン文字列とアクション（`block` / `warn`）、必要なら `is_regex=true` を付けて投げます。

```json
{
  "pattern": "社外秘プロジェクトX",
  "action": "block",
  "is_regex": false
}
```

正規表現として登録する場合は事前に `re.compile()` 相当でコンパイルされ、無効なら `INVALID_REGEX` で 400 が返ります。

#### 4.10.4 プロンプトインジェクションパターンの追加

`routers/chat.py:55-91` の `INJECTION_PATTERNS` / `EXFILTRATION_PATTERNS` リストに正規表現を追加します。コード組み込みのため、追加後は再起動が必要です。

---

## 5. PII の検出とマスキング

### 5.1 設計思想：ベクター DB にはマスク済みのみ入れる

PII（Personally Identifiable Information：個人情報・社外秘情報）対策の基本方針は、「検索対象として広く露出するベクター DB（ChromaDB）には、原則としてマスク済みの本文だけを入れる」というものです。生本文（raw）は別系統で暗号化保管し、管理者ロールに限って引き出せるようにします。

この作りにより、次のような状況で漏えい経路を絞ります。

- 検索ヒットして LLM プロンプトに混入する経路 → マスク済み本文のみが渡る
- ChromaDB のデータをそのままダンプ・コピーされる経路 → マスク済みのみ
- DB ファイルを物理的に持ち去られる経路 → raw 側は Fernet で暗号化済み

これを実現するため、Cynovela は取込時マスキング（Tier1）と回答時マスキング（Tier2）の二重防御を採用しています。

> **廃止済み: マスキングなし取り込み（`collections.raw_only = 1`）** — マスキングを迂回する取り込み（Raw モード）は 2026-07-24 に廃止しました。いま指定すると HTTP 400 で拒否されます（2026-08-02 実測）。過去に作られた `raw_only = 1` のコレクションだけが masked 層を持たない状態で残り得ます（詳細は [architecture.md](architecture.md) §3.5.1「廃止済み: `raw_only`」）。

### 5.2 Tier1：取込時マスキング

#### 5.2.1 役割

Publish（コレクションを ChromaDB に流し込む処理）の途中で、各 chunk について「生本文（raw）」と「マスク済み本文（masked）」の dual-row を生成します。両方が SQLite の `chunks` テーブルと ChromaDB の両 collection に保存されます。

#### 5.2.2 実装箇所

`rag.py:984-1075`（抜粋）：

```python
pii_flag = 1 if pii_pat.search(chunk or "") else 0
# §段1b: マスク済本文を生成 (context prefix 付き全文を対象)
try:
    _masked_chunk, _mask_spans = _mtws_publish(chunk or "")
except Exception as _me:
    _log.warning(f"§段1b mask 失敗 doc_id={doc_id}: {_me}")
    _masked_chunk, _mask_spans = (chunk or ""), []
# 項目④: 検出種別 × 件数のみを集計（値は捨てる）
...
_masked_doc_id = f"{doc_id}__masked"
# §段1b: masked 本文に対する PII 再評価 (マスクが十分なら 0)
_masked_pii_flag = 1 if pii_pat.search(_masked_chunk or "") else 0
...
_meta_raw["tier"] = "raw"
...
_meta_masked["tier"] = "masked"
all_docs_masked.append(_masked_chunk or "")
```

`_mtws_publish` は `guardrail.mask_text_with_spans` のエイリアスで、正規表現ベースのマスクを各 chunk に適用します。

#### 5.2.3 保管先

| 保管先 | raw tier | masked tier |
|--------|----------|-------------|
| SQLite `chunks` テーブル | `doc_id` 行（`tier='raw'`） | `doc_id + '__masked'` 行（`tier='masked'`） |
| ChromaDB | `{collection_id}__raw` コレクション | `{collection_id}__masked` コレクション |
| 暗号化 | Fernet で暗号化（`enc:` プレフィックス） | 暗号化なし（検索性能確保） |

#### 5.2.4 失敗時の挙動

マスク処理に例外が出ても Publish は止めず、`_log.warning` でログに出してから raw 本文のまま masked 側にも保存します。これは「取込が止まると業務が止まる」リスクを避けるための設計です。

### 5.3 Tier2：回答時マスキング

#### 5.3.1 役割

LLM が生成した回答テキストに対して、利用者のロールに応じてさらに出口マスクを適用します。これにより、何らかの理由で raw 本文が context に混入した場合でも、admin 以外の利用者に対しては出口マスクが掛かります。

#### 5.3.2 実装箇所

`routers/chat.py:128-162`：

```python
def _mask_for_viewer(text: str, user: dict | None) -> str:
    """M1 (設計正本準拠): 利用者の保管庫 tier (raw/masked) に応じて
    LLM 生成出力に出口マスクを適用する。

    判定は rag.tier_for_role() に一元化:
      - tier_for_role(role) == "raw"    → 素通し (= admin・素側保管庫の利用者)
      - tier_for_role(role) == "masked" → マスク (= curator/viewer/legacy/未設定・伏せ側保管庫)
    """
    if not text or not user:
        return text
    try:
        from rag import tier_for_role
        if tier_for_role(user.get("role") or "") == "raw":
            return text
    except Exception:
        pass
    try:
        from guardrail import mask_text_with_spans
        masked, _spans = mask_text_with_spans(text)
        return masked
    except Exception:
        return text
```

`_mask_for_viewer` は chat 経路 4 箇所（通常応答 / Compare A / Compare B / SSE 経路）で呼ばれます（`routers/chat.py:653 / 655 / 681 / 1814`）。admin 以外は強制的に出口マスクが適用されます。

### 5.4 ロール別の振り分け

`rag.py:1726-1737`：

```python
def tier_for_role(role: str) -> str:
    """§段2: ロールに応じて保管庫の tier を決める。
    admin → 'raw'   (生本文を保管する管理者保管庫を引く)
    その他 → 'masked' (マスク済本文の一般保管庫を引く)
    """
    return "raw" if (role or "").strip() == "admin" else "masked"
```

`tier_for_role` は、ChromaDB の引き先（`{cid}__raw` か `{cid}__masked` か）と、出口マスクを通すか素通しするか、の両方を決めるため、二重防御として機能します。

- **admin** → `raw` 側のコレクションを参照し、回答表示では出口マスクも素通し（原本がそのまま表示されます）
- **viewer / 未指定**（`curator` 等は viewer に正規化）→ `masked` 側のコレクションを参照し、出口マスクも適用（マスキングされたまま表示されます）

> ただし外部（非ローカル）LLM を使う場合は、crag-egress-guard により admin でも raw の下読み（context_preview）が外部へ送出されません（CRAG スキップ）。上記の admin 素通しは「ローカル LLM での回答表示」を前提とした記述であり、「admin＝常に生本文が外部 LLM へ渡る」わけではありません。

### 5.5 ロール別の見え方

| ロール | 引き先保管庫 | 出口マスク | 結果として見えるもの |
|--------|--------------|------------|----------------------|
| `admin` | raw tier（暗号化を復号した生本文） | 素通し | 生本文 |
| `curator` | masked tier | 通す | マスク済み本文 |
| `viewer` | masked tier | 通す | マスク済み本文 |
| 未認証・未設定 | masked tier | 通す | マスク済み本文 |

これにより、設定ミスでロールが空になっていても、振り分けは masked tier に落ちます。

### 5.6 Fernet 暗号化（vault）

#### 5.6.1 役割と設計方針

raw tier の本文を SQLite と ChromaDB に保存する直前に Fernet（対称鍵暗号方式の一つで、認証付きの AES-128-CBC + HMAC）で暗号化し、`enc:` というプレフィックス付きで保存します。冪等な実装（既に `enc:` で始まる文字列は再暗号化しない）になっており、二重暗号化を避けます。

- **対象**: 原本本文（raw tier のみ）。masked tier は素通し（二重防御不要、検索パフォーマンス確保のため）
- **インターフェース**: `vault_enc.py` の `enc_raw()` / `dec_raw()` を介す
- **冪等性**: `enc:` プレフィックスをマーカーにして二重暗号化を防ぐ
- **鍵**: 環境変数 `CYNOVELA_SECRET_KEY` の Fernet 鍵を使用

#### 5.6.2 実装

- **鍵管理**: `config.py:62` で `Fernet(_KEY)` を初期化。`CYNOVELA_SECRET_KEY` 環境変数で鍵を渡します。明示的にこの環境変数を設定することが推奨されています。

```python
_fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)
```

- **インターフェース**: `vault_enc.py` の `enc_raw(text)` / `dec_raw(text)` が薄いラッパーを提供します。

```python
ENC_PREFIX = "enc:"

def enc_raw(text: str | None) -> str:
    """raw 本文を暗号化形式に揃える (冪等)。
    - 既に "enc:" 始まり: 二重暗号化しない
    - それ以外: "enc:" + config.encrypt(text) を返す """

def dec_raw(text: str | None) -> str:
    """暗号化形式なら復号、それ以外 (masked / 旧平文) はそのまま素通し (冪等)。"""
```

#### 5.6.3 適用箇所

| 経路 | 適用箇所 | 対象 |
|------|----------|------|
| Chroma 投入時 | `rag.py:1285` | raw tier の `documents` 配列に `enc_raw` を一括適用 |
| SQLite `chunks` 保存時 | `rag.py:1393` | raw tier 行の `content` を `enc_raw` |
| SQLite `parent_chunks` 保存時 | `rag.py:1131` | parent の raw tier に `enc_raw` |

masked tier は暗号化しません。検索パフォーマンス（埋め込み計算や全文検索）を確保するためです。raw tier は ChromaDB の `documents` に暗号化済みのバイト列として入るため、引き出し時に `dec_raw` で復号する必要があります。

#### 5.6.4 既存データの移行

`tools/vault_enc_migrate.py` が既存の SQLite / ChromaDB データを一括で `enc:` 形式に揃えるツールとして用意されています。

### 5.7 PII カテゴリ全件

PII 検出には 2 系統があります。

#### 5.7.1 一次系：`guardrail.py`（正規表現ベース）

`guardrail.py:137-153` で 8 種類を定義しています。

| entity_type | 検出対象 | マスク後トークン |
|-------------|----------|------------------|
| `URL` | `https?://...` | `[MASKED:URL]` |
| `EMAIL` | メールアドレス（`\b[\w.+-]+@[\w.-]+\.\w+\b`） | `[MASKED:EMAIL]` |
| `PHONE_JP` | 携帯番号（070/080/090） | `[MASKED:PHONE]` |
| `PHONE_LAND` | 固定電話番号 | `[MASKED:PHONE]` |
| `CREDIT` | クレジットカード番号（4-4-4-4 形式） | `[MASKED:CREDIT]` |
| `MYNUMBER` | マイナンバー（12 桁） | `[MASKED:MYNUM]` |
| `PASSPORT` | パスポート番号（英 2 + 数字 7） | `[MASKED:PASSPORT]` |
| `IPV4` | IPv4 アドレス | `[MASKED:IP]` |

#### 5.7.2 二次系：`utils/metadata/pii.py`（presidio + GiNZA フォールバック）

presidio（Microsoft Presidio：PII 検出・匿名化ライブラリ）が利用可能なら presidio を使い、ダメなら正規表現フォールバックに切り替わります。日本語・英語両対応。日本語 NER は GiNZA（spaCy ベースの日本語 NLP ライブラリ）で固有表現抽出を行います。

検出される追加カテゴリ：

| entity_type | 説明 |
|-------------|------|
| `EMAIL` | メールアドレス（正規表現） |
| `PHONE_JP` | 日本の電話番号 |
| `PHONE_INTL` | 国際電話番号 |
| `IP_ADDRESS` | IP アドレス |
| `MY_NUMBER` | マイナンバー |
| `CREDIT_CARD` | クレジットカード番号 |
| `INTERNAL_URL` | 内部 URL |
| `EMAIL_ADDRESS` | presidio が検出するメール |
| `PHONE_NUMBER` | presidio が検出する電話番号 |
| `DATE_TIME` | presidio が検出する日時 |
| `PERSON_JP` | GiNZA が検出する人名（日本語） |
| `ORG_JP` | GiNZA が検出する組織名（日本語） |
| `LOC_JP` | GiNZA が検出する地名（日本語） |
| `ADDRESS_JP` | 日本語住所ルール |

`HIGH_RISK_TYPES` として `{CREDIT_CARD, MY_NUMBER, SSN, PASSPORT, IBAN_CODE}` が定義されており、感度スコア（0〜100）の計算で重く扱われます。

#### 5.7.3 ポリシーマトリクス対象

`routers/policies.py:159` で、Workspace ポリシーから選択可能な PII タイプは次の 6 種に絞られています。

```python
pii_types = ["EMAIL", "PHONE_JP", "PHONE_LAND", "CREDIT", "MYNUMBER", "IPV4"]
```

URL と PASSPORT は検出はされますがポリシー UI からの選択肢には入っていません。

### 5.8 `pii_mode` の違い

#### 5.8.1 設定方法

`cynovela.yaml` の `pii_mode` キーで設定します。CLI 引数（旧 `--pii-mode`）は廃止されました。実行時に変更したい場合は `/api/settings/pii-mode`（PUT）で切り替えられます（admin 限定）。

#### 5.8.2 3 モードの動作

| 値 | 検出方式 | 速度 | 精度 | 主用途 |
|----|----------|------|------|--------|
| `lite` | 正規表現のみ | 高速 | 低〜中 | 大量取込・軽量環境 |
| `standard`（既定） | 正規表現 + GiNZA NER | 中庸 | 中〜高 | 既定値・推奨 |
| `quality` | 正規表現 + GiNZA NER + 詳細フィルタリング | 低速 | 高 | 研究開発・機微情報の精査 |

無効な値が与えられた場合は `standard` にリセットされます（`server.py:3135-3137`）。

起動時に次のようなログが出ます：

```
[Cynovela] PII detection mode: standard (from cynovela.yaml)
```

### 5.9 検出件数の集計

PII 検出は次の 2 系統で集計されます。

- **`/api/guardrails/pii-detections`（GET）**: `audit_logs` テーブルから集計（admin 限定）
- **`/api/pii-detections`（GET）**: `chunks` テーブルからドキュメント単位で集計（admin 限定）

両方とも admin ロール必須で、`_require_admin(request)` がエンドポイント先頭で呼ばれます。

### 5.10 旧実装からの移行

旧 `utils/pii_detector.py` は削除され、実装は `utils/metadata/pii.py` に集約されました。新実装の `llm_judge_pi(text)` は LLM judge ベースで追加判定を行う関数です。

---

## 6. 推奨しない使用方法

以下の使い方は仕様上ブロックされていないか、ブロックが不完全なため、行わないでください。

### 6-1. インターネットへの直接公開

`--lan` で `0.0.0.0` バインドした状態でインターネット側に直接ポート開放することは厳禁です。理由は次のとおりです。

- HTTPS 化されていない（平文通信）
- IP アローリストは既定では制限なしで、`--allow-subnet` / `--allow-tailscale` を指定しなければ全通過する（§2.7）
- ロール検査はルーター配下の約 242 箇所に分散しており、1 か所に集約されていない（§3.6）
- ファイルアップロード制限が緩い

### 6-2. 機密文書での本番運用

本番の機密文書をそのまま投入することは推奨しません。

- raw 本文の Fernet 暗号化は稼働中だが、鍵管理（`CYNOVELA_SECRET_KEY`）は個人運用前提
- audit_logs の改ざん防止は API 経由のみで、DB 直接アクセスは保護対象外
- バックアップと復元は用意されている（`/api/admin/backup` と `/api/admin/backups/{name}/restore`、および `docs/operations.md` の手動手順）が、実行と控えの置き場の管理は運用側に委ねられている

### 6-3. 信頼できないユーザーへの LAN 共有

LAN 共有時は、ネットワーク上の全ユーザーが信頼できる前提です。`--allow-subnet` で接続元を厳密に絞ったうえで、信頼できるメンバーのみでの利用を推奨します。

### 6-4. 監査ログの DB 直接編集

`audit_logs` テーブルへの API 経由の変更・削除は禁止しています。DB 直接編集（`sqlite3` コマンド等）も整合性破壊につながるため避けてください。

### 6-5. 同時複数 Publish の強制実行

同一 Collection への複数 Publish 同時実行は `collection_locks` で防いでいますが、強制的に DB ロックを解除して並列実行することはデータ整合性破壊につながります。

### 6-6. モックモードでの品質確認

RAG 品質確認テストは必ず実 LLM（LM Studio など）起動環境で行ってください。以前あった `--mock`（LLM を呼ばずに動かす指定）は撤去済みです。

### 6-7. `INSERT OR REPLACE` 文の新規追加

`INSERT OR REPLACE` は SQLite の FK CASCADE を不本意に発火させるため、コードベースで使用禁止です。既存行更新は `INSERT ... ON CONFLICT(id) DO UPDATE SET ...` を使用してください。

---

## 7. 推奨運用構成

以下のいずれかの構成を推奨します。

### 7-1. 完全ローカル運用（露出が最も狭い構成）

```bash
python server.py --demo --local-only
```

- `--local-only` を付けるとバインドは `127.0.0.1`（既定は `0.0.0.0`）
- 検証・デモ・チュートリアル向け

### 7-2. ローカル LLM 運用

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

- LM Studio または Ollama を同一マシンで起動
- ネットワーク露出なし
- 個人の学習・実験向け

### 7-3. 個人 VPN 経由運用

```bash
python server.py --lan --allow-tailscale
```

- Tailscale 経由のみ許可
- 信頼できる個人デバイス間でのみアクセス
- 外出先からの個人検証向け

---

## 8. 脆弱性報告

Cynovela は個人プロジェクトであり、正式な脆弱性報告窓口を持ちません。発見された問題は GitHub Issues 等で報告いただければ、可能な範囲で対応を検討します。

---
