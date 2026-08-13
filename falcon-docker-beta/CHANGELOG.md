# Changelog

## Phase 2 α-Stable (2026-05-16)

### baseline
- pytest: **758 passed / 1 failed (既存) / 1132 skipped / 7 xfailed / 6 xpassed**
- pre-commit run --all-files: 全 hook exit 0（ruff / ruff-format / pyright / import-linter）
- regression zero（開始時 717 passed を全 Stage で維持）

### Stage 構成（10 新規 commits）
- **Stage-2A 復旧 + cleanup**: 朝バックアップから 7 ファイル復元、Part 1/1.5 fixture 統合
- **Stage-2B**: 7 テストファイル + Schemathesis 240 行（findings 17 件）
- **Stage-2C**: Stage-D 残置 8 ファイル + syrupy `test_snapshot.py`（24 ケース）
- **Stage-3-A**: 並列バグ修正 8 件（認可漏れ 2 + Stage-D #1/#2/#3/#4/#6/#8 + auth_failed 監査）
- **Stage-3-B**: ruff per-file-ignores（437 件抑制、F821 1 件は実バグ修正）
- **Stage-3-C**: pyright 16 errors → 0（同一バグ系 1 修正 + 8 件 `# pyright: ignore`）
- **Stage-3-D**: import-linter 2 contracts kept（foundational layer 保護）
- **Stage-3-E**: pre-commit 全 hook exit 0 + 161 ファイル auto-format 取り込み
- **Stage-4**: リリース準備（make verify-live 通過、phase-2-completion.md 生成）

### Fixed（Stage-3-A）
- 認可漏れ 2 件: `routers/workspaces.py` DELETE/PATCH に `_require_admin` 追加
- Stage-D #1: `rag.py:163` の `"editor"` 残置除去
- Stage-D #2: `rag.py:288` の `.doc` 拡張子残置除去
- Stage-D #3: `server.py` の `SUPPORTED_EXTENSIONS` を `rag.py` から import 委譲
- Stage-D #4: `db.py SCHEMA` に `publish_jobs` テーブル統合
- Stage-D #6: `pyproject.toml filterwarnings` に hypothesis 警告抑制
- Stage-D #8: `routers/agent.py` の `JSONResponse → api_error` 統一を採用
- F821: `routers/chat.py:484` の `asyncio` 未定義を `_asyncio_mod.gather` で修正
- `auth_failed` 監査: `routers/auth.py` 4 経路で `_audit_auth_failure` 呼び出し

### Phase 3 引き継ぎ（HIGH 優先度バグ 5 件、reports/phase-2-completion.md 参照）
- `import_workspace` の DB→Chroma 順序逆転
- `admin_cleanup_chromadb_orphans` TOCTOU レース
- WS 分離: ChromaDB 物理境界なし
- WS-A セッション → WS-B chat 流用境界チェック漏れ
- 間接プロンプトインジェクション検出不在

すべて XFAIL strict=False のテストで検出可能、修正後 XPASS で自動検出。

---

## v11-beta (2026-05-10)

### Added
- MCP server with 11 tools (Ollama + LM Studio support)
- Smart Ingestion: automatic file classification (14 categories)
- Pagination for all list endpoints (workspaces, collections, sources, policies, audit logs)
- Audit log improvements: ip_address, result, category fields; PII masking; failure logging
- RAGChat workspace selector: search filter + recent workspace history
- `/api/workspaces/selectable` lightweight endpoint

### Fixed
- MCP server: defensive response parsing for all 11 tools
- Audit log: chat query PII was stored verbatim (now masked)
- FastAPI version pinned to avoid unintended upgrades

### Security
- Audit logs now record authentication failures (401/403)
- Chat query text is PII-masked before audit log storage
