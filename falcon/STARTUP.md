# Cynovela 起動・運用ガイド

**日本語版はこちら → [日本語](#日本語)**

## English

Cynovela Startup and Operations Guide.

If this is your first time, please start with QUICKSTART.md.

## Everyday startup procedure

This form runs on a single path inside a container. There is no path for running
`python server.py` directly on the host (the only entry point is `./launch.sh`).

There are two kinds of startup. **`--demo` is the demo** (the state with the bundled dummy documents loaded),
and **no argument is production** (it starts from an empty database, and you ingest and use your own documents).
Double-clicking `Cynovela-start.command` starts production (empty). The demo is started with `./launch.sh --demo`.

```bash
# Start the demo (with the bundled dummy documents)
./launch.sh --demo

# Start production (empty database)
./launch.sh

# Open it in a browser
# http://localhost:8801  (this form opens on host-side 8801)
```

### First time only: a screen for choosing whether to download the AI model appears

In forms that do not bundle the model (the lightweight package, or using this repository as it is), the AI model
for reading documents (the embedding model bge-m3) is not yet present the first time. Only when it is missing,
the following three choices appear in the middle of startup.

1. **Download it now** — receives about 2.2 GB from the internet (download source: Hugging Face). A connection is required.
2. **Connect a folder you already have** — connects a model folder you have on hand.
3. **Stop** — place the model later, then start again.

No communication begins until you choose one of them.
(If you started from a double-click of `Cynovela-start.command`, the same content appears on a "Download / Cancel" screen.)

## Startup options

| Option | Description |
|---|---|
| `--mode text` | Text mode (standard) |
| `--demo` | Start with the demo DB that has the dummy documents loaded (if not given, production = an empty database) |
| `--reset-admin` | **It is not wired into the entry point of this line (`./launch.sh`).** This form runs on a single path inside a container, and the entry point does not accept this option (0 receivers in `./launch.sh`). Change the administrator password after you enter the screen. The initial password is in the "Login" section below |
| `--local-only` | Restrict to inside your own machine only (the default listens on all addresses, `0.0.0.0`) |
| `--port N` | Port number (default 8801. It can be changed with `server.port` in `cynovela.yaml`) |

### List of startup forms (--mode) (measured in DD-CYN-0097, 2026-08-12)

| Form | What changes |
|---|---|
| `--mode text` | Default. It runs with all features of text RAG |
| `--mode lite` | Switching is not wired, so only the displayed name changes (behavior is the same as text) |
| `--mode lite-en` | Switching is not wired, so only the displayed name changes (behavior is the same as text) |

All of them can be specified in the form `./launch.sh --demo --mode <name> --port <number>` (measured).


## Startup in a container (podman)

Instead of starting directly on the host, you can start in a container (podman).

```bash
# Build and start (./launch.sh does build -> start -> initial setup hints)
# With no argument it starts production (an empty database)
./launch.sh

# If you want to try it first, use the demo (with the dummy documents)
./launch.sh --demo
```

- The published port is `HOSTPORT` (default 8801). By default it is also visible from other Macs on the same network (published to all addresses). To close it to the inside of your own Mac only, add `--local-only` (it is narrowed to 127.0.0.1 only).
- The key of the safe is placed on the host side at `keys/secret.key`, and is passed to the container read-only (the first time, it is copied from the bundled `store/secret.key`. The bundled demo documents are encrypted with this key, so without the copy even the administrator cannot read the original text).
- The model (store/models) is a read-only mount. **The lightweight package does not bundle the model, so place the model first by the procedure in `SETUP-ACCELERATOR.md`** (if you start without it, it stops before starting). Data is saved in a named volume of the container.

### Passing multiple ingest sources

You can pass any number of ingest sources (the root folders of documents) at startup.

```bash
# Specify several at startup (each one lines up in the list of the folder browsing screen)
./launch.sh --ingest ~/Documents/契約 --ingest /path/to/資料

# Only add, without starting (a restart is required for it to take effect)
# * Add, list, and remove use python of the 3.12 line (if this is your first time,
#   press Cynovela-start.command once first, and it is prepared inside the package)
./launch.sh --add-path /path/to/新しい取り込み元

# Add from the folder selection screen (macOS. A double-click of Cynovela-add-folder.command is the same)
./launch.sh --add

# List and delete (list and "remove" can also be done from Settings -> 📁 ingest sources on the screen)
./launch.sh --list
./launch.sh --remove <internal name>
```

- `--ingest` is **an argument of the container startup script**. The startup options of `server.py` in this form do not have `--ingest` (measured 2026-08-02: the argparse of `server.py` in the container edition does not have `--ingest`; it exists only in the host direct-start edition).
- An addition takes effect **only after a restart**. Until then, the status column of the list says "it can be loaded after a restart". In this form you cannot add from the screen. If you press "add an ingest source" on the screen, the one line to type in a terminal is shown in a form you can copy.
- Registered roots are kept in the backup file `store/ingest-roots.json`.
- If you pass no root at all, it starts with the dummy documents inside this package (`dummy-corpus`) as the ingest source. When there is no root at all in the folder browsing of the screen, the guide "there is not even one ingest source yet" appears.
- Paths outside the roots are refused with 403 (please add them as an ingest source first, then use them).
- After logging in as the administrator, if you run `./launch.sh --sync-labels <Bearer token>`, the path display on the screen becomes the actual location on the Mac side.

## Login (default user names and initial passwords)

The default user names are **administrator `cynovela`** / **viewer `demo`** (not `admin`).
The initial passwords are as follows.

- Administrator: user name `cynovela` / password: `Cynovela1!`
- Viewer: user name `demo` / password: `demo1234`

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
   When calling from the container form, **enable "Serve on Local Network"** on the LM Studio side.
3. Open **Settings > LLM Provider** in the left menu of Cynovela, and set
   - Provider: `LM Studio`
   - Base URL:
     - `http://localhost:1234` for a host direct start
     - `http://host.containers.internal:1234` for the container form
     (the screen is filled in with the default value for the form from the start)
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

# When calling from the container form, make Ollama listen on all addresses
OLLAMA_HOST=0.0.0.0 ollama serve
```

In Settings > LLM Provider, set Provider: `Ollama`; for Base URL,
`http://localhost:11434` for a host direct start, or `http://host.containers.internal:11434`
for the container form; and for Model, enter **the model name that appears in `ollama list`**
as it is (as with LM Studio, always specify an existing chat model name).

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
# Host direct start: specify it with --port (default 8765). When using the demo, add --demo as well
python server.py --mode text --port 8900
```

```bash
# Container form: the published port is specified with the environment variable HOSTPORT (default 8801)
#   Inside the container it stays 8765. Only the published port on the host side changes.
./launch.sh --port 8900
```

When it does not work: if the specified port is already in use, startup fails.
Check the process that is using it with `lsof -i :8900`, and choose another port.

## Checking the logs

```bash
# Server log (real time). When using the demo, add --demo as well
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

---

# 日本語

はじめて使う方は QUICKSTART.md からどうぞ。

## 日常の起動手順

この形態はコンテナの中で動く 1 本道です。ホストで直接 `python server.py` を
動かす道はありません（入口は `./launch.sh` の 1 本です）。

起動の中身は 2 通りあります。**`--demo` はデモ**（同梱のダミー資料が載った状態）、
**引数なしは本番**（空のデータベースから始まり、自分の資料を取り込んで使う）です。
`Cynovela-start.command` のダブルクリックは本番（空）で立ち上がります。デモは `./launch.sh --demo` で起こします。

```bash
# デモ（同梱のダミー資料入り）で起動する
./launch.sh --demo

# 本番（空のデータベース）で起動する
./launch.sh

# ブラウザで開く
# http://localhost:8801  (この形態はホスト側 8801 で開きます)
```

### 初回だけ：AIモデルのダウンロードを選ぶ画面が出ます

モデルを同梱しない形（軽量版や、このリポジトリをそのまま使う形）では、資料を読み取る
ための AI モデル（埋め込みモデル bge-m3）が初回はまだ入っていません。無いときだけ、
起動の途中で次の三択が出ます。

1. **いまダウンロードする** — インターネットから約 2.2 GB を受け取ります（ダウンロード元: Hugging Face）。通信が要ります。
2. **すでに持っているフォルダをつなぐ** — 手元にあるモデルのフォルダをつなぎます。
3. **やめる** — あとでモデルを置いてから、もう一度起動します。

どれかを選ぶまで、通信は始まりません。
（`Cynovela-start.command` のダブルクリックから始めた場合は、同じ内容が「ダウンロードする／キャンセル」の画面で出ます。）

## 起動オプション

| オプション | 説明 |
|---|---|
| `--mode text` | テキストモード（標準） |
| `--demo` | ダミー資料が載ったデモDBで起動（付けなければ本番＝空のデータベース） |
| `--reset-admin` | **この系統の入口（`./launch.sh`）には配線されていません。**この形はコンテナの中で動く1本道で、入口はこの指定を受け取りません（`./launch.sh` に受け口 0 件）。管理者のパスワードは、画面に入ってから変えてください。最初のパスワードは下の「ログイン」の節にあります |
| `--local-only` | 自分のマシンの中だけに絞る（既定は全アドレス `0.0.0.0` で待ち受け） |
| `--port N` | ポート番号（既定 8801。`cynovela.yaml` の `server.port` で変えられます） |

### 起動の形（--mode）の一覧（DD-CYN-0097 実測・2026-08-12）

| 形 | 何が変わるか |
|---|---|
| `--mode text` | 既定。テキストRAGの全機能で動きます |
| `--mode lite` | 切替は未配線のため、表示名が変わるだけです（動作は text と同じ） |
| `--mode lite-en` | 切替は未配線のため、表示名が変わるだけです（動作は text と同じ） |

いずれも `./launch.sh --demo --mode <名前> --port <番号>` の形で指定できます（実測済み）。


## コンテナでの起動（podman）

ホスト直起動の代わりに、コンテナ（podman）で起動できます。

```bash
# ビルドと起動（./launch.sh がビルド→起動→初期設定ヒントまで行う）
# 引数なしは本番（空のデータベース）で起動します
./launch.sh

# 最初に試すならデモ（ダミー資料入り）で
./launch.sh --demo
```

- 公開ポートは `HOSTPORT`（既定 8801）。既定では同じネットワークの別の Macからも見えます（全アドレス向け公開）。自分の Mac の中だけに閉じるには `--local-only` を付けてください（127.0.0.1 のみに絞られます）。
- 金庫の鍵はホスト側 `keys/secret.key` に置かれ、読み取り専用でコンテナへ渡されます（初回は同梱の `store/secret.key` からコピーされます。同梱デモの資料はこの鍵で暗号化されているため、コピーしないと管理者でも原文を読めません）。
- モデル（store/models）は読み取り専用マウントです。**軽量版はモデルを同梱していないため、先に `SETUP-ACCELERATOR.md` の手順でモデルを置いてください**（無いまま起動すると、起動する前に止まります）。データはコンテナの named volume に保存されます。

### 取り込み元を複数渡す

取り込み元（ドキュメントのルートフォルダ）は起動時に何件でも渡せます。

```bash
# 起動時に複数指定（それぞれがフォルダ参照画面の一覧に並ぶ）
./launch.sh --ingest ~/Documents/契約 --ingest /path/to/資料

# 起動せずに追加だけ行う（反映には起動し直しが必要）
# ※ 追加・一覧・外すは 3.12 系の python を使います（はじめてなら先に一度
#    Cynovela-start.command を押すと、配布物の中に用意されます）
./launch.sh --add-path /path/to/新しい取り込み元

# フォルダ選択画面から追加（macOS。Cynovela-add-folder.command のダブルクリックでも同じ）
./launch.sh --add

# 一覧・削除（一覧と「外す」は画面の Settings → 📁 取り込み元 からもできます）
./launch.sh --list
./launch.sh --remove <中の名前>
```

- `--ingest` は**コンテナ起動用スクリプトの引数**です。本形態の `server.py` の起動指定に `--ingest` はありません（2026-08-02 実測: コンテナ版の `server.py` の argparse に `--ingest` は無く、ホスト直起動版にのみ在ります）。
- 追加が効くのは**起動し直したあと**です。それまで一覧の状態の欄には「起動し直すと読み込めます」と出ます。この形では画面から足せません。画面の「取り込み元を足す」を押すと、ターミナルで叩く1行がコピーできる形で表示されます。
- 登録済みのルートはバックアップファイル `store/ingest-roots.json` に保持されます。
- ルートを1件も渡さない場合は、この配布物の中のダミー資料（`dummy-corpus`）を取り込み元にして起動します。画面のフォルダ参照でルートが1件も無いときは「取り込み元がまだ1件もありません」とガイドが出ます。
- ルートの外のパスは 403 で拒否されます（先に取り込み元として足してから使ってください）。
- 管理者でログイン後、`./launch.sh --sync-labels <Bearerトークン>` を実行すると、画面のパス表示が Mac 側の実際の場所になります。

## ログイン（既定の利用者名と初期パスワード）

既定の利用者名は **管理者 `cynovela`** / **閲覧者 `demo`** です（`admin` ではありません）。
初期パスワードは次のとおりです。

- 管理者: ユーザー名 `cynovela` / パスワード: `Cynovela1!`
- 閲覧者: ユーザー名 `demo` / パスワード: `demo1234`

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
   コンテナ形態から呼ぶ場合は、LM Studio 側で **"Serve on Local Network" を有効**にする。
3. Cynovela の左メニュー **Settings > LLM Provider** を開き、
   - Provider: `LM Studio`
   - Base URL:
     - ホスト直起動なら `http://localhost:1234`
     - コンテナ形態なら `http://host.containers.internal:1234`
     （画面には形態に応じた既定値が最初から入ります）
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

# コンテナ形態から呼ぶ場合は Ollama を全アドレスで待ち受けさせる
OLLAMA_HOST=0.0.0.0 ollama serve
```

Settings > LLM Provider で Provider: `Ollama`、Base URL は
ホスト直起動なら `http://localhost:11434`、コンテナ形態なら
`http://host.containers.internal:11434`、Model は **`ollama list` に出るモデル名**を
そのまま入力します（LM Studio と同じく、実在するチャット用モデル名を必ず指定）。

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
# ホスト直起動: --port で指定する（既定 8765）。デモで使う場合は --demo も付ける
python server.py --mode text --port 8900
```

```bash
# コンテナ形態: 公開ポートは環境変数 HOSTPORT で指定する（既定 8801）
#   コンテナ内は 8765 のまま。ホスト側の公開ポートだけが変わる。
./launch.sh --port 8900
```

うまくいかないとき: 指定したポートが既に使われていると起動に失敗します。
`lsof -i :8900` で使用中のプロセスを確認し、別のポートを選んでください。

## ログ確認

```bash
# サーバーログ（リアルタイム）。デモで使う場合は --demo も付ける
python server.py --mode text 2>&1 | tee ~/cynovela.log
```
