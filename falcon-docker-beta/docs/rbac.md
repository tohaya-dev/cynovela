> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# RBAC（ロールベースアクセス制御）

Cynovela は、API リクエストの権限管理を **ロール（役割）ベース** で行います。利用者ごとに「何ができるか」をロールで決め、各 API エンドポイントの先頭でロール検査ヘルパーを呼ぶ実装方式を取っています。

---

## 1. ロール定義（3 ロール）

データベース側で次の CHECK 制約が掛かっており、登録できるロールはこの 3 種類のみです。

```sql
role TEXT NOT NULL CHECK(role IN ('admin', 'curator', 'viewer'))
```

| ロール | 想定する利用者像 | 主な権限 |
|---|---|---|
| **admin** | システム管理者 | API 全エンドポイント。ユーザー管理、システム設定変更、監査ログ閲覧、PII（個人情報）原本の閲覧 |
| **viewer** | 一般利用者 | RAG（検索拡張生成）の問い合わせ、レポート閲覧などの読み取り操作 |

> DB の CHECK 制約は後方互換のため `role IN ('admin', 'curator', 'viewer')` を許容しますが、現行実装では `curator`（および `data-scientist` 等）は `viewer` に正規化され、固有の権限はありません。実効ロールは `admin` / `viewer` の 2 値です。

---

## 2. ロール検査ヘルパー

`core/auth.py` に 4 種類のロール検査関数を用意しており、ルーター層の各エンドポイントでこれらを呼び出して認可（権限チェック）を行います。

| 関数名 | 検査内容 | 不合格時の挙動 |
|---|---|---|
| `_require_admin()` | role が admin か | 例外送出（権限不足） |
| `_require_authenticated()` | 認証済みか（ロール不問） | 例外送出 |
| `_require_role(roles)` | 指定ロールのいずれかに合致するか | 例外送出 |
| `_require_admin_or_self()` | admin か、または当該 user_id 本人か | 例外送出 |

ロール検査の呼び出しはルーター配下に **約 242 箇所** 分散しています。

---

## 3. ロール別 主要エンドポイント（admin 限定）

`_require_admin` が掛けられているルーターを抜粋すると、次のとおりです。**13 個のルーター** に admin 限定のエンドポイントが含まれています。

| ルーター | admin 限定の対象 | 役割 |
|---|---|---|
| `routers/alerts.py` | アラート操作 | 通知系の管理 |
| `routers/auth.py` | ユーザー作成・削除・一覧 | アカウント管理 |
| `routers/files.py` | ファイル削除・一括操作・上限変更 | アップロード管理 |
| `routers/catalog.py` | カタログ編集系 | データカタログ管理 |
| `routers/archived.py` | アーカイブ照会・復元 | 保管対象の整理 |
| `routers/models.py` | モデル設定 | LLM / Embedding モデル選択 |
| `routers/compliance.py` | コンプライアンス操作 | 監査・ポリシー周辺 |
| `routers/health.py` | 一部の健全性確認 | 内部状態の参照 |
| `routers/sessions.py` | セッション管理 | チャット履歴の管理 |
| `routers/llm.py` | LLM 接続設定 | プロバイダー切替 |
| `routers/feedback.py` | フィードバック取得・編集 | 👍👎 集計の照会 |
| `routers/guardrails.py` | PII 検出履歴・禁止トピック編集 | 保護ルールの管理 |
| `routers/policies.py` | ガードレールポリシー編集 | ポリシーマトリクス |

加えて、PII 検出履歴を返す `/api/guardrails/pii-detections` は **admin 限定** に固定されています（`routers/guardrails.py` の `_require_admin(request)` を冒頭で呼ぶ実装）。

---

## 4. ロール別の回答の違い（PII の見え方）

Cynovela は、二段構えの PII マスキング（個人情報のマスキング）でロールに応じた回答内容を切り替えます。

### 4.1 取込時マスキング（Tier1）

Publish（公開）の段階で、原本本文 (raw) とマスキング本文 (masked) を **両方** 保存します。
- SQLite `chunks` テーブルには `tier='raw'` と `tier='masked'` の 2 行が並びます。
- ChromaDB（ベクター検索）側にも `{cid}__raw` と `{cid}__masked` の 2 コレクションを並列に作ります。

### 4.2 回答時マスキング（Tier2）

チャット応答の出口（LLM 生成結果に対して）で、利用者のロールに応じて表示用テキストを再マスクします。判定ロジックは次のとおりです。

```python
def tier_for_role(role: str) -> str:
    return "raw" if (role or "").strip() == "admin" else "masked"
```

- **admin** → `raw` 側のコレクションを参照し、回答表示では出口マスクも素通し（原本がそのまま表示されます）
- **viewer / 未指定**（`curator` 等は viewer に正規化）→ `masked` 側のコレクションを参照し、出口マスクも適用（マスキングされたまま表示されます）

> ただし外部（非ローカル）LLM を使う場合は、crag-egress-guard により admin でも raw の下読み（context_preview）が外部へ送出されません（CRAG スキップ）。上記の admin 素通しは「ローカル LLM での回答表示」を前提とした記述であり、「admin＝常に生本文が外部 LLM へ渡る」わけではありません。

`routers/chat.py` の通常応答 / 比較 A / 比較 B / SSE（イベントストリーム）の 4 経路すべてで出口マスクが呼ばれます。

### 4.3 ロール別 回答スタイルの違い

`rag.py` のロール接頭辞で、回答のトーンも切り替えます。

| ロール | 接頭辞の方針 |
|---|---|
| admin | 技術的な詳細・設定値・内部構造を含む完全な情報を提供 |
| reader | 要点を絞ったわかりやすい説明、専門用語は避ける |

---

## 5. ワークスペース単位のアクセス制御

ワークスペース（Workspace、データの保管単位）には、利用者を割り当てるための中間テーブル `workspace_users (workspace_id, user_id)` が存在します。これにより、利用者がアクセスできるワークスペースを限定できます。

加えて、コレクション（Collection、ファイル群の単位）には次のメタデータが付きます。

| カラム | 用途 |
|---|---|
| `access_level` | `public` / `internal` / `confidential` の 3 段階 |
| `allowed_roles_json` | コレクション単位で許可するロールの一覧（JSON） |
| `acl_roles` | ACL（アクセス制御リスト）相当のロール集合 |

検索パイプライン（`rag.py` の `rag_retrieve`）の中で **ACL フィルター** が動作し、利用者のロールが `allowed_roles` に含まれない場合は検索結果から除外されます。

`features.acl_filter` を `false` にすると ACL フィルターをスキップできます（既定は `true`）。

---

## 6. Alpha GA 時点の制限

- 認証は `/api/auth/login` が発行する JWT（JSON Web Token）のみです。`Bearer demo-token-{user_id}` 形式の簡易トークンは 2026-07-29 に廃止し、`--demo` 起動でも 401 で拒否します。
<!-- BACKLOG: JWT 導入時のロール検査ヘルパーの変更点は未定義 -->
- ロール検査の実装は **約 242 箇所に分散** しているため、共通化（例: FastAPI Depends ベースへの統合）は今後の整理候補です。
- ワンクリック入室（ユーザーカードからの未認証ログイン）は完全撤去済みです。`username` と `password` の入力が必須となっています。

---

最終更新: 2026-05-26 / Alpha GA 対応版
