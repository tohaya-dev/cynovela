#!/usr/bin/env python3
"""Cynovela CLI クライアント (PHASE B-2).

Cynovela サーバーへ HTTP API でアクセスする薄いラッパー。
標準ライブラリのみで実装し、追加依存なしで動作する。

使用方法:
  ~/.cynovela_cli.env に次の 2 行を書く (環境変数では受け取らない):
    CYNOVELA_URL=http://100.x.x.x:8765
    CYNOVELA_TOKEN=<ログインで発行されたトークン>   # 任意。Bearer Authorization に使う

  python scripts/cynovela_cli.py status
  python scripts/cynovela_cli.py workspaces list
  python scripts/cynovela_cli.py collections list --workspace WS_ID
  python scripts/cynovela_cli.py scan --source SRC_ID
  python scripts/cynovela_cli.py publish --collection COL_ID
  python scripts/cynovela_cli.py chat --workspace WS_ID --query "質問文"
  python scripts/cynovela_cli.py chat --workspace WS_ID --query "..." --mode standard

設定ファイル:
  ~/.cynovela_cli.env  →  KEY=VALUE 形式で CYNOVELA_URL / CYNOVELA_TOKEN を読み込む
                         (環境変数より優先度は低い)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


# ─── 設定ロード ─────────────────────────────────────────────────
def _load_env_file(path: Path) -> dict:
    out: dict = {}
    if not path.is_file():
        return out
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


_env_file = _load_env_file(Path.home() / ".cynovela_cli.env")


def _cfg(key: str, default: str = "") -> str:
    # DD-CYN-0067 G-2: 環境変数からは受け取らない。出どころは ~/.cynovela_cli.env の 1 本。
    return _env_file.get(key) or default


BASE_URL = _cfg("CYNOVELA_URL", "http://127.0.0.1:8765").rstrip("/")
TOKEN = _cfg("CYNOVELA_TOKEN", "")


# ─── HTTP ヘルパ (urllib) ────────────────────────────────────────
def _request(method: str, path: str, body: Any = None, timeout: float = 60.0) -> tuple[int, Any]:
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw or b"null")
            except Exception:
                return r.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return e.code, body_text
    except Exception as e:
        return 0, f"connection error: {e}"


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ─── コマンド実装 ──────────────────────────────────────────────
def cmd_status(_args) -> int:
    code, data = _request("GET", "/api/health", timeout=5)
    if code == 200:
        print(f"✅ 接続OK: {BASE_URL}")
        _print_json(data)
        return 0
    print(f"❌ 接続失敗 ({code}): {data}", file=sys.stderr)
    return 1


def cmd_workspaces_list(_args) -> int:
    code, data = _request("GET", "/api/workspaces")
    if code != 200:
        print(f"FAIL ({code}): {data}", file=sys.stderr)
        return 1
    if isinstance(data, list):
        for ws in data:
            wid = ws.get("id", "?")
            name = ws.get("name", "?")
            print(f"{wid}\t{name}")
        return 0
    _print_json(data)
    return 0


def cmd_collections_list(args) -> int:
    qs = f"?workspace_id={args.workspace}" if args.workspace else ""
    code, data = _request("GET", f"/api/collections{qs}")
    if code != 200:
        print(f"FAIL ({code}): {data}", file=sys.stderr)
        return 1
    if isinstance(data, list):
        for c in data:
            print(f"{c.get('id','?')}\t{c.get('name','?')}\t{c.get('access_level','-')}")
        return 0
    _print_json(data)
    return 0


def cmd_scan(args) -> int:
    if not args.source:
        print("--source SRC_ID は必須です", file=sys.stderr)
        return 2
    code, data = _request("POST", f"/api/sources/{args.source}/scan", body={})
    print(f"scan trigger: status={code}")
    _print_json(data)
    # 完了をポーリング
    deadline = time.time() + 120
    while time.time() < deadline:
        c2, d2 = _request("GET", f"/api/sources/{args.source}", timeout=10)
        if c2 == 200 and isinstance(d2, dict) and d2.get("status") in ("completed", "idle"):
            print(f"✅ scan {d2.get('status')}: file_count={d2.get('file_count', '?')}")
            return 0
        time.sleep(1)
    print("⏱️  scan タイムアウト (120s) — サーバー側でまだ進行中の可能性", file=sys.stderr)
    return 1


def cmd_publish(args) -> int:
    if not args.collection:
        print("--collection COL_ID は必須です", file=sys.stderr)
        return 2
    code, data = _request("POST", f"/api/collections/{args.collection}/publish", body={}, timeout=600)
    print(f"publish: status={code}")
    _print_json(data)
    return 0 if code in (200, 201, 202) else 1


def cmd_chat(args) -> int:
    if not args.workspace or not args.query:
        print("--workspace WS_ID と --query 'テキスト' は必須です", file=sys.stderr)
        return 2
    body: dict = {"query": args.query, "workspace_id": args.workspace, "temperature": float(args.temperature)}
    if args.mode:
        # PHASE A-7 の preset (lite/standard/hq)
        body["preset"] = args.mode
    if args.role:
        body["role_override"] = args.role
    if args.session:
        body["session_id"] = args.session
    code, data = _request("POST", "/api/chat", body=body, timeout=300)
    if code != 200:
        print(f"FAIL ({code}): {data}", file=sys.stderr)
        return 1
    if isinstance(data, dict):
        print(data.get("answer", "(empty answer)"))
        srcs = data.get("sources") or []
        if srcs and not args.no_sources:
            print("\n--- sources ---")
            for s in srcs[:10]:
                if isinstance(s, dict):
                    print(f"  - {s.get('source_doc') or s.get('filename') or s.get('preview','')[:80]}")
                else:
                    print(f"  - {s}")
        return 0
    _print_json(data)
    return 0


# ─── argparse 構築 ──────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cynovela_cli", description="Cynovela CLI クライアント")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="サーバー疎通確認 (/api/health)")

    p_ws = sub.add_parser("workspaces", help="ワークスペース操作")
    p_ws_sub = p_ws.add_subparsers(dest="ws_cmd", required=True)
    p_ws_sub.add_parser("list", help="ワークスペース一覧")

    p_col = sub.add_parser("collections", help="コレクション操作")
    p_col_sub = p_col.add_subparsers(dest="col_cmd", required=True)
    p_col_list = p_col_sub.add_parser("list", help="コレクション一覧")
    p_col_list.add_argument("--workspace", help="絞り込み workspace_id (任意)")

    p_scan = sub.add_parser("scan", help="ソースをスキャン")
    p_scan.add_argument("--source", required=True, help="ソース ID")

    p_pub = sub.add_parser("publish", help="コレクションを Publish")
    p_pub.add_argument("--collection", required=True, help="コレクション ID")

    p_chat = sub.add_parser("chat", help="RAG チャット送信")
    p_chat.add_argument("--workspace", required=True, help="workspace_id")
    p_chat.add_argument("--query", required=True, help="質問文")
    p_chat.add_argument("--mode", choices=["lite", "standard", "hq"], default=None, help="RAG プリセット (PHASE A-7)")
    p_chat.add_argument("--role", help="role_override (admin/viewer 等)")
    p_chat.add_argument("--session", help="session_id (継続会話)")
    p_chat.add_argument("--temperature", default=0.1, help="LLM temperature (default 0.1)")
    p_chat.add_argument("--no-sources", action="store_true", help="sources を表示しない")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "workspaces" and args.ws_cmd == "list":
        return cmd_workspaces_list(args)
    if args.cmd == "collections" and args.col_cmd == "list":
        return cmd_collections_list(args)
    if args.cmd == "scan":
        return cmd_scan(args)
    if args.cmd == "publish":
        return cmd_publish(args)
    if args.cmd == "chat":
        return cmd_chat(args)
    print(f"未知のコマンド: {args.cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
