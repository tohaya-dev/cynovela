# クイックスタート

**日本語版はこちら → [日本語](#日本語)**

## English

These are the shortest steps to start Cynovela for the first time and throw your first RAG question. The target is version `1.0.2` (working directory `<the folder where you extracted the package>`).

> For an even shorter startup note, see [STARTUP.md](STARTUP.md).

---

## 1. Prerequisite Environment

| Item | Content |
|---|---|
| Python | The conda environment `cynovela` (verified with the Python 3.12 series / environment.yml pins 3.12.13) |
| Local LLM | LM Studio or an OpenAI-compatible API |
| Recommended RAM | 8GB or more (the required models are the same in every startup mode) |
| Network | Needed for the model download on the first start |

---

## 2. Setting Up the conda Environment

```bash
# conda 環境を作成（例: cynovela）
conda create -n cynovela python=3.12 -y

# 依存ライブラリをインストール
conda run -n cynovela python -m pip install -r requirements.txt
```

Main dependencies: FastAPI / uvicorn / ChromaDB / sentence-transformers / spaCy + ja-ginza / torch / pypdf and others (see `requirements.txt`).

---

## 3. A Note on SSL_CERT_FILE (Important)

In a conda environment, `SSL_CERT_FILE` may point to a wrong certificate path, and the HuggingFace model download at startup fails. Please `unset` it and use the system default certificates.

```bash
unset SSL_CERT_FILE
```

The bundled `launch.sh` contains this `unset`, so it is unnecessary if you use it. **Only when you run `conda run` manually**, please run it yourself.

---

## 4. Starting

### Method 1: The Bundled Launcher (Recommended)

```bash
cd<配布物を展開したフォルダ>

# launch.sh に渡した引数は、そのまま server.py へ届きます
# （実装: launch.sh の `exec "$PY" server.py "${APP_ARGS[@]}"`。2026-08-02 実測）。
# 引数なしは本番（空のデータベース）です。デモを見るなら --demo を明示します。
./launch.sh --demo            # デモデータ + 実 LLM（既定は 0.0.0.0 で待ち受け。自分の機械の中だけに絞るなら --local-only）
./launch.sh --demo --lan      # デモデータ + LAN 公開
./launch.sh --check           # 起動せずに動く条件だけを調べる
```

To stop:

```bash
./stop.sh
```

### Method 2: Manual Start

```bash
cd<配布物を展開したフォルダ>
unset SSL_CERT_FILE

# デモデータ + 実 LLM（LM Studio を http://localhost:1234 で起動しておく）
conda run -n cynovela python server.py --demo
```

To access:

```bash
open http://127.0.0.1:8765
```

> ⚠️ **A real LLM is required**: To produce answers to questions, an LLM such as LM Studio is required. The `--mock` option that used to exist (a setting to run without calling an LLM) has been removed, and specifying it now stops with an error.

> If you run the **container edition (podman)**, use `deploy/container/run-container.sh` (for the details of the ingest folder, see the README). Note: the container procedure is bundled only with the container edition (the direct host start edition has no `deploy/`).

---

## 5. Startup Modes (`--mode`) and Required Models

| Mode | Required model | Approximate size |
|---|---|---|
| `text` (default) | BAAI/bge-m3 | About 2.3GB |
| `lite` | The switch is **not wired** = it is actually BAAI/bge-m3 (the behavior is the same as text; only the display name changes) | — |
| `lite-en` | The switch is **not wired** = it is actually BAAI/bge-m3 (the behavior is the same as text; only the display name changes) | — |

If the model has not been fetched at the first start, an interactive prompt from the preflight check (download / switch to another mode / cancel) is displayed. In a non-interactive environment, if you set `CYNOVELA_NONINTERACTIVE=1` it stops with exit code 2 when the model is not cached.

```bash
# 例: 表示名を変えて起動する（動作と必要モデルは text と同じ・切替は未配線）
./launch.sh --demo --mode lite
```

---

## 6. Logging In with a Demo Account

Open `http://127.0.0.1:8765` in a browser. With `--demo`, demo users are inserted automatically, but authentication is enforced as usual (a user name and password are required). The roles that the DB holds are the **2 values `admin` / `viewer`**.

| Role | Rights | Search target |
|---|---|---|
| `admin` | All features | The raw vault (no output masking) |
| `viewer` | Mainly viewing | The masked vault (with exit masking) |

> Names such as `curator` / `data-scientist` are normalized internally to `viewer`.

The actual login information of the shipped `demo.db`:

| User name (default. It is not `admin`) | Role | Password |
|---|---|---|
| `cynovela` | admin | A change is forced at the first login (no fixed password is distributed) |
| `demo` | viewer | See `viewer_password` in the bundled credential file (the `*.admin-password.txt` you receive separately from the package tar). No fixed password is distributed |

---

## 7. Your First File Ingest and Publish

1. On a `--demo` start, **only 1 workspace containing the bundled dummy material** is included (the 3 empty seed workspaces were removed on 2026-07-30 and are taken out at startup; measured 2026-08-02: right after a `--demo` start, `/api/workspaces` has only "デモワークスペース"). Create your own workspace from "新しいワークスペースを作成".
2. Specify a name and a RAG strategy in "コレクション作成"
3. Upload files
4. Run "Publish（公開）" and bring it to the `ready` state

In Publish, text extraction -> chunk splitting -> PII detection/masking -> embedding generation (saved to ChromaDB) -> BM25 index construction are performed. The progress is returned by SSE, and on completion the counts and elapsed time are recorded in `publish_history`.

---

## 8. Your First Question

Ask a question from the RAG Chat screen against a collection in the `ready` state.

```
このドキュメントで扱われている主なトピックは何ですか？
```

In the answer, chunks are shown as sources with citation numbers like `[1][2]`. `admin` searches the raw body text and `viewer` the masked body text, and for `viewer` the exit masking is also applied to the LLM output.

---

## 9. Checking Behavior (Tests)

> **The package does not contain `tests/`** (it is taken out when the package is built). On the package you received, `pytest` / `make test` cannot be run.
> To check the behavior, please use `conda run -n cynovela python scripts/test_comprehensive_e2e.py`.

```bash
# 開発ツリー（tests/ が在る側）での実行

# 手動 pytest（軽量・最初の失敗で停止）
cd<開発ツリーのフォルダ>
unset SSL_CERT_FILE
conda run -n cynovela python -m pytest -x -q
```

`make test` / `make test-quick` / `make verify-live` in the `Makefile` can also be used. The `live` family assumes that the server is running at `http://127.0.0.1:8765`.

---

## Next Steps

- [architecture.md](architecture.md) — Understand the system configuration
- [handson-basic.md](handson-basic.md) — Try the basic operations
- [rag-pipeline.md](rag-pipeline.md) — Understand the RAG pipeline

---

## Troubleshooting

- **The model download or HTTPS fails with SSL** -> Please `unset SSL_CERT_FILE` before starting or testing (unnecessary when using the launcher).
- **It cannot be opened from another device on the LAN** -> Since it listens on `0.0.0.0` by default, first check the port and the destination IP (if you added `--local-only`, it is narrowed to your own machine).
- **The quality is not stable** -> Please check the model and settings on the LM Studio side.
- **You forgot the admin password** -> It can be reissued with `conda run -n cynovela python server.py --reset-admin`.
- **Port 8765 is in use** -> Check with `lsof -i :8765`. Because `./stop.sh` stops only the PID recorded at startup (the Cynovela server itself), even if 8765 is used for another purpose that process is not affected. If there is no recorded PID and you stop it manually, please confirm that the target is Cynovela and then use something like `pkill -f "python server.py"`.

For anything else, please see [faq.md](faq.md).

---

# 日本語

Cynovela を初めて起動し、最初の RAG 質問を投げるまでの最短手順です。対象は版 `1.0.2`（作業ディレクトリ `<配布物を展開したフォルダ>`）です。

> さらに短い起動メモは [STARTUP.md](STARTUP.md) を参照してください。

---

## 1. 前提環境

| 項目 | 内容 |
|---|---|
| Python | conda 環境 `cynovela`（Python 3.12 系で検証 / environment.yml は 3.12.13 を固定） |
| ローカル LLM | LM Studio もしくは OpenAI 互換 API |
| 推奨 RAM | 8GB 以上（どの起動モードでも必要なモデルは同じです） |
| ネットワーク | 初回起動時のモデルダウンロードに必要 |

---

## 2. conda 環境のセットアップ

```bash
# conda 環境を作成（例: cynovela）
conda create -n cynovela python=3.12 -y

# 依存ライブラリをインストール
conda run -n cynovela python -m pip install -r requirements.txt
```

主な依存: FastAPI / uvicorn / ChromaDB / sentence-transformers / spaCy + ja-ginza / torch / pypdf ほか（`requirements.txt` 参照）。

---

## 3. SSL_CERT_FILE の注意（重要）

conda 環境では `SSL_CERT_FILE` が誤った証明書パスを指すことがあり、起動時の HuggingFace モデルダウンロードが失敗します。`unset` してシステムデフォルトの証明書を使ってください。

```bash
unset SSL_CERT_FILE
```

同梱の `launch.sh` はこの `unset` を内包しているため、これを使う場合は不要です。**手動で `conda run` を実行する場合のみ**、各自で実行してください。

---

## 4. 起動

### 方法 1: 同梱ランチャー（推奨）

```bash
cd<配布物を展開したフォルダ>

# launch.sh に渡した引数は、そのまま server.py へ届きます
# （実装: launch.sh の `exec "$PY" server.py "${APP_ARGS[@]}"`。2026-08-02 実測）。
# 引数なしは本番（空のデータベース）です。デモを見るなら --demo を明示します。
./launch.sh --demo            # デモデータ + 実 LLM（既定は 0.0.0.0 で待ち受け。自分の機械の中だけに絞るなら --local-only）
./launch.sh --demo --lan      # デモデータ + LAN 公開
./launch.sh --check           # 起動せずに動く条件だけを調べる
```

停止:

```bash
./stop.sh
```

### 方法 2: 手動起動

```bash
cd<配布物を展開したフォルダ>
unset SSL_CERT_FILE

# デモデータ + 実 LLM（LM Studio を http://localhost:1234 で起動しておく）
conda run -n cynovela python server.py --demo
```

アクセス:

```bash
open http://127.0.0.1:8765
```

> ⚠️ **実 LLM が要ります**: 質問への答えを作るには LM Studio などの LLM が要ります。以前あった `--mock`（LLM を呼ばずに動かす指定）は撤去済みで、いま指定するとエラーで止まります。

> **コンテナ版（podman）** で動かす場合は `deploy/container/run-container.sh` を使います（取り込みフォルダの詳細は README を参照）。※ コンテナ手順はコンテナ版にのみ同梱されています（ホスト直起動版には `deploy/` はありません）。

---

## 5. 起動モード（`--mode`）と必要モデル

| モード | 必要モデル | サイズ目安 |
|---|---|---|
| `text`（既定） | BAAI/bge-m3 | 約 2.3GB |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — |

初回起動でモデルが未取得の場合、Preflight チェックの対話プロンプト（ダウンロード / 別モードへ切替 / キャンセル）が表示されます。非対話環境では `CYNOVELA_NONINTERACTIVE=1` を設定すると、未キャッシュ時に終了コード 2 で停止します。

```bash
# 例: 表示名を変えて起動する（動作と必要モデルは text と同じ・切替は未配線）
./launch.sh --demo --mode lite
```

---

## 6. デモアカウントでログイン

ブラウザで `http://127.0.0.1:8765` を開きます。`--demo` ではデモ用ユーザーが自動投入されますが、認証は通常どおり強制されます（ユーザー名とパスワードの入力が要ります）。DB が保持するロールは **`admin` / `viewer` の 2 値**です。

| ロール | 権限 | 検索対象 |
|---|---|---|
| `admin` | 全機能 | raw 保管庫（出力マスクなし） |
| `viewer` | 閲覧中心 | masked 保管庫（出口マスクあり） |

> `curator` / `data-scientist` 等の名称は内部的に `viewer` へ正規化されます。

出荷 `demo.db` の実ログイン情報:

| ユーザー名（既定。`admin` ではありません） | ロール | パスワード |
|---|---|---|
| `cynovela` | admin | 初回ログイン時に変更を強制（固定 PW は配布しません） |
| `demo` | viewer | 同梱の資格情報ファイル（配布物の tar とは別便で受け取る `*.admin-password.txt`）の `viewer_password` を参照。固定 PW は配布しません |

---

## 7. 最初のファイル取り込みと Publish

1. `--demo` 起動では、**同梱のダミー資料が入ったワークスペースが 1 件だけ**入っています（空のシード WS 3 件は 2026-07-30 に撤去済みで、起動時に取り除かれます。2026-08-02 実測: `--demo` 起動直後の `/api/workspaces` は「デモワークスペース」のみ）。自分用のワークスペースは「新しいワークスペースを作成」から作ります。
2. 「コレクション作成」で名前と RAG 戦略を指定
3. ファイルをアップロード
4. 「Publish（公開）」を実行し `ready` 状態にする

Publish では テキスト抽出 → チャンク分割 → PII 検出/マスキング → Embedding 生成（ChromaDB 保存）→ BM25 インデックス構築 が行われます。進捗は SSE で返り、完了時に `publish_history` へ件数・所要時間が記録されます。

---

## 8. 最初の質問

`ready` 状態のコレクションに対し、RAG Chat 画面から質問します。

```
このドキュメントで扱われている主なトピックは何ですか？
```

回答には出典として `[1][2]` の引用番号付きでチャンクが表示されます。`admin` は raw 本文、`viewer` はマスク済み本文を検索し、`viewer` では LLM 出力にも出口マスクが適用されます。

---

## 9. 動作確認（テスト）

> **配布物には `tests/` は入っていません**（配布物を作るときに外されます）。受け取った配布物では `pytest` / `make test` は実行できません。
> 動作を確かめるには `conda run -n cynovela python scripts/test_comprehensive_e2e.py` を使ってください。

```bash
# 開発ツリー（tests/ が在る側）での実行

# 手動 pytest（軽量・最初の失敗で停止）
cd<開発ツリーのフォルダ>
unset SSL_CERT_FILE
conda run -n cynovela python -m pytest -x -q
```

`Makefile` の `make test` / `make test-quick` / `make verify-live` も利用できます。`live` 系はサーバが `http://127.0.0.1:8765` で稼働していることが前提です。

---

## 次のステップ

- [architecture.md](architecture.md) — システム構成を理解する
- [handson-basic.md](handson-basic.md) — 基本操作を試す
- [rag-pipeline.md](rag-pipeline.md) — RAG パイプラインを理解する

---

## トラブルシューティング

- **モデルダウンロードや HTTPS が SSL で失敗** → `unset SSL_CERT_FILE` してから起動・テストしてください（ランチャー使用時は不要）。
- **LAN の他の端末から開けない** → 既定で `0.0.0.0` 待ち受けなので、まずポートと接続先 IP を確認してください（`--local-only` を付けていると自マシン内に絞られます）。
- **品質が安定しない** → LM Studio 側のモデルと設定を確認してください。
- **admin パスワードを忘れた** → `conda run -n cynovela python server.py --reset-admin` で再発行できます。
- **ポート 8765 が使用中** → `lsof -i :8765` で確認します。`./stop.sh` は起動時に記録した PID（Cynovela サーバー自身）のみを停止するため、8765 を他用途で使っている場合でもそのプロセスには影響しません。記録 PID が無く手動で止める場合は、対象が Cynovela であることを確認したうえで `pkill -f "python server.py"` などを使ってください。

その他は [faq.md](faq.md) を参照してください。
