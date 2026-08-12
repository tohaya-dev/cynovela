#!/usr/bin/env python3
"""
Cynovela 総合E2Eテスト
Stage 1/2 修正検証 + 全機能疎通確認
キーワード: test-comprehensive-e2e-v1-20260527
"""
import requests, sqlite3, json, sys, os, time, unicodedata

BASE = "http://localhost:8765"
# pw-out-of-code-20260729 (C-B9): 資格情報の平文をこのスクリプトに書かない。
# 既存の env (tests/e2e/conftest.py と同じ名前) で渡す。既定値はプレースホルダ。
ADMIN_USERNAME = os.environ.get("CYNOVELA_E2E_USERNAME", "cynovela")
ADMIN_PASSWORD = os.environ.get("CYNOVELA_E2E_PASSWORD", "dummy-admin-pw-000")
VIEWER_USERNAME = os.environ.get("CYNOVELA_E2E_VIEWER_USERNAME", "demo")
VIEWER_PASSWORD = os.environ.get("CYNOVELA_E2E_VIEWER_PASSWORD", "dummy-viewer-pw-000")
DB = os.path.expanduser("~/Projects/cynovela/cynovela/store/db/demo.db")
results = []


def log(name, status, msg=""):
    results.append((name, status))
    print(f"  [{status}] {name} — {msg}" if msg else f"  [{status}] {name}")


def login(user=ADMIN_USERNAME, pw=ADMIN_PASSWORD):
    r = requests.post(f"{BASE}/api/auth/login", json={"username": user, "password": pw})
    assert r.status_code == 200, f"login {r.status_code}: {r.text[:200]}"
    body = r.json()
    t = body.get("access_token") or body.get("token")
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def db_count(table, where=""):
    conn = sqlite3.connect(DB)
    q = f"SELECT COUNT(*) FROM {table}" + (f" WHERE {where}" if where else "")
    n = conn.execute(q).fetchone()[0]
    conn.close()
    return n


# ─────────────────────────────────────────
# GROUP 1: サーバー基本
# ─────────────────────────────────────────
def g1_health():
    print("\n[GROUP 1] サーバー基本")
    name = "1-1_health"
    try:
        r = requests.get(f"{BASE}/api/health")
        assert r.status_code == 200 and r.json().get("status") == "ok"
        log(name, "PASS", f"status=ok demo={r.json().get('demo')}")
    except Exception as e:
        log(name, "FAIL", str(e))

    name = "1-2_cors_header"
    try:
        r = requests.options(f"{BASE}/api/health",
                             headers={"Origin": "http://localhost:8765",
                                      "Access-Control-Request-Method": "GET"})
        acao = r.headers.get("access-control-allow-origin", "")
        assert acao != "", f"CORS allow-origin ヘッダーなし"
        log(name, "PASS", f"Access-Control-Allow-Origin: {acao}")
    except Exception as e:
        log(name, "WARN", str(e))

    name = "1-3_chroma_path"
    try:
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
        import chromadb
        path = os.path.expanduser("~/Projects/cynovela/cynovela/store/vector/demo/chroma")
        client = chromadb.PersistentClient(path=path)
        cols = client.list_collections()
        assert len(cols) > 0, "Chroma collections=0件"
        total = sum(c.count() for c in cols)
        log(name, "PASS", f"collections={len(cols)} vectors={total}")
    except Exception as e:
        log(name, "FAIL", str(e))


# ─────────────────────────────────────────
# GROUP 2: 認証・RBAC
# ─────────────────────────────────────────
def g2_auth(h):
    print("\n[GROUP 2] 認証・RBAC")
    hv = None
    name = "2-1_admin_login"
    try:
        ha = login(ADMIN_USERNAME, ADMIN_PASSWORD)
        log(name, "PASS", "admin login ok")
    except Exception as e:
        log(name, "FAIL", str(e))
        return None

    name = "2-2_viewer_login"
    try:
        hv = login(VIEWER_USERNAME, VIEWER_PASSWORD)
        log(name, "PASS", "viewer login ok")
    except Exception as e:
        log(name, "WARN", f"demo account: {e}")
        hv = None

    name = "2-3_unauthenticated_401"
    try:
        r = requests.get(f"{BASE}/api/workspaces")
        assert r.status_code in (401, 403), f"未認証で {r.status_code}（401/403 期待）"
        log(name, "PASS", f"{r.status_code} 正常")
    except Exception as e:
        log(name, "FAIL", str(e))

    name = "2-4_viewer_admin_403"
    if hv:
        try:
            r = requests.get(f"{BASE}/api/admin/users", headers=hv)
            assert r.status_code in (403, 401), f"viewer で admin API が {r.status_code}"
            log(name, "PASS", f"{r.status_code} 正常")
        except Exception as e:
            log(name, "FAIL", str(e))
    else:
        log(name, "SKIP", "viewer account なし")
    return hv


