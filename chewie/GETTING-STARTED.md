# はじめかた（Mac から直接起動する形態）

**日本語版はこちら → [日本語](#日本語)**

## English

If this is your first time, please start with QUICKSTART.md.

This guide is written so that you can get all the way to the end with only the 2 items you received.

- `<配布物名>.tar.gz` … the complete Cynovela set
The initial password is written in the "ログイン" (Login) section of `STARTUP.md` inside the tar. There is no separate file to receive.

Rough time required: 30-60 minutes for the first run (most of it is waiting for the runtime environment to be created and for the model to load).
Run the steps in this guide in order from the top.

---

## 0. What to prepare

| What you need | How to check it |
|---|---|
| macOS (Apple silicon recommended) | — |
| conda (miniforge recommended) | Run `conda --version` in a terminal and confirm that a version is printed |
| LM Studio (the LLM that writes the answers) | You can start the app (it is used in step 5) |
| 20GB or more of free space | The Avail column of `df -h /` |

If conda is not installed, install miniforge.
(From https://github.com/conda-forge/miniforge/releases/latest, get `Miniforge3-MacOSX-arm64.sh` for Apple silicon and run it.)

What to check when it does not work:

- `conda: command not found` → In most cases the terminal has not been reopened after the installation.
  Open a new terminal and check again.

---

## 1. Extract

```bash
cd ~/Downloads                # tar.gz を置いた場所へ
tar -xzf <配布物名>.tar.gz
cd <展開してできたフォルダ>      # 名前は cynovela- で始まります (ls で確認できます)
ls launch.sh                  # このファイルが見えれば展開できています
```

What to check when it does not work:

- `tar: Error opening archive` → The download was cut off partway. Please receive it again.
- "No such file or directory" on `cd` → The name of the extracted folder is different.
  Replace it with the folder name that `ls` printed.

---

## 2. Create the runtime environment and start

For your first time, we recommend trying the **demo**, which comes with the bundled dummy documents. Start it with `--demo` (if you start it without `--demo`, it starts as **production**, that is, with an empty database).

```bash
./launch.sh --demo
```

This single command goes all the way from creating the conda environment, to installing the required components, to starting up.
The screen prints the following in order.

```
[Step 1] conda を確認中...
✅ conda: /Users/xxx/miniforge3
[Step 2] conda環境 'cynovela' を確認中...
⚠️  環境 'cynovela' が見つかりません。作成します...
   （初回は5〜15分かかります）
[Step 3] 環境 'cynovela' をアクティベート中...
[Step 4] pip パッケージを確認中...
[Step 5] ポート8765の状態を確認中...
[Step 6] Cynovela を起動します...
Cynovela を起動します... (http://localhost:8765)
```

- The listening port is **8765** by default. To change it, use `./launch.sh --demo --port 8900`.
- From the second time on, the environment creation is skipped and it starts in about 1 minute.

What to check when it does not work:

- **You are asked "ポート8765はすでに使用中です" (port 8765 is already in use)** → A previous run is still there.
  Choosing `r` (stop the existing one and start again) is the safe option.
- **The environment creation in Step 2 fails** → Check the free space and the internet connection
  (a connection is needed only for the first run, to fetch the components).
- **When you want to stop it** → Run `bash stop.sh` in another terminal.

---

### First time only: a screen appears for choosing how to download the AI model

In the forms that do not bundle the model (the lightweight package, or using this repository as-is), the AI model
that reads the documents (the embedding model bge-m3) is not yet present on the first run. Only when it is missing,
the following three choices appear in the middle of startup.

1. **Download it now** — Receive about 2.2-2.3 GB from the internet (download source: Hugging Face). A connection is required.
2. **Choose a folder you already have** — Connect a model folder you already have at hand.
3. **Start with the lightest settings without downloading** — Start without any connection.

No communication starts until you choose one of them.
(If you started by double-clicking `Cynovela-start.command`, the same content appears as a "download / cancel" dialog.)

## 3. Open it in a browser

Open the following in a browser (if you changed the port in step 2, read it as that number).

```
http://localhost:8765
```

If the login screen ("ユーザー名／パスワードでログイン") appears, it worked.

What to check when it does not work:

- The page does not appear → Check whether an error is printed in the terminal you started it from.
- The display is blank white → Right after startup it may still be preparing. Wait about 10 seconds and reload.

---

## 4. First login and password change

1. Enter **`cynovela`** as the user name.
2. For the password, enter the administrator value written in the **"ログイン" (Login) section of the bundled `STARTUP.md`**.
3. When you log in, "**初回パスワードの変更**" (change your initial password) appears.
   Enter the value you received in "現在のパスワード" (current password), a value of your own choosing in
   "新しいパスワード（8文字以上）" (new password, 8 characters or more), enter the same value in the confirmation
   field as well, and press "**パスワードを変更して続行**" (change the password and continue).

**Until you finish this change, administrative operations such as settings will not go through** (only the change operation goes through).
Be sure to change it here.

What to check when it does not work:

- "ユーザー名またはパスワードが正しくありません" (the user name or password is incorrect) → Copy and paste the value from the
  password file and enter it again (leading/trailing spaces and newlines easily get mixed in here).
- After the change, the admin screen says "初回パスワードの変更が必要です" (the initial password must be changed) → Log out once
  and log in again with the new password.

---

## 5. Connect the LLM that writes the answers

Cynovela is responsible up to the point of finding the documents, and **leaves the text generation to an LLM running on the same Mac**.
The bundled default is **LM Studio**.

### 5-1. Preparation on the LM Studio side

1. Start LM Studio.
2. Download and load a **model for chat (for generation)**.
   Example: a conversational model such as `gemma-4-12b-it`.
   **Embedding-only models (those with `embed` or `bge` in the name) cannot write answers.**
3. In the "**Developer**" tab on the left, **Start** the local server (default port 1234).

### 5-2. Settings on the Cynovela side

Open **Settings** → **LLM Provider** in the left menu and set it as follows.

| Item | Value to enter |
|---|---|
| Provider | `LM Studio` |
| Base URL | `http://localhost:1234` |
| Model | Press "📋 モデル一覧を取得" (get the model list) and choose the **chat model you loaded in 5-1** |

Press "🔌 接続テスト" (connection test) to confirm success,
and save with "💾 LLM設定をまとめて適用" (apply the LLM settings together).

**Do not leave Model blank.**
When it is blank, the **first entry** of the model list returned by LM Studio is used. If the first entry is an
embedding-only model, the generation request is rejected, no answer comes back, and you get an error (HTTP 400).
Always choose a chat model from the list.

What to check when it does not work:

- The connection test fails → Check in the LM Studio Developer tab whether the server is in the Start state.
- Nothing appears with "モデル一覧を取得" → No model is loaded in LM Studio.
  Load a model on the LM Studio side and press it again.

- Even if you specify the name of a model that is not loaded, LM Studio may not refuse and may
  answer with a different model that is loaded. In the Model field, enter a model name that
  actually exists, chosen from the list.
- If you run several large models at the same time in LM Studio, the answers may break down or
  become slow. It returns to normal automatically after some time.

---

## 6. Try asking a question

1. Open **RAG Chat** in the left menu.
2. Choose the target workspace in "🏢 Workspace" at the top.
3. Write your question in the input field at the bottom and press **▶** on the right (Shift+Enter also sends it).
4. If the answer text appears with **the list of documents it referred to** below it, it worked.

What to check when it does not work:

- **Only "該当なし" (no match) comes back** → There are no published documents in that workspace.
  Ingest and publish documents in step 7.
- **You get an error / the answer is empty** → Check whether Model in step 5-2 is a chat model
  (this is the most common cause).
- **It is very slow** → A large model takes tens of seconds for a single answer. Try a smaller model first.

---

## 7. Ingest your own documents

### 7-1. Register the folder to ingest from

Only **the range of the registered folders** can be read. You can add them from the screen.

**Add from the screen (recommended)**: left menu **Settings** → **"📁 取り込み元"** (ingest sources) → **"取り込み元を足す"** (add an ingest source).
You browse and choose a folder. **What you add is usable immediately. No restart is needed.**
Removing is done from the same screen with **"外す"** (remove).

**Add by double-clicking**: Double-click **`Cynovela-add-folder.command`** in the package.
A folder chooser appears, and when you choose one it is written to the backup and becomes selectable immediately
from the screen that is already running.

* When you use it for the first time, press `Cynovela-start.command` once first. The Python (the 3.12 series) that
handles the backup is prepared during that first run. If you try to add without it, the installation steps are
printed and it stops (it does not fall back to the old python3 that comes with the Mac).

From a terminal, do it as follows.

```bash
# フォルダを選ぶ画面から追加する（macOS）
./launch.sh --add

# パスを直接指定して追加する
./launch.sh --add-path ~/Documents/契約

# 今どれが登録されているか見る／消す
./launch.sh --list
./launch.sh --remove <一覧に出た名前>
```

Your own documents are used in **production** (no arguments). Do not add `--demo` here.
You can also pass them all at once at startup.

```bash
./launch.sh --ingest ~/Documents/契約 --ingest ~/資料
```

### 7-2. Ingest and publish from the screen

1. Left menu **Data Sources** → "**＋ソース追加**" (add source) at the top right.
2. Enter an easy-to-understand name in "名前" (name), choose with "📁 参照" (browse) the folder you registered in
   7-1 (or a subfolder inside it), and press "次へ" (next).
3. Choose the workspace to add it to (if there is none, "新しいワークスペースを作成" = create a new workspace) → "追加" (add).
4. Wait for the scan to finish.
5. Left menu **Collections** → "**＋ Collection作成**" (create a Collection) to link the workspace and the source.
6. Press "**Publish**" on the Collection you created. For how to read PDFs you can choose from
   fast, quality, or vision (read as images).
7. When the "**✅ Publish 完了**" (publish complete) receipt appears, go back to step 6 and ask a question.

What to check when it does not work:

- **"取り込み元がまだ1件もありません" (there is not a single ingest source yet) appears** → You have not done the registration in 7-1 yet.
  Add one from "取り込み元を足す" on the screen. It is usable immediately.
- **You cannot choose a folder in the browse screen / you get a 403** → You are pointing outside the range registered in 7-1.
  Choose a folder inside the registered range.
- **Publish does not finish** → It takes time when there are many large PDFs. Try fast first.

---

## Appendix: frequently used operations

```bash
# 起動（2 回目以降）。引数なしは本番。デモで使っていた場合は --demo を付ける
./launch.sh

# 停止
bash stop.sh

# ログを流しながら起動したいとき（デモで使う場合は --demo も付ける）
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

- For detailed startup options, or when using Ollama, see `STARTUP.md`.
- Do not put passwords or tokens in a memo app or a shared folder.
  For a token when calling the API directly, use the one issued each time by login (`POST /api/auth/login`).
  A fixed, password-like token is not accepted.

---

# 日本語

はじめて使う方は QUICKSTART.md からどうぞ。

受け取ったもの 2 点だけで、最後まで進められるようにした手引きです。

- `<配布物名>.tar.gz` … Cynovela 一式
初期パスワードは tar の中の `STARTUP.md` の「ログイン」の節に書いてあります。別便で受け取るファイルはありません。

所要時間の目安: 初回 30〜60 分（うち大半は動作環境の作成待ちとモデルの読み込み待ち）。
このガイドの手順は上から順に実行してください。

---

## 0. 用意するもの

| 必要なもの | 確認のしかた |
|---|---|
| macOS（Apple シリコン推奨） | — |
| conda（miniforge 推奨） | ターミナルで `conda --version` を実行して版が出ること |
| LM Studio（回答を作る LLM） | アプリを起動できること（手順 5 で使います） |
| 空き容量 20GB 以上 | `df -h /` の Avail 欄 |

conda が入っていない場合は miniforge を入れてください。
（https://github.com/conda-forge/miniforge/releases/latest から、Apple シリコンなら
`Miniforge3-MacOSX-arm64.sh` を取得して実行します。）

うまくいかないときに確認すること:

- `conda: command not found` → インストール後にターミナルを開き直していないことが多いです。
  新しいターミナルを開いてもう一度確認してください。

---

## 1. 展開する

```bash
cd ~/Downloads                # tar.gz を置いた場所へ
tar -xzf <配布物名>.tar.gz
cd <展開してできたフォルダ>      # 名前は cynovela- で始まります (ls で確認できます)
ls launch.sh                  # このファイルが見えれば展開できています
```

うまくいかないときに確認すること:

- `tar: Error opening archive` → ダウンロードが途中で切れています。もう一度受け取り直してください。
- `cd` で「No such file or directory」→ 展開先のフォルダ名が違います。
  `ls` で出てきたフォルダ名に読み替えてください。

---

## 2. 動作環境を作って起動する

はじめての方は、同梱のダミー資料が載った**デモ**で試すのがおすすめです。`--demo` を付けて起動してください（付けずに起動すると**本番**＝空のデータベースで始まります）。

```bash
./launch.sh --demo
```

このコマンド 1 本で、conda 環境の作成 → 必要な部品の導入 → 起動まで進みます。
画面には次の順で出ます。

```
[Step 1] conda を確認中...
✅ conda: /Users/xxx/miniforge3
[Step 2] conda環境 'cynovela' を確認中...
⚠️  環境 'cynovela' が見つかりません。作成します...
   （初回は5〜15分かかります）
[Step 3] 環境 'cynovela' をアクティベート中...
[Step 4] pip パッケージを確認中...
[Step 5] ポート8765の状態を確認中...
[Step 6] Cynovela を起動します...
Cynovela を起動します... (http://localhost:8765)
```

- 待ち受けポートは既定 **8765** です。変えたいときは `./launch.sh --demo --port 8900`。
- 2 回目以降は環境の作成が省かれ、1 分ほどで起動します。

うまくいかないときに確認すること:

- **「ポート8765はすでに使用中です」と聞かれる** → 前回の起動が残っています。
  `r`（既存を止めて起動し直す）を選ぶのが安全です。
- **Step 2 の環境作成でエラーになる** → 空き容量とインターネット接続を確認してください
  （初回だけ部品の取得に接続が必要です）。
- **止めたいとき** → 別のターミナルで `bash stop.sh` を実行します。

---

### 初回だけ：AIモデルのダウンロードを選ぶ画面が出ます

モデルを同梱しない形（軽量版や、このリポジトリをそのまま使う形）では、資料を読み取る
ための AI モデル（埋め込みモデル bge-m3）が初回はまだ入っていません。無いときだけ、
起動の途中で次の三択が出ます。

1. **いまダウンロードする** — インターネットから約 2.2〜2.3 GB を受け取ります（ダウンロード元: Hugging Face）。通信が要ります。
2. **すでに持っているフォルダを選ぶ** — 手元にあるモデルのフォルダをつなぎます。
3. **ダウンロードせずに、いちばん軽い設定で始める** — 通信なしで始めます。

どれかを選ぶまで、通信は始まりません。
（`Cynovela-start.command` のダブルクリックから始めた場合は、同じ内容が「ダウンロードする／キャンセル」の画面で出ます。）

## 3. ブラウザで開く

ブラウザで次を開きます（手順 2 でポートを変えた場合はその番号に読み替え）。

```
http://localhost:8765
```

ログイン画面（「ユーザー名／パスワードでログイン」）が出れば成功です。

うまくいかないときに確認すること:

- ページが出ない → 起動したターミナルにエラーが出ていないか見てください。
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

### 5-2. Cynovela 側の設定

左メニューの **Settings** → **LLM Provider** を開き、次のように設定します。

| 項目 | 入れる値 |
|---|---|
| Provider | `LM Studio` |
| Base URL | `http://localhost:1234` |
| Model | 「📋 モデル一覧を取得」を押し、**5-1 でロードしたチャット用モデル**を選ぶ |

「🔌 接続テスト」を押して成功を確認し、
「💾 LLM設定をまとめて適用」で保存します。

**Model を空欄のままにしないでください。**
空欄のときは LM Studio が返すモデル一覧の**先頭**が使われます。先頭が埋め込み専用モデルだと
生成要求が拒否され、回答が返らずエラー（HTTP 400）になります。
必ず一覧からチャット用モデルを選んでください。

うまくいかないときに確認すること:

- 接続テストが失敗する → LM Studio の Developer タブでサーバーが Start 状態か確認してください。
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

### 7-1. 取り込み元のフォルダを登録する

読み取れるのは、**登録してあるフォルダの範囲だけ**です。追加は画面からできます。

**画面から足す（おすすめ）**: 左メニュー **Settings** → **「📁 取り込み元」** → **「取り込み元を足す」**。
フォルダを辿って選びます。**足したものはすぐ使えます。起動し直しは要りません。**
外すのも同じ画面の **「外す」** でできます。

**ダブルクリックで足す**: 配布物の中の **`Cynovela-add-folder.command`** をダブルクリックします。
フォルダを選ぶ画面が出て、選ぶとバックアップに書かれ、いま動いている画面からすぐに選べます。

※ はじめて使うときは、先に `Cynovela-start.command` を一度押してください。バックアップを扱う
Python（3.12 系）はその最初の一度で用意されます。無いまま足そうとすると、入れ方の手順が
出て止まります（Mac に元から入っている古い python3 へは倒れません）。

ターミナルからは次のようにします。

```bash
# フォルダを選ぶ画面から追加する（macOS）
./launch.sh --add

# パスを直接指定して追加する
./launch.sh --add-path ~/Documents/契約

# 今どれが登録されているか見る／消す
./launch.sh --list
./launch.sh --remove <一覧に出た名前>
```

自分の資料は**本番**（引数なし）で使います。ここでは `--demo` は付けません。
起動時にまとめて渡すこともできます。

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

- **「取り込み元がまだ1件もありません」と出る** → 7-1 の登録をまだ行っていません。
  画面の「取り込み元を足す」から足してください。すぐに使えます。
- **参照画面でフォルダを選べない／403 になる** → 7-1 で登録した範囲の外を指しています。
  登録した範囲の中のフォルダを選んでください。
- **Publish が終わらない** → 大きな PDF が多いと時間がかかります。まず fast で試してください。

---

## 付録: よく使う操作

```bash
# 起動（2 回目以降）。引数なしは本番。デモで使っていた場合は --demo を付ける
./launch.sh

# 停止
bash stop.sh

# ログを流しながら起動したいとき（デモで使う場合は --demo も付ける）
python server.py --mode text 2>&1 | tee ~/cynovela.log
```

- 詳しい起動オプションや Ollama を使う場合は `STARTUP.md` を見てください。
- パスワードやトークンをメモ帳や共有フォルダに置かないでください。
  API を直接叩く場合のトークンは、ログイン（`POST /api/auth/login`）で毎回発行されるものを使います。
  固定のパスワードのようなトークンは受け付けません。
