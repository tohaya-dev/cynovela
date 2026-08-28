#!/usr/bin/env python3
"""Cynovela MCP Server v3.1 — protocol 2026-07-28 (stdio).

2024-11-05 世代の手書き JSON-RPC を現行仕様へ作り直した。
  - `server/discover` に応える。initialize/initialized の握手も Mcp-Session-Id も
    要求しない (接続に状態を持たせない)。旧世代クライアントから initialize が
    来た場合は同じ内容で応えるだけで、握手の完了を待たない。
  - 道具の入出力を JSON Schema 2020-12 で宣言し、結果は structuredContent で
    構造化して返す (出典・件数を文章に埋めない)。content の text は人が読む控え。
  - 資料が無いとき (対象の workspace / collection が見つからない・API が 404) は
    JSON-RPC エラー -32602 で返す。
  - Roots / Sampling / Logging / 旧 HTTP+SSE は実装しない。転送は stdio のみ。
  - 外部依存を持たない (requests をやめ urllib に置き換えた。CLI と同じ条件)。

認証: 管理画面のログインで発行されたトークンを CYNOVELA_TOKEN に入れて渡す。
接続先: CYNOVELA_BASE 環境変数を優先、未設定なら --cynovela-url (既定 127.0.0.1:8765)。

注意: routers/mcp.py の /api/mcp/config は本ファイルの `TOOLS = [...]` リテラルを
ast で読んで道具名の一覧を出す。TOOLS はモジュール直下のリスト・リテラルのまま保つこと。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--cynovela-url", default="http://127.0.0.1:8765")
args = parser.parse_args()
BASE = os.environ.get("CYNOVELA_BASE", "").strip().rstrip("/") or args.cynovela_url.rstrip("/")

PROTOCOL_VERSION = "2026-07-28"
# 旧世代クライアントとの版の交渉 (仕様の交渉規則): initialize で頼まれた版が日付形式で
# 自分の版より古い・同じなら、その版で応える。本実装が出すのは全版共通の部分集合
# (tools のみ) なので、旧版のクライアントにもそのまま通じる。未来の版は名乗らない。
_REV_RE = r"^\d{4}-\d{2}-\d{2}$"
SERVER_INFO = {"name": "cynovela-mcp", "version": "3.1"}
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# ─────────────────────────────────────────
# ツール定義 (25本 = 開放22 + 既定閉3。全て実在する REST の口だけを叩く。
#             16本が先行し、9本を作業の単位で追加)
#   追加分:
#   server_status → GET /api/health + /api/collections (稼働と索引の状態)
#   ingest_source → POST /api/ingest-roots + /api/sources + /api/sources/{id}/scan/async (1道具)
#   get_job_status → GET /api/jobs/{job_id} (走査と公開の進み具合)
#   cancel_scan → POST /api/sources/{id}/scan/cancel
#   create_collection → POST /api/collections (+ link-files)
#   publish_control → POST /api/collections/{id}/publish/{stop|recover}
#   delete_item / manage_users / manage_backups
#     → 既定で閉じる。CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 のときだけ tools/list に現れる
#   (publish_collection は publish/async を叩き job_id を即返す形へ変更)
#   search_collection / search_across_collections / rag_with_role / rag_general
#     → POST /api/chat
#   list_workspaces → GET /api/workspaces + GET /api/collections
#   get_workspace_info → GET /api/workspaces/{id}
#   get_collection_info → GET /api/collections?workspace_id=
#   get_audit_logs → GET /api/audit-logs
#   list_sources → GET /api/sources?workspace_id=
#   publish_collection → POST /api/collections/{id}/publish
#   create_workspace → POST /api/workspaces
#   settings_show → GET /api/settings/{llm|reranker|classifier|embedding|pii-mode|vector-store|datasync}
#   settings_models → GET /api/settings/models
#   settings_test → POST /api/settings/test-connection
#   settings_set → POST (pii のみ PUT) 同上の各口 (既定で閉・CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1 で開)
#   settings_providers → GET /api/llm/presets
# ─────────────────────────────────────────
TOOLS = [
    {
        "name": "search_collection",
        "description": (
            "CynovelaのRAGコレクションに対してクエリを実行します。"
            "workspace_idとcollection_idはlist_workspacesで取得してください。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "検索クエリ"},
                "workspace_id": {"type": "string", "description": "ワークスペースID"},
                "collection_id": {"type": "string", "description": "コレクションID"},
                "preset": {"type": "string", "description": "lite / standard / hq（デフォルト: standard）"},
            },
            "required": ["query", "workspace_id", "collection_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer",
                                      "description": "回答本文の [N] と同じ番号"},
                            "file_name": {"type": "string"},
                            "score": {"type": "number"},
                            "text": {"type": "string"},
                        },
                    },
                },
                "source_count": {"type": "integer"},
            },
            "required": ["answer", "sources", "source_count"],
        },
    },
    {
        "name": "search_across_collections",
        "description": (
            "複数のRAGコレクションを横断してクエリを実行します。"
            "collection_idsに複数のIDを渡すと全て検索して統合した結果を返します。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "検索クエリ"},
                "workspace_id": {"type": "string", "description": "ワークスペースID"},
                "collection_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "コレクションIDのリスト（複数指定可）",
                },
                "preset": {"type": "string", "description": "lite / standard / hq（デフォルト: standard）"},
            },
            "required": ["query", "workspace_id", "collection_ids"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "collections_searched": {"type": "integer"},
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer",
                                      "description": "回答本文の [N] と同じ番号"},
                            "file_name": {"type": "string"},
                            "score": {"type": "number"},
                            "text": {"type": "string"},
                        },
                    },
                },
                "source_count": {"type": "integer"},
            },
            "required": ["answer", "sources", "source_count"],
        },
    },
    {
        "name": "rag_with_role",
        "description": (
            "ユーザーのロールに応じて回答スタイルを変えてRAG検索を実行します。"
            "admin=技術詳細・reader=平易な説明。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "検索クエリ"},
                "workspace_id": {"type": "string", "description": "ワークスペースID"},
                "collection_id": {"type": "string", "description": "コレクションID"},
                "style_role": {"type": "string", "description": "admin / reader"},
                "preset": {"type": "string", "description": "lite / standard / hq（デフォルト: standard）"},
            },
            "required": ["query", "workspace_id", "collection_id", "style_role"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "style_role": {"type": "string"},
                "source_count": {"type": "integer"},
            },
            "required": ["answer", "style_role", "source_count"],
        },
    },
    {
        "name": "rag_general",
        "description": (
            "RAGを使わずLLMの学習データで直接回答します（一般知識モード）。"
            "ワークスペース内のドキュメントを参照しないため、sourcesは空になります。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "質問"},
                "workspace_id": {"type": "string", "description": "ワークスペースID（ログ記録用）"},
            },
            "required": ["query", "workspace_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "rag_used": {"type": "boolean"},
            },
            "required": ["answer", "rag_used"],
        },
    },
    {
        "name": "list_workspaces",
        "description": (
            "利用可能なワークスペースとコレクション一覧を返します。"
            "search_collectionを呼ぶ前にこのツールでIDを確認してください。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {},
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "workspaces": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "collections": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "status": {"type": ["string", "null"]},
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "required": ["workspaces"],
        },
    },
    {
        "name": "get_workspace_info",
        "description": "指定ワークスペースの詳細情報（名前・ガードレール設定・作成日時等）を返します。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ワークスペースID"},
            },
            "required": ["workspace_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "id": {"type": ["string", "null"]},
                "name": {"type": ["string", "null"]},
                "description": {"type": ["string", "null"]},
                "created_at": {"type": ["string", "null"]},
                "updated_at": {"type": ["string", "null"]},
                "guardrail_policy_id": {"type": ["string", "integer", "null"]},
            },
            "required": ["id", "name"],
        },
    },
    {
        "name": "get_collection_info",
        "description": "指定コレクションの詳細情報（ドキュメント数・ステータス・アクセスレベル等）を返します。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ワークスペースID"},
                "collection_id": {"type": "string", "description": "コレクションID"},
            },
            "required": ["workspace_id", "collection_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "id": {"type": ["string", "null"]},
                "name": {"type": ["string", "null"]},
                "status": {"type": ["string", "null"]},
                "chunk_count": {"type": ["integer", "null"]},
                "access_level": {"type": ["string", "integer", "null"]},
                "created_at": {"type": ["string", "null"]},
                "allowed_roles": {"type": ["string", "array", "null"]},
            },
            "required": ["id", "name"],
        },
    },
    {
        "name": "get_audit_logs",
        "description": "ワークスペースの直近の監査ログを返します（RAG Chat履歴・PII検出・エラー等）。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ワークスペースID"},
                "limit": {"type": "integer", "description": "取得件数（デフォルト10・最大50）"},
            },
            "required": ["workspace_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "logs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": ["string", "null"]},
                            "action": {"type": ["string", "null"]},
                            "target": {"type": ["string", "null"]},
                            "detail": {"type": ["string", "null"]},
                        },
                    },
                },
                "count": {"type": "integer"},
            },
            "required": ["logs", "count"],
        },
    },
    {
        "name": "list_sources",
        "description": "登録済みデータソースの一覧を返します（ファイルパス・ステータス・ファイル数等）。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ワークスペースID（フィルタ）"},
            },
            "required": ["workspace_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": ["string", "integer", "null"]},
                            "name": {"type": ["string", "null"]},
                            "path": {"type": ["string", "null"]},
                            "status": {"type": ["string", "null"]},
                            "file_count": {"type": ["integer", "null"]},
                        },
                    },
                },
                "count": {"type": "integer"},
            },
            "required": ["sources", "count"],
        },
    },
    {
        "name": "publish_collection",
        "description": (
            "指定コレクションのPublish（公開）を始めます。開始した時点で job_id を返して"
            "すぐ戻ります (待ちません)。進み具合は get_job_status で job_id を渡して見ます。"
            "Publish後はRAG Chatで検索可能になります。既にready状態でも再Publishが可能です。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "collection_id": {"type": "string", "description": "コレクションID"},
            },
            "required": ["collection_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "collection_id": {"type": "string"},
                "job_id": {"type": ["string", "null"]},
                "status": {"type": ["string", "null"]},
                "message": {"type": ["string", "null"]},
            },
            "required": ["ok", "collection_id"],
        },
    },
    {
        "name": "create_workspace",
        "description": "新しいワークスペースを作成します。作成後にデータソース登録・コレクション作成が必要です。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "ワークスペース名"},
                "description": {"type": "string", "description": "説明（任意）"},
            },
            "required": ["name"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "id": {"type": ["string", "null"]},
                "name": {"type": ["string", "null"]},
                "description": {"type": ["string", "null"]},
            },
            "required": ["ok"],
        },
    },
    # ─── 設定系 (管理者トークンが必要。API キーの値は入力にだけ現れ、
    #     応答には *_set の bool しか出さない) ───
    {
        "name": "settings_show",
        "description": "サーバの設定を見ます (管理者のみ)。name で対象を選びます (既定: llm)。APIキーの値は返さず、設定あり/なし (api_key_set) だけを返します。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "対象 (既定: llm)",
                    "enum": ["llm", "reranker", "classifier", "embedding", "pii", "vector-store", "datasync"],
                },
            },
            "required": [],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "settings": {"type": "object"},
            },
            "required": ["name", "settings"],
        },
    },
    {
        "name": "settings_models",
        "description": "接続先の推論サーバにあるモデルの一覧を出します (管理者のみ)。注意: ダウンロード済み全件であり、読み込み済みを意味しません。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {},
            "required": [],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "models": {"type": "array", "items": {"type": "string"}},
                "count": {"type": "integer"},
            },
            "required": ["models", "count"],
        },
    },
    {
        "name": "settings_test",
        "description": "LLM への接続を確かめ、通ったか通らなかったかを言葉で返します (管理者のみ)。引数を渡すと保存済み設定の代わりにその値で試します。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "試すプロバイダー (任意)"},
                "base_url": {"type": "string", "description": "試す接続先 (任意)"},
                "model": {"type": "string", "description": "試すモデル (任意)"},
            },
            "required": [],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "connected": {"type": "boolean"},
                "status": {"type": "string"},
                "endpoint": {"type": ["string", "null"]},
                "models": {"type": ["integer", "null"]},
                "error": {"type": ["string", "null"]},
            },
            "required": ["connected", "status"],
        },
    },
    {
        "name": "settings_set",
        "description": "サーバの設定を変えます (管理者のみ)。この道具は既定で閉じており、MCP サーバの環境変数 CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1 を設定したときだけ実行できます。name で対象を選び (既定: llm)、values に変える項目だけを入れます。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "対象 (既定: llm)",
                    "enum": ["llm", "reranker", "classifier", "embedding", "pii", "vector-store", "datasync"],
                },
                "values": {"type": "object", "description": "変える項目と値 (例: {\"model\": \"...\"})"},
            },
            "required": ["values"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "name": {"type": "string"},
                "applied": {"type": "boolean"},
                "after": {"type": "object"},
            },
            "required": ["ok", "name", "applied"],
        },
    },
    {
        "name": "settings_providers",
        "description": "選べる LLM プロバイダーのプリセット一覧を出します (管理者のみ)。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {},
            "required": [],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "providers": {"type": "array", "items": {"type": "object"}},
                "count": {"type": "integer"},
            },
            "required": ["providers", "count"],
        },
    },
    # ─── 作業の単位で足した道具 (開放6) ───
    {
        "name": "server_status",
        "description": "サーバの稼働と索引の状態を見ます (GET /api/health と、まとまりごとの塊の数)。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {},
            "required": [],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "up": {"type": "boolean"},
                "version": {"type": ["string", "null"]},
                "collections": {"type": "array", "items": {"type": "object"}},
                "total_chunks": {"type": "integer"},
            },
            "required": ["up"],
        },
    },
    {
        "name": "ingest_source",
        "description": (
            "資料を入れます: 取り込み元を足し、資料として登録し、走査を始める、を1道具で行います。"
            "走査は始めた時点で job_id を返してすぐ戻ります。進み具合は get_job_status で見ます。"
            "workspace_id を渡すと、その作業場所へも結び付けます。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "取り込むフォルダの絶対パス"},
                "name": {"type": "string", "description": "資料の名前 (省略時: フォルダ名)"},
                "workspace_id": {"type": "string", "description": "結び付ける作業場所 (任意)"},
            },
            "required": ["path"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "source_id": {"type": ["string", "null"]},
                "job_id": {"type": ["string", "null"]},
                "steps": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["ok"],
        },
    },
    {
        "name": "get_job_status",
        "description": "走査 (scan) と公開 (publish) の進み具合を見ます。job_id は ingest_source / publish_collection が返した値です。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ジョブID"},
            },
            "required": ["job_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "kind": {"type": ["string", "null"]},
                "status": {"type": ["string", "null"]},
                "stage": {"type": ["string", "null"]},
                "progress": {"type": ["integer", "null"]},
                "total": {"type": ["integer", "null"]},
                "message": {"type": ["string", "null"]},
                "error": {"type": ["string", "null"]},
            },
            "required": ["status"],
        },
    },
    {
        "name": "cancel_scan",
        "description": "走行中の走査に中止を要求します。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "description": "取り込み元 (source) のID"},
            },
            "required": ["source_id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "status": {"type": ["string", "null"]},
            },
            "required": ["ok"],
        },
    },
    {
        "name": "create_collection",
        "description": (
            "作業場所の中にまとまり (collection) を作ります。source_id を渡すと、その資料の"
            "全ファイルを結び付けます (公開は publish_collection で別に始めます)。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "作業場所のID"},
                "name": {"type": "string", "description": "まとまりの名前"},
                "source_id": {"type": "string", "description": "この資料の全ファイルを結び付ける (任意)"},
            },
            "required": ["workspace_id", "name"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "id": {"type": ["string", "null"]},
                "name": {"type": ["string", "null"]},
                "linked_files": {"type": "integer"},
            },
            "required": ["ok"],
        },
    },
    {
        "name": "publish_control",
        "description": "公開 (publish) を止める・固着から復旧する。action に stop か recover を渡します。",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "collection_id": {"type": "string", "description": "コレクションID"},
                "action": {"type": "string", "enum": ["stop", "recover"]},
            },
            "required": ["collection_id", "action"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "action": {"type": "string"},
                "result": {"type": "object"},
            },
            "required": ["ok", "action"],
        },
    },
    # ─── 既定で閉じる道具 (3)。CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 の
    #     ときだけ tools/list に現れる。閉じたまま呼ばれた場合も実行しない (二重の守り)。
    #     これは機能差ではなく、資料の中身に引きずられた AI の暴発を止める仕掛け (§0-2 C)。───
    {
        "name": "delete_item",
        "description": (
            "資料 (source)・まとまり (collection)・作業場所 (workspace) を消します。"
            "既定で閉じています: MCP サーバの env に CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を書いたときだけ使えます。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["source", "collection", "workspace"]},
                "id": {"type": "string", "description": "消す対象のID"},
            },
            "required": ["kind", "id"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "kind": {"type": "string"},
                "id": {"type": "string"},
            },
            "required": ["ok"],
        },
    },
    {
        "name": "manage_users",
        "description": (
            "利用者を管理します (list / create / update / delete / reset_password)。"
            "delete は既定では使えなくするだけです。purge=true で行そのものを消します。"
            "既定で閉じています: MCP サーバの env に CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を書いたときだけ使えます。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete", "reset_password"]},
                "user_id": {"type": "string", "description": "update / delete / reset_password の対象"},
                "username": {"type": "string", "description": "create のログイン名"},
                "password": {"type": "string", "description": "create / reset_password の合言葉 (8文字以上)"},
                "role": {"type": "string", "description": "create / update の役割 (admin / viewer)"},
                "display_name": {"type": "string", "description": "create / update の表示名"},
                "is_active": {"type": "boolean", "description": "update の有効/無効"},
                "purge": {"type": "boolean",
                          "description": "delete のとき true にすると、行そのものを消します "
                                         "(既定は false = 使えなくするだけ)。監査の記録は残ります。"},
            },
            "required": ["action"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "action": {"type": "string"},
                "users": {"type": "array", "items": {"type": "object"}},
                "result": {"type": "object"},
            },
            "required": ["ok", "action"],
        },
    },
    {
        "name": "manage_backups",
        "description": (
            "控えを扱います (list / create / restore / delete)。restore はいまのデータを控えの中身に置き換えます。"
            "既定で閉じています: MCP サーバの env に CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を書いたときだけ使えます。"
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "restore", "delete"]},
                "name": {"type": "string", "description": "restore / delete の控えの名前"},
                "label": {"type": "string", "description": "create の短い札 (任意)"},
            },
            "required": ["action"],
        },
        "outputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "action": {"type": "string"},
                "backups": {"type": "array", "items": {"type": "object"}},
                "result": {"type": "object"},
            },
            "required": ["ok", "action"],
        },
    },
]


# ─────────────────────────────────────────
# エラーの形
# ─────────────────────────────────────────
class NotFoundError(Exception):
    """資料が無い (対象が見つからない・API 404)。JSON-RPC -32602 で返す。"""


class ToolFailure(Exception):
    """道具の実行に失敗した (接続不能・認証失敗・5xx 等)。isError: true で返す。"""


# ─────────────────────────────────────────
# Cynovela API ヘルパー (urllib・標準ライブラリのみ)
# ─────────────────────────────────────────
def _token() -> str:
    """API 呼び出しに使う Bearer トークンを CYNOVELA_TOKEN から取る。

    C-B5 (2026-07-29): 固定トークンのフォールバックは撤去済み。未設定は設定漏れなので
    その場で理由の分かる失敗にする。トークンは管理画面のログインで発行される値を
    CYNOVELA_TOKEN に入れて渡すこと。
    """
    env_tok = os.environ.get("CYNOVELA_TOKEN", "").strip()
    if env_tok:
        return env_tok
    raise ToolFailure(
        "CYNOVELA_TOKEN が設定されていません。"
        "Cynovela にログインして発行されたトークンを CYNOVELA_TOKEN に設定してください"
    )


def _api(method: str, path: str, body=None, timeout: float = 30.0):
    """(status, parsed_json) を返す。404 は NotFoundError、その他の失敗は ToolFailure。"""
    url = f"{BASE}{path}"
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if not raw:
                return r.status, {}
            try:
                return r.status, json.loads(raw)
            except Exception as e:
                raise ToolFailure(f"JSONパース失敗: {e} / body={raw[:200]!r}")
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        if e.code == 404:
            raise NotFoundError(f"対象が見つかりません ({path}): {detail}")
        raise ToolFailure(f"APIエラー ({e.code}): {detail}")
    except urllib.error.URLError as e:
        raise ToolFailure(f"Cynovela ({BASE}) へ到達できません: {e.reason}")
    except TimeoutError:
        raise ToolFailure(f"応答が期限 ({timeout:.0f}s) 内に返りませんでした。推論サーバのモデルが重い可能性があります")


def _norm_source(s) -> dict:
    """/api/chat の sources 要素は dict のことも str のこともある (sokessan-fix-a9-20260711)。"""
    if isinstance(s, dict):
        return {
            "file_name": str(s.get("file_name") or s.get("source_doc") or s.get("filename") or "?"),
            "score": float(s.get("score") or 0),
            "text": str(s.get("text") or s.get("preview") or "")[:300],
        }
    return {"file_name": str(s)[:200], "score": 0.0, "text": ""}


def _chat_fragments(d: dict, limit: int) -> list:
    """出典の断片。/api/chat の "sources" はファイル名の文字列一覧で、断片の本文と
    スコアは "citations" (source_filename / chunk_preview / score) に入っている。
    citations を優先し、無ければ sources に倒す。"""
    # index を落とさずに渡す。回答本文の [N] はこの番号であり、
    #   受け取った側が一覧を数え直すと本文と食い違う (従来はここで番号を捨てていた)。
    frags = [
        {
            "index": int(c.get("index") or (n + 1)),
            "file_name": str(c.get("source_filename") or "?"),
            "score": float(c.get("score") or 0),
            "text": str(c.get("chunk_preview") or "")[:300],
        }
        for n, c in enumerate((d.get("citations") or [])[:limit])
        if isinstance(c, dict)
    ]
    if frags:
        return frags
    return [_norm_source(s) for s in (d.get("sources") or [])[:limit]]


def _as_list(data, *keys):
    """一覧 API の応答は素の配列のことも {"items": [...]} の包みのこともある
    (mcp-empty-list-fix-20260727)。見つからないときは空を返さず失敗にする。
    空を返すと「資料が無い」と区別がつかないため。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            v = data.get(k)
            if isinstance(v, list):
                return v
        lists = [v for v in data.values() if isinstance(v, list)]
        if len(lists) == 1:
            return lists[0]
        raise ToolFailure(f"一覧が見つかりません。期待キー={list(keys)} / 実際のキー={sorted(data.keys())}")
    raise ToolFailure(f"一覧を取り出せません: {type(data).__name__}")


