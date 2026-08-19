# Cynovela 起動・運用ガイド

**日本語版はこちら → [日本語](#日本語)**

## English

Cynovela Startup and Operations Guide.

If this is your first time, please start with quickstart.md.

## Everyday startup procedure

There are two ways to start. **No argument is production** (it starts from an empty database, and you ingest and use your own documents), and **adding `--demo` is the demo** (the demo DB with the dummy documents loaded).

```bash
# The entry point is launch.sh (or double-click Cynovela-start.command)
./launch.sh            # production: an empty database
./launch.sh --demo     # if you want to try it first, use the demo (with the dummy documents)

# Open it in a browser
# http://localhost:8765
```

If you must start the server by hand instead of through `launch.sh` (the environment must already exist — the dedicated name is `cynovela-dist`; never create or modify a shared environment):

```bash
# 1. Activate the dedicated environment of this package
conda activate cynovela-dist

# 2. Countermeasure for the SSL certificate error (macOS. launch.sh does this for you)
unset SSL_CERT_FILE

# 3. Start the server
python server.py --mode text          # production
python server.py --mode text --demo   # demo
```

### First time only: a screen for choosing whether to download the AI model appears

In forms that do not bundle the model (the lightweight package, or using this repository as it is), the AI model
for reading documents (the embedding model bge-m3) is not yet present the first time. Only when it is missing,
the following three choices appear in the middle of startup.

1. **Download it now** — receives about 2.2 to 2.3 GB from the internet (download source: Hugging Face). A connection is required.
2. **Choose a folder you already have** — connects a model folder you have on hand.
3. **Start with the lightest settings, without downloading** — starts with no communication.

No communication begins until you choose one of them.
(If you started from a double-click of `Cynovela-start.command`, the same content appears on a "Download / Cancel" screen.)

## Startup options

| Option | Description |
|---|---|
| `--mode text` | Text mode (standard) |
| `--demo` | Start with the demo DB that has the dummy documents loaded (if not given, production = an empty database) |
| `--reset-admin` | Reset the administrator password, show the new value, and exit. **The target database is chosen by the same rule as the other options, so when fixing the administrator of the demo, write `--demo` together** (without it, production `store/db/cynovela.db` becomes the target, and it is newly created if it does not exist. The demo side does not change, so the demo login stays 401. Measured 2026-08-02) |
| `--local-only` | Restrict to inside your own machine only (the default listens on all addresses, `0.0.0.0`) |
| `--port N` | Port number (default 8765) |

### List of startup forms (--mode) (measured in , 2026-08-12)

| Form | What changes |
|---|---|
| `--mode text` | Default. It runs with all features of text RAG |
| `--mode lite` | Switching is not wired, so only the displayed name changes (behavior is the same as text) |
| `--mode lite-en` | Switching is not wired, so only the displayed name changes (behavior is the same as text) |

All of them can be specified in the form `./launch.sh --demo --mode<name> --port<number>` (measured).


### Passing multiple ingest sources

You can pass any number of ingest sources (the root folders of documents) at startup (`--ingest` of `server.py` is an append option. Measured 2026-08-02).

```bash
# Specify several at startup (each one lines up in the list of the folder browsing screen)
./launch.sh --demo --ingest ~/Documents/契約 --ingest /path/to/資料

# Only add, without starting (it can be chosen right away from the running screen)
# * Add, list, and remove use python of the 3.12 line (if this is your first time,
#   press Cynovela-start.command once first, and it is prepared)
./launch.sh --add-path /path/to/新しい取り込み元

# Add from the folder selection screen (macOS. A double-click of Cynovela-add-folder.command is the same)
./launch.sh --add

# List and delete (add, view, and remove can also be done from Settings -> 📁 ingest sources on the screen)
./launch.sh --list
./launch.sh --remove<internal name>
```

- In this form, **adding and removing from the screen take effect as they are. A restart is not required** (the backup is re-read every time it is referenced).
- Registered roots are kept in the backup file `store/ingest-roots.json`.
- If you pass no root at all, it starts with the dummy documents inside this package (`dummy-corpus`) as the ingest source. When there is no root at all in the folder browsing of the screen, "there is not even one ingest source yet" appears, and you can add one from "add an ingest source" right there.
- Paths outside the roots are refused with 403 (please add them with "add an ingest source" on the screen, then use them).

## Login (default user names and initial passwords)

The default user names are **administrator `cynovela`** / **viewer `demo`** (not `admin`).
**The initial passwords are printed on the screen the first time you start it.**
They are not written in this file, so that a copy of the documentation cannot
be used to sign in. Look at the terminal window that opens on the first start.

The administrator is asked to change the password at the first login. After changing it, enter with the new value.
The viewer can be used as it is. **After you receive it, change the administrator password first.**

## How to create a viewer when you started with nothing loaded

If you started with nothing loaded, at first only the administrator exists. You create the viewer yourself.
Enter as the administrator, add a new user from user management, and choose viewer as the role.
If you started with the trial documents, a viewer is prepared in advance.

## LLM provider settings

The bundled default is **LM Studio** (`llm.provider: lmstudio` /
`llm.base_url: http://localhost:1234` in `cynovela.yaml`). Please use this default as it is at first.

### When using LM Studio (default, recommended)

1. Start LM Studio and **load a model for chat (for generation)**.
2. Start the local server on the "Developer" tab of LM Studio (default port 1234).
3. Open **Settings > LLM Provider** in the left menu of Cynovela, and set
   - Provider: `LM Studio`
   - Base URL: `http://localhost:1234` (this form starts directly from the host, so localhost)
   - Model: **press "📋 fetch the model list" and choose an existing chat model from the list**
4. Confirm success with "🔌 connection test", and save with "💾 apply the LLM settings together".

**Please do not leave Model blank (`auto`).**
When the model name is not specified, the **first** entry of the model list returned by LM Studio is used.
If the first one is an embedding-only model (bge-m3 and so on), the generation request is refused, no answer comes back,
and it becomes an error (HTTP 400). Choosing a **chat model** from the list resolves it.
(Measured 2026-07-29: an answer was obtained just by changing the model name to an existing chat model.
Whether or not `/v1` is added to the end of the Base URL does not affect the result.)

- LM Studio does not refuse even if you specify the name of a model that is not loaded,
  and it may answer with a different model that is already loaded. In the Model field, enter
  an existing model name chosen from the list.
- If you run several large models at the same time in LM Studio, the answers may break down or
  become slow. It returns to normal automatically after a while.

### When using Ollama (it is not the default)

It also works with Ollama, but that is not the bundled default configuration. The procedure below is only for when you use it.

```bash
# Get the chat model you want to use (the model name is up to you. The following is one example)
ollama pull qwen3:8b
```

In Settings > LLM Provider, set Provider: `Ollama`, Base URL: `http://localhost:11434`,
and for Model, enter **the model name that appears in `ollama list`** as it is
(as with LM Studio, always specify an existing chat model name).

**Note**: When using LM Studio and Ollama at the same time, be careful about memory.
When switching, it is recommended to unload the LM Studio model before switching.

## Document ingest procedure

1. "Add a source" on the **Sources** page
   - Enter a local path (example: `/Users/username/Documents/`)
   - Wait until the scan finishes

2. "Create a collection" on the **Collections** page
   - Choose a WS (workspace)
   - Link the sources

3. **Publish**
   - Choose a collection and press "Publish"
   - PDF mode: fast / quality / vision (OCR)
   - Wait until it finishes (large PDFs take time)

4. Start the RAG chat in **Chat**

## Backup

```bash
# Backup of the DB and Chroma
cp -r store/ ~/cynovela-backup-$(date +%Y%m%d)/
```

## Changing the port

The port **is decided by the argument at startup**. Even if you rewrite `server.port` in `cynovela.yaml`,
it is not reflected in the listening port (the setting is loaded, but it is not passed to the listener).

```bash
# Specify it with --port (default 8765). The arguments passed to launch.sh reach server.py as they are.
# When using the demo, please add --demo as well.
./launch.sh --port 8900

# If you activate the conda environment yourself, doing it directly is the same
python server.py --mode text --port 8900
```

When it does not work: if the specified port is already in use, startup fails.
Check the process that is using it with `lsof -i :8900`, and choose another port.
Note that `./launch.sh` only looks at the usage of the default port 8765 and prompts you to confirm.
When you specify another port, check with `lsof` yourself.

## Checking the logs

```bash
# Server log (real time). When using the demo, add --demo as well
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

---

# 日本語

はじめて使う方は quickstart.md からどうぞ。

## 日常の起動手順

起動は 2 通りあります。**引数なしは本番**（空のデータベースから始まり、自分の資料を取り込んで使う）、**`--demo` を付けるとデモ**（ダミー資料が載ったデモDB）です。

```bash
# 入口は launch.sh です（または Cynovela-start.command をダブルクリック）
./launch.sh            # 本番: 空のデータベース
./launch.sh --demo     # 最初に試すならデモ（ダミー資料入り）で

# ブラウザで開く
# http://localhost:8765
```

`launch.sh` を通さず手でサーバーを起動する場合（環境が既に在ることが前提です。専用の名前は `cynovela-dist`。共有の環境は作らない・書き換えないでください）:

```bash
# 1. この配布物専用の環境を有効化
conda activate cynovela-dist

# 2. SSL証明書エラー対策（macOS。launch.sh はこれを内包しています）
unset SSL_CERT_FILE

# 3. サーバー起動
python server.py --mode text          # 本番
python server.py --mode text --demo   # デモ
```

### 初回だけ：AIモデルのダウンロードを選ぶ画面が出ます

モデルを同梱しない形（軽量版や、このリポジトリをそのまま使う形）では、資料を読み取る
ための AI モデル（埋め込みモデル bge-m3）が初回はまだ入っていません。無いときだけ、
起動の途中で次の三択が出ます。

1. **いまダウンロードする** — インターネットから約 2.2〜2.3 GB を受け取ります（ダウンロード元: Hugging Face）。通信が要ります。
2. **すでに持っているフォルダを選ぶ** — 手元にあるモデルのフォルダをつなぎます。
3. **ダウンロードせずに、いちばん軽い設定で始める** — 通信なしで始めます。

どれかを選ぶまで、通信は始まりません。
（`Cynovela-start.command` のダブルクリックから始めた場合は、同じ内容が「ダウンロードする／キャンセル」の画面で出ます。）

## 起動オプション

| オプション | 説明 |
|---|---|
| `--mode text` | テキストモード（標準） |
| `--demo` | ダミー資料が載ったデモDBで起動（付けなければ本番＝空のデータベース） |
| `--reset-admin` | 管理者パスワードをリセットし、新しい値を表示して終了する。**対象のデータベースは他の指定と同じ規則で選ばれるため、デモの管理者を直すときは `--demo` を併記する**（付けないと本番の `store/db/cynovela.db` が対象になり、無ければ新規作成される。デモ側は変わらないのでデモのログインは 401 のまま。2026-08-02 実測） |
| `--local-only` | 自分のマシンの中だけに絞る（既定は全アドレス `0.0.0.0` で待ち受け） |
| `--port N` | ポート番号（既定 8765） |

### 起動の形（--mode）の一覧（実測・2026-08-12）

| 形 | 何が変わるか |
|---|---|
| `--mode text` | 既定。テキストRAGの全機能で動きます |
| `--mode lite` | 切替は未配線のため、表示名が変わるだけです（動作は text と同じ） |
| `--mode lite-en` | 切替は未配線のため、表示名が変わるだけです（動作は text と同じ） |

いずれも `./launch.sh --demo --mode<名前> --port<番号>` の形で指定できます（実測済み）。


### 取り込み元を複数渡す

取り込み元（ドキュメントのルートフォルダ）は起動時に何件でも渡せます（`server.py` の `--ingest` は append 指定。2026-08-02 実測）。

```bash
# 起動時に複数指定（それぞれがフォルダ参照画面の一覧に並ぶ）
./launch.sh --demo --ingest ~/Documents/契約 --ingest /path/to/資料

# 起動せずに追加だけ行う（動いている画面からすぐに選べます）
# ※ 追加・一覧・外すは 3.12 系の python を使います（はじめてなら先に一度
#    Cynovela-start.command を押すと用意されます）
./launch.sh --add-path /path/to/新しい取り込み元

# フォルダ選択画面から追加（macOS。Cynovela-add-folder.command のダブルクリックでも同じ）
./launch.sh --add

# 一覧・削除（足す・見る・外すは画面の Settings → 📁 取り込み元 からもできます）
./launch.sh --list
./launch.sh --remove<中の名前>
```

- この形態では、**画面から足す・外すがそのまま効きます。起動し直しは要りません**（バックアップは参照のたびに読み直されます）。
- 登録済みのルートはバックアップファイル `store/ingest-roots.json` に保持されます。
- ルートを1件も渡さない場合は、この配布物の中のダミー資料（`dummy-corpus`）を取り込み元にして起動します。画面のフォルダ参照でルートが1件も無いときは「取り込み元がまだ1件もありません」と出て、その場の「取り込み元を足す」から足せます。
- ルートの外のパスは 403 で拒否されます（画面の「取り込み元を足す」で足してから使ってください）。

## ログイン（既定の利用者名と初期パスワード）

既定の利用者名は **管理者 `cynovela`** / **閲覧者 `demo`** です（`admin` ではありません）。
**初期パスワードは、はじめて起動したときに画面に出ます。**
この文書には書いていません。文書のコピーだけでログインできてしまうのを避けるためです。
初回の起動で開くターミナルの画面をご覧ください。

管理者は初回ログインでパスワードの変更を求められます。変更したあとは新しい値で入ってください。
閲覧者はそのまま使えます。**受け取ったあと、最初に管理者のパスワードを変えてください。**

## 何も入れずに始めた場合の、閲覧者の作り方

何も入れずに始めた場合、最初に居るのは管理者だけです。閲覧者はご自身で作ります。
管理者で入り、利用者の管理から新しい利用者を追加し、役割に閲覧者を選んでください。
お試しの資料で始めた場合は、閲覧者があらかじめ用意されています。

## LLMプロバイダーの設定

同梱の既定は **LM Studio** です（`cynovela.yaml` の `llm.provider: lmstudio` /
`llm.base_url: http://localhost:1234`）。まずはこの既定のまま使ってください。

### LM Studio を使う場合（既定・推奨）

1. LM Studio を起動し、**チャット用（生成用）のモデルをロード**する。
2. LM Studio の「Developer」タブでローカルサーバーを開始する（既定ポート 1234）。
3. Cynovela の左メニュー **Settings > LLM Provider** を開き、
   - Provider: `LM Studio`
   - Base URL: `http://localhost:1234`（本形態はホストから直接起動するため localhost）
   - Model: **「📋 モデル一覧を取得」を押し、一覧から実在するチャット用モデルを選ぶ**
4. 「🔌 接続テスト」で成功を確認し、「💾 LLM設定をまとめて適用」で保存する。

**Model を空欄（`auto`）のままにしないでください。**
モデル名が未指定のときは LM Studio が返すモデル一覧の**先頭**が使われます。
先頭が埋め込み専用モデル（bge-m3 等）だと生成要求が拒否され、回答が返らず
エラー（HTTP 400）になります。一覧から**チャット用モデル**を選べば解消します。
（2026-07-29 実測: モデル名を実在のチャット用モデルに変えるだけで回答が成立。
Base URL の末尾に `/v1` を付けるかどうかは結果に影響しません。）

・LM Studio は、読み込んでいないモデルの名前を指定しても断らず、
  読み込み済みの別のモデルで答えることがあります。Model 欄には、
  一覧から選んだ実在のモデル名を入れてください。
・LM Studio で大きなモデルを同時にいくつも動かすと、回答が崩れたり
  遅くなったりすることがあります。時間が経つと自動で元に戻ります。

### Ollama を使う場合（既定ではありません）

Ollama でも動きますが、同梱の既定構成ではありません。使う場合のみ次の手順です。

```bash
# 使いたいチャット用モデルを取得する（モデル名は任意。以下は一例）
ollama pull qwen3:8b
```

Settings > LLM Provider で Provider: `Ollama`、Base URL: `http://localhost:11434`、
Model は **`ollama list` に出るモデル名**をそのまま入力します
（LM Studio と同じく、実在するチャット用モデル名を必ず指定）。

**注意**: LM Studio と Ollama を同時使用する場合はメモリに注意。
切り替え時はLM Studioのモデルをアンロードしてから切り替えることを推奨。

## ドキュメントの取り込み手順

1. **Sources** ページで「ソース追加」
   - ローカルパス（例: `/Users/username/Documents/`）を入力
   - スキャン完了まで待つ

2. **Collections** ページで「コレクション作成」
   - WS（ワークスペース）を選択
   - ソースを紐付ける

3. **Publish**
   - コレクションを選択して「Publish」
   - PDFモード: fast（高速）/ quality（高品質）/ vision（OCR）
   - 完了まで待つ（大容量PDFは時間がかかります）

4. **Chat** でRAGチャット開始

## バックアップ

```bash
# DBとChromaのバックアップ
cp -r store/ ~/cynovela-backup-$(date +%Y%m%d)/
```

## ポート変更

ポートは**起動時の引数で決まります**。`cynovela.yaml` の `server.port` を書き換えても
待ち受けポートには反映されません（設定は読み込まれますが待ち受けには渡っていません）。

```bash
# --port で指定する（既定 8765）。launch.sh に渡した引数はそのまま server.py へ届きます。
# デモで使う場合は --demo も付けてください。
./launch.sh --port 8900

# conda 環境を自分で有効化している場合は直接でも同じです
python server.py --mode text --port 8900
```

うまくいかないとき: 指定したポートが既に使われていると起動に失敗します。
`lsof -i :8900` で使用中のプロセスを確認し、別のポートを選んでください。
なお `./launch.sh` は既定ポート 8765 の使用状況だけを見て確認を促します。
別ポートを指定したときは自分で `lsof` を確認してください。

## ログ確認

```bash
# サーバーログ（リアルタイム）。デモで使う場合は --demo も付ける
python server.py --mode text 2>&1 | tee ~/cynovela.log
```
