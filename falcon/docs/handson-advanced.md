# ハンズオン（応用編）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built so that an individual can
> understand the concepts of AI platform tools by actually running them.
> It is not a commercial product and not an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official view of any company or product.

This hands-on covers workspace separation, differences in how things look per role, switching the startup mode, LAN sharing, and MCP (Model Context Protocol: the protocol for calling Cynovela from an external AI assistant) connection.

---

## 1. Demo of workspace separation

### Purpose

A workspace is a boundary of an information domain. You experience the behavior that, even for the same user, the visible collections change when the workspace they belong to is different.

### Related schema

The workspace area consists of the following tables.

- `workspaces`: the workspace itself
- `workspace_users`: the membership relation between a workspace and users
- `workspace_policies`: the link between a workspace and guardrail policies
- `workspace_sources`: the link between a workspace and data sources
- `collections`: the collections under a workspace (related by `workspace_id`)

### Example combinations of policies and workspaces

When started with `--demo`, only one workspace containing the bundled dummy documents is present (the three empty seeded workspaces were removed on 2026-07-30). In this exercise, please create workspaces yourself. The three seeded policies can be assigned to the workspaces you create, for example as follows.

| Policy to assign | Content | Example of the assumed domain |
|------------|----------|---------|
| pol-pii | mask PII, exclude Financial | Sales |
| pol-strict | Strongly control PII + Financial + HR | Human resources |
| pol-log | Log only for PII / Financial | Engineering |

### Steps to try

1. Create two workspaces, assign a different policy to each (for example pol-pii for sales and pol-strict for human resources), separate the member users, and log in
2. Open the "collection list" and confirm that the visible collections differ
3. Specify the `collection_id` of one workspace and try to chat from the other, and confirm that the boundary works

> **Note**: Of the workspace separation, the physical boundary at the ChromaDB level is still being strengthened. `<!-- BACKLOG: A-6 仕様で「WS 分離: ChromaDB 物理境界なし」が Phase 3 引き継ぎ HIGH バグとして明示されています -->`

---

## 2. Differences in how things look for admin / viewer

### Purpose

You check the behavior that combines role-based access control (RBAC: Role-Based Access Control) with Tier1/Tier2 masking.

### Summary of role permissions

| Role | Main permissions |
|--------|--------|
| `admin` | All management functions. User management, viewing the PII detection history, searching the raw store, no exit masking |
| `viewer` | Viewing only. RAG search and report viewing, searching the masked store, exit masking applied |

> Names such as `curator` / `data-scientist` are normalized to `viewer` and have no permissions of their own (the effective roles are the two values `admin` / `viewer`).

### Internal decision logic (outline)

- The store to search is decided by `tier_for_role(role)` (admin → raw / others → masked)
- The output of the LLM is masked according to the role by `_mask_for_viewer()`
- Some endpoints (PII detection history, audit logs, user management and so on) have `_require_admin` applied, so anyone other than admin cannot call them at all

### Steps to try

1. Prepare a collection in which a file containing PII has been published
2. Log in as `admin` and ask "tell me the contact information" in RAG Chat → the original text is shown
3. Ask the same question as `viewer` → it is replaced with `[MASKED:EMAIL]` and so on
4. Try to access the audit log screen as `viewer` → 403 Forbidden

---

## 3. Switching `--mode`

### Purpose

You check the switching of the display name of the startup mode (`--mode`). Because the switching is not wired, the behavior and the required models are the same as text for any value.

### List of modes

| `--mode` value | Required model | Embedding implementation | Recommended environment |
|-----------|----------|--------------|---------|
| `text` (default) | BAAI/bge-m3 | BGE-M3 (about 2.3GB) | General purpose, no GPU needed |
| `lite` | The switching is **not wired** = in fact BAAI/bge-m3 (the behavior is the same as text, only the display name changes) | — | — |
| `lite-en` | The switching is **not wired** = in fact BAAI/bge-m3 (the behavior is the same as text, only the display name changes) | — | — |

### Examples of switching