# ─────────────────────────────────────────
# ツール実装 — 各実装は (structured: dict, text: str) を返す
# ─────────────────────────────────────────
def _chat(payload: dict, timeout: float = 300.0) -> dict:
    # 300s: 回答の生成は読み込まれたモデル次第で 120 秒を超える (2026-08-19 実測 153s)
    _st, d = _api("POST", "/api/chat", body=payload, timeout=timeout)
    if not isinstance(d, dict):
        raise ToolFailure(f"dict期待だが{type(d).__name__}が返った")
    return d


def _tool_search_collection(a):
    d = _chat({
        "query": a["query"],
        "workspace_id": a["workspace_id"],
        "collection_ids": [a["collection_id"]],
        "preset": a.get("preset", "standard"),
    })
    sources = _chat_fragments(d, 5)
    structured = {"answer": d.get("answer", ""), "sources": sources, "source_count": len(sources)}
    text = f"回答: {structured['answer']}\n参照ソース: {structured['source_count']}件"
    return structured, text


def _tool_search_across_collections(a):
    col_ids = a["collection_ids"]
    d = _chat({
        "query": a["query"],
        "workspace_id": a["workspace_id"],
        "collection_ids": col_ids,
        "preset": a.get("preset", "standard"),
    })
    sources = _chat_fragments(d, 8)
    structured = {
        "answer": d.get("answer", ""),
        "collections_searched": len(col_ids),
        "sources": sources,
        "source_count": len(sources),
    }
    text = (
        f"回答（{len(col_ids)}コレクション横断）: {structured['answer']}\n"
        f"参照ソース: {structured['source_count']}件"
    )
    return structured, text


