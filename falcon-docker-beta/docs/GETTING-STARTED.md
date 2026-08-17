# はじめかた（コンテナ形態）

**日本語版はこちら → [日本語](#日本語)**

## English

If this is your first time, please start with quickstart.md.

This is a guide written so that you can go all the way through with only the 2 things you received.

- `<配布物名>.tar.gz` … the complete Cynovela set
The initial password is written in the "ログイン" (Login) section of `STARTUP.md` inside the tar. There is no file that arrives separately.

Rough time required: 30–60 minutes for the first run (most of it is waiting for the container build and for the model to load).
Run the steps in this guide in order from the top.

---

## 0. What you need

| What you need | How to check it |
|---|---|
| macOS (Apple silicon recommended) | — |
| podman | Run `podman --version` in a terminal and confirm that a version appears |
| LM Studio (the LLM that writes the answers) | You can start the app (used in step 5) |
| 20GB or more of free space | The Avail column of `df -h /` |

If podman is not installed, install Podman Desktop (https://podman-desktop.io/).
Only for the first time, the following 2 lines start the Podman virtual machine that runs the containers.

```bash
podman machine init      # 初回のみ。既に作ってあれば「already exists」と出るので次へ進む
podman machine start
```

What to check when it does not work:

- `podman: command not found` → podman is not installed, or you have not opened a new terminal.
- `podman machine start` fails → it may already be running. If STATE is `running` in `podman machine list`, you may go on to the next step as is.

---

## 1. Extract it

```bash
cd ~/Downloads                      # tar.gz を置いた場所へ
tar -xzf<配布物名>.tar.gz
cd<展開してできたフォルダ>            # 名前は cynovela- で始まります (ls で確認できます)
ls launch.sh # このファイルが見えれば展開できています
```

What to check when it does not work:

- `tar: Error opening archive` → the download was cut off partway. Please receive it again.
- "No such file or directory" on `cd` → the name of the extracted folder is different.
  Read it as the folder name that `ls` shows.

---

## 2. Start it

> **If you received the lightweight version, put the model in place first.**
> The lightweight version (the one whose tar.gz is a few MB) does not bundle the embedding model. Follow the steps
> in `SETUP-ACCELERATOR.md`, put bge-m3 into `store/models/models--BAAI--bge-m3/snapshots/<版>/`, and then
> go on to the next command. If you run it without doing that, it stops with
> 「埋め込みモデルの保存先がありません」 (there is no place to store the embedding model).
> The all-in-one version (the one whose tar.gz is a few GB) already bundles it, so you can go on as is.

For a first try, we recommend the **demo**, which is loaded with the bundled dummy documents. Start it with `--demo` (if you start it without that, you begin with **production** = an empty database).

```bash
./launch.sh --demo
```

This command runs "build the container → start → wait for it to come up" in one go.

The screen shows the following, in this order.

```
[build] context=...            ← 組み立て開始（初回は 5〜20 分かかります）
[run] mode=text port=8801      ← 起動
[wait] http://127.0.0.1:8801/
ready (12s)                    ← ここまで出れば起動完了
```

- The published port is **8801** by default. To change it, use `./launch.sh --port 8900 --demo`.
- To keep it closed inside your own Mac, add `--local-only` at the end
  (without it, other Macs on the same network can see it too).

What to check when it does not work:

- **It stops without printing `ready`** → `podman logs cynovela-all-in-one` shows what is going on inside.
- **`port is already allocated` appears** → something else is using 8801.
  Start it on a different port, like `./launch.sh --port 8900 --demo`.
- **The first build stops** → only the beginning of the build needs an internet connection
  (it pulls the container image). Check the connection and run it again.

---

## 3. Open it in a browser

Open the following in a browser (if you changed the port in step 2, read it as that number).

```
http://127.0.0.1:8801
```

If the login screen (「ユーザー名／パスワードでログイン」 — log in with user name and password) appears, it worked.

What to check when it does not work:

- The page does not appear → check with `podman ps` whether `cynovela-all-in-one` is running.
- The display is blank → right after startup it may still be getting ready. Wait about 10 seconds and reload.

---

## 4. The first login and the password change

1. Enter **`cynovela`** as the user name.
2. For the password, enter the administrator value written in **the "ログイン" (Login) section of the bundled `STARTUP.md`**.
3. When you log in, 「**初回パスワードの変更**」 (change your initial password) appears.
   Enter the value you received in "現在のパスワード" (current password) and a value you decide yourself in "新しいパスワード（8文字以上）" (new password, 8 characters or more),
   enter the same value in the confirmation field as well, and press 「**パスワードを変更して続行**」 (change the password and continue).

**Until you finish this change, administrative operations such as settings do not go through** (only the change operation goes through).
Be sure to change it here.

What to check when it does not work:

- 「ユーザー名またはパスワードが正しくありません」 (the user name or password is not correct) → copy and paste the value from the password file
  and enter it again (leading or trailing spaces and newlines easily get mixed in here).
- 「初回パスワードの変更が必要です」 (the initial password must be changed) appears on the admin screen after the change → log out once and
  log in again with the new password.

---

## 5. Connect the LLM that writes the answers

Cynovela is in charge of finding the documents, and **leaves generating the text to an LLM running on the same Mac**.
The bundled default is **LM Studio**.

### 5-1. Preparation on the LM Studio side

1. Start LM Studio.
2. Download and load a **chat (generation) model**.
   Example: a conversational model such as `gemma-4-12b-it`.
   **A model dedicated to embedding (one with `embed` or `bge` in its name) cannot write answers.**
3. On the **Developer** tab on the left, **Start** the local server (default port 1234).
4. **Enable** **Serve on Local Network** on the same screen.
   This is needed because it is called from inside the container.

### 5-2. Settings on the Cynovela side

Open **Settings** → **LLM Provider** in the left menu, and set it as follows.

| Item | Value to enter |
|---|---|
| Provider | `LM Studio` |
| Base URL | `http://host.containers.internal:1234` |
| Model | Press 「📋 モデル一覧を取得」 (get the model list) and choose **the chat model you loaded in 5-1** |

Press 「🔌 接続テスト」 (connection test) and confirm that it succeeds,
then save with 「💾 LLM設定をまとめて適用」 (apply the LLM settings together).

**Do not leave Model blank.**
When it is blank, the **first** entry of the model list that LM Studio returns is used. If the first one is an embedding-only model,
the generation request is rejected, no answer comes back, and you get an error (HTTP 400).
Always choose a chat model from the list.

What to check when it does not work:

- The connection test fails → check on the LM Studio Developer tab that the server is in the Start state,
  and that "Serve on Local Network" is enabled.
- Nothing appears with "モデル一覧を取得" → no model is loaded in LM Studio.
  Load a model on the LM Studio side and press it again.

・LM Studio does not refuse a model name that has not been loaded; it may
  answer with a different model that is loaded. In the Model field, enter
  a real model name chosen from the list.
・If you run several large models at the same time in LM Studio, the answers may break down or
  become slow. It returns to normal by itself after a while.

---

## 6. Try asking a question

1. Open **RAG Chat** in the left menu.
2. Choose the target workspace in 「🏢 Workspace」 at the top.
3. Write your question in the input field below, and press **▶** on the right (Shift+Enter sends it too).
4. If the answer body and, below it, **the list of documents it referenced** appear, it worked.

What to check when it does not work:

- **Only 「該当なし」 (no match) comes back** → there are no published documents in that workspace.
  Ingest and publish documents in step 7.
- **You get an error / the answer is empty** → check that Model in step 5-2 is a chat model
  (this is the most common cause).
- **It is very slow** → a large model takes tens of seconds for one answer. Try a smaller model first.

---

## 7. Ingest your own documents

### 7-1. Register the folder to ingest from (a restart is required)

From inside the container, **only the folders passed at startup** can be read. Add more in one of the following ways.

**The easiest way to add one**: double-click **`Cynovela-add-folder.command`** in the package.
A folder chooser appears, and what you choose is written to the backup.

From a terminal, do it like this.

```bash
# フォルダを選ぶ画面から追加する（macOS）
./launch.sh --add

# パスを直接指定して追加する
./launch.sh --add-path ~/Documents/契約

# 今どれが登録されているか見る／消す
./launch.sh --list
./launch.sh --remove<一覧に出た名前>
```

**You can also remove them from the screen** (Settings → 📁 取り込み元 → 「外す」). The list is on the same screen.
In this form, pressing "取り込み元を足す" (add an ingest source) on the screen shows the one line to type in a terminal, in a copyable form.

Registering alone does not take effect. **Run `./launch.sh` once more** to
restart it (you can also pass them all together at startup). Until then, the status column of the list shows
「起動し直すと読み込めます」 (it becomes readable after you restart).
Use your own documents in **production** (no arguments). Do not add `--demo` here.

```bash
./launch.sh --ingest ~/Documents/契約 --ingest ~/資料
```

### 7-2. Ingest and publish from the screen

1. Left menu **Data Sources** → 「**＋ソース追加**」 (add a source) at the top right.
2. Enter an easy-to-understand name in "名前" (name), choose the folder you registered in 7-1 (or a
   subfolder inside it) with 「📁 参照」 (browse), and press 「次へ」 (next).
3. Choose the workspace to add it to (if there is none, 「新しいワークスペースを作成」 create a new workspace) → 「追加」 (add).
4. Wait for the scan to finish.
5. Left menu **Collections** → 「**＋ Collection作成**」 (create a Collection) ties the workspace and the source together.
6. Press **Publish** on the Collection you made. For how PDFs are read, you can choose from
   fast / quality (high accuracy) / vision (read as images).
7. When the 「**✅ Publish 完了**」 (Publish finished) receipt appears, go back to step 6 and you can ask questions.

What to check when it does not work:

- **「取り込み元がまだ1件もありません」 (there is not a single ingest source yet) appears** → either you have not done 7-1,
  or you have not restarted after registering.
- **You cannot choose a folder on the browse screen / you get 403** → you are pointing outside the range registered in 7-1.
  Choose a folder inside the registered range.
- **Publish does not finish** → it takes time when there are many large PDFs. Try fast first.

---

## Appendix: Common operations

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

- For detailed startup options and for using Ollama, see `STARTUP.md`.
- For a configuration that runs the embedding model on an external accelerator, see
  `SETUP-ACCELERATOR.md` (if you received the lightweight version, which does not include `store/models`, you need this one).
- Do not put passwords or tokens in a notes app or a shared folder.
  If you call the API directly, use the token that login (`POST /api/auth/login`) issues each time.
  A fixed, password-like token is not accepted.

---

# 日本語

はじめて使う方は quickstart.md からどうぞ。

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
