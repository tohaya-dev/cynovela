#!/usr/bin/env python3
"""Cynovela CLI — use Cynovela from the terminal / ターミナルから Cynovela を使う.

DD-CYN-0140 §5-J. Standard library only. Talks only to the REST API — it never
reads the database, store/, or the configuration behind the server's back
(doctor inspects local files read-only, and changes nothing).

Commands (all read-only; nothing here changes server state):
  doctor        What is missing right now, and the one line to run next.
                Works even when the server is not running.
  status        Is the server up? (GET /api/health)
  search        Search and return source fragments (no answer is shown).
  workspaces    List workspaces.
  collections   List collections (optionally per workspace).
  index-status  Chunk counts per collection.

Exit codes:  0 = OK   1 = bad user input   2 = server unreachable
             3 = authentication failed    4 = server returned an error

Configuration (checked in this order):
  --url / --token flags  >  ~/.cynovela_cli.env (CYNOVELA_URL= / CYNOVELA_TOKEN=)
  Default URL: http://127.0.0.1:8765
  The token is the value issued when you sign in on the web screen.

Language: --lang en|ja (default: ja when LANG/LC_ALL contains "ja", else en).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# ─── exit codes (§5-J-1) ───────────────────────────────────────
EXIT_OK = 0
EXIT_USER = 1
EXIT_UNREACHABLE = 2
EXIT_AUTH = 3
EXIT_SERVER = 4


# ─── language ──────────────────────────────────────────────────
def _default_lang() -> str:
    for k in ("LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(k, "")
        if "ja" in v.lower():
            return "ja"
    return "en"


MSG = {
    "unreachable": {
        "en": "Cannot reach the server at {url}. Is Cynovela running? Start it with: ./launch.sh",
        "ja": "サーバ {url} へ到達できません。Cynovela は起動していますか？ 起動は: ./launch.sh",
    },
    "auth_failed": {
        "en": "Authentication failed ({code}). Pass the token issued at web sign-in via --token or ~/.cynovela_cli.env (CYNOVELA_TOKEN=...).",
        "ja": "認証に失敗しました ({code})。画面のログインで発行されたトークンを --token か ~/.cynovela_cli.env の CYNOVELA_TOKEN= で渡してください。",
    },
    "server_error": {
        "en": "The server returned an error ({code}): {detail}",
        "ja": "サーバが誤りを返しました ({code}): {detail}",
    },
    "search_note": {
        "en": "Note: search shows source fragments only. The server generates an answer internally, but it is not shown here (use the web screen or the chat for answers).",
        "ja": "注意: search は出典の断片だけを表示します。サーバは内部で回答も生成しますが、ここには表示しません（回答が要るときは画面かチャットを使ってください）。",
    },
    "index_note": {
        "en": "Note: there is no dedicated index endpoint; these figures are the chunk_count values from GET /api/collections.",
        "ja": "注意: 索引専用の口は無いため、この数字は GET /api/collections の chunk_count です。",
    },
}


def _m(key: str, lang: str, **kw) -> str:
    return MSG[key][lang].format(**kw)


# ─── config file (same file as the older cynovela_cli.py: G-2) ─
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


# ─── tiny cynovela.yaml reader (doctor only; no yaml dependency) ─
def _yaml_scalar(text: str, section: str, key: str) -> str:
    """Pull `section:` → indented `key: value` out of cynovela.yaml, no library."""
    in_section = False
    for line in text.splitlines():
        if re.match(rf"^{re.escape(section)}\s*:", line):
            in_section = True
            continue
        if in_section:
            if line and not line[0].isspace() and not line.startswith("#"):
                break  # next top-level key
            m = re.match(rf"^\s+{re.escape(key)}\s*:\s*(.*?)\s*(#.*)?$", line)
            if m:
                return m.group(1).strip().strip("'\"")
    return ""


# ─── HTTP (urllib, stdlib only) ────────────────────────────────
class Ctx:
    def __init__(self, url: str, token: str, lang: str, as_json: bool):
        self.url = url.rstrip("/")
        self.token = token
        self.lang = lang
        self.as_json = as_json


def _request(ctx: Ctx, method: str, path: str, body=None, timeout: float = 60.0):
    """Return (status, data). status 0 means connection failure."""
    headers = {"Accept": "application/json"}
    if ctx.token:
        headers["Authorization"] = f"Bearer {ctx.token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(f"{ctx.url}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw or b"null")
            except Exception:
                return r.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        return e.code, detail
    except Exception as e:
        return 0, str(e)


def _fail(ctx: Ctx, command: str, status: int, detail) -> int:
    """Map an HTTP failure to the unified exit codes and print it."""
    if status == 0:
        code, msg = EXIT_UNREACHABLE, _m("unreachable", ctx.lang, url=ctx.url)
    elif status in (401, 403):
        code, msg = EXIT_AUTH, _m("auth_failed", ctx.lang, code=status)
    else:
        code, msg = EXIT_SERVER, _m("server_error", ctx.lang, code=status, detail=str(detail)[:200])
    if ctx.as_json:
        print(json.dumps({"ok": False, "command": command, "exit_code": code,
                          "error": {"http_status": status, "message": msg}}, ensure_ascii=False))
    else:
        print(msg, file=sys.stderr)
    return code


def _ok(ctx: Ctx, command: str, data, text_lines) -> int:
    if ctx.as_json:
        print(json.dumps({"ok": True, "command": command, "exit_code": EXIT_OK, "data": data},
                         ensure_ascii=False, indent=2))
    else:
        for line in text_lines:
            print(line)
    return EXIT_OK


# ─── doctor ────────────────────────────────────────────────────
def _http_probe(url: str, timeout: float = 3.0):
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()[:400]
    except Exception as e:
        return None, str(e)


def _model_snapshot(name: str):
    """Same look as the in-app judgement: snapshots/<hash>/ must be a non-empty dir.

    Candidate order mirrors config.resolve_model_path (DD-CYN-0139: all 6 sites
    look only at snapshots/<hash>/ being a non-empty directory).
    """
    folder = "models--" + name.replace("/", "--")
    candidates = [
        APP_DIR / "store" / "models" / folder,
        APP_DIR.parent / folder,
        Path.home() / ".cynovela" / "models" / folder,
        Path.home() / ".cynovela" / "hf_cache" / folder,
        Path.home() / ".cache" / "huggingface" / "hub" / folder,
    ]
    for base in candidates:
        snaps = sorted((base / "snapshots").glob("*"), reverse=True)
        for snap in snaps:
            if snap.is_dir() and any(snap.iterdir()):
                return str(snap)
    return ""


def cmd_doctor(ctx: Ctx, _args) -> int:
    """Report what is missing and the next line to run. Never dies because the
    server is down — reporting that state is exactly this command's job."""
    ja = ctx.lang == "ja"
    checks = []

    def add(name_en, name_ja, ok, detail, next_en="", next_ja=""):
        checks.append({
            "check": name_ja if ja else name_en,
            "ok": ok,
            "detail": detail,
            "next": (next_ja if ja else next_en) if not ok else "",
        })

    # 1) Python
    py_ok = sys.version_info >= (3, 12)
    add("Python version", "Python の版", py_ok,
        f"{sys.version.split()[0]} ({sys.executable})",
        "Install Python 3.12 or later, or run ./launch.sh --setup (it prepares one).",
        "Python 3.12 以上を入れるか、./launch.sh --setup を実行してください（環境ごと用意されます）。")

    # 2) models
    for mname in ("BAAI/bge-m3", "BAAI/bge-reranker-v2-m3"):
        snap = _model_snapshot(mname)
        add(f"Model {mname}", f"モデル {mname}", bool(snap),
            snap or ("not found (snapshots/<hash>/ missing or empty)" if not ja else "見つかりません（snapshots/<hash>/ が無いか空です）"),
            "Download the models file from the release page and place it under store/models/ (see START-HERE.md section 1), or let the first ./launch.sh fetch it.",
            "リリースページのモデルのファイルを落として store/models/ に置くか（START-HERE.md の1節）、初回の ./launch.sh に取得させてください。")

    # 3) inference servers (both looked at; neither present is reported, not fatal)
    yaml_text = ""
    try:
        yaml_text = (APP_DIR / "cynovela.yaml").read_text(encoding="utf-8")
    except Exception:
        pass
    llm_base = _yaml_scalar(yaml_text, "execution", "llm_base_url") or "http://localhost:1234"
    st_lm, _ = _http_probe(f"{llm_base.rstrip('/')}/v1/models")
    st_ol, _ = _http_probe("http://localhost:11434/api/tags")
    lm_up, ol_up = st_lm == 200, st_ol == 200
    add("Inference server (LLM)", "推論サーバ（LLM）", lm_up or ol_up,
        f"LM Studio({llm_base}): {'up' if lm_up else 'down'} / Ollama(localhost:11434): {'up' if ol_up else 'down'}",
        "Neither LM Studio nor Ollama answered. Start LM Studio and load a model, or `ollama serve`. Questions cannot be answered without one.",
        "LM Studio も Ollama も応答しません。LM Studio を起動してモデルを読み込むか、`ollama serve` を実行してください。どちらも居ないと質問に答えられません。")

    # 4) port
    try:
        port = int(_yaml_scalar(yaml_text, "server", "port") or "8765")
    except ValueError:
        port = 8765
    in_use = False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            in_use = True
    except OSError:
        pass
    if in_use:
        st_h, _ = _http_probe(f"http://127.0.0.1:{port}/api/health")
        who = ("Cynovela is answering there" if st_h == 200 else "another process holds it") if not ja else \
              ("Cynovela がそこで応答しています" if st_h == 200 else "別のプロセスが使っています")
        add(f"Port {port}", f"番号 {port}", st_h == 200, f"in use — {who}" if not ja else f"使用中 — {who}",
            f"Stop the other process, or start with ./launch.sh --port <other-number>.",
            f"そのプロセスを止めるか、./launch.sh --port <別の番号> で起動してください。")
    else:
        add(f"Port {port}", f"番号 {port}", True,
            "free (the server is not running yet)" if not ja else "空いています（サーバは未起動です）")

    # 5) database
    for rel in ("store/db/cynovela.db", "store/db/demo.db"):
        p = APP_DIR / rel
        if p.is_file():
            add(f"Database {rel}", f"データベース {rel}", True, f"{p} ({p.stat().st_size:,} bytes)")
        else:
            add(f"Database {rel}", f"データベース {rel}", True,
                ("not created yet — made at first start" if not ja else "まだありません — 初回の起動で作られます"))

    # 6) conda (absence is fine: source-edition choice 2 works without it)
    conda = shutil.which("conda") or next(
        (str(p) for p in (Path.home() / "miniforge3" / "bin" / "conda",
                          Path("/opt/homebrew/bin/conda")) if p.exists()), "")
    add("conda", "conda", True,
        conda or ("not found — fine: the package edition and source-edition choice 2 run without conda"
                  if not ja else "見つかりません — 問題ありません: パッケージ版とソース版の選択肢2 は conda 無しで動きます"))

    lines = []
    for c in checks:
        mark = "OK " if c["ok"] else "NG "
        lines.append(f"[{mark}] {c['check']}: {c['detail']}")
        if c["next"]:
            lines.append(("    next: " if not ja else "    次に打つ1行: ") + c["next"])
    n_ng = sum(1 for c in checks if not c["ok"])
    lines.append(("-- doctor finished: %d item(s) need attention" % n_ng) if not ja
                 else ("-- doctor 完了: 直すものは %d 件です" % n_ng))
    return _ok(ctx, "doctor", {"checks": checks, "needs_attention": n_ng}, lines)


