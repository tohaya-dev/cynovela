# クイックスタート

**日本語版はこちら → [日本語](#日本語)**

## English

This is the shortest procedure from starting Cynovela for the first time to sending your first RAG question. The target is version `1.0.2` (working directory `<the folder where the package was extracted>`).

> For an even shorter startup note, see [STARTUP.md](../STARTUP.md).

---

## 1. Prerequisites

| Item | Content |
|---|---|
| Python | conda environment `cynovela` (verified on the Python 3.12 line / environment.yml pins 3.12.13) |
| Local LLM | LM Studio, or an OpenAI-compatible API |
| Recommended RAM | 8GB or more (the required models are the same in every startup mode) |
| Network | Needed for the model download on the first startup |

---

## 2. Setting up the conda environment

```bash
# conda 環境を作成（例: cynovela）
conda create -n cynovela python=3.12 -y

# 依存ライブラリをインストール
conda run -n cynovela python -m pip install -r requirements.txt
```

Main dependencies: FastAPI / uvicorn / ChromaDB / sentence-transformers / spaCy + ja-ginza / torch / pypdf and others (see `requirements.txt`).

---

## 3. Note on SSL_CERT_FILE (important)

In a conda environment, `SSL_CERT_FILE` may point at a wrong certificate path, and the HuggingFace model download at startup then fails. Please `unset` it and use the system default certificates.

```bash
unset SSL_CERT_FILE
```

The bundled `launch.sh` contains this `unset` inside it, so it is unnecessary when you use it. **Only when you run `conda run` manually**, run it yourself.

---

## 4. Startup

### Method 1: the bundled launcher (recommended)

```bash
cd <配布物を展開したフォルダ>

# launch.sh に渡した引数は、そのまま server.py へ届きます
# （実装: launch.sh の `exec "$PY" server.py "${APP_ARGS[@]}"`。2026-08-02 実測）。
# 引数なしは本番（空のデータベース）です。デモを見るなら --demo を明示します。
./launch.sh --demo            # デモデータ + 実 LLM（既定は 0.0.0.0 で待ち受け。自分の機械の中だけに絞るなら --local-only）
./launch.sh --demo --lan      # デモデータ + LAN 公開
./launch.sh --check           # 起動せずに動く条件だけを調べる
```

To stop:

```bash
bash stop.sh
```

(Its content is `podman stop cynovela-all-in-one`. If you started it under a different name, use that name.)

### Method 2: manual startup

```bash
cd <配布物を展開したフォルダ>
unset SSL_CERT_FILE

# デモデータ + 実 LLM（LM Studio を http://localhost:1234 で起動しておく）
conda run -n cynovela python server.py --demo
```

To access it:

```bash
open http://127.0.0.1:8801
```

(The default number is 8801. When nothing is specified, a free number is chosen automatically, so use the number that was displayed at startup.)

> ⚠️ **A real LLM is required**: to produce an answer to a question, an LLM such as LM Studio is required. The `--mock` option that used to exist (running without calling an LLM) has been removed, and specifying it now stops with an error.

> **The container edition (podman)** is run with `./launch.sh` (for the details of the ingest folder, see the README). Note: the container procedure is bundled only with the container edition (the host direct-start edition has no `deploy/`).

---

## 5. Startup modes (`--mode`) and the required models

| Mode | Required model | Approximate size |
|---|---|---|
| `text` (default) | BAAI/bge-m3 | About 2.3GB |
| `lite` | Switching is **not wired up**, so it is actually BAAI/bge-m3 (behaves the same as text, only the displayed name changes) | — |
| `lite-en` | Switching is **not wired up**, so it is actually BAAI/bge-m3 (behaves the same as text, only the displayed name changes) | — |

If the model has not been obtained yet on the first startup, an interactive prompt of the Preflight check (download / switch to another mode / cancel) is displayed. In a non-interactive environment, setting `CYNOVELA_NONINTERACTIVE=1` makes it stop with exit code 2 when the model is not cached.

```bash
# 例: 表示名を変えて起動する（動作と必要モデルは text と同じ・切替は未配線）
./launch.sh --demo --mode lite
```

---

## 6. Log in with a demo account

Open `http://127.0.0.1:8801` in a browser (if a different number was displayed at startup, use that number). With `--demo`, demo users are inserted automatically, but authentication is still enforced as usual (a username and a password have to be entered). The roles that the DB holds are the **2 values `admin` / `viewer`**.

| Role | Permissions | Search target |
|---|---|---|
| `admin` | All features | The raw vault (no output mask) |
| `viewer` | Mainly viewing | The masked vault (exit mask applied) |

> Names such as `curator` / `data-scientist` are normalized internally to `viewer`.

The actual login information of the shipped `demo.db`:

| Username (default. It is not `admin`) | Role | Password |
|---|---|---|
| `cynovela` | admin | A change is forced at the first login (no fixed password is distributed) |
| `demo` | viewer | See `viewer_password` in the bundled credentials file (`*.admin-password.txt`, received separately from the package tar). No fixed password is distributed |

---

## 7. Your first file ingest and Publish

1. On a `--demo` startup, **only 1 workspace containing the bundled dummy material** is present (the 3 empty seed WSs were removed on 2026-07-30, and are stripped at startup. Measured on 2026-08-02: `/api/workspaces` right after a `--demo` startup contains only "デモワークスペース"). Create your own workspace from "create a new workspace".
2. Specify a name and a RAG strategy in "create collection"
3. Upload files
4. Run "Publish" and get it into the `ready` state

In Publish, text extraction → chunk splitting → PII detection/masking → Embedding generation (stored in ChromaDB) → BM25 index construction are performed. Progress is returned over SSE, and on completion the counts and the elapsed time are recorded into `publish_history`.

---

## 8. Your first question

Ask a question from the RAG Chat screen against a collection in the `ready` state.

```
このドキュメントで扱われている主なトピックは何ですか？
```

In the answer, chunks are displayed as citations with citation numbers `[1][2]`. `admin` searches the raw body text and `viewer` searches the masked body text, and for `viewer` an exit mask is applied to the LLM output as well.

---

## 9. Checking the behavior (tests)

> **`tests/` is not included in the package** (it is excluded when the package is built). With the package you received, `pytest` / `make test` cannot be run.
> To check the behavior, use `conda run -n cynovela python scripts/test_comprehensive_e2e.py`.

```bash
# 開発ツリー（tests/ が在る側）での実行

# 手動 pytest（軽量・最初の失敗で停止）
cd <開発ツリーのフォルダ>
unset SSL_CERT_FILE
conda run -n cynovela python -m pytest -x -q
```

`make test` / `make test-quick` / `make verify-live` of the `Makefile` are also available. The `live` ones assume that the server is running at `http://127.0.0.1:8801` (the number displayed at startup).

---

## Next steps

- [architecture.md](architecture.md) — understand the system composition
- [handson-basic.md](handson-basic.md) — try the basic operations
- [rag-pipeline.md](rag-pipeline.md) — understand the RAG pipeline

---

## Troubleshooting

- **The model download or HTTPS fails with SSL** → run `unset SSL_CERT_FILE` before starting and testing (unnecessary when using the launcher).
- **It cannot be opened from another device on the LAN** → it listens on `0.0.0.0` by default, so first check the port and the destination IP (if `--local-only` is given, it is limited to the local machine).
- **The quality is not stable** → check the model and the settings on the LM Studio side.
- **The admin password was forgotten** → it can be reissued with `conda run -n cynovela python server.py --reset-admin`.
- **Port 8801 is in use** → check with `lsof -i :8801`. When nothing is specified, a free number is chosen automatically, so it can be started as-is. To stop it, use `bash stop.sh` (its content is `podman stop cynovela-all-in-one`. If you started it under a different name, use that name).

For anything else, see [faq.md](faq.md).

---

# 日本語

Cynovela を初めて起動し、最初の RAG 質問を投げるまでの最短手順です。対象は版 `1.0.2`（作業ディレクトリ `<配布物を展開したフォルダ>`）です。

> さらに短い起動メモは [STARTUP.md](../STARTUP.md) を参照してください。

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
cd <配布物を展開したフォルダ>

# launch.sh に渡した引数は、そのまま server.py へ届きます
# （実装: launch.sh の `exec "$PY" server.py "${APP_ARGS[@]}"`。2026-08-02 実測）。
# 引数なしは本番（空のデータベース）です。デモを見るなら --demo を明示します。
./launch.sh --demo            # デモデータ + 実 LLM（既定は 0.0.0.0 で待ち受け。自分の機械の中だけに絞るなら --local-only）
./launch.sh --demo --lan      # デモデータ + LAN 公開
./launch.sh --check           # 起動せずに動く条件だけを調べる
```

停止:

```bash
bash stop.sh
```

（中身は `podman stop cynovela-all-in-one` です。別の名前で起動した場合は、その名前を使ってください。）

### 方法 2: 手動起動

```bash
cd <配布物を展開したフォルダ>
unset SSL_CERT_FILE

# デモデータ + 実 LLM（LM Studio を http://localhost:1234 で起動しておく）
conda run -n cynovela python server.py --demo
```

アクセス:

```bash
open http://127.0.0.1:8801
```

（既定の番号は 8801 です。何も付けないときは空いている番号を自分で選ぶため、起動時に表示された番号を使ってください。）

> ⚠️ **実 LLM が要ります**: 質問への答えを作るには LM Studio などの LLM が要ります。以前あった `--mock`（LLM を呼ばずに動かす指定）は撤去済みで、いま指定するとエラーで止まります。

> **コンテナ版（podman）** で動かす場合は `./launch.sh` を使います（取り込みフォルダの詳細は README を参照）。※ コンテナ手順はコンテナ版にのみ同梱されています（ホスト直起動版には `deploy/` はありません）。

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

ブラウザで `http://127.0.0.1:8801` を開きます（起動時に別の番号が表示されたときは、その番号）。`--demo` ではデモ用ユーザーが自動投入されますが、認証は通常どおり強制されます（ユーザー名とパスワードの入力が要ります）。DB が保持するロールは **`admin` / `viewer` の 2 値**です。

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
cd <開発ツリーのフォルダ>
unset SSL_CERT_FILE
conda run -n cynovela python -m pytest -x -q
```

`Makefile` の `make test` / `make test-quick` / `make verify-live` も利用できます。`live` 系はサーバが `http://127.0.0.1:8801`（起動時に表示された番号）で稼働していることが前提です。

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
- **ポート 8801 が使用中** → `lsof -i :8801` で確認します。何も付けないときは空いている番号を自分で選ぶため、そのまま起動できます。止めるときは `bash stop.sh` です（中身は `podman stop cynovela-all-in-one`。別の名前で起動した場合は、その名前を使ってください）。

その他は [faq.md](faq.md) を参照してください。
