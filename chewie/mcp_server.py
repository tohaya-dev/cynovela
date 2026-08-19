#!/usr/bin/env python3
"""Cynovela MCP Server v3.0 — protocol 2026-07-28 (stdio).

DD-CYN-0140 §5-K: 2024-11-05 世代の手書き JSON-RPC を現行仕様へ作り直した。
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
SERVER_INFO = {"name": "cynovela-mcp", "version": "3.0"}
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# ─────────────────────────────────────────
# ツール定義 (16本。全て実在する REST の口だけを叩く — DD-CYN-0140 §4 Agent D 実測、
#             設定系5本は DD-CYN-0141 §5-C)
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
            "指定コレクションをPublish（公開）します。"
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
    # ─── 設定系 (DD-CYN-0141 §5-C。管理者トークンが必要。API キーの値は入力にだけ現れ、
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
    frags = [
        {
            "file_name": str(c.get("source_filename") or "?"),
            "score": float(c.get("score") or 0),
            "text": str(c.get("chunk_preview") or "")[:300],
        }
        for c in (d.get("citations") or [])[:limit]
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
    # §6-6-2: Publish は埋め込みの計算を伴い 120 秒を超えることがある
    _st, d = _api("POST", f"/api/collections/{a['collection_id']}/publish", body={}, timeout=600)
    d = d if isinstance(d, dict) else {}
    structured = {
        "ok": True,
        "collection_id": a["collection_id"],
        "status": d.get("status"),
        "message": d.get("message", "Publish成功"),
    }
    return structured, f"Publish 完了: {a['collection_id']} ({structured['status']})"


def _tool_create_workspace(a):
    _st, d = _api("POST", "/api/workspaces", body={"name": a["name"], "description": a.get("description", "")}, timeout=10)
    if not isinstance(d, dict):
        raise ToolFailure(f"dict期待だが{type(d).__name__}が返った")
    structured = {"ok": True, "id": d.get("id"), "name": d.get("name"), "description": d.get("description")}
    return structured, f"ワークスペース作成: {structured['name']} ({structured['id']})"


# ─── 設定系の実装 (DD-CYN-0141 §5-C) ───
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
    # DD-CYN-0141 §5-B: 設定を変える道具は既定で閉じる。MCP を呼ぶのは直前に読んだ資料の
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
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

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
            # 資料が無いときは -32602 (DD-CYN-0140 §5-K-1)
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