def _tool_rag_with_role(a):
    d = _chat({
        "query": a["query"],
        "workspace_id": a["workspace_id"],
        "collection_ids": [a["collection_id"]],
        "preset": a.get("preset", "standard"),
        "style_role": a["style_role"],
    })
    structured = {
        "answer": d.get("answer", ""),
        "style_role": a["style_role"],
        "source_count": len(d.get("sources") or []),
    }
    text = f"回答（{a['style_role']}ロール向け）: {structured['answer']}"
    return structured, text


def _tool_rag_general(a):
    d = _chat({
        "query": a["query"],
        "workspace_id": a["workspace_id"],
        "collection_ids": [],
        "rag_mode": "general",
        "preset": "standard",
    })
    structured = {"answer": d.get("answer", ""), "rag_used": bool(d.get("sources"))}
    text = f"回答（RAGなし・LLM直接回答）: {structured['answer']}"
    return structured, text


def _tool_list_workspaces(_a):
    _st, ws_data = _api("GET", "/api/workspaces", timeout=10)
    if not isinstance(ws_data, list):
        ws_data = _as_list(ws_data, "workspaces", "items")
    result = []
    for ws in ws_data:
        ws_id = ws.get("id", "")
        try:
            _st2, cols_data = _api("GET", f"/api/collections?workspace_id={ws_id}", timeout=10)
            cols = cols_data if isinstance(cols_data, list) else []
        except (NotFoundError, ToolFailure):
            cols = []
        result.append({
            "id": ws_id,
            "name": ws.get("name", ""),
            "collections": [
                {"id": c.get("id"), "name": c.get("name"), "status": c.get("status")}
                for c in cols
                if not c.get("archived_at")
            ],
        })
    structured = {"workspaces": result}
    text = "ワークスペース: " + (", ".join(f"{w['name']}({len(w['collections'])}件)" for w in result) or "0件")
    return structured, text


