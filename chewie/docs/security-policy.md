# セキュリティ ポリシー・既知制限

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual to understand
> the concepts of AI infrastructure tools hands-on. It is not a commercial product or an official implementation.
> The implementation is entirely original and consists of an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela is a learning tool, and it does not meet the security requirements of production operation. This document organizes the explicit disclaimers, the known limitations as of Alpha GA, and the ways of use that are not recommended.

---

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

## 2. Known limitations as of Alpha GA

### 2-1. Authentication and authorization

- **Authentication is JWT**: It is issued by `POST /api/auth/login`, and is required even with a `--demo` startup. The old `Bearer demo-token-<user_id>` form was abolished on 2026-07-29.
- **Scope of the RBAC implementation**: RBAC checks are implemented in 33 routers. Authentication itself is enforced regardless of the startup form, and it is not loosened even with a `--demo` startup.
- **No API key management feature**: Issuing and revoking per-user API keys is not implemented.

### 2-2. Communication encryption

- **HTTPS is not supported**: The main body listens over HTTP only. TLS termination needs to be delegated to a reverse proxy (nginx etc.).
- **LLM communication is also plain text**: The connection to LM Studio / Ollama is also plain HTTP. Publishing outside the LAN is not recommended.
- **The old `transcribe` audio path has been removed**: To close the egress hole of raw PII, the router was disabled, and `voice.py` takes its place.

### 2-3. Settings that are not persisted

- **Embedding / Reranker settings**: Changes at runtime (via the UI) are not persisted to the YAML, and revert to the defaults on restart.

### 2-4. Features that are skeleton only

- **Qdrant VectorStore**: Only the abstraction layer and a connection stub. `add` / `search` / `delete_collection` / `export` / `import_data` are not implemented.
- **MLX Embedding**: `NotImplementedError`. An Apple Silicon optimized version is for the future.
- **MLX Reranker**: `NotImplementedError`. For the future.
- **LanceDB backend**: Initialization only, the substance is not implemented.
- **GraphRAG strategy**: Abstract class only, `retrieve` / `build_graph` / `traverse_with_acl` are not implemented.

### 2-5. DataSyncService

- **Publish linkage not integrated**: The hash based differential sync only writes logs, and the actual connection to rag.publish is a noop.
- **No content_hash comparison**: Difference detection is currently per path only (addition / deletion). Detection of content changes is not supported.

### 2-6. RAG pipeline

- **Structured answer template not implemented**: A free form answer is the standard. Forcing an answer in JSON format or XML tag format is not supported.
- **Low confidence fallback partially implemented**: confidence_threshold (0.50) is defined, but the processing that switches automatically to `GENERAL_KNOWLEDGE_SYSTEM_PROMPT` when there are 0 search results is not integrated.

### 2-7. UI

- **Some elements of the i18n switch**: Some elements whose display is controlled by the language switch (Japanese / English) are fixed.
- **Hiding before tab initialization**: Some UI elements are `display:none` until the JavaScript initialization.

### 2-8. Areas skipped in the tests

- **Demo mode related**: 4 authentication boundary tests remain `@pytest.mark.skip` (lines 11 / 51 / 56 / 157 of `tests/test_auth_boundary.py`). The reason text says "`--demo` モードでは認証バイパスが仕様", but because it was changed on 2026-07-29 into a form that enforces authentication even with a `--demo` startup, this reason no longer matches the implementation.
- **Sources API**: Because of the path registration form, 2 tests are skipped.
- **Publish Semaphore**: Because mock injection at module scope is difficult, 1 xfail. A change to a lazy accessor is planned for Stage-3.

---

## 3. Ways of use that are not recommended

The following ways of use are either not blocked by design or the blocking is incomplete, so do not do them.

### 3-1. Publishing directly to the internet

Opening the port directly to the internet side while bound to `0.0.0.0` with `--lan` is strictly forbidden. The reasons are as follows.

- It is not made HTTPS (plain text communication)
- JWT authentication is not implemented
- RBAC enforcement is limited
- File upload restrictions are loose

### 3-2. Production operation with confidential documents

Feeding in real confidential documents as they are is not recommended.

- Fernet encryption of the raw body text is in operation, but key management (`CYNOVELA_SECRET_KEY`) assumes personal operation
- Tamper prevention of audit_logs is only via the API, and direct DB access is out of scope of the protection
- A backup and disaster recovery mechanism is not implemented