# ─── read-only server commands ─────────────────────────────────
def cmd_status(ctx: Ctx, _args) -> int:
    status, data = _request(ctx, "GET", "/api/health", timeout=5)
    if status != 200:
        return _fail(ctx, "status", status, data)
    txt = ["server: up", f"url: {ctx.url}", json.dumps(data, ensure_ascii=False)] if ctx.lang == "en" else \
          ["サーバ: 稼働中", f"接続先: {ctx.url}", json.dumps(data, ensure_ascii=False)]
    return _ok(ctx, "status", {"health": data, "url": ctx.url}, txt)


def cmd_workspaces(ctx: Ctx, _args) -> int:
    status, data = _request(ctx, "GET", "/api/workspaces", timeout=15)
    if status != 200:
        return _fail(ctx, "workspaces", status, data)
    ws = data if isinstance(data, list) else []
    lines = [f"{w.get('id','?')}\t{w.get('name','?')}" for w in ws]
    lines.append(f"({len(ws)} workspaces)" if ctx.lang == "en" else f"（ワークスペース {len(ws)}件）")
    return _ok(ctx, "workspaces", {"workspaces": ws, "count": len(ws)}, lines)


def cmd_collections(ctx: Ctx, args) -> int:
    qs = f"?workspace_id={args.workspace}" if args.workspace else ""
    status, data = _request(ctx, "GET", f"/api/collections{qs}", timeout=15)
    if status != 200:
        return _fail(ctx, "collections", status, data)
    cols = data if isinstance(data, list) else []
    lines = [f"{c.get('id','?')}\t{c.get('name','?')}\t{c.get('status','-')}\t{c.get('access_level','-')}" for c in cols]
    lines.append(f"({len(cols)} collections)" if ctx.lang == "en" else f"（コレクション {len(cols)}件）")
    return _ok(ctx, "collections", {"collections": cols, "count": len(cols)}, lines)