def _tool_get_workspace_info(a):
    _st, d = _api("GET", f"/api/workspaces/{a['workspace_id']}", timeout=10)
    if not isinstance(d, dict):
        raise ToolFailure(f"dict期待だが{type(d).__name__}が返った")
    structured = {
        "id": d.get("id"),
        "name": d.get("name"),
        "description": d.get("description"),
        "created_at": d.get("created_at"),
        "updated_at": d.get("updated_at"),
        "guardrail_policy_id": d.get("guardrail_policy_id"),
    }
    return structured, f"ワークスペース {structured['name']} ({structured['id']})"


def _tool_get_collection_info(a):
    _st, data = _api("GET", f"/api/collections?workspace_id={a['workspace_id']}", timeout=10)
    cols = data if isinstance(data, list) else []
    col = next((c for c in cols if c.get("id") == a["collection_id"]), None)
    if not col:
        raise NotFoundError(f"コレクション {a['collection_id']} が見つかりません")
    structured = {
        "id": col.get("id"),
        "name": col.get("name"),
        "status": col.get("status"),
        "chunk_count": col.get("chunk_count", 0),
        "access_level": col.get("access_level"),
        "created_at": col.get("created_at"),
        "allowed_roles": col.get("allowed_roles_json"),
    }
    return structured, f"コレクション {structured['name']} ({structured['status']}, {structured['chunk_count']}塊)"