### 3-3. LAN sharing with users you cannot trust

When sharing on a LAN, the premise is that all users on the network can be trusted. It is recommended to narrow the connection sources strictly with `--allow-subnet` and use it only among members you can trust.

### 3-4. Editing the audit log directly in the DB

Changing or deleting rows of the `audit_logs` table via the API is prohibited. Direct DB editing (with the `sqlite3` command etc.) also leads to breaking consistency, so avoid it.

### 3-5. Forcing multiple simultaneous Publishes

Running multiple Publishes for the same Collection at the same time is prevented with `collection_locks`, but forcibly releasing the DB lock and running them in parallel leads to breaking data consistency.

### 3-6. Checking quality in mock mode

Always run RAG quality check tests in an environment where a real LLM (such as LM Studio) is running. The `--mock` option that used to exist (a specification for running without calling an LLM) has been removed.

### 3-7. Adding new `INSERT OR REPLACE` statements

`INSERT OR REPLACE` fires the SQLite FK CASCADE against your intention, so it is forbidden in the codebase. For updating an existing row, use `INSERT ... ON CONFLICT(id) DO UPDATE SET ...`.

---

## 4. Recommended operation configurations

One of the following configurations is recommended.

### 4-1. Fully local operation (the safest)

```bash
python server.py --demo --local-only
```

- Adding `--local-only` makes the bind `127.0.0.1` (the default is `0.0.0.0`)
- For verification, demos and tutorials

### 4-2. Local LLM operation

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

- Start LM Studio or Ollama on the same machine
- No network exposure
- For personal learning and experiments

### 4-3. Operation via a personal VPN

```bash
python server.py --lan --allow-tailscale
```

- Allows only via Tailscale
- Access only between personal devices you can trust
- For personal verification while away from home

---

## 5. Vulnerability reports

Cynovela is a personal project, and has no formal vulnerability report contact. If you report a problem you found on GitHub Issues or similar, handling it will be considered as far as possible.

---

Last updated: 2026-05-26 / Alpha GA edition

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela は学習用ツールであり、本番運用のセキュリティ要件を満たすものではありません。本ドキュメントでは明示的な免責、Alpha GA 時点での既知制限、推奨しない使用方法を整理します。

---

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

## 2. Alpha GA 時点の既知制限

### 2-1. 認証・認可

- **認証は JWT**: `POST /api/auth/login` が発行し、`--demo` 起動でも必要。旧 `Bearer demo-token-<user_id>` 形式は 2026-07-29 に廃止済み。
- **RBAC の実装範囲**: 33 ルーターに RBAC チェックを実装済み。認証そのものは起動形態によらず強制され、`--demo` 起動でも緩みません。
- **API キー管理機能なし**: ユーザー単位の API キー発行・失効機能は未実装。

### 2-2. 通信暗号化

- **HTTPS 化未対応**: 本体は HTTP のみで待ち受け。TLS 終端はリバースプロキシ（nginx 等）に委譲する必要あり。
- **LLM 通信も平文**: LM Studio / Ollama への接続も HTTP 平文。LAN 外への公開は推奨しない。
- **旧 `transcribe` 音声経路は撤去済み**: 生 PII の egress ホール封鎖のため router を無効化し、`voice.py` が代替します。

### 2-3. 永続化されない設定

- **Embedding / Reranker 設定**: 実行時変更（UI 経由）は YAML に永続化されず、再起動でデフォルトに戻る。

### 2-4. 骨格のみの機能

- **Qdrant VectorStore**: 抽象層と接続スタブのみ。`add` / `search` / `delete_collection` / `export` / `import_data` は未実装。
- **MLX Embedding**: `NotImplementedError`。Apple Silicon 最適化版は将来対応。
- **MLX Reranker**: `NotImplementedError`。将来対応。
- **LanceDB バックエンド**: 初期化のみ、実体は未実装。
- **GraphRAG 戦略**: 抽象クラスのみ、`retrieve` / `build_graph` / `traverse_with_acl` は未実装。

### 2-5. DataSyncService

- **publish 連携未統合**: ハッシュ差分同期はログ出力のみで、実際の rag.publish への接続は noop。
- **content_hash 比較なし**: 差分検出は現状パス単位のみ（追加 / 削除）。内容変更の検出は未対応。

### 2-6. RAG パイプライン