```bash
# 表示名: lite（動作は text と同じ・切替は未配線）
python server.py --demo --mode lite

# 表示名: lite-en（動作は text と同じ・切替は未配線）
python server.py --demo --mode lite-en

```

> **Note**: The `--mock` option that used to exist (the option that fixed the embedding to TF-IDF and the reranker to `NoReranker` regardless of the mode) has been removed. If you specify it now, it stops with an error.

---

## 4. Starting with LAN sharing

### Purpose

You make Cynovela running on your own PC reachable from another PC or a tablet on the same LAN.

### Default restrictions

- Bind address: `0.0.0.0` (default; narrow it to `127.0.0.1` with `--local-only`)
- An IP allow-list middleware is in place and rejects anything other than `127.0.0.1` / `localhost`

### Publishing to the LAN

Adding the `--lan` flag makes the bind `0.0.0.0`.

```bash
python server.py --demo --lan
```

To allow custom subnets, you can specify `--allow-subnet` multiple times.

```bash
python server.py --demo --lan --allow-subnet 192.168.1.0/24 --allow-subnet 10.0.0.0/8
```

### Access through Tailscale

If Tailscale (a private mesh VPN) is installed on your machine, you can automatically allow `100.64.0.0/10` with `--allow-tailscale`.

```bash
python server.py --demo --allow-tailscale
```

> **Note on the behavior**: At startup the IP is detected with `tailscale ip -4` and added to the allowed subnets. If Tailscale is not installed, it is ignored.

### Changing the port

```bash
python server.py --demo --lan --port 9000
```

---

## 5. Checking the MCP (Model Context Protocol) connection

### Purpose

MCP is the protocol for calling Cynovela's RAG search and workspace management tools from an external AI assistant. Cynovela ships with an MCP server implementation (`mcp_server.py`).

### Provided tools (11)

| Category | Tool name | Description |
|------|--------|------|
| RAG search | `search_collection` | RAG search of a single collection |
| RAG search | `search_across_collections` | RAG search across multiple collections |
| RAG search | `rag_with_role` | RAG with the answer style of each role |
| RAG search | `rag_general` | Ask the LLM directly without RAG (general knowledge answer) |
| Information | `list_workspaces` | List of workspaces and collections |
| Information | `get_workspace_info` | Details of a workspace |
| Information | `get_collection_info` | Details of a collection |
| Information | `get_audit_logs` | Get audit logs (up to 50) |
| Management | `list_sources` | List of data sources |
| Management | `publish_collection` | Publish a collection |
| Management | `create_workspace` | Create a workspace |

### How to check the connection

1. Start the Cynovela server (`python server.py --demo`)
2. Configure the MCP client (for example Claude Desktop or another supported client) to start `mcp_server.py`
3. Call `list_workspaces` and confirm that the demo seeded workspace is returned
4. Pass `query` / `workspace_id` / `collection_id` to `search_collection` and run a RAG search

> **Caution**: The MCP server sends authenticated requests to Cynovela's REST API internally. The Python path used to run MCP can be specified with the environment variable `CYNOVELA_MCP_PYTHON`.

> **Known limitation**: Running the MCP server assumes a conda environment.

---

## 6. Elements you were able to experience

| Element | Content |
|------|------|
| Workspace separation | The correspondence between user membership and the visible range of collections |
| Behavior per role | The store switching and exit masking of admin / viewer |
| `--mode` switching | The configuration differences of text / lite / lite-en |
| LAN sharing | `--lan` / `--allow-tailscale` / `--allow-subnet` |
| MCP integration | Operating Cynovela from an external assistant with 11 tools |

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

このハンズオンでは、ワークスペース分離、ロール別の見え方の違い、起動モード切り替え、LAN 共有、MCP（Model Context Protocol：外部 AI アシスタントから Cynovela を呼び出すための連携プロトコル）接続を扱います。

---

## 1. ワークスペース分離のデモ

### 目的

ワークスペースは情報領域の境界です。同じユーザーでも、所属するワークスペースが違えば見えるコレクションが変わる、という挙動を体験します。