def cmd_search(ctx: Ctx, args) -> int:
    body = {
        "query": args.query,
        "workspace_id": args.workspace,
        "collection_ids": [args.collection],
        "preset": args.preset,
    }
    status, data = _request(ctx, "POST", "/api/chat", body=body, timeout=300)
    if status != 200:
        return _fail(ctx, "search", status, data)
    data = data if isinstance(data, dict) else {}
    # /api/chat の "sources" はファイル名の文字列一覧。断片の本文とスコアは
    # "citations" (source_filename / chunk_preview / score) に入っている。
    frags = []
    for c in data.get("citations") or []:
        if isinstance(c, dict):
            frags.append({
                "file_name": str(c.get("source_filename") or "?"),
                "score": float(c.get("score") or 0),
                "text": str(c.get("chunk_preview") or "")[:300],
            })
    if not frags:
        for s in data.get("sources") or []:
            if isinstance(s, dict):
                frags.append({
                    "file_name": str(s.get("file_name") or s.get("source_doc") or s.get("filename") or "?"),
                    "score": float(s.get("score") or 0),
                    "text": str(s.get("text") or s.get("preview") or "")[:300],
                })
            else:
                frags.append({"file_name": str(s)[:200], "score": 0.0, "text": ""})
    lines = [_m("search_note", ctx.lang)]
    for i, f in enumerate(frags):
        lines.append(f"[{i+1}] {f['file_name']} (score={f['score']:.3f})")
        if f["text"]:
            lines.append(f"    {f['text']}")
    lines.append(f"({len(frags)} source fragments)" if ctx.lang == "en" else f"（出典の断片 {len(frags)}件）")
    return _ok(ctx, "search", {"sources": frags, "source_count": len(frags),
                               "note": _m("search_note", ctx.lang)}, lines)


