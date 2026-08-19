#!/usr/bin/env python3
"""Cynovela CLI — use Cynovela from the terminal / ターミナルから Cynovela を使う.

DD-CYN-0140 §5-J. Standard library only. Talks only to the REST API — it never
reads the database, store/, or the configuration behind the server's back
(doctor inspects local files read-only, and changes nothing).

Commands (read-only except `settings set`, which never runs without an explicit --yes):
  doctor        What is missing right now, and the one line to run next.
                Works even when the server is not running.
  status        Is the server up? (GET /api/health)
  search        Search and return source fragments (no answer is shown).
  workspaces    List workspaces.
  collections   List collections (optionally per workspace).
  index-status  Chunk counts per collection.
  settings      Show or change server settings (admin token required; DD-CYN-0141 §5-A):
                  settings show [llm|reranker|classifier|embedding|pii|vector-store|datasync]
                  settings models       models visible at the configured endpoint
                  settings test         test the LLM connection (words, not codes)
                  settings providers    selectable provider presets
                  settings set [name] --set KEY=VALUE ...  (--dry-run to preview;
                                        nothing is written unless --yes is given)
                API keys are write-only: `settings show` prints set / not set, never values.

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
    "settings_need_yes": {
        "en": "Not applied. Re-run the same line with --yes to apply the change shown above.",
        "ja": "まだ変更していません。上に並べた変更を実行するには、同じ行に --yes を付けて打ち直してください。",
    },
    "settings_dry_run": {
        "en": "Dry run: nothing was changed.",
        "ja": "確認だけの実行です: 何も変更していません。",
    },
    "settings_secret_note": {
        "en": "API keys are write-only here: shown as set / not set, never as values.",
        "ja": "APIキーは書き込み専用です: 値は表示せず、設定あり / なし だけを示します。",
    },
    "settings_bad_pair": {
        "en": "--set expects KEY=VALUE. Allowed keys for '{name}': {keys}",
        "ja": "--set は KEY=VALUE の形で指定してください。'{name}' で使える KEY: {keys}",
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

    # 3b) 設定されたモデルが実際に読み込まれているか (DD-CYN-0141 §5-D)。
    #    /v1/models はダウンロード済み全件で読み込み状態を持たない。読み込み状態は
    #    LM Studio の /api/v0/models にしか無い。口が無い接続先では判定できない旨を出す。
    #    質問がタイムアウトになるとき、サーバの回答文と同じ言葉をここで事前に言う。
    def _fetch_json(url: str):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as r:
                return json.loads(r.read())
        except Exception:
            return None

    if lm_up:
        v0 = _fetch_json(f"{llm_base.rstrip('/')}/api/v0/models")
        if v0 is None:
            add("Loaded model", "読み込み済みモデル", True,
                ("cannot judge: this endpoint has no /api/v0/models (load state is only visible on LM Studio)"
                 if not ja else
                 "判定できません: この接続先に /api/v0/models がありません（読み込み状態は LM Studio でのみ見えます）"))
        else:
            items = v0.get("data") or []
            loaded = [m.get("id") for m in items
                      if isinstance(m, dict) and m.get("state") == "loaded" and m.get("id")
                      and not any(h in str(m.get("id")).lower() for h in ("embed", "embedding", "rerank", "reranker"))]
            cfg_model = ""
            if ctx.token:
                st_llm, d_llm = _request(ctx, "GET", "/api/settings/llm", timeout=5)
                if st_llm == 200 and isinstance(d_llm, dict):
                    cfg_model = str(d_llm.get("model") or "")
            if cfg_model and cfg_model not in ("auto",):
                ok_loaded = cfg_model in loaded
                add("Loaded model", "読み込み済みモデル", ok_loaded,
                    (f"configured model: {cfg_model} — {'loaded' if ok_loaded else 'NOT loaded'} (loaded now: {len(loaded)})"
                     if not ja else
                     f"設定されたモデル: {cfg_model} — {'読み込み済み' if ok_loaded else '未読込'}（現在読み込み済み {len(loaded)}件）"),
                    f"The configured model '{cfg_model}' is not loaded on the inference server yet. "
                    "Next step: load it in LM Studio, or pick an already-loaded model in the settings "
                    "(the web Settings screen / cynovela-cli settings set llm / MCP settings_set).",
                    f"設定されたモデル『{cfg_model}』は推論サーバにまだ読み込まれていません。"
                    "次の一手: LM Studio でこのモデルを読み込むか、設定（画面の Settings / "
                    "cynovela-cli settings set llm / MCP settings_set）で読み込み済みのモデルを選んでください。")
            else:
                add("Loaded model", "読み込み済みモデル", bool(loaded),
                    (f"{len(loaded)} chat-capable model(s) loaded" + ("" if ctx.token else " (pass --token to also check the configured model)")
                     if not ja else
                     f"チャットに使えるモデル {len(loaded)}件が読み込み済み" + ("" if ctx.token else "（--token を渡すと設定モデルとの照合もします）")),
                    "No model is loaded on the inference server. Load one in LM Studio; questions will time out until then.",
                    "推論サーバに読み込み済みのモデルがありません。LM Studio でモデルを読み込んでください。それまで質問はタイムアウトになります。")

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


# ─── settings (DD-CYN-0141 §5-A; REST only, admin token required) ─
# 各対象の 読む口 / 書く口 / 書ける KEY。pii だけ書き込みが PUT である
# (routers/settings.py の実装どおり)。KEY の型は送る前の変換にだけ使う。
SETTINGS_KINDS = {
    "llm": {"get": ("GET", "/api/settings/llm"), "set": ("POST", "/api/settings/llm"),
            "keys": {"provider": str, "base_url": str, "model": str, "api_key": str}},
    "reranker": {"get": ("GET", "/api/settings/reranker"), "set": ("POST", "/api/settings/reranker"),
                 "keys": {"provider": str, "model": str, "base_url": str, "device": str,
                          "api_key": str, "top_n": int}},
    "classifier": {"get": ("GET", "/api/settings/classifier"), "set": ("POST", "/api/settings/classifier"),
                   "keys": {"provider": str, "api_url": str, "api_key": str}},
    "embedding": {"get": ("GET", "/api/settings/embedding"), "set": ("POST", "/api/settings/embedding"),
                  "keys": {"provider": str, "model": str, "base_url": str, "api_key": str}},
    "pii": {"get": ("GET", "/api/settings/pii-mode"), "set": ("PUT", "/api/settings/pii-mode"),
            "keys": {"mode": str}},
    "vector-store": {"get": ("GET", "/api/settings/vector-store"), "set": ("POST", "/api/settings/vector-store"),
                     "keys": {"provider": str, "path": str, "qdrant_url": str, "qdrant_api_key": str}},
    "datasync": {"get": ("GET", "/api/settings/datasync"), "set": ("POST", "/api/settings/datasync"),
                 "keys": {"enabled": bool, "interval_sec": int}},
}
_SECRET_KEYS = {"api_key", "qdrant_api_key"}


def _settings_lines(data: dict, lang: str):
    """dict → 表示行。秘密の値はサーバが返さない (api_key_set の bool のみ) が、
    念のためこちら側でも secret 名の値は出さない。"""
    lines = []
    for k in sorted(data):
        v = data[k]
        if k in _SECRET_KEYS:
            v = "(hidden)"
        lines.append(f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}")
    return lines


def cmd_settings_show(ctx: Ctx, args) -> int:
    kind = SETTINGS_KINDS[args.name]
    method, path = kind["get"]
    status, data = _request(ctx, method, path, timeout=30)
    if status != 200:
        return _fail(ctx, f"settings show {args.name}", status, data)
    data = data if isinstance(data, dict) else {"value": data}
    lines = [f"[{args.name}]"] + _settings_lines(data, ctx.lang) + [_m("settings_secret_note", ctx.lang)]
    return _ok(ctx, f"settings show {args.name}",
               {"name": args.name, "settings": data, "note": _m("settings_secret_note", ctx.lang)}, lines)


def cmd_settings_models(ctx: Ctx, _args) -> int:
    status, data = _request(ctx, "GET", "/api/settings/models", timeout=30)
    if status != 200:
        return _fail(ctx, "settings models", status, data)
    raw = data.get("data") if isinstance(data, dict) else data
    models = []
    for m in raw if isinstance(raw, list) else []:
        models.append(str(m.get("id") or m.get("name") or "?") if isinstance(m, dict) else str(m))
    lines = models + [f"({len(models)} models)" if ctx.lang == "en" else f"（モデル {len(models)}件）"]
    return _ok(ctx, "settings models", {"models": models, "count": len(models)}, lines)


def cmd_settings_test(ctx: Ctx, args) -> int:
    body = {}
    if args.provider:
        body["provider"] = args.provider
    if args.base_url:
        body["base_url"] = args.base_url
    if args.model:
        body["model"] = args.model
    status, data = _request(ctx, "POST", "/api/settings/test-connection", body=body, timeout=120)
    if status != 200:
        return _fail(ctx, "settings test", status, data)
    data = data if isinstance(data, dict) else {}
    st = str(data.get("status") or "unknown")
    endpoint = str(data.get("endpoint") or "")
    n_models = data.get("models")
    if st == "connected":
        word = (f"Connected. {endpoint} answered ({n_models} models visible)." if ctx.lang == "en"
                else f"接続できました。{endpoint} が応答しました（見えるモデル {n_models}件）。")
    elif st == "warning":
        word = (f"Reached {endpoint}, but with a warning: {data.get('error') or ''}" if ctx.lang == "en"
                else f"{endpoint} へ届きましたが、注意があります: {data.get('error') or ''}")
    else:
        word = (f"Not connected. {endpoint or ctx.url}: {data.get('error') or st}" if ctx.lang == "en"
                else f"接続できませんでした。{endpoint or ctx.url}: {data.get('error') or st}")
    return _ok(ctx, "settings test", {"result": data, "connected": st == "connected"}, [word])


def cmd_settings_providers(ctx: Ctx, _args) -> int:
    status, data = _request(ctx, "GET", "/api/llm/presets", timeout=30)
    if status != 200:
        return _fail(ctx, "settings providers", status, data)
    data = data if isinstance(data, dict) else {}
    rows = []
    for group in ("presets", "custom"):
        for pset in data.get(group) or []:
            if isinstance(pset, dict):
                rows.append({"id": pset.get("id"), "label": pset.get("label"),
                             "provider": pset.get("provider"), "base_url": pset.get("base_url"),
                             "model": pset.get("model"), "group": group})
    lines = [f"{r['id']}\t{r['label']}\t{r['provider']}\t{r['base_url'] or '-'}\t{r['model'] or '-'}" for r in rows]
    lines.append(f"({len(rows)} presets)" if ctx.lang == "en" else f"（プリセット {len(rows)}件）")
    return _ok(ctx, "settings providers", {"providers": rows, "count": len(rows)}, lines)


def _mask(kind_key: str, value):
    return "(hidden)" if kind_key in _SECRET_KEYS else value


def cmd_settings_set(ctx: Ctx, args) -> int:
    kind = SETTINGS_KINDS[args.name]
    allowed = kind["keys"]

    def bad_input(msg: str) -> int:
        if ctx.as_json:
            print(json.dumps({"ok": False, "command": f"settings set {args.name}", "exit_code": EXIT_USER,
                              "error": {"http_status": None, "message": msg}}, ensure_ascii=False))
        else:
            print(msg, file=sys.stderr)
        return EXIT_USER

    changes = {}
    for pair in args.pairs:
        if "=" not in pair:
            return bad_input(_m("settings_bad_pair", ctx.lang, name=args.name, keys=", ".join(allowed)))
        k, v = pair.split("=", 1)
        k = k.strip()
        if k not in allowed:
            return bad_input(_m("settings_bad_pair", ctx.lang, name=args.name, keys=", ".join(allowed)))
        typ = allowed[k]
        try:
            if typ is bool:
                if v.strip().lower() not in ("true", "false", "1", "0", "yes", "no"):
                    raise ValueError(v)
                changes[k] = v.strip().lower() in ("true", "1", "yes")
            elif typ is int:
                changes[k] = int(v.strip())
            else:
                changes[k] = v
        except ValueError:
            return bad_input(_m("settings_bad_pair", ctx.lang, name=args.name, keys=", ".join(allowed)))

    # 変更前を読む (秘密は *_set の bool でしか返らない)
    g_method, g_path = kind["get"]
    status, before = _request(ctx, g_method, g_path, timeout=30)
    if status != 200:
        return _fail(ctx, f"settings set {args.name}", status, before)
    before = before if isinstance(before, dict) else {}

    ja = ctx.lang == "ja"
    diff_rows = []
    for k, v in changes.items():
        if k in _SECRET_KEYS:
            old_disp = ("set" if before.get(f"{k}_set") or before.get("api_key_set") else "not set")
            new_disp = "(new value hidden)" if v else "(cleared)"
        else:
            old_disp = before.get(k, "(unset)")
            new_disp = v
        diff_rows.append({"key": k, "before": _mask(k, old_disp), "after": _mask(k, new_disp)})
    lines = [f"[{args.name}]"]
    lines += [(f"{r['key']}: {r['before']}  ->  {r['after']}") for r in diff_rows]

    if args.dry_run:
        lines.append(_m("settings_dry_run", ctx.lang))
        return _ok(ctx, f"settings set {args.name}",
                   {"name": args.name, "applied": False, "dry_run": True, "diff": diff_rows}, lines)
    if not args.yes:
        lines.append(_m("settings_need_yes", ctx.lang))
        if ctx.as_json:
            print(json.dumps({"ok": False, "command": f"settings set {args.name}", "exit_code": EXIT_USER,
                              "data": {"name": args.name, "applied": False, "diff": diff_rows},
                              "error": {"http_status": None, "message": _m("settings_need_yes", ctx.lang)}},
                             ensure_ascii=False))
        else:
            for line in lines:
                print(line)
        return EXIT_USER

    s_method, s_path = kind["set"]
    status, resp = _request(ctx, s_method, s_path, body=changes, timeout=60)
    if status != 200:
        return _fail(ctx, f"settings set {args.name}", status, resp)
    # 変更後を読み直して見せる
    status2, after = _request(ctx, g_method, g_path, timeout=30)
    after = after if (status2 == 200 and isinstance(after, dict)) else {}
    lines.append("applied." if not ja else "変更しました。")
    lines += _settings_lines(after, ctx.lang)
    return _ok(ctx, f"settings set {args.name}",
               {"name": args.name, "applied": True, "diff": diff_rows, "after": after}, lines)


def cmd_settings(ctx: Ctx, args) -> int:
    return {
        "show": cmd_settings_show,
        "models": cmd_settings_models,
        "test": cmd_settings_test,
        "set": cmd_settings_set,
        "providers": cmd_settings_providers,
    }[args.settings_cmd](ctx, args)


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

    kinds = list(SETTINGS_KINDS)
    p_st = sub.add_parser("settings", help="show or change server settings (admin token required)")
    st_sub = p_st.add_subparsers(dest="settings_cmd", required=True)
    s_show = st_sub.add_parser("show", help="current settings (api keys shown as set / not set only)")
    s_show.add_argument("name", nargs="?", choices=kinds, default="llm")
    st_sub.add_parser("models", help="models visible at the configured endpoint (GET /api/settings/models)")
    s_test = st_sub.add_parser("test", help="test the LLM connection (POST /api/settings/test-connection)")
    s_test.add_argument("--provider", help="test this provider instead of the saved one")
    s_test.add_argument("--base-url", dest="base_url", help="test this endpoint instead of the saved one")
    s_test.add_argument("--model", help="model name to test with")
    s_set = st_sub.add_parser("set", help="change settings; shows before/after and needs --yes to write")
    s_set.add_argument("name", nargs="?", choices=kinds, default="llm")
    s_set.add_argument("--set", dest="pairs", action="append", required=True, metavar="KEY=VALUE",
                       help="repeatable; e.g. --set model=qwen3-4b --set base_url=http://localhost:1234")
    s_set.add_argument("--yes", action="store_true", help="actually apply the change")
    s_set.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    st_sub.add_parser("providers", help="selectable provider presets (GET /api/llm/presets)")
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
        "settings": cmd_settings,
    }
    return dispatch[args.cmd](ctx, args)


if __name__ == "__main__":
    sys.exit(main())