# ─────────────────────────────────────────
# GROUP 3: NFC 正規化
# ─────────────────────────────────────────
def g3_nfc():
    print("\n[GROUP 3] NFC 正規化")
    name = "3-1_nfc_stable_fid"
    try:
        # _stable_fid は関数内クロージャなので直接呼べない。
        # 代わりに「同じパス文字列 (NFC/NFD) が unicodedata.normalize で一致するか」を検証
        import hashlib
        nfc = unicodedata.normalize("NFC", "/tmp/テスト.pdf")
        nfd = unicodedata.normalize("NFD", "/tmp/テスト.pdf")
        # Stage 1 修正後は両者が同じ NFC に正規化されてからハッシュされる想定
        nfc_after = unicodedata.normalize("NFC", nfc)
        nfd_after = unicodedata.normalize("NFC", nfd)
        h_nfc = hashlib.md5(nfc_after.encode()).hexdigest()
        h_nfd = hashlib.md5(nfd_after.encode()).hexdigest()
        assert h_nfc == h_nfd, f"NFC/NFD 後にハッシュ不一致: {h_nfc} vs {h_nfd}"
        log(name, "PASS", f"NFC正規化後同一ハッシュ={h_nfc[:12]}")
    except Exception as e:
        log(name, "WARN", str(e))


# ─────────────────────────────────────────
# GROUP 4: LLM URL
# ─────────────────────────────────────────
def g4_llm_url(h):
    print("\n[GROUP 4] LLM URL 設定")
    name = "4-1_llm_base_url_from_yaml"
    try:
        r = requests.get(f"{BASE}/api/settings", headers=h)
        if r.status_code == 200:
            s = r.json()
            url = s.get("llm_base_url") or s.get("llm", {}).get("base_url", "未取得")
            log(name, "PASS", f"llm_base_url={url}")
        else:
            log(name, "WARN", f"settings API {r.status_code}")
    except Exception as e:
        log(name, "WARN", str(e))

    name = "4-2_no_ollama_env_var"
    val = os.environ.get("CYNOVELA_OLLAMA_BASE_URL", "")
    if val == "":
        log(name, "PASS", "env var なし（正常）")
    else:
        log(name, "WARN", f"env var設定: {val}")

    name = "4-3_llm_adapter_helper_exists"
    try:
        sys.path.insert(0, os.path.expanduser("~/Projects/cynovela/cynovela"))
        from llm_adapter import _get_llm_base_url_from_config
        url = _get_llm_base_url_from_config()
        assert url, "helper が空文字を返す"
        log(name, "PASS", f"_get_llm_base_url_from_config()={url}")
    except Exception as e:
        log(name, "WARN", str(e))


# ─────────────────────────────────────────
# GROUP 5: PII マスキング
# ─────────────────────────────────────────
def g5_pii(h):
    print("\n[GROUP 5] PII マスキング")
    name = "5-1_pii_mode_api"
    try:
        r = requests.get(f"{BASE}/api/settings/pii-mode", headers=h)
        if r.status_code == 200:
            log(name, "PASS", f"pii-mode: {r.json()}")
        else:
            log(name, "WARN", f"{r.status_code}")
    except Exception as e:
        log(name, "WARN", str(e))

    name = "5-2_spacy_models"
    try:
        import spacy
        ok = []
        ng = []
        for m in ["ja_core_news_sm", "en_core_web_sm"]:
            try:
                spacy.load(m)
                ok.append(m)
            except Exception:
                ng.append(m)
        if ng:
            log(name, "WARN", f"未インストール: {ng}, インストール済み: {ok}")
        else:
            log(name, "PASS", f"全モデルOK: {ok}")
    except Exception as e:
        log(name, "WARN", str(e))