def cmd_index_status(ctx: Ctx, args) -> int:
    qs = f"?workspace_id={args.workspace}" if args.workspace else ""
    status, data = _request(ctx, "GET", f"/api/collections{qs}", timeout=15)
    if status != 200:
        return _fail(ctx, "index-status", status, data)
    cols = data if isinstance(data, list) else []
    rows = [{"id": c.get("id"), "name": c.get("name"), "status": c.get("status"),
             "chunk_count": int(c.get("chunk_count") or 0)} for c in cols]
    total = sum(r["chunk_count"] for r in rows)
    lines = [_m("index_note", ctx.lang)]
    for r in rows:
        lines.append(f"{r['id']}\t{r['name']}\t{r['status']}\t{r['chunk_count']}")
    lines.append((f"total: {total} chunks in {len(rows)} collections") if ctx.lang == "en"
                 else (f"合計: {len(rows)}コレクション {total}塊"))
    return _ok(ctx, "index-status", {"collections": rows, "total_chunks": total,
                                     "note": _m("index_note", ctx.lang)}, lines)


# ─── argparse (exit code 1 on bad input, not argparse's 2) ─────
class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: {message}", file=sys.stderr)
        sys.exit(EXIT_USER)


def build_parser() -> Parser:
    p = Parser(prog="cynovela-cli", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", help="server URL (default: ~/.cynovela_cli.env CYNOVELA_URL, else http://127.0.0.1:8765)")
    p.add_argument("--token", help="Bearer token (default: ~/.cynovela_cli.env CYNOVELA_TOKEN)")
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    p.add_argument("--lang", choices=["en", "ja"], help="message language (default: from LANG)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="what is missing right now (works without the server)")
    sub.add_parser("status", help="is the server up (GET /api/health)")
    sub.add_parser("workspaces", help="list workspaces")

    p_col = sub.add_parser("collections", help="list collections")
    p_col.add_argument("--workspace", help="filter by workspace_id")

    p_se = sub.add_parser("search", help="search; shows source fragments only (no answer)")
    p_se.add_argument("--workspace", required=True, help="workspace_id (see: workspaces)")
    p_se.add_argument("--collection", required=True, help="collection_id (see: collections)")
    p_se.add_argument("--query", required=True, help="query text")
    p_se.add_argument("--preset", choices=["lite", "standard", "hq"], default="standard")

    p_ix = sub.add_parser("index-status", help="chunk counts per collection")
    p_ix.add_argument("--workspace", help="filter by workspace_id")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    env = _load_env_file(Path.home() / ".cynovela_cli.env")
    ctx = Ctx(
        url=args.url or env.get("CYNOVELA_URL") or "http://127.0.0.1:8765",
        token=args.token or env.get("CYNOVELA_TOKEN") or "",
        lang=args.lang or _default_lang(),
        as_json=bool(args.json),
    )
    dispatch = {
        "doctor": cmd_doctor,
        "status": cmd_status,
        "workspaces": cmd_workspaces,
        "collections": cmd_collections,
        "search": cmd_search,
        "index-status": cmd_index_status,
    }
    return dispatch[args.cmd](ctx, args)


if __name__ == "__main__":
    sys.exit(main())