def _tool_get_audit_logs(a):
    limit = min(int(a.get("limit", 10)), 50)
    _st, data = _api("GET", f"/api/audit-logs?workspace_id={a['workspace_id']}&limit={limit}", timeout=10)
    # API 側のキーは "items" (mcp-empty-list-fix-20260727)
    logs = _as_list(data, "items", "logs", "audit_logs")
    result = [
        {
            "timestamp": l.get("timestamp"),
            "action": l.get("action"),
            "target": l.get("target"),
            "detail": str(l.get("detail", ""))[:120],
        }
        for l in logs[:limit]
    ]
    structured = {"logs": result, "count": len(result)}
    return structured, f"監査ログ {len(result)}件"


def _tool_list_sources(a):
    _st, data = _api("GET", f"/api/sources?workspace_id={a['workspace_id']}", timeout=10)
    # /api/sources は素の JSON 配列を返す (mcp-empty-list-fix-20260727)
    sources = _as_list(data, "sources", "items")
    result = [
        {
            "id": s.get("id"),
            "name": s.get("name"),
            "path": s.get("path"),
            "status": s.get("status"),
            "file_count": s.get("file_count", 0),
        }
        for s in sources
    ]
    structured = {"sources": result, "count": len(result)}
    return structured, f"データソース {len(result)}件"


def _tool_publish_collection(a):
    # 開始だけを返す口 (publish/async) を叩き、job_id を即返す。
    # 進み具合は get_job_status。以前の同期版は埋め込みの計算で数分待たせていた。
    _st, d = _api("POST", f"/api/collections/{a['collection_id']}/publish/async", body={}, timeout=60)
    d = d if isinstance(d, dict) else {}
    structured = {
        "ok": True,
        "collection_id": a["collection_id"],
        "job_id": d.get("job_id"),
        "status": d.get("status"),
        "message": "公開を始めました。進み具合は get_job_status に job_id を渡して見てください。",
    }
    return structured, f"Publish 開始: {a['collection_id']} (job {structured['job_id']})"


def _tool_create_workspace(a):
    _st, d = _api("POST", "/api/workspaces", body={"name": a["name"], "description": a.get("description", "")}, timeout=10)
    if not isinstance(d, dict):
        raise ToolFailure(f"dict期待だが{type(d).__name__}が返った")
    structured = {"ok": True, "id": d.get("id"), "name": d.get("name"), "description": d.get("description")}
    return structured, f"ワークスペース作成: {structured['name']} ({structured['id']})"


# ─── 設定系の実装 ───
# 各対象の 読む口 / 書く口。pii だけ書き込みが PUT (routers/settings.py の実装どおり)。
_SETTINGS_KINDS = {
    "llm": ("GET", "/api/settings/llm", "POST", "/api/settings/llm"),
    "reranker": ("GET", "/api/settings/reranker", "POST", "/api/settings/reranker"),
    "classifier": ("GET", "/api/settings/classifier", "POST", "/api/settings/classifier"),
    "embedding": ("GET", "/api/settings/embedding", "POST", "/api/settings/embedding"),
    "pii": ("GET", "/api/settings/pii-mode", "PUT", "/api/settings/pii-mode"),
    "vector-store": ("GET", "/api/settings/vector-store", "POST", "/api/settings/vector-store"),
    "datasync": ("GET", "/api/settings/datasync", "POST", "/api/settings/datasync"),
}
_SECRET_ARG_KEYS = ("api_key", "qdrant_api_key")