- **構造化回答テンプレート未実装**: 自由形式の回答が標準。JSON 形式や XML タグ形式での回答強制は未対応。
- **低信頼度フォールバック部分実装**: confidence_threshold（0.50）は定義済みだが、検索結果が 0 件のときに `GENERAL_KNOWLEDGE_SYSTEM_PROMPT` へ自動切替する処理は未統合。

### 2-7. UI

- **i18n 切替の一部要素**: 言語切替（日本語 / 英語）で表示制御される要素が一部固定。
- **タブ初期化前の隠蔽**: 一部 UI 要素は JavaScript 初期化まで `display:none`。

### 2-8. テストでスキップされている領域

- **デモモード関連**: 認証境界テスト 4 件が `@pytest.mark.skip` のままです（`tests/test_auth_boundary.py` の 11 / 51 / 56 / 157 行）。理由文には「`--demo` モードでは認証バイパスが仕様」と書かれていますが、2026-07-29 に `--demo` 起動でも認証を強制する形へ変えたため、この理由はすでに実装と合っていません。
- **Sources API**: path 登録形式のため一部テスト 2 件をスキップ。
- **Publish Semaphore**: モジュールスコープでのモック注入困難により xfail 1 件。Stage-3 で lazy accessor 化予定。

---

## 3. 推奨しない使用方法

以下の使い方は仕様上ブロックされていないか、ブロックが不完全なため、行わないでください。

### 3-1. インターネットへの直接公開

`--lan` で `0.0.0.0` バインドした状態でインターネット側に直接ポート開放することは厳禁です。理由は次のとおりです。

- HTTPS 化されていない（平文通信）
- JWT 認証が未実装
- RBAC 強制が限定的
- ファイルアップロード制限が緩い

### 3-2. 機密文書での本番運用

本番の機密文書をそのまま投入することは推奨しません。

- raw 本文の Fernet 暗号化は稼働中だが、鍵管理（`CYNOVELA_SECRET_KEY`）は個人運用前提
- audit_logs の改ざん防止は API 経由のみで、DB 直接アクセスは保護対象外
- バックアップ・ディザスタリカバリの仕組みは未実装

### 3-3. 信頼できないユーザーへの LAN 共有

LAN 共有時は、ネットワーク上の全ユーザーが信頼できる前提です。`--allow-subnet` で接続元を厳密に絞ったうえで、信頼できるメンバーのみでの利用を推奨します。

### 3-4. 監査ログの DB 直接編集

`audit_logs` テーブルへの API 経由の変更・削除は禁止しています。DB 直接編集（`sqlite3` コマンド等）も整合性破壊につながるため避けてください。

### 3-5. 同時複数 Publish の強制実行

同一 Collection への複数 Publish 同時実行は `collection_locks` で防いでいますが、強制的に DB ロックを解除して並列実行することはデータ整合性破壊につながります。

### 3-6. モックモードでの品質確認

RAG 品質確認テストは必ず実 LLM（LM Studio など）起動環境で行ってください。以前あった `--mock`（LLM を呼ばずに動かす指定）は撤去済みです。

### 3-7. `INSERT OR REPLACE` 文の新規追加

`INSERT OR REPLACE` は SQLite の FK CASCADE を不本意に発火させるため、コードベースで使用禁止です。既存行更新は `INSERT ... ON CONFLICT(id) DO UPDATE SET ...` を使用してください。

---

## 4. 推奨運用構成

以下のいずれかの構成を推奨します。

### 4-1. 完全ローカル運用（最も安全）

```bash
python server.py --demo --local-only
```

- `--local-only` を付けるとバインドは `127.0.0.1`（既定は `0.0.0.0`）
- 検証・デモ・チュートリアル向け

### 4-2. ローカル LLM 運用

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

- LM Studio または Ollama を同一マシンで起動
- ネットワーク露出なし
- 個人の学習・実験向け

### 4-3. 個人 VPN 経由運用

```bash
python server.py --lan --allow-tailscale
```

- Tailscale 経由のみ許可
- 信頼できる個人デバイス間でのみアクセス
- 外出先からの個人検証向け

---

## 5. 脆弱性報告

Cynovela は個人プロジェクトであり、正式な脆弱性報告窓口を持ちません。発見された問題は GitHub Issues 等で報告いただければ、可能な範囲で対応を検討します。

---

最終更新: 2026-05-26 / Alpha GA 対応版
