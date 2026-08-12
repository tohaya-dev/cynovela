> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# MCP（Model Context Protocol）連携ガイド

Cynovela は MCP（Model Context Protocol、Anthropic が提唱する AI ツール連携プロトコル）の MCP サーバーとして自身の機能を外部の LLM クライアントへ公開できます。本ドキュメントでは MCP の概念と Cynovela が公開している MCP ツール、接続手順を説明します。

---

## 1. MCP とは

MCP は、AI アシスタント（クライアント）が外部システムの機能（ツール）を呼び出すための標準プロトコルです。

- **クライアント**: LM Studio や対応する LLM クライアントなど、ユーザーが対話する側
- **サーバー**: 機能を提供する側（Cynovela がここに該当）
- **ツール**: サーバーが公開する操作（検索、登録、参照など）

MCP を使うと、ユーザーが LLM クライアントに「うちの社内文書を検索して」と話しかけたときに、LLM が Cynovela の検索ツールを呼び出し、結果を踏まえて回答を生成する、という連携が成立します。

---

## 2. Cynovela が公開する MCP ツール（全 11 件）

### 2-1. RAG 検索系（4 件）

#### `search_collection`
- **引数（必須）**: `query`, `workspace_id`, `collection_id`
- **引数（任意）**: `preset`
- **説明**: 単一の Collection（コレクション、文書群）に対して RAG 検索を行います。

#### `search_across_collections`
- **引数（必須）**: `query`, `workspace_id`, `collection_ids`
- **引数（任意）**: `preset`
- **説明**: 複数の Collection を横断して RAG 検索を行います。

#### `rag_with_role`
- **引数（必須）**: `query`, `workspace_id`, `collection_id`, `style_role`
- **引数（任意)**: `preset`
- **説明**: ロール別の回答スタイル（管理者向け / 一般ユーザー向けなど）を切り替えて RAG 検索します。

#### `rag_general`
- **引数（必須）**: `query`, `workspace_id`
- **説明**: RAG を使わず、LLM の一般知識のみで回答を生成します。社内文書に依存しない一般的な質問用です。

### 2-2. 情報取得系（4 件）

#### `list_workspaces`
- **引数**: なし
- **説明**: 全ワークスペースとそのコレクション一覧を取得します。

#### `get_workspace_info`
- **引数（必須）**: `workspace_id`
- **説明**: 指定ワークスペースの詳細情報（名前、ガードレールポリシー、作成日時など）を返します。

#### `get_collection_info`
- **引数（必須）**: `workspace_id`, `collection_id`
- **説明**: コレクションの詳細（ドキュメント数、ステータス、アクセスレベル）を返します。

#### `get_audit_logs`
- **引数（必須）**: `workspace_id`
- **引数（任意）**: `limit`（既定 10、上限 50）
- **説明**: 監査ログ（チャット履歴、PII 検出、エラー）を取得します。

### 2-3. 管理系（3 件）

#### `list_sources`
- **引数（必須）**: `workspace_id`
- **説明**: ワークスペース配下のデータソース一覧（ファイルパス、ステータス、ファイル数）を返します。

#### `publish_collection`
- **引数（必須）**: `collection_id`
- **説明**: 指定コレクションを RAG 検索可能な状態に公開します。

#### `create_workspace`
- **引数（必須）**: `name`
- **引数（任意）**: `description`
- **説明**: 新規ワークスペースを作成します。

---

## 3. LM Studio からの接続

LM Studio は MCP クライアント機能を備えており、設定ファイルで MCP サーバーを登録できます。

### 3-1. 接続フロー

```
LM Studio（ユーザー対話）
  ↓ MCP プロトコル（標準入出力経由）
Cynovela MCP サーバー（mcp_server.py）
  ↓ HTTP API
Cynovela 本体（FastAPI サーバー）
```

### 3-2. 設定例

LM Studio の MCP サーバー設定に以下を登録します。実際のキー名はクライアント側のドキュメントを参照してください。

```json
{
  "mcpServers": {
    "cynovela": {
      "command": "/path/to/python",
      "args": [
        "/Users/<ユーザー名>/Projects/cynovela/cynovela/mcp_server.py"
      ],
      "env": {
        "CYNOVELA_BASE_URL": "http://127.0.0.1:8765",
        "CYNOVELA_TOKEN": "<認証トークン>"
      }
    }
  }
}
```

---

## 4. conda 環境固有の制限

Cynovela は conda 環境（`cynovela`）で動作する前提で構築されています。MCP サーバーから本体 API を呼び出す際は、Python 実行ファイルパスを明示する必要があります。

### 4-1. Python パスの指定

環境変数 `CYNOVELA_MCP_PYTHON` で MCP スクリプト実行用 Python の絶対パスを指定できます。

```bash
export CYNOVELA_MCP_PYTHON=~/miniforge3/envs/cynovela/bin/python
```

この指定がない場合、LM Studio などのクライアントが起動した子プロセスでは conda 環境がアクティブにならず、依存ライブラリの ImportError が発生する可能性があります。

---

## 5. 認証の注意

### 5-1. ベアラートークン

MCP サーバーは Cynovela 本体 API に対して `Authorization: Bearer <token>` ヘッダーで認証します。トークンはクライアント側の環境変数で渡します。

- 認証は `POST /api/auth/login` が発行する JWT です。旧 `Bearer demo-token-<user_id>` 形式は廃止済みで受理しません。
- 本番運用では JWT 認証導入が必要です（現時点では未実装）。

### 5-2. ロール権限

MCP 経由の呼び出しも本体 API と同じロール（admin / curator / viewer）の権限チェックを通過します。特に `create_workspace` や `publish_collection` などの管理系ツールは admin 権限を要する場合があります。

### 5-3. 監査ログ

MCP 経由の操作も本体と同じ監査ログ（`audit_logs` テーブル）に記録されます。`get_audit_logs` で履歴を確認できます。

---

## 6. トラブルシューティング

| 症状 | 確認ポイント |
|---|---|
| ツールが見つからない | Cynovela 本体（`server.py`）が `http://127.0.0.1:8765` で起動済みか |
| 認証エラー | `CYNOVELA_TOKEN` 環境変数の値、トークンの有効性 |
| ImportError が出る | `CYNOVELA_MCP_PYTHON` で conda 環境の Python パスを指定済みか |
| 結果が空 | 対象 Collection が `ready` ステータスに到達済みか |

---

最終更新: 2026-05-26 / Alpha GA 対応版