def _strip_secrets(d) -> dict:
    """応答へ秘密の値を出さない (§5-C)。サーバの GET は *_set の bool しか返さないが、
    こちら側でも secret 名のキーは落とす (二重の守り)。"""
    if not isinstance(d, dict):
        return {}
    return {k: v for k, v in d.items() if k not in _SECRET_ARG_KEYS}


def _tool_settings_show(a):
    name = a.get("name") or "llm"
    g_m, g_p, _sm, _sp = _SETTINGS_KINDS[name]
    _st, d = _api(g_m, g_p, timeout=30)
    structured = {"name": name, "settings": _strip_secrets(d)}
    return structured, f"設定 {name}: " + json.dumps(structured["settings"], ensure_ascii=False)


def _tool_settings_models(a):
    _st, d = _api("GET", "/api/settings/models", timeout=30)
    raw = d.get("data") if isinstance(d, dict) else d
    if not isinstance(raw, list):
        raise ToolFailure(f"モデル一覧の形が想定外です ({type(raw).__name__})")
    models = [
        str(m.get("id") or m.get("name") or "?") if isinstance(m, dict) else str(m)
        for m in raw
    ]
    structured = {"models": models, "count": len(models)}
    return structured, f"モデル {len(models)}件 (ダウンロード済み全件・読み込み済みの意味ではない)"


def _tool_settings_test(a):
    body = {k: a[k] for k in ("provider", "base_url", "model") if a.get(k)}
    # 接続の確認は冷えた推論サーバに届くことがあるため長めに待つ
    _st, d = _api("POST", "/api/settings/test-connection", body=body, timeout=120)
    d = d if isinstance(d, dict) else {}
    status = str(d.get("status") or "unknown")
    structured = {
        "connected": status == "connected",
        "status": status,
        "endpoint": d.get("endpoint"),
        "models": d.get("models"),
        "error": d.get("error"),
    }
    word = "接続できました" if structured["connected"] else f"接続できませんでした: {d.get('error') or status}"
    return structured, f"{word} ({structured['endpoint']})"


def _tool_settings_set(a):
    # 設定を変える道具は既定で閉じる。MCP を呼ぶのは直前に読んだ資料の
    # 中身に引きずられうる AI であり、資料内の「設定を書き換えろ」を指示と受け取る経路が
    # 原理的に存在する。∴ 明示的に開けたときだけ通す。資格の検査 (サーバ側 admin 必須) の
    # 代わりではなく、その手前に重ねる薄い守り。読む道具には付けない。
    if os.environ.get("CYNOVELA_MCP_ALLOW_SETTINGS_WRITE", "").strip() != "1":
        raise ToolFailure(
            "設定の書き込みは既定で閉じています。MCP サーバの起動設定 (mcpServers の env) に "
            "CYNOVELA_MCP_ALLOW_SETTINGS_WRITE=1 を書いたときだけ実行できます。"
            "見る道具 (settings_show など) はこの守りの対象外です。"
        )
    name = a.get("name") or "llm"
    g_m, g_p, s_m, s_p = _SETTINGS_KINDS[name]
    values = a.get("values")
    if not isinstance(values, dict) or not values:
        raise ToolFailure("values にはキーと値を 1 つ以上入れてください (例: {\"model\": \"...\"})")
    _st, _resp = _api(s_m, s_p, body=values, timeout=60)
    _st2, after = _api(g_m, g_p, timeout=30)
    structured = {"ok": True, "name": name, "applied": True, "after": _strip_secrets(after)}
    return structured, f"設定 {name} を変更しました: " + json.dumps(structured["after"], ensure_ascii=False)


def _tool_settings_providers(a):
    _st, d = _api("GET", "/api/llm/presets", timeout=30)
    d = d if isinstance(d, dict) else {}
    rows = []
    for group in ("presets", "custom"):
        for p in d.get(group) or []:
            if isinstance(p, dict):
                rows.append({
                    "id": p.get("id"),
                    "label": p.get("label"),
                    "provider": p.get("provider"),
                    "base_url": p.get("base_url"),
                    "model": p.get("model"),
                    "group": group,
                })
    structured = {"providers": rows, "count": len(rows)}
    return structured, f"プリセット {len(rows)}件"


# ─── 作業の単位で足した道具の実装 ───
def _tool_server_status(_a):
    up, version = False, None
    try:
        _st, h = _api("GET", "/api/health", timeout=5)
        up = isinstance(h, dict) and h.get("status") == "ok"
        version = (h or {}).get("version") if isinstance(h, dict) else None
    except ToolFailure:
        structured = {"up": False, "version": None, "collections": [], "total_chunks": 0}
        return structured, "サーバは応答しません (起動していない可能性)"
    cols_out, total = [], 0
    try:
        _st2, cols = _api("GET", "/api/collections", timeout=15)
        for c in (cols if isinstance(cols, list) else []):
            n = int(c.get("chunk_count") or 0)
            total += n
            cols_out.append({"id": c.get("id"), "name": c.get("name"),
                             "status": c.get("status"), "chunk_count": n})
    except (NotFoundError, ToolFailure):
        pass
    structured = {"up": up, "version": version, "collections": cols_out, "total_chunks": total}
    return structured, f"稼働中 (v{version}) / まとまり{len(cols_out)}件・合計{total}塊"


def _tool_ingest_source(a):
    steps = []
    # 1) 取り込み元を足す (登録済み already / 容器形態では 400 → 資料の登録は続ける)
    try:
        _st, d_r = _api("POST", "/api/ingest-roots", body={"path": a["path"]}, timeout=30)
        steps.append({"step": "ingest-root", "ok": True, "result": d_r})
    except (NotFoundError, ToolFailure) as e:
        steps.append({"step": "ingest-root", "ok": False, "detail": str(e)[:200]})
    # 2) 資料として登録 (走査は 4 で開始だけを返す口を使う)
    name = a.get("name") or os.path.basename(a["path"].rstrip("/")) or a["path"]
    _st, d_s = _api("POST", "/api/sources",
                    body={"name": name, "path": a["path"], "auto_scan": False}, timeout=30)
    sid = (d_s or {}).get("id")
    steps.append({"step": "source", "ok": True, "id": sid, "name": name})
    # 3) 作業場所へ結び付け (任意)。PUT の source_ids は全置換のため現在の一覧に足して送る。
    if a.get("workspace_id"):
        _st, d_l = _api("GET", f"/api/sources?workspace_id={a['workspace_id']}", timeout=30)
        existing = [s.get("id") for s in (d_l if isinstance(d_l, list) else [])]
        ids = existing + ([sid] if sid not in existing else [])
        _api("PUT", f"/api/workspaces/{a['workspace_id']}", body={"source_ids": ids}, timeout=30)
        steps.append({"step": "workspace-link", "ok": True, "workspace_id": a["workspace_id"]})
    # 4) 走査を始める (開始だけを返す口)
    _st, d_j = _api("POST", f"/api/sources/{sid}/scan/async", timeout=30)
    job_id = (d_j or {}).get("job_id")
    steps.append({"step": "scan", "ok": True, "job_id": job_id})
    structured = {"ok": True, "source_id": sid, "job_id": job_id, "steps": steps}
    return structured, f"資料を登録し走査を始めました: source {sid} / job {job_id} (進み具合は get_job_status)"


