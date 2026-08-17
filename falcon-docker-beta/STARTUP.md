# Cynovela 起動・運用ガイド

**日本語版はこちら → [日本語](#日本語)**

## English

If this is your first time, please start from QUICKSTART.md.

## Everyday startup steps

This form runs inside a container along a single path. There is no way to run
`python server.py` directly on the host (the only entry point is `./launch.sh`).

There are 2 kinds of startup content. **`--demo` is the demo** (the state with the bundled
dummy documents loaded), and **no argument is production** (it starts from an empty database,
and you ingest your own documents and use them).
Double-clicking `Cynovela-start.command` starts up in production (empty). The demo is started with `./launch.sh --demo`.

```bash
# デモ（同梱のダミー資料入り）で起動する
./launch.sh --demo

# 本番（空のデータベース）で起動する
./launch.sh

# ブラウザで開く
# http://localhost:8801  (この形態はホスト側 8801 で開きます)
```

## Startup options

| Option | Description |
|---|---|
| `--mode text` | Text mode (standard) |
| `--demo` | Start with the demo DB that has the dummy documents loaded (without it, production = an empty database) |
| `--reset-admin` | **It is not wired into the entry point of this line (`./launch.sh`).** This form runs inside a container along a single path, and the entry point does not accept this option (0 receivers in `./launch.sh`). Please change the administrator password after you get into the screen. The first password is in the "Login" section below |
| `--local-only` | Limit it to inside your own machine only (the default listens on all addresses, `0.0.0.0`) |
| `--port N` | Port number (default 8801. It can be changed with `server.port` in `cynovela.yaml`) |

### List of the startup forms (--mode) (measured in DD-CYN-0097, 2026-08-12)

| Form | What changes |
|---|---|
| `--mode text` | Default. It runs with all functions of text RAG |
| `--mode lite` | The switch is not wired, so only the displayed name changes (the behavior is the same as text) |
| `--mode lite-en` | The switch is not wired, so only the displayed name changes (the behavior is the same as text) |

All of them can be specified in the form `./launch.sh --demo --mode <name> --port <number>` (measured).


## Startup in a container (podman)

Instead of starting directly on the host, you can start it in a container (podman).

```bash
# ビルドと起動（./launch.sh がビルド→起動→初期設定ヒントまで行う）
# 引数なしは本番（空のデータベース）で起動します
./launch.sh

# 最初に試すならデモ（ダミー資料入り）で
./launch.sh --demo
```

- The published port is `HOSTPORT` (default 8801). By default it is visible from other Macs on the same network as well (published to all addresses). To close it to inside your own Mac only, add `--local-only` (it is narrowed to 127.0.0.1 only).
- The vault key is placed on the host side at `keys/secret.key` and is passed to the container read-only (on the first run it is copied from the bundled `store/secret.key`. The bundled demo documents are encrypted with this key, so without the copy even an administrator cannot read the original text).
- The models (store/models) are a read-only mount. **The lightweight version does not bundle the models, so please place the models first, following the steps in `SETUP-ACCELERATOR.md`** (if you start without them, it stops before starting). The data is saved in a named volume of the container.

### Passing multiple ingest sources

You can pass any number of ingest sources (root folders of documents) at startup.

```bash
# 起動時に複数指定（それぞれがフォルダ参照画面の一覧に並ぶ）
./launch.sh --ingest ~/Documents/契約 --ingest /path/to/資料

# 起動せずに追加だけ行う（反映には起動し直しが必要）
./launch.sh --add-path /path/to/新しい取り込み元

# フォルダ選択画面から追加（macOS。Cynovela-add-folder.command のダブルクリックでも同じ）
./launch.sh --add

# 一覧・削除（一覧と「外す」は画面の Settings → 📁 取り込み元 からもできます）
./launch.sh --list
./launch.sh --remove <中の名前>
```

- `--ingest` is **an argument of the container startup script**. The startup options of `server.py` in this form do not have `--ingest` (measured 2026-08-02: the argparse of `server.py` of the container version has no `--ingest`; it exists only in the host direct-start version).
- An addition takes effect **only after a restart**. Until then, the status column of the list shows "起動し直すと読み込めます" (it can be loaded after a restart). In this form you cannot add it from the screen. When you press "取り込み元を足す" (add an ingest source) on the screen, the one line to type in the terminal is shown in a copyable form.
- Registered roots are kept in the backup file `store/ingest-roots.json`.
- If you pass no root at all, it starts with the dummy documents (`dummy-corpus`) inside this package as the ingest source. When there is no root at all in the folder browse screen, the guide "取り込み元がまだ1件もありません" (there is not a single ingest source yet) is shown.
- Paths outside the roots are rejected with 403 (please add them as an ingest source first).
- After logging in as an administrator, if you run `./launch.sh --sync-labels <Bearer token>`, the path display on the screen becomes the actual location on the Mac side.

## Login (default user names and initial passwords)

The default user names are **administrator `cynovela`** / **viewer `demo`** (not `admin`).
The initial passwords are as follows.

- Administrator: user name `cynovela` / password: `Cynovela1!`
- Viewer: user name `demo` / password: `demo1234`

The administrator is asked to change the password at the first login. After changing it, please log in with the new value.
The viewer can be used as is. **After you receive this, please change the administrator password first.**

## How to create a viewer when you started without loading anything

When you started without loading anything, the only one there at first is the administrator. You create the viewer yourself.
Log in as the administrator, add a new user from the user management, and choose the viewer role.
When you started with the trial documents, a viewer is prepared in advance.

## LLM provider settings

The bundled default is **LM Studio** (`llm.provider: lmstudio` /
`llm.base_url: http://localhost:1234` in `cynovela.yaml`). Please use this default as it is at first.

### When you use LM Studio (default, recommended)

1. Start LM Studio and **load a model for chat (for generation)**.
2. Start the local server in the "Developer" tab of LM Studio (default port 1234).
   When you call it from the container form, **enable "Serve on Local Network"** on the LM Studio side.
3. Open **Settings > LLM Provider** in the left menu of Cynovela, and
   - Provider: `LM Studio`
   - Base URL:
     - `http://localhost:1234` if it is a host direct start
     - `http://host.containers.internal:1234` if it is the container form
     (the screen is filled in with the default value for the form from the beginning)
   - Model: **press "📋 モデル一覧を取得" (get the model list) and choose an existing chat model from the list**
4. Confirm success with "🔌 接続テスト" (connection test), and save with "💾 LLM設定をまとめて適用" (apply the LLM settings together).

**Please do not leave Model blank (`auto`).**
When the model name is not specified, the **first** of the model list returned by LM Studio is used.
If the first one is an embedding-only model (bge-m3 etc.), the generation request is rejected, no answer comes back,
and it becomes an error (HTTP 400). It is resolved if you choose a **chat model** from the list.
(Measured 2026-07-29: the answer worked just by changing the model name to an existing chat model.
Whether or not you put `/v1` at the end of the Base URL does not affect the result.)

- Even if you specify the name of a model that is not loaded, LM Studio does not refuse it,
  and it may answer with another model that is loaded. In the Model field, please enter
  an existing model name that you chose from the list.
- If you run several large models at the same time in LM Studio, the answers may break down
  or become slow. It returns to normal automatically after some time.

### When you use Ollama (it is not the default)

It also works with Ollama, but it is not the bundled default configuration. The following steps are only for when you use it.

```bash
# 使いたいチャット用モデルを取得する（モデル名は任意。以下は一例）
ollama pull qwen3:8b

# コンテナ形態から呼ぶ場合は Ollama を全アドレスで待ち受けさせる
OLLAMA_HOST=0.0.0.0 ollama serve
```

In Settings > LLM Provider, set Provider: `Ollama`; for Base URL,
`http://localhost:11434` if it is a host direct start, or
`http://host.containers.internal:11434` if it is the container form; and for Model, enter
**the model name that appears in `ollama list`** as it is (the same as LM Studio, always specify an existing chat model name).

**Note**: When you use LM Studio and Ollama at the same time, be careful about memory.
When switching, it is recommended to unload the LM Studio model before switching.

## Steps for ingesting documents

1. "ソース追加" (add a source) on the **Sources** page
   - Enter a local path (e.g. `/Users/username/Documents/`)
   - Wait until the scan is complete

2. "コレクション作成" (create a collection) on the **Collections** page
   - Choose the WS (workspace)
   - Link the sources

3. **Publish**
   - Choose the collection and press "Publish"
   - PDF mode: fast / quality / vision (OCR)
   - Wait until it is complete (a large PDF takes time)

4. Start the RAG chat in **Chat**

## Backup

```bash
# DBとChromaのバックアップ
cp -r store/ ~/cynovela-backup-$(date +%Y%m%d)/
```

## Changing the port

The port **is decided by the argument at startup**. Even if you rewrite `server.port` in `cynovela.yaml`,
it is not reflected in the listening port (the setting is loaded, but it is not passed to the listening).

```bash
# ホスト直起動: --port で指定する（既定 8765）。デモで使う場合は --demo も付ける
python server.py --mode text --port 8900
```

```bash
# コンテナ形態: 公開ポートは環境変数 HOSTPORT で指定する（既定 8801）
#   コンテナ内は 8765 のまま。ホスト側の公開ポートだけが変わる。
./launch.sh --port 8900
```

When it does not go well: if the port you specified is already in use, the startup fails.
Check the process that is using it with `lsof -i :8900`, and choose another port.

## Checking the logs

```bash
# サーバーログ（リアルタイム）。デモで使う場合は --demo も付ける
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