### 関連スキーマ

ワークスペースまわりは以下のテーブルで構成されています。

- `workspaces`: ワークスペース本体
- `workspace_users`: ワークスペースとユーザーの所属関係
- `workspace_policies`: ワークスペースとガードレールポリシーのリンク
- `workspace_sources`: ワークスペースとデータソースのリンク
- `collections`: ワークスペース配下のコレクション群（`workspace_id` で関連）

### ポリシーとワークスペースの組み合わせ例

`--demo` で起動すると、同梱のダミー資料が入ったワークスペースが 1 件だけ入っています（空のシード WS 3 件は 2026-07-30 に撤去済み）。演習では自分でワークスペースを作ってください。シードされるポリシー 3 件は、作成したワークスペースへ例えば次のように割り当てて使えます。

| 割り当てるポリシー | 内容 | 想定領域の例 |
|------------|----------|---------|
| pol-pii | PII を mask、Financial を exclude | 営業 |
| pol-strict | PII + Financial + HR を強く制御 | 人事 |
| pol-log | PII / Financial をログのみ | 技術 |

### 体験手順

1. ワークスペースを 2 つ作成して別々のポリシーを割り当て（例: 営業用に pol-pii・人事用に pol-strict）、所属ユーザーを分けてログイン
2. 「コレクション一覧」を開き、見えるコレクションが異なることを確認
3. 一方のワークスペースの `collection_id` を指定して他方からチャットを試み、境界が機能していることを確認

> **補足**: ワークスペース分離のうち、ChromaDB レベルでの物理境界は強化が継続中です。`<!-- BACKLOG: A-6 仕様で「WS 分離: ChromaDB 物理境界なし」が Phase 3 引き継ぎ HIGH バグとして明示されています -->`

---

## 2. admin / viewer の見え方の違い

### 目的

ロールベースアクセス制御（RBAC：Role-Based Access Control）と Tier1/Tier2 マスキングを組み合わせた振る舞いを確認します。

### ロールの権限まとめ

| ロール | 主な権限 |
|--------|--------|
| `admin` | 全管理機能。ユーザー管理・PII 検出履歴閲覧・raw 保管庫検索・出口マスクなし |
| `viewer` | 閲覧のみ。RAG 検索とレポート閲覧・masked 保管庫検索・出口マスクあり |

> `curator` / `data-scientist` 等の名称は `viewer` に正規化され、固有権限はありません（実効ロールは `admin` / `viewer` の 2 値）。

### 内部の判定ロジック（概略）

- 検索対象の保管庫は `tier_for_role(role)` で決定（admin → raw / その他 → masked）
- LLM の出力は `_mask_for_viewer()` でロールに応じてマスク適用
- 一部のエンドポイント（PII 検出履歴、監査ログ、ユーザー管理など）には `_require_admin` が掛かっており、admin 以外はそもそも呼べません

### 体験手順

1. 同じ PII 入りファイルを Publish 済みのコレクションを用意
2. `admin` でログインして RAG Chat に「連絡先を教えて」と質問 → 生本文が表示される
3. `viewer` で同じ質問 → `[MASKED:EMAIL]` などに置換される
4. `viewer` で監査ログ画面にアクセスを試みる → 403 Forbidden

---

## 3. `--mode` 切り替え

### 目的

起動モード（`--mode`）の表示名の切り替えを確認します。切替は未配線のため、どの指定でも動作と必要なモデルは text と同じです。

### モード一覧

| `--mode` 値 | 必須モデル | Embedding 実装 | 推奨環境 |
|-----------|----------|--------------|---------|
| `text`（既定） | BAAI/bge-m3 | BGE-M3（約 2.3GB） | 汎用・GPU 不要 |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — |

### 切り替え例

```bash
# 表示名: lite（動作は text と同じ・切替は未配線）
python server.py --demo --mode lite

# 表示名: lite-en（動作は text と同じ・切替は未配線）
python server.py --demo --mode lite-en

```