def _tool_get_job_status(a):
    _st, d = _api("GET", f"/api/jobs/{a['job_id']}", timeout=15)
    d = d if isinstance(d, dict) else {}
    structured = {k: d.get(k) for k in ("kind", "status", "stage", "progress", "total", "message", "error")}
    return structured, (f"{structured.get('kind')} {structured.get('status')} "
                        f"{structured.get('progress')}/{structured.get('total')} {structured.get('message') or ''}")


def _tool_cancel_scan(a):
    _st, d = _api("POST", f"/api/sources/{a['source_id']}/scan/cancel", timeout=15)
    d = d if isinstance(d, dict) else {}
    structured = {"ok": bool(d.get("ok")), "status": d.get("status")}
    return structured, "走査に中止を要求しました"


def _tool_create_collection(a):
    _st, d = _api("POST", "/api/collections",
                  body={"name": a["name"], "workspace_id": a["workspace_id"]}, timeout=60)
    d = d if isinstance(d, dict) else {}
    cid = d.get("id")
    linked = 0
    if a.get("source_id") and cid:
        _st2, files = _api("GET", f"/api/sources/{a['source_id']}/files", timeout=60)
        fids = [f.get("id") for f in (files if isinstance(files, list) else [])
                if isinstance(f, dict) and not f.get("missing")]
        if fids:
            _api("POST", f"/api/collections/{cid}/link-files", body={"file_ids": fids}, timeout=60)
            linked = len(fids)
    structured = {"ok": True, "id": cid, "name": d.get("name"), "linked_files": linked}
    return structured, f"まとまりを作りました: {cid} (結び付けたファイル {linked}件)"


def _tool_publish_control(a):
    action = a["action"]
    _st, d = _api("POST", f"/api/collections/{a['collection_id']}/publish/{action}", timeout=60)
    structured = {"ok": True, "action": action, "result": d if isinstance(d, dict) else {}}
    return structured, f"publish {action}: " + json.dumps(structured["result"], ensure_ascii=False)


# ─── 既定で閉じる道具。settings_set と同じ形の env 門。───
_ADMIN_WRITE_TOOLS = ("delete_item", "manage_users", "manage_backups")


def _require_admin_write_open():
    if os.environ.get("CYNOVELA_MCP_ALLOW_ADMIN_WRITE", "").strip() != "1":
        raise ToolFailure(
            "この道具は既定で閉じています。MCP サーバの起動設定 (mcpServers の env) に "
            "CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を書いたときだけ実行できます。"
            "見る道具はこの守りの対象外です。"
        )


def _tool_delete_item(a):
    _require_admin_write_open()
    path = {"source": "/api/sources/{id}", "collection": "/api/collections/{id}",
            "workspace": "/api/workspaces/{id}"}[a["kind"]].format(id=a["id"])
    _api("DELETE", path, timeout=120)
    structured = {"ok": True, "kind": a["kind"], "id": a["id"]}
    return structured, f"{a['kind']} {a['id']} を消しました"


def _tool_manage_users(a):
    _require_admin_write_open()
    action = a["action"]
    if action == "list":
        _st, d = _api("GET", "/api/admin/users", timeout=30)
        users = [{k: u.get(k) for k in ("id", "username", "role", "is_active")}
                 for u in (d if isinstance(d, list) else [])]
        return {"ok": True, "action": action, "users": users}, f"利用者 {len(users)}件"
    if action == "create":
        body = {k: a[k] for k in ("username", "password", "role", "display_name") if a.get(k)}
        _st, d = _api("POST", "/api/admin/users", body=body, timeout=30)
        return ({"ok": True, "action": action, "result": d if isinstance(d, dict) else {}},
                f"利用者を作りました: {a.get('username')}")
    if action == "update":
        body = {}
        for src_k, dst_k in (("role", "role"), ("display_name", "display_name"), ("is_active", "is_active")):
            if src_k in a:
                body[dst_k] = a[src_k]
        _st, d = _api("PATCH", f"/api/admin/users/{a['user_id']}", body=body, timeout=30)
        return ({"ok": True, "action": action, "result": d if isinstance(d, dict) else {}},
                f"利用者を変えました: {a.get('user_id')}")
    if action == "delete":
        # purge=true で完全に消す。既定は従来どおり使えなくするだけ。
        _purge = bool(a.get("purge"))
        _qs = "?purge=true" if _purge else ""
        _st, d = _api("DELETE", f"/api/admin/users/{a['user_id']}{_qs}", timeout=30)
        return ({"ok": True, "action": action, "result": d if isinstance(d, dict) else {}},
                ("利用者を完全に消しました: " if _purge else "利用者を使えなくしました: ") + str(a.get("user_id")))
    if action == "reset_password":
        _st, d = _api("POST", f"/api/admin/users/{a['user_id']}/reset-password",
                      body={"password": a.get("password") or ""}, timeout=30)
        return ({"ok": True, "action": action, "result": d if isinstance(d, dict) else {}},
                f"合言葉を出し直しました: {a.get('user_id')}")
    raise ToolFailure(f"未知の action: {action}")


