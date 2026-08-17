# はじめての方へ — 開いてから最初の質問が返るまで

**日本語版はこちら → [日本語](#日本語)**

## English

With this one page alone, you can get to the point where your first question is answered.
**The path that is done entirely on the screen is written first.** The path that uses the terminal is gathered at the back.

---

## 0. What to know first (this is where most people stumble)

- **When you first log in as the administrator, "please change your password" always appears.**
- **Until you finish changing it, all administrative operations (adding an ingest source, ingesting
  documents, changing settings) are refused.** Please change it first.
- The viewer (demo) is not asked to change it. However, a viewer cannot ingest.

This package runs inside a container. podman is required.

---

## 1. Start it

### There are 2 ways to start it, and 2 kinds of startup content as well

**Start it by pressing (the easiest)**

Double-click **`Cynovela-start.command`** in the folder you expanded.
To stop it, double-click **`Cynovela-stop.command`**.
To add a folder to read, double-click **`Cynovela-add-folder.command`**
(when you use it for the first time, please press `Cynovela-start.command` once first. The Python
that handles the folder backup is prepared inside the package by that first press).

**This operation procedure starts up with an empty database (production).** When you try it with the bundled dummy documents, type `./launch.sh --demo` from the terminal.
Right after it opens, you can ask questions about the bundled documents. Both the administrator and the viewer can log in as they are with the passwords in section 2 below.

When you want to use it with your own documents only, type it from the terminal **with no argument**. This one starts from **an empty database**
(production). There is no viewer in an empty production (you log in as the administrator, ingest documents, and then use it).

| Startup content | What happens | How to bring it up |
|---|---|---|
| Demo | It starts up with the bundled dummy documents **already ingested** (you can ask questions right away) | `./launch.sh --demo` from the terminal |
| Production | It starts up with an empty database. When there are 0 ingest sources, the dummy documents inside this package become the ingest source | Double-click `Cynovela-start.command`, or `./launch.sh` (no argument) |

**Start it from the terminal**

In the folder you expanded, run the following 1 line. **This is the only entry point when you use it from the terminal.**

```bash
./launch.sh --demo
```

This starts up with the bundled dummy documents already ingested.
When you use it with your own documents, run `./launch.sh` without adding anything.

If something needed to run it is missing, **before it starts** it says "足りないものがあるので起動しません" (something is missing, so it will not start).
In that case, please run the following.

```bash
./launch.sh --setup
```

You can bring up the list of what you can do at any time with this.

```bash
./launch.sh --help
```

---

### First time only: a screen for choosing to download the AI model appears

In the forms that do not bundle the models (the lightweight version, or the form that uses this repository
as it is), the AI model for reading the documents (the embedding model bge-m3) is not yet in place the first time.
Only when it is missing, the following 3 choices appear in the middle of the startup.

1. **Download it now** — it receives about 2.2 GB from the internet (download source: Hugging Face). Communication is required.
2. **Connect a folder you already have** — it connects a folder of models you have at hand.
3. **Quit** — place the model later, and start it again.

Communication does not begin until you choose one of them.
(When you started from a double-click of `Cynovela-start.command`, the same content appears in a "download / cancel" screen.)

## 2. Open it and log in

Open **http://localhost:8801** in a browser.

| | |
|---|---|
| Administrator user name | `cynovela` |
| Viewer user name | `demo` |

The first passwords are written **in the "Login" section of the bundled `STARTUP.md`**.

When you log in as the administrator, you are asked to change the password. **Please be sure to change it here.**
Until you finish changing it, all the operations after this are refused.

---

## 3. Add the folder to read (the ingest source)

What this application can read is **only the folders you have added as an ingest source**.
A place you have not added cannot be opened, even by an administrator.

When you have added nothing, **the dummy documents (`dummy-corpus`) inside this package are the ingest source from the beginning.**
If you only want to try it as it is, you may skip this section.

### In this form, you cannot add a folder by browsing from inside the screen

Because this package runs inside a container, you cannot browse the folders of your machine from the screen.
**The list and "外す" (remove) can be done on the screen (Settings → 📁 取り込み元).** When you press
"取り込み元を足す" (add an ingest source) on the screen, the 1 line to type in the terminal is shown in a copyable form.

Adding is done in either of the following ways.

- Double-click **`Cynovela-add-folder.command`** in the package
- Type it from the terminal:

```bash
./launch.sh --add
```

A screen for choosing a folder appears. When you choose one, it is kept in the backup.
**What you added becomes readable only after you start it up again.** Until then, the status column of the list
shows "起動し直すと読み込めます" (it can be loaded after a restart).

---

## 4. Ingest the documents

1. Open **Data Sources** on the left and press **"+ ソース追加"** (add a source) at the upper right
2. Enter a name, and choose a folder inside the ingest source from **"参照"** (browse)
3. Choose the destination (workspace) and confirm
4. In **Collections** on the left, create the unit to ingest and publish it

While it is ingesting, the progress appears on the screen. The stages advance in the following order.

```
読み込み中 → チャンク書き込み中 → マスキング処理中 → マスキング処理中(まとめ) → Embedding生成中 → 完了
```

**The ingest continues even if you close the screen.** When you open it again, it returns to the current stage and the item count.
With large documents the masking stage takes time, but if the count keeps moving, it is progressing.

---

## 5. Ask a question

Open **RAG Chat** on the left, choose a workspace, and type your question.
Below the answer, the documents that became the grounds (the citations) are listed.

---

## 6. Stop it and bring it up again

```bash
bash stop.sh
```

**It is fine to run `./launch.sh` again while it is still up.**
It stops what is already up and then brings it up again. When it could not be stopped,
it shows on the screen what is up and how to stop it by hand, and stops there.

---

## 7. The path done in the terminal (summary)

It is the same as what appears in `./launch.sh --help`.

| What you type | What happens |
|---|---|
| `./launch.sh` | Start in production (an empty database). If there are 0 ingest sources, use the bundled dummy documents |
| `./launch.sh --demo` | Start with the bundled dummy documents already ingested |
| `./launch.sh --setup` | Install what is required to run it (it stops after installing) |
| `./launch.sh --check` | Without starting, check only the conditions for running and write them to 1 file |
| `./launch.sh --add` | Bring up a screen for choosing a folder and add an ingest source |
| `./launch.sh --add-path <パス>` | Specify a location and add an ingest source |
| `./launch.sh --list` | List the ingest sources you have added |
| `./launch.sh --remove <名前>` | Remove an ingest source (the name is the one that appears in `--list`) |
| `./launch.sh --ingest <パス>` | Add it and start up as it is |
| `./launch.sh --port <番号>` | Change the number to open (default 8801) |
| `./launch.sh --local-only` | Narrow the place it opens to inside your own machine only |
| `./launch.sh --engine <値>` | Specify the executable to use for the container (a name or an absolute path). The setting with the same meaning: `engine:` under `container:` in `cynovela.yaml` |
| `./launch.sh --engine-command <値>` | Replace the command used for startup itself (the default is empty). The setting with the same meaning: `engine_command:` under `container:` in `cynovela.yaml` |
| `./launch.sh --sync-labels <トークン>` | Match the display names of the ingest sources to the running body |
| `./launch.sh <モード>` | `text` / `lite` / `lite-en` (default `text`) |
| `bash stop.sh` | Stop it |

When you type an option it does not know, it does not fall over silently; this list (the help) appears.

---

## 8. When it does not go well

| What appears on the screen | What to do |
|---|---|
| "取り込み元がまだ1件もありません" (there is not a single ingest source yet) | Double-click `Cynovela-add-folder.command`, or add it from the terminal (section 3): `./launch.sh --add`. **Because this form runs in a container, you cannot add a folder by browsing from inside the screen** (the list and "外す" (remove) can be done on the screen at Settings → 📁 取り込み元) |
| "初回パスワードの変更が必要です" (the first password must be changed) | Section 0. Change the password first |
| "ポート 8801 を別のものが使っています" (something else is using port 8801) | Bring it up on another number: `./launch.sh --port <別の番号>` |
| "足りないものがあるので起動しません" (something is missing, so it will not start) | Run `./launch.sh --setup` |
| The progress looks stopped | If the count is moving, it is progressing. The masking stage takes time |

---

This guide is `HAJIMETE.md` inside the package.
More detailed stories are in the bundled `README.md` and `STARTUP.md`.

---

# 日本語

この1枚だけで、最初の質問が返るところまで行けます。
**画面だけで済む道を先に書いています。** ターミナルを使う道は後ろにまとめました。

---

## 0. 先に知っておくこと（ここでつまずく人が一番多いところ）

- **管理者で最初に入ると、必ず「パスワードを変えてください」と出ます。**
- **変え終わるまで、管理の操作（取り込み元を足す・資料を取り込む・設定を変える）は
  すべて断られます。** 先に変えてください。
- 閲覧者（demo）は変更を求められません。ただし閲覧者は取り込みができません。

この配布物は、コンテナの中で動きます。podman が要ります。

---

## 1. 起動する

### 起動の仕方は 2 通り、起動の中身も 2 通りあります

**押して起動する（いちばん簡単）**

展開したフォルダの中の **`Cynovela-start.command`** をダブルクリックします。
止めるときは **`Cynovela-stop.command`** をダブルクリックします。
読み込むフォルダを足すときは **`Cynovela-add-folder.command`** をダブルクリックします
（はじめて使うときは、先に `Cynovela-start.command` を一度押してください。フォルダの
バックアップを扱う Python はその最初の一度で配布物の中に用意されます）。

**この操作手順は、中身が空のデータベース（本番）で立ち上がります。** 同梱のダミー資料で試すときは、ターミナルから `./launch.sh --demo` を叩きます。
開いてすぐ、同梱の資料に質問できます。管理者・閲覧者とも、下の 2 節のパスワードでそのまま入れます。

自分の資料だけで使いたいときは、ターミナルから**引数なし**で叩きます。こちらは**中身が空のデータベース**
（本番）から始まります。空の本番に閲覧者は居ません（管理者で入って資料を取り込んでから使います）。

| 起動の中身 | どうなるか | 出し方 |
|---|---|---|
| デモ | 同梱のダミー資料が**取り込み済み**の状態で立ち上がる（すぐ質問できる） | ターミナルから `./launch.sh --demo` |
| 本番 | 中身が空のデータベースで立ち上がる。取り込み元が 0 件のときは、この配布物の中のダミー資料が取り込み元になる | `Cynovela-start.command` をダブルクリック、または `./launch.sh`（引数なし） |

**ターミナルから起動する**

展開したフォルダの中で、次の1行を実行します。**ターミナルから使うときの入口はこの1本だけです。**

```bash
./launch.sh --demo
```

これは、同梱のダミー資料が取り込み済みの状態で立ち上がります。
自分の資料で使うときは、何も付けずに `./launch.sh` を実行します。

動かすのに足りないものがあると、**起動する前に**「足りないものがあるので起動しません」と出ます。
そのときは次を実行してください。

```bash
./launch.sh --setup
```

できることの一覧は、いつでもこれで出せます。

```bash
./launch.sh --help
```

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

## 2. 開いて入る

ブラウザで **http://localhost:8801** を開きます。

| | |
|---|---|
| 管理者の利用者名 | `cynovela` |
| 閲覧者の利用者名 | `demo` |

最初のパスワードは、**同梱の `STARTUP.md` の「ログイン」の節**に書いてあります。

管理者で入るとパスワードの変更を求められます。**ここで必ず変えてください。**
変え終わるまで、この先の操作はすべて断られます。

---

## 3. 読ませるフォルダ（取り込み元）を足す

このアプリが読めるのは、**取り込み元として足したフォルダだけ**です。
足していない場所は、たとえ管理者でも開けません。

何も足していないときは、**この配布物の中のダミー資料（`dummy-corpus`）が最初から取り込み元になっています。**
そのまま試すだけなら、この節は飛ばして構いません。

### この形では、画面の中からフォルダを辿って足すことはできません

この配布物はコンテナの中で動くため、画面からお使いの機械のフォルダを辿れません。
**一覧と「外す」は画面（Settings → 📁 取り込み元）でできます。** 画面の「取り込み元を足す」を
押すと、ターミナルで叩く1行がコピーできる形で表示されます。

足すのは次のどちらかで行います。

- 配布物の中の **`Cynovela-add-folder.command`** をダブルクリックする
- ターミナルから叩く:

```bash
./launch.sh --add
```

フォルダを選ぶ画面が出ます。選ぶとバックアップに残ります。
**足したものが読めるようになるのは、もう一度起動し直したあとです。** それまで一覧の状態の欄には
「起動し直すと読み込めます」と出ます。

---

## 4. 資料を取り込む

1. 左の **Data Sources** を開き、右上の **「+ ソース追加」** を押す
2. 名前を入れ、**「参照」** から取り込み元の中のフォルダを選ぶ
3. 追加先（ワークスペース）を選んで確定する
4. 左の **Collections** で、取り込むまとまりを作って公開する

取り込みの間は、進み具合が画面に出ます。段は次の順に進みます。

```
読み込み中 → チャンク書き込み中 → マスキング処理中 → マスキング処理中(まとめ) → Embedding生成中 → 完了
```

**画面を閉じても取り込みは続きます。** 開き直すと、いまの段と何件目かに戻ります。
大きな資料ではマスキングの段に時間がかかりますが、件数が動き続けていれば進んでいます。

---

## 5. 質問する

左の **RAG Chat** を開き、ワークスペースを選んで質問を打ちます。
答えの下に、根拠になった資料（出典）が並びます。

---

## 6. 止める・掛け直す

```bash
bash stop.sh
```

**上がったまま、もう一度 `./launch.sh` を実行しても構いません。**
先に上がっているものを止めてから上げ直します。止められなかったときは、
何が上がっているかと手で止める方法を画面に出して、そこで止まります。

---

## 7. ターミナルで行う道（まとめ）

`./launch.sh --help` に出るものと同じです。

| 打つもの | 何が起きるか |
|---|---|
| `./launch.sh` | 本番（空のデータベース）で起動。取り込み元が0件なら同梱のダミー資料を使う |
| `./launch.sh --demo` | 同梱のダミー資料が取り込み済みの状態で起動 |
| `./launch.sh --setup` | 動かすのに要るものを入れる（入れたら止まる） |
| `./launch.sh --check` | 起動せず、動く条件だけを調べて1本のファイルへ書く |
| `./launch.sh --add` | フォルダを選ぶ画面を出して取り込み元を足す |
| `./launch.sh --add-path <パス>` | 場所を指定して取り込み元を足す |
| `./launch.sh --list` | 足してある取り込み元を一覧で出す |
| `./launch.sh --remove <名前>` | 取り込み元を外す（名前は `--list` に出るもの） |
| `./launch.sh --ingest <パス>` | 足して、そのまま起動する |
| `./launch.sh --port <番号>` | 開く番号を変える（既定 8801） |
| `./launch.sh --local-only` | 開く先を自分のマシンの中だけに絞ります |
| `./launch.sh --engine <値>` | コンテナに使う実行ファイルを指定する（名前または絶対パス）。同じ意味の設定: `cynovela.yaml` の `container:` の `engine:` |
| `./launch.sh --engine-command <値>` | 起動に使うコマンドそのものを差し替える（既定は空）。同じ意味の設定: `cynovela.yaml` の `container:` の `engine_command:` |
| `./launch.sh --sync-labels <トークン>` | 取り込み元の表示名を動いている本体へ合わせる |
| `./launch.sh <モード>` | `text` / `lite` / `lite-en`（既定 `text`） |
| `bash stop.sh` | 止める |

知らない指定を打ったときは、黙って落ちずにこの一覧（ヘルプ）が出ます。

---

## 8. うまくいかないとき

| 画面に出ること | どうするか |
|---|---|
| 「取り込み元がまだ1件もありません」 | `Cynovela-add-folder.command` のダブルクリック、またはターミナルから足します（3節）: `./launch.sh --add`。**この形はコンテナで動くため、画面の中からフォルダを辿って足すことはできません**（一覧と「外す」は画面の Settings → 📁 取り込み元 でできます） |
| 「初回パスワードの変更が必要です」 | 0節。先にパスワードを変える |
| 「ポート 8801 を別のものが使っています」 | 別の番号で上げる: `./launch.sh --port <別の番号>` |
| 「足りないものがあるので起動しません」 | `./launch.sh --setup` を実行する |
| 進み具合が止まって見える | 件数が動いていれば進んでいます。マスキングの段は時間がかかります |

---

この手引きは配布物の中の `HAJIMETE.md` です。
より詳しい話は同梱の `README.md` と `STARTUP.md` にあります。