> **補足**: 以前あった `--mock`（モードに関わらず Embedding を TF-IDF、Reranker を `NoReranker` に固定する指定）は撤去済みです。いま指定するとエラーで止まります。

---

## 4. LAN 共有起動

### 目的

自分の PC で動かしている Cynovela を、同じ LAN 上の別 PC やタブレットから触れるようにします。

### 既定の制限

- バインドアドレス: `0.0.0.0`（既定・`--local-only` で `127.0.0.1` に絞る）
- IP アローリストミドルウェアが入り、`127.0.0.1` / `localhost` 以外を拒否

### LAN 公開

`--lan` フラグを付けるとバインドが `0.0.0.0` になります。

```bash
python server.py --demo --lan
```

カスタムサブネットを許可する場合は `--allow-subnet` で複数指定できます。

```bash
python server.py --demo --lan --allow-subnet 192.168.1.0/24 --allow-subnet 10.0.0.0/8
```

### Tailscale 経由でのアクセス

Tailscale（プライベートメッシュ VPN）が手元にインストールされている場合は、`--allow-tailscale` で `100.64.0.0/10` を自動許可できます。

```bash
python server.py --demo --allow-tailscale
```

> **動作の補足**: 起動時に `tailscale ip -4` で IP を検出し、許可サブネットへ追加します。Tailscale が入っていない場合は無視されます。

### ポート変更

```bash
python server.py --demo --lan --port 9000
```

---

## 5. MCP（Model Context Protocol）接続確認

### 目的

MCP は、外部の AI アシスタントから Cynovela の RAG 検索やワークスペース管理ツールを呼び出すための連携プロトコルです。Cynovela には MCP サーバー実装（`mcp_server.py`）が同梱されています。

### 提供されているツール（11 個）

| 区分 | ツール名 | 説明 |
|------|--------|------|
| RAG 検索 | `search_collection` | 単一コレクションの RAG 検索 |
| RAG 検索 | `search_across_collections` | 複数コレクションを横断する RAG 検索 |
| RAG 検索 | `rag_with_role` | ロール別の回答スタイルで RAG |
| RAG 検索 | `rag_general` | RAG なしで LLM に直接質問（一般知識回答） |
| 情報 | `list_workspaces` | ワークスペースとコレクション一覧 |
| 情報 | `get_workspace_info` | ワークスペースの詳細 |
| 情報 | `get_collection_info` | コレクションの詳細 |
| 情報 | `get_audit_logs` | 監査ログ取得（最大 50 件） |
| 管理 | `list_sources` | データソース一覧 |
| 管理 | `publish_collection` | コレクションを公開 |
| 管理 | `create_workspace` | ワークスペース作成 |

### 接続確認の進め方

1. Cynovela サーバーを起動（`python server.py --demo`）
2. MCP クライアント（例: Claude Desktop など対応クライアント）から `mcp_server.py` を起動するよう設定
3. `list_workspaces` を呼んで、デモシードのワークスペースが返ってくるか確認
4. `search_collection` に `query` / `workspace_id` / `collection_id` を渡して RAG 検索を実行

> **注意**: MCP サーバーは内部で Cynovela の REST API に対して認証付きリクエストを送ります。MCP 実行用の Python パスは環境変数 `CYNOVELA_MCP_PYTHON` で指定可能です。

> **既知の制限**: MCP サーバーの実行は conda 環境前提です。<!-- BACKLOG: A-5 仕様に「MCP の conda 限定」の旨が known-limitations 候補として挙げられているが、原因の明示はなし -->

---

## 6. 体験できた要素

| 要素 | 内容 |
|------|------|
| ワークスペース分離 | ユーザー所属とコレクション可視範囲の対応 |
| ロール別動作 | admin / viewer の保管庫切替と出口マスク |
| `--mode` 切替 | text / lite / lite-en の構成差 |
| LAN 共有 | `--lan` / `--allow-tailscale` / `--allow-subnet` |
| MCP 連携 | 11 ツールで外部アシスタントから Cynovela 操作 |

---