def _tool_manage_backups(a):
    _require_admin_write_open()
    action = a["action"]
    if action == "list":
        _st, d = _api("GET", "/api/admin/backups", timeout=30)
        items = d if isinstance(d, list) else (d or {}).get("items") or []
        return {"ok": True, "action": action, "backups": items}, f"控え {len(items)}件"
    if action == "create":
        _st, d = _api("POST", "/api/admin/backup", body={"label": a.get("label") or ""}, timeout=300)
        return ({"ok": True, "action": action, "result": d if isinstance(d, dict) else {}},
                f"控えを取りました: {(d or {}).get('name')}")
    if action == "restore":
        _st, d = _api("POST", f"/api/admin/backups/{a['name']}/restore", timeout=600)
        return ({"ok": True, "action": action, "result": d if isinstance(d, dict) else {}},
                f"控えを戻しました: {a.get('name')}")
    if action == "delete":
        _st, d = _api("DELETE", f"/api/admin/backups/{a['name']}", timeout=60)
        return ({"ok": True, "action": action, "result": d if isinstance(d, dict) else {}},
                f"控えを消しました: {a.get('name')}")
    raise ToolFailure(f"未知の action: {action}")


_TOOL_IMPL = {
    "search_collection": _tool_search_collection,
    "search_across_collections": _tool_search_across_collections,
    "rag_with_role": _tool_rag_with_role,
    "rag_general": _tool_rag_general,
    "list_workspaces": _tool_list_workspaces,
    "get_workspace_info": _tool_get_workspace_info,
    "get_collection_info": _tool_get_collection_info,
    "get_audit_logs": _tool_get_audit_logs,
    "list_sources": _tool_list_sources,
    "publish_collection": _tool_publish_collection,
    "create_workspace": _tool_create_workspace,
    "settings_show": _tool_settings_show,
    "settings_models": _tool_settings_models,
    "settings_test": _tool_settings_test,
    "settings_set": _tool_settings_set,
    "settings_providers": _tool_settings_providers,
    "server_status": _tool_server_status,
    "ingest_source": _tool_ingest_source,
    "get_job_status": _tool_get_job_status,
    "cancel_scan": _tool_cancel_scan,
    "create_collection": _tool_create_collection,
    "publish_control": _tool_publish_control,
    "delete_item": _tool_delete_item,
    "manage_users": _tool_manage_users,
    "manage_backups": _tool_manage_backups,
}

_TOOL_DEFS = {t["name"]: t for t in TOOLS}


def _validate_input(tool_def: dict, arguments: dict) -> str:
    """宣言した inputSchema の required / 素朴な型だけを検める。足りなければ理由を返す。"""
    schema = tool_def.get("inputSchema") or {}
    for key in schema.get("required", []):
        if key not in arguments:
            return f"必須の引数 {key} がありません"
    props = schema.get("properties") or {}
    for key, val in arguments.items():
        p = props.get(key)
        if not p:
            continue
        t = p.get("type")
        if t == "string" and not isinstance(val, str):
            return f"引数 {key} は string である必要があります"
        if t == "integer" and not isinstance(val, int):
            return f"引数 {key} は integer である必要があります"
        if t == "array" and not isinstance(val, list):
            return f"引数 {key} は array である必要があります"
        if t == "object" and not isinstance(val, dict):
            return f"引数 {key} は object である必要があります"
        enum_vals = p.get("enum")
        if enum_vals and val not in enum_vals:
            return f"引数 {key} は {enum_vals} のいずれかである必要があります"
    return ""


# ─────────────────────────────────────────
# JSON-RPC ループ (stdio・状態を持たない)
# ─────────────────────────────────────────
def _discover_result(protocol_version: str = PROTOCOL_VERSION) -> dict:
    return {
        "protocolVersion": protocol_version,
        "serverInfo": SERVER_INFO,
        "capabilities": {"tools": {"listChanged": False}},
    }


def handle(req: dict):
    method = req.get("method", "")
    rid = req.get("id")
    is_notification = ("id" not in req) or (rid is None)

    # 2026-07-28: 状態を持たない発見。握手も Mcp-Session-Id も要らない。
    if method == "server/discover":
        return {"jsonrpc": "2.0", "id": rid, "result": _discover_result()}

    # 旧世代クライアント互換: initialize が来ても同じ内容で応えるだけ。
    # 握手の完了 (notifications/initialized) は待たず、どの順でも全 method に応える。
    if method == "initialize":
        import re as _re
        req_ver = str(((req.get("params") or {}).get("protocolVersion")) or "")
        ver = req_ver if (_re.match(_REV_RE, req_ver) and req_ver <= PROTOCOL_VERSION) else PROTOCOL_VERSION
        return {"jsonrpc": "2.0", "id": rid, "result": _discover_result(ver)}

    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}

    if method == "tools/list":
        # 既定で閉じる道具は、開けたときだけ一覧に現れる。
        if os.environ.get("CYNOVELA_MCP_ALLOW_ADMIN_WRITE", "").strip() == "1":
            visible = TOOLS
        else:
            visible = [t for t in TOOLS if t["name"] not in _ADMIN_WRITE_TOOLS]
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": visible}}

    if method == "tools/call":
        params = req.get("params", {}) or {}
        name = params.get("name", "")
        # Bridge は <server>.<tool> 形式でツール名を渡すので prefix を剥がす
        if "." in name:
            name = name.split(".", 1)[1]
        arguments = params.get("arguments", {}) or {}
        impl = _TOOL_IMPL.get(name)
        if impl is None:
            return {
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -32602, "message": f"未知のツール: {name}"},
            }
        bad = _validate_input(_TOOL_DEFS[name], arguments)
        if bad:
            return {
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -32602, "message": bad},
            }
        try:
            structured, text = impl(arguments)
        except NotFoundError as e:
            # 資料が無いときは -32602
            return {
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -32602, "message": str(e)},
            }
        except ToolFailure as e:
            return {
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "content": [{"type": "text", "text": str(e)}],
                    "structuredContent": {"error": str(e)},
                    "isError": True,
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "content": [{"type": "text", "text": f"エラー: {type(e).__name__}: {e}"}],
                    "structuredContent": {"error": f"{type(e).__name__}: {e}"},
                    "isError": True,
                },
            }
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "content": [{"type": "text", "text": text}],
                "structuredContent": structured,
                "isError": False,
            },
        }

    # 不明 method: notification なら無応答、それ以外はエラー
    if is_notification:
        return None
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}}


if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            # パース失敗時のみ id=null で返す
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}},
                             ensure_ascii=False), flush=True)
            continue
        try:
            resp = handle(req)
        except Exception as e:
            resp = {"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32603, "message": str(e)}}
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False), flush=True)