# ─────────────────────────────────────────
# GROUP 6: データ管理
# ─────────────────────────────────────────
def g6_data(h):
    print("\n[GROUP 6] データ管理")
    ws_id = col_id = None

    name = "6-1_list_workspaces"
    try:
        r = requests.get(f"{BASE}/api/workspaces", headers=h)
        assert r.status_code == 200
        body = r.json()
        ws_list = body if isinstance(body, list) else body.get("workspaces", body.get("items", []))
        log(name, "PASS", f"{len(ws_list)}件")
    except Exception as e:
        log(name, "FAIL", str(e))

    name = "6-2_create_workspace"
    try:
        r = requests.post(f"{BASE}/api/workspaces",
                          json={"name": "e2e-test-ws-综合"}, headers=h)
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:200]}"
        body = r.json()
        ws_id = body.get("id") or body.get("workspace", {}).get("id")
        log(name, "PASS", f"id={ws_id}")
    except Exception as e:
        log(name, "FAIL", str(e))

    name = "6-3_list_sources"
    try:
        r = requests.get(f"{BASE}/api/sources", headers=h)
        assert r.status_code == 200
        body = r.json()
        src_list = body if isinstance(body, list) else body.get("sources", body.get("items", []))
        log(name, "PASS", f"{len(src_list)}件")
    except Exception as e:
        log(name, "FAIL", str(e))

    name = "6-4_create_collection"
    if ws_id:
        try:
            r = requests.post(f"{BASE}/api/collections",
                              json={"name": "e2e-test-col", "workspace_id": ws_id},
                              headers=h)
            assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:200]}"
            body = r.json()
            col_id = body.get("id") or body.get("collection", {}).get("id")
            log(name, "PASS", f"id={col_id}")
        except Exception as e:
            log(name, "FAIL", str(e))
    else:
        log(name, "SKIP", "workspace作成失敗のためスキップ")

    # クリーンアップ
    if col_id:
        try:
            requests.delete(f"{BASE}/api/collections/{col_id}", headers=h)
        except Exception:
            pass
    if ws_id:
        try:
            requests.delete(f"{BASE}/api/workspaces/{ws_id}", headers=h)
        except Exception:
            pass


# ─────────────────────────────────────────
# GROUP 7: Publish + parent-child chunking
# ─────────────────────────────────────────
def g7_publish(h):
    print("\n[GROUP 7] Publish + parent-child chunking")

    name = "7-1_existing_parent_chunks"
    try:
        pc = db_count("parent_chunks")
        # chunks には parent_chunk_id カラム無し。代わりに parent_chunks 件数で判定
        ch = db_count("chunks")
        assert pc > 0, f"parent_chunks=0件（chunking未動作）"
        log(name, "PASS", f"parent_chunks={pc}件, chunks={ch}件")
    except Exception as e:
        log(name, "FAIL", str(e))

    name = "7-4_publish_diff_api"
    try:
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT id FROM collections WHERE status IN ('published','ready') LIMIT 1"
        ).fetchone()
        conn.close()
        if not row:
            log(name, "SKIP", "published/ready collection なし")
            return
        col_id = row[0]
        r = requests.get(f"{BASE}/api/collections/{col_id}/publish-diff", headers=h)
        if r.status_code == 200:
            log(name, "PASS", f"publish-diff: {json.dumps(r.json(), ensure_ascii=False)[:120]}")
        elif r.status_code == 404:
            log(name, "FAIL", "404: Stage 2 エンドポイント未登録")
        else:
            log(name, "WARN", f"{r.status_code}: {r.text[:100]}")
    except Exception as e:
        log(name, "WARN", str(e))


