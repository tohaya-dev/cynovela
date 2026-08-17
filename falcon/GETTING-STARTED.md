# はじめかた（コンテナ形態）

**日本語版はこちら → [日本語](#日本語)**

## English

If this is your first time, please start with QUICKSTART.md.

This guide is written so that the two items you received are all you need to get to the end.

- `<配布物名>.tar.gz` … the complete Cynovela set
The initial passwords are written in the "ログイン" (Login) section of `STARTUP.md` inside the tar. There is no separate file sent to you.

Rough time required: 30 to 60 minutes for the first run (most of it is waiting for the container build and for the models to load).
Please carry out the steps in this guide in order, from the top.

---

## 0. What you need

| Requirement | How to check it |
|---|---|
| macOS (Apple silicon recommended) | — |
| podman | Run `podman --version` in Terminal and confirm that a version is printed |
| LM Studio (the LLM that writes the answers) | You can launch the app (it is used in step 5) |
| 20 GB or more of free space | The Avail column of `df -h /` |

If podman is not installed, please install Podman Desktop (https://podman-desktop.io/).
Only the first time, start the Podman virtual machine that runs containers with the following two lines.

```bash
podman machine init      # First time only. If it already exists you will see "already exists"; go on to the next line
podman machine start
```

If something does not work, check the following:

- `podman: command not found` → podman is not installed, or you have not opened a new Terminal window.
- `podman machine start` fails → it may already be running. If `podman machine list` shows
  STATE as `running`, you can simply go on to the next step.

---

## 1. Extract the package

```bash
cd ~/Downloads                      # Go to where you put the tar.gz
tar -xzf<配布物名>.tar.gz
cd<展開してできたフォルダ>            # The name starts with cynovela- (you can check it with ls)
ls launch.sh # If you can see this file, the package extracted correctly
```

If something does not work, check the following:

- `tar: Error opening archive` → the download was cut off partway. Please obtain the file again.
- "No such file or directory" on `cd` → the extracted folder name is different.
  Replace it with the folder name that `ls` shows.

---

## 2. Start it

> **If you received the lightweight package, put the model in place first.**
> The lightweight package (the tar.gz that is a few MB) does not include the embedding model. Follow the
> steps in `SETUP-ACCELERATOR.md` to put bge-m3 into
> `store/models/models--BAAI--bge-m3/snapshots/<版>/`, and then go on to the next command.
> If you run it without doing so, it stops with a message saying that there is no place to store the
> embedding model.
> The all-in-one package (the tar.gz that is a few GB) already includes it, so you can go straight on.

If this is your first time, we recommend trying the **demo**, which comes with sample dummy documents already loaded. Start it with `--demo` (if you start it without that option, you get **production** mode, that is, an empty database).

```bash
./launch.sh --demo
```

This command carries out "build the container → start it → wait for it to come up" in one go.

The screen shows the following, in this order.

```
[build] context=...            ← Build starts (the first time it takes 5 to 20 minutes)
[run] mode=text port=8801      ← Start
[wait] http://127.0.0.1:8801/
ready (12s)                    ← Once you see this, startup is complete
```

- The published port is **8801** by default. To change it, use `./launch.sh --port 8900 --demo`.
- To keep it inside your own Mac only, add `--local-only` at the end
  (without it, other Macs on the same network can also see it).

If something does not work, check the following:

- **It stops without printing `ready`** → `podman logs cynovela-all-in-one` shows what is happening inside.
- **It says `port is already allocated`** → something else is using 8801.
  Start it on a different port, for example `./launch.sh --port 8900 --demo`.
- **The first build stops partway** → only the beginning of the build needs an Internet connection
  (it fetches the container images). Check your connection and run it again.

---

### First time only: a screen asking you to choose how to download the AI model

In the forms that do not bundle the model (the lightweight package, or using this repository as it is), the
AI model that reads your documents (the embedding model bge-m3) is not yet present on the first run. Only when
it is missing, the following three choices appear during startup.

1. **Download it now** — receives about 2.2 GB from the Internet (download source: Hugging Face). A connection is required.
2. **Connect a folder you already have** — connects a model folder you already have at hand.
3. **Cancel** — put the model in place later, then start it again.

No communication starts until you choose one of them.
(If you started from a double-click on `Cynovela-start.command`, the same content appears as a "Download / Cancel" dialog.)

## 3. Open it in a browser

Open the following in a browser (if you changed the port in step 2, use that number instead).

```
http://127.0.0.1:8801
```

If the login screen ("ユーザー名／パスワードでログイン", that is, log in with user name and password) appears, it worked.

If something does not work, check the following:

- The page does not appear → check with `podman ps` that `cynovela-all-in-one` is running.
- The display is blank → right after startup it may still be getting ready. Wait about 10 seconds and reload.

---

## 4. The first login and changing the password

1. Enter **`cynovela`** as the user name.
2. For the password, enter the administrator value written in the **"ログイン" (Login) section of the bundled `STARTUP.md`**.
3. When you log in, "**初回パスワードの変更**" (change your initial password) appears.
   Enter the value you received in "現在のパスワード" (current password), a value of your own choosing in
   "新しいパスワード（8文字以上）" (new password, 8 characters or more), the same value in the confirmation
   field, and press "**パスワードを変更して続行**" (change the password and continue).

**Until you have finished this change, administrative operations such as settings will not go through** (only the change operation goes through).
Please be sure to make the change here.

If something does not work, check the following:

- "ユーザー名またはパスワードが正しくありません" (the user name or password is not correct) → copy and paste the
  value from the password file again (leading and trailing spaces and newlines easily get mixed in here).
- After the change, the admin screen still says "初回パスワードの変更が必要です" (you must change your initial
  password) → log out once, and log in again with the new password.

---

## 5. Connect the LLM that writes the answers

Cynovela is in charge of finding the documents, and **leaves the generation of the text to an LLM running on the same Mac**.
The bundled default is **LM Studio**.

### 5-1. Preparation on the LM Studio side

1. Launch LM Studio.
2. Download and load a **model for chat (for generation)**.
   For example, a conversational model such as `gemma-4-12b-it`.
   **Embedding-only models (those with `embed` or `bge` in the name) cannot write answers.**
3. In the "**Developer**" tab on the left, **Start** the local server (default port 1234).
4. **Enable** "**Serve on Local Network**" on the same screen.
   This is required because the call comes from inside the container.

### 5-2. Settings on the Cynovela side

Open **Settings** → **LLM Provider** in the left menu, and set it as follows.

| Item | Value to enter |
|---|---|
| Provider | `LM Studio` |
| Base URL | `http://host.containers.internal:1234` |
| Model | Press "📋 モデル一覧を取得" (get the model list) and choose **the chat model you loaded in 5-1** |

Press "🔌 接続テスト" (connection test) and confirm that it succeeds,
then save with "💾 LLM設定をまとめて適用" (apply the LLM settings together).

**Please do not leave Model blank.**
When it is blank, the **first entry** of the model list returned by LM Studio is used. If the first entry is an
embedding-only model, the generation request is rejected and no answer comes back; you get an error (HTTP 400).
Be sure to choose a chat model from the list.

If something does not work, check the following:

- The connection test fails → check in the LM Studio Developer tab that the server is in the Start state and
  that "Serve on Local Network" is enabled.
- Nothing appears when you press "モデル一覧を取得" (get the model list) → no model is loaded in LM Studio.
  Load a model in LM Studio and press it again.

- LM Studio does not refuse a model name that it has not loaded; it may answer with a different model that it
  has already loaded. Enter in the Model field an existing model name that you chose from the list.
- If you run several large models at the same time in LM Studio, the answers may become broken or slow.
  It returns to normal by itself after a while.

---

## 6. Try asking a question

1. Open **RAG Chat** in the left menu.
2. Choose the workspace you want in "🏢 Workspace" at the top.
3. Write your question in the input field below and press **▶** on the right (Shift+Enter also sends it).
4. If the answer text appears with **a list of the documents it referred to** below it, it worked.

If something does not work, check the following:

- **Only "該当なし" (no match) comes back** → there are no published documents in that workspace.
  Ingest and publish documents following step 7.
- **You get an error / the answer is empty** → check that Model in step 5-2 is a chat model
  (this is by far the most common cause).
- **It is very slow** → a large model takes tens of seconds for a single answer. Try a smaller model first.

---

## 7. Ingest your own documents

### 7-1. Register the folders to ingest from (a restart is required)

From the container, **only the folders handed to it at startup** can be read. Add them in one of the following ways.

**The easiest way to add one**: double-click **`Cynovela-add-folder.command`** in the package.
A folder chooser appears, and what you choose is written to the backup.

Note: when you use it for the first time, please press `Cynovela-start.command` once first. The Python (the
3.12 series) that handles the backup is prepared inside the package on that first run. If you try to add a
folder without it, the instructions for installing it appear and it stops (it does not fall back to the old
python3 that comes with the Mac).

From the Terminal, do it as follows.

```bash
# Add from a folder chooser (macOS)
./launch.sh --add

# Add by specifying the path directly
./launch.sh --add-path ~/Documents/契約

# See which folders are registered now / remove one
./launch.sh --list
./launch.sh --remove<一覧に出た名前>
```

**You can also remove them from the screen** (Settings → 📁 取り込み元 → "外す"). The list is visible on the same screen.
In this form, pressing "取り込み元を足す" (add an ingest source) on the screen shows the one line to type in the Terminal, in a form you can copy.

Registering alone does not take effect. **Run `./launch.sh` once more** to restart it
(you can also hand the folders over all at once at startup). Until then, the status column of the list says
"起動し直すと読み込めます" (it can be read once you restart).
Your own documents are used in **production** mode (no arguments). Do not add `--demo` here.

```bash
./launch.sh --ingest ~/Documents/契約 --ingest ~/資料
```

### 7-2. Ingest and publish from the screen

1. **Data Sources** in the left menu → "**＋ソース追加**" (add a source) at the top right.
2. Enter an easy-to-understand name in "名前" (name), choose with "📁 参照" (browse) the folder you registered in
   7-1 (or a subfolder inside it), and press "次へ" (next).
3. Choose the workspace to add it to (if there is none, "新しいワークスペースを作成", create a new workspace) → "追加" (add).
4. Wait for the scan to finish.
5. **Collections** in the left menu → "**＋ Collection作成**" (create a collection) to tie the workspace and the source together.
6. Press "**Publish**" on the collection you created. For how to read PDFs, you can choose from
   fast, quality (high accuracy) and vision (read as images).
7. Once the "**✅ Publish 完了**" (publish complete) receipt appears, go back to step 6 and you can ask questions.

If something does not work, check the following:

- **It says "取り込み元がまだ1件もありません" (there are no ingest sources yet)** → either you have not done 7-1,
  or you have not restarted after registering.
- **You cannot choose a folder in the browse screen / you get a 403** → you are pointing outside the range you
  registered in 7-1. Choose a folder inside the range you registered.
- **Publish does not finish** → it takes time when there are many large PDFs. Try fast first.

---

## Appendix: frequently used operations

```bash
# See whether it is running
podman ps

# See the logs inside
podman logs -f cynovela-all-in-one

# Stop it
podman stop cynovela-all-in-one

# Run it again (if it is already built, it comes up right away)
# No arguments means production. If you were using the demo, add --demo
./launch.sh
```

- For detailed startup options, or for using Ollama, see `STARTUP.md`.
- For the configuration that runs the embedding model on an external accelerator, see
  `SETUP-ACCELERATOR.md` (you need it if you received the lightweight package, which does not contain `store/models`).
- Please do not put passwords or tokens in a notes app or a shared folder.
  When you call the API directly, use the token issued each time by the login (`POST /api/auth/login`).
  Tokens that work like a fixed password are not accepted.

---

# 日本語

はじめて使う方は QUICKSTART.md からどうぞ。

受け取ったもの 2 点だけで、最後まで進められるようにした手引きです。

- `<配布物名>.tar.gz` … Cynovela 一式
初期パスワードは tar の中の `STARTUP.md` の「ログイン」の節に書いてあります。別便で受け取るファイルはありません。

所要時間の目安: 初回 30〜60 分（うち大半はコンテナのビルド待ちとモデルの読み込み待ち）。
このガイドの手順は上から順に実行してください。

---

## 0. 用意するもの

| 必要なもの | 確認のしかた |
|---|---|
| macOS（Apple シリコン推奨） | — |
| podman | ターミナルで `podman --version` を実行して版が出ること |
| LM Studio（回答を作る LLM） | アプリを起動できること（手順 5 で使います） |
| 空き容量 20GB 以上 | `df -h /` の Avail 欄 |

podman が入っていない場合は Podman Desktop（https://podman-desktop.io/）を入れてください。
初回だけ、次の 2 行でコンテナを動かす Podman の仮想機械を起動します。

```bash
podman machine init      # 初回のみ。既に作ってあれば「already exists」と出るので次へ進む
podman machine start
```

うまくいかないときに確認すること:

- `podman: command not found` → podman が未インストール、または新しいターミナルを開き直していない。
- `podman machine start` が失敗する → 既に起動済みのことがあります。`podman machine list` で
  STATE が `running` なら、そのまま次へ進んでかまいません。

---

## 1. 展開する

```bash
cd ~/Downloads                      # tar.gz を置いた場所へ
tar -xzf<配布物名>.tar.gz
cd<展開してできたフォルダ>            # 名前は cynovela- で始まります (ls で確認できます)
ls launch.sh # このファイルが見えれば展開できています
```

うまくいかないときに確認すること:

- `tar: Error opening archive` → ダウンロードが途中で切れています。もう一度受け取り直してください。
- `cd` で「No such file or directory」→ 展開先のフォルダ名が違います。
  `ls` で出てきたフォルダ名に読み替えてください。

---

## 2. 起動する

> **軽量版を受け取った方は、先にモデルを置いてください。**
> 軽量版（tar.gz が数 MB のもの）は埋め込みモデルを同梱していません。`SETUP-ACCELERATOR.md`
> の手順に従って `store/models/models--BAAI--bge-m3/snapshots/<版>/` へ bge-m3 を置いてから、
> 次のコマンドへ進んでください。置かずに実行すると「埋め込みモデルの保存先がありません」と
> 表示されて止まります。
> 全部入り（tar.gz が数 GB のもの）は同梱済みなので、このまま進めます。

はじめての方は、同梱のダミー資料が載った**デモ**で試すのがおすすめです。`--demo` を付けて起動してください（付けずに起動すると**本番**＝空のデータベースで始まります）。

```bash
./launch.sh --demo
```

このコマンドは「コンテナの組み立て → 起動 → 起動待ち」までを続けて行います。

画面には次の順で出ます。

```
[build] context=...            ← 組み立て開始（初回は 5〜20 分かかります）
[run] mode=text port=8801      ← 起動
[wait] http://127.0.0.1:8801/
ready (12s)                    ← ここまで出れば起動完了
```

- 公開ポートは既定 **8801** です。変えたいときは `./launch.sh --port 8900 --demo`。
- 自分の Mac の中だけに閉じたいときは末尾に `--local-only` を付けてください
  （付けないと同じネットワークの別の Macからも見えます）。

うまくいかないときに確認すること:

- **`ready` が出ないまま止まる** → `podman logs cynovela-all-in-one` で中の様子が見えます。
- **`port is already allocated` と出る** → 8801 を他のものが使っています。
  `./launch.sh --port 8900 --demo` のように別のポートで起動してください。
- **初回の組み立てで止まる** → 組み立ての最初だけインターネット接続が必要です
  （コンテナのイメージを取得します）。接続を確認してからもう一度実行してください。

---

### 初回だけ：AIモデルのダウンロードを選ぶ画面が出ます

モデルを同梱しない形（軽量版や、このリポジトリをそのまま使う形）では、資料を読み取る
ための AI モデル（埋め込みモデル bge-m3）が初回はまだ入っていません。無いときだけ、
起動の途中で次の三択が出ます。

1. **いまダウンロードする** — インターネットから約 2.2 GB を受け取ります（ダウンロード元: Hugging Face）。通信が要ります。
2. **すでに持っているフォルダをつなぐ** — 手元にあるモデルのフォルダをつなぎます。
3. **やめる** — あとでモデルを置いてから、もう一度起動します。

どれかを選ぶまで、通信は始まりません。
（`Cynovela-start.command` のダブルクリックから始めた場合は、同じ内容が「ダウンロードする／キャンセル」の画面で出ます。）

## 3. ブラウザで開く

ブラウザで次を開きます（手順 2 でポートを変えた場合はその番号に読み替え）。

```
http://127.0.0.1:8801
```

ログイン画面（「ユーザー名／パスワードでログイン」）が出れば成功です。

うまくいかないときに確認すること:

- ページが出ない → `podman ps` で `cynovela-all-in-one` が動いているか確認してください。
- 表示が真っ白 → 起動直後は準備中のことがあります。10 秒ほど待って再読み込みしてください。

---

## 4. 最初のログインとパスワード変更

1. ユーザー名に **`cynovela`** を入力します。
2. パスワードは、**同梱の `STARTUP.md` の「ログイン」の節**に書いてある管理者の値を入力します。
3. ログインすると「**初回パスワードの変更**」が出ます。
   「現在のパスワード」に受け取った値、「新しいパスワード（8文字以上）」に自分で決めた値を入れ、
   確認欄にも同じ値を入れて「**パスワードを変更して続行**」を押します。

**この変更を済ませるまで、設定などの管理操作は通りません**（変更操作だけが通ります）。
必ずここで変更してください。

うまくいかないときに確認すること:

- 「ユーザー名またはパスワードが正しくありません」→ パスワードファイルの値をコピー＆貼り付けで
  入れ直してください（前後の空白や改行が混ざりやすいところです）。
- 変更後に管理画面で「初回パスワードの変更が必要です」と出る → 一度ログアウトして、
  新しいパスワードでログインし直してください。

---

## 5. 回答を作る LLM をつなぐ

Cynovela は資料を探すところまでを担当し、**文章の生成は同じ Mac で動く LLM に任せます**。
同梱の既定は **LM Studio** です。

### 5-1. LM Studio 側の準備

1. LM Studio を起動する。
2. **チャット用（生成用）のモデル**をダウンロードしてロードする。
   例: `gemma-4-12b-it` のような会話用のモデル。
   **埋め込み専用のモデル（名前に `embed` や `bge` が入るもの）は回答を作れません。**
3. 左の「**Developer**」タブでローカルサーバーを **Start** する（既定ポート 1234）。
4. 同じ画面の「**Serve on Local Network**」を**有効**にする。
   コンテナの中から呼ぶため、これが必要です。

### 5-2. Cynovela 側の設定

左メニューの **Settings** → **LLM Provider** を開き、次のように設定します。

| 項目 | 入れる値 |
|---|---|
| Provider | `LM Studio` |
| Base URL | `http://host.containers.internal:1234` |
| Model | 「📋 モデル一覧を取得」を押し、**5-1 でロードしたチャット用モデル**を選ぶ |

「🔌 接続テスト」を押して成功を確認し、
「💾 LLM設定をまとめて適用」で保存します。

**Model を空欄のままにしないでください。**
空欄のときは LM Studio が返すモデル一覧の**先頭**が使われます。先頭が埋め込み専用モデルだと
生成要求が拒否され、回答が返らずエラー（HTTP 400）になります。
必ず一覧からチャット用モデルを選んでください。

うまくいかないときに確認すること:

- 接続テストが失敗する → LM Studio の Developer タブでサーバーが Start 状態か、
  「Serve on Local Network」が有効かを確認してください。
- 「モデル一覧を取得」で何も出ない → LM Studio にモデルがロードされていません。
  LM Studio 側でモデルを読み込んでから、もう一度押してください。

・LM Studio は、読み込んでいないモデルの名前を指定しても断らず、
  読み込み済みの別のモデルで答えることがあります。Model 欄には、
  一覧から選んだ実在のモデル名を入れてください。
・LM Studio で大きなモデルを同時にいくつも動かすと、回答が崩れたり
  遅くなったりすることがあります。時間が経つと自動で元に戻ります。

---

## 6. 質問してみる

1. 左メニューの **RAG Chat** を開きます。
2. 上部の「🏢 Workspace」で対象のワークスペースを選びます。
3. 下の入力欄に質問を書き、右の **▶** を押します（Shift+Enter でも送信できます）。
4. 回答本文と、その下に**参照した資料の一覧**が出れば成功です。

うまくいかないときに確認すること:

- **「該当なし」しか返らない** → そのワークスペースに公開済みの資料がありません。
  手順 7 で資料を取り込んで公開してください。
- **エラーになる／回答が空** → 手順 5-2 の Model がチャット用モデルになっているか確認してください
  （ここが原因のことが最も多いところです）。
- **とても遅い** → 大きなモデルは 1 回の回答に数十秒かかります。まずは小さめのモデルで試してください。

---

## 7. 自分の資料を取り込む

### 7-1. 取り込み元のフォルダを登録する（起動し直しが必要）

コンテナからは、**起動時に渡したフォルダだけ**が読めます。追加は次のいずれかで行います。

**いちばん簡単な足し方**: 配布物の中の **`Cynovela-add-folder.command`** をダブルクリックします。
フォルダを選ぶ画面が出て、選ぶとバックアップに書かれます。

※ はじめて使うときは、先に `Cynovela-start.command` を一度押してください。バックアップを扱う
Python（3.12 系）はその最初の一度で配布物の中に用意されます。無いまま足そうとすると、
入れ方の手順が出て止まります（Mac に元から入っている古い python3 へは倒れません）。

ターミナルからは次のようにします。

```bash
# フォルダを選ぶ画面から追加する（macOS）
./launch.sh --add

# パスを直接指定して追加する
./launch.sh --add-path ~/Documents/契約

# 今どれが登録されているか見る／消す
./launch.sh --list
./launch.sh --remove<一覧に出た名前>
```

**外すのは画面からもできます**（Settings → 📁 取り込み元 → 「外す」）。一覧も同じ画面で見られます。
この形では、画面の「取り込み元を足す」を押すと、ターミナルで叩く1行がコピーできる形で表示されます。

登録しただけでは反映されません。**もう一度 `./launch.sh` を実行**して
起動し直してください（起動時にまとめて渡すこともできます）。それまで一覧の状態の欄には
「起動し直すと読み込めます」と出ます。
自分の資料は**本番**（引数なし）で使います。ここでは `--demo` は付けません。

```bash
./launch.sh --ingest ~/Documents/契約 --ingest ~/資料
```

### 7-2. 画面で取り込みと公開を行う

1. 左メニュー **Data Sources** →右上の「**＋ソース追加**」。
2. 「名前」に分かりやすい名前を入れ、「📁 参照」で 7-1 で登録したフォルダ（またはその中の
   サブフォルダ）を選び、「次へ」。
3. 追加先のワークスペースを選ぶ（無ければ「新しいワークスペースを作成」）→「追加」。
4. スキャンが終わるのを待ちます。
5. 左メニュー **Collections** → 「**＋ Collection作成**」でワークスペースとソースを結び付けます。
6. 作った Collection の「**Publish**」を押します。PDF の読み取り方は
   fast（速い）/ quality（高精度）/ vision（画像として読む）から選べます。
7. 「**✅ Publish 完了**」の受領書が出たら、手順 6 に戻って質問できます。

うまくいかないときに確認すること:

- **「取り込み元がまだ1件もありません」と出る** → 7-1 をやっていないか、
  登録後に起動し直していません。
- **参照画面でフォルダを選べない／403 になる** → 7-1 で登録した範囲の外を指しています。
  登録した範囲の中のフォルダを選んでください。
- **Publish が終わらない** → 大きな PDF が多いと時間がかかります。まず fast で試してください。

---

## 付録: よく使う操作

```bash
# 動いているか見る
podman ps

# 中のログを見る
podman logs -f cynovela-all-in-one

# 止める
podman stop cynovela-all-in-one

# もう一度動かす（組み立て済みならすぐ立ち上がります）
# 引数なしは本番。デモで使っていた場合は --demo を付ける
./launch.sh
```

- 詳しい起動オプションや Ollama を使う場合は `STARTUP.md` を見てください。
- 埋め込み用のモデルを外部のアクセラレータで動かす構成については `SETUP-ACCELERATOR.md` を
  見てください（`store/models` が入っていない軽量版を受け取った場合は、こちらが必要です）。
- パスワードやトークンをメモ帳や共有フォルダに置かないでください。
  API を直接叩く場合のトークンは、ログイン（`POST /api/auth/login`）で毎回発行されるものを使います。
  固定のパスワードのようなトークンは受け付けません。