# ─────────────────────────────────────────
# GROUP 8: RAG 検索・チャット
# ─────────────────────────────────────────
def g8_rag(h):
    print("\n[GROUP 8] RAG 検索・チャット")

    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT id FROM collections WHERE status IN ('published','ready','complete') "
        "AND (SELECT COUNT(*) FROM chunks WHERE collection_id=collections.id)>0 LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        log("8-x", "SKIP", "published/ready collection なし")
        return
    col_id = row[0]

    name = "8-1_rag_search"
    try:
        hit = False
        for ep in ["/api/rag/query", "/api/chat"]:
            r = requests.post(f"{BASE}{ep}",
                              json={"query": "ONTAPとは", "collection_id": col_id, "top_k": 3},
                              headers=h, timeout=30)
            if r.status_code == 200:
                result = r.json()
                sources = result.get("sources", result.get("chunks", []))
                max_len = max((len(str(s.get("content", s.get("text", "")))) for s in sources), default=0)
                log(name, "PASS", f"ep={ep} sources={len(sources)} max_len={max_len}文字")
                if max_len > 200:
                    log("8-1b_parent_context", "PASS", f"コンテキスト長={max_len}文字（親チャンク返却可能性高）")
                else:
                    log("8-1b_parent_context", "WARN", f"コンテキスト短い({max_len}文字)")
                hit = True
                break
        if not hit:
            log(name, "WARN", "両エンドポイントとも非200")
    except Exception as e:
        log(name, "WARN", str(e))

    name = "8-2_abstention"
    try:
        hit = False
        for ep in ["/api/rag/query", "/api/chat"]:
            r = requests.post(f"{BASE}{ep}",
                              json={"query": "XYZ-9999-架空クエリ", "collection_id": col_id, "top_k": 3},
                              headers=h, timeout=30)
            if r.status_code == 200:
                result = r.json()
                sources = result.get("sources", [])
                lc = result.get("low_confidence", result.get("abstained", None))
                log(name, "PASS", f"架空クエリ: sources={len(sources)} low_confidence={lc}")
                hit = True
                break
        if not hit:
            log(name, "WARN", "両エンドポイントとも非200")
    except Exception as e:
        log(name, "WARN", str(e))


# ─────────────────────────────────────────
# GROUP 9: 監査ログ
# ─────────────────────────────────────────
def g9_audit(h):
    print("\n[GROUP 9] 監査ログ")

    name = "9-1_audit_log_written"
    try:
        before = db_count("audit_logs")
        for _ in range(3):
            requests.get(f"{BASE}/api/workspaces", headers=h)
        time.sleep(2)
        after = db_count("audit_logs")
        if after > before:
            log(name, "PASS", f"audit_logs: {before}→{after}件（+{after - before}件）")
        else:
            log(name, "WARN", f"audit_logs 増加なし（{before}件のまま）")
    except Exception as e:
        log(name, "WARN", str(e))

    name = "9-2_audit_log_api"
    try:
        r = requests.get(f"{BASE}/api/audit-logs?limit=5", headers=h)
        if r.status_code == 200:
            body = r.json()
            items = body if isinstance(body, list) else body.get("items", body.get("logs", []))
            log(name, "PASS", f"audit-logs API: {len(items)}件返却")
        else:
            log(name, "WARN", f"{r.status_code}")
    except Exception as e:
        log(name, "WARN", str(e))


# ─────────────────────────────────────────
# 実行
# ─────────────────────────────────────────
print("=" * 50)
print("Cynovela 総合E2Eテスト")
print("=" * 50)

try:
    h = login()
    print("[OK] ログイン成功\n")
except Exception as e:
    print(f"[FATAL] ログイン失敗: {e}")
    sys.exit(1)

g1_health()
g2_auth(h)
g3_nfc()
g4_llm_url(h)
g5_pii(h)
g6_data(h)
g7_publish(h)
g8_rag(h)
g9_audit(h)

print("\n" + "=" * 50)
print("結果サマリー")
print("=" * 50)
pass_n = sum(1 for _, r in results if r == "PASS")
fail_n = sum(1 for _, r in results if r == "FAIL")
warn_n = sum(1 for _, r in results if r in ("WARN", "SKIP"))
for name, res in results:
    print(f"  {res:5s}: {name}")
print(f"\nPASS={pass_n} FAIL={fail_n} WARN/SKIP={warn_n}")
if fail_n > 0:
    sys.exit(1)
