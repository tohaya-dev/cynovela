# QUICKSTART — 5分でひととおり見る

**日本語版はこちら → [日本語](#日本語)**

## English

QUICKSTART — a walk through the whole thing in 5 minutes.

## 0. The easiest way to start — double-click a file

When you extract the package, it contains three files: **`Cynovela-start.command`**,
**`Cynovela-stop.command`** and **`Cynovela-add-folder.command`**. These three are the
only ones you touch.

- **Start**: double-click `Cynovela-start.command`. A terminal opens and the progress
  scrolls past as text: checking the conditions for running -> preparing -> starting.
  When it is ready, the browser opens automatically.
- **Stop**: double-click `Cynovela-stop.command`. A terminal opens, it stops, and the
  fact that it stopped is printed as text.
- **Add a folder to be read**: double-click `Cynovela-add-folder.command`. A folder
  chooser appears, and what you choose is written to the backup. A folder you added can
  be selected right away from the screen of the Cynovela that is currently running.
  Note: the first time you use it, press `Cynovela-start.command` once first. The Python
  (the 3.12 series) that handles the backup is prepared during that first run. If you
  try to add a folder without it, the installation procedure is printed and it stops
  (it does not fall back to the old python3 that came with the Mac).

> **The first time only, the way it opens may be different.**
> This file is not signed, so opening it directly may be blocked by macOS.
> In that case, **right-click the file (or control-click it) and choose "Open"**.
> From the second time on, a normal double-click is enough.

### About where python is prepared — conda is looked for first

This form is installed directly on this Mac and runs there. To run it, a place to put
python is required.

- **If conda is available, conda is used first.** A new environment dedicated to this
  package is created, and nothing is written to the shared environment.
- **Only when conda is absent**, a dedicated folder (`.venv-cynovela`) is created inside
  this package.
- The preparation is done with `./launch.sh --setup`. Which one it will be is shown on
  the screen. You are not asked.

If you want to decide in advance, write `conda` / `venv` / `none` in `base.prefer` of
`cynovela.yaml` (the default is `conda`).

### If you want to change the settings

All the settings are collected in `cynovela.yaml` in the same folder (if you do not
rewrite it, it runs with the defaults). The ones used most often are as follows.

```
server:
  port: 8765        ポート番号。ブラウザで開く番号です
  host: 0.0.0.0     外部アクセス。同じネットワーク上の別の Macからも開けます
                    127.0.0.1 にすると、この Mac の中からだけ開けます
base:
  prefer: conda     python を用意する場所。conda / venv / none
paths:
  data_dir: ./store データの保存先
```

In English: `server.port` is the port number, the number you open in the browser.
`server.host` is external access — with `0.0.0.0` it can also be opened from another Mac
on the same network; with `127.0.0.1` it can be opened only from inside this Mac.
`base.prefer` is where python is prepared: `conda` / `venv` / `none`.
`paths.data_dir` is where the data is stored.

If you would rather start from the terminal, see "2. How to start it" below. Either way
the same thing runs.

## 1. What this is

Cynovela is a tool for running, on a single machine at hand, a mechanism that
"accumulates in-house documents and answers your questions with citations", so that you
can see it for yourself. It exists for verifying the behaviour and for demonstrations,
and it is not something to use in business as it is.

## 2. How to start it

To bring it up with the demo documents already loaded, start it **with --demo
attached**.

```bash
./launch.sh --demo
```

With no arguments it comes up empty (for production use).

## 3. Open it and log in

Open the following address in your browser.

- http://127.0.0.1:8765

The administrator user name is **cynovela** and the viewer user name is **demo**. The
initial passwords are written in **the "ログイン" (Login) section of the bundled
`STARTUP.md`**. On the first login, the administrator is asked to change the password,
so please change it to a new one.

Note that by default it comes up in a state where it can also be opened from outside
this machine (from another Mac on the same network). If you want to restrict it to your
own machine only, add `--local-only` when starting it.

## 4. Four steps to try

1. **Look at the list of documents** — open "データカタログ (Data Catalog)" from the
   menu on the left. You can see a list of the documents included for the demo (a
   company profile, work rules and so on of a fictional company).
2. **Ask a question** — open "RAG Chat" from the menu on the left and try asking
   「情報システム担当の受付時間と連絡先を教えてください」 ("Please tell me the office
   hours and contact details of the information systems staff"). Wait a little until the
   answer is complete (the first question can take a dozen or so seconds). Check that,
   together with the answer, the documents it was based on (the citations) are shown.
3. **Sign in again as a viewer** — log out once, sign in again as the viewer with the
   user name **demo**, and ask the same question. This time, check that the **phone
   number, email address and the address of the inventory ledger server** in the answer
   have been replaced by masked text such as `[MASKED:PHONE]`. The mechanism that
   automatically hides information not to be shown to viewers is at work.
4. **See that a record is kept** — sign in again as the administrator (cynovela) and
   open "監査ログ (Audit Log)" from the menu on the left. Check that the questions you
   just asked and your login operations remain there as records.

## 5. Two things for when it does not work

- **No answer comes back** — the part that composes the text of the answer is handled by
  a separate piece of software (an external inference server, such as LM Studio). It
  needs to be running at http://localhost:1234. You can check the connection target
  under "LM Studio 接続設定" (LM Studio connection settings) in "Settings" on the screen.
- **You want to put your own documents in** — the registration of ingest sources starts
  from 0 entries. For how to register a folder, see **7-1 of GETTING-STARTED.md**.

---

# 日本語

## 0. いちばん簡単な始め方 — ファイルをダブルクリック

配布物を展開すると、その中に **`Cynovela-start.command`**・**`Cynovela-stop.command`**・
**`Cynovela-add-folder.command`** という3つのファイルが入っています。触るのはこの3つだけです。

- **始める**: `Cynovela-start.command` をダブルクリックします。ターミナルが開き、
  動く条件の確認 → 用意 → 起動、まで進み具合が文字で流れます。
  できあがるとブラウザが自動で開きます。
- **止める**: `Cynovela-stop.command` をダブルクリックします。ターミナルが開いて止まり、
  止まったことが文字で出ます。
- **読み込むフォルダを足す**: `Cynovela-add-folder.command` をダブルクリックします。フォルダを
  選ぶ画面が出て、選ぶとバックアップに書かれます。足したフォルダは、いま動いている Cynovela の
  画面からすぐに選べます。
  ※ はじめて使うときは、先に `Cynovela-start.command` を一度押してください。バックアップを扱う
  Python（3.12 系）はその最初の一度で用意されます。無いまま足そうとすると、入れ方の手順が
  出て止まります（Mac に元から入っている古い python3 へは倒れません）。

> **初回だけ、開き方が変わることがあります。**
> このファイルには署名を付けていないため、そのまま開くと macOS が止めることがあります。
> そのときは **ファイルを右クリック（または control を押しながらクリック）→「開く」** と進んでください。
> 2回目からは、ふつうにダブルクリックだけで開きます。

### python を用意する場所について — conda を先に見に行きます

この形は、この Mac に直接入れて動かします。動かすには python を置く場所が要ります。

- **conda が使えるなら、conda を先に使います。** この配布物専用の環境を新しく作り、
  共有の環境には書き込みません。
- **conda が無いときだけ**、この配布物の中に専用のフォルダ（`.venv-cynovela`）を作ります。
- 用意は `./launch.sh --setup` で行います。どちらになるかは画面に出ます。聞かれません。

先に決めておきたい方は、`cynovela.yaml` の `base.prefer` に `conda` / `venv` / `none` を書きます
（既定は `conda`）。

### 設定を変えたい方へ

同じフォルダの `cynovela.yaml` に、設定はすべてまとまっています
（書き替えなければ既定のまま動きます）。よく使うものは次のとおりです。

```
server:
  port: 8765        ポート番号。ブラウザで開く番号です
  host: 0.0.0.0     外部アクセス。同じネットワーク上の別の Macからも開けます
                    127.0.0.1 にすると、この Mac の中からだけ開けます
base:
  prefer: conda     python を用意する場所。conda / venv / none
paths:
  data_dir: ./store データの保存先
```

ターミナルから始めたい方は、この下の「2. 起動のしかた」をどうぞ。どちらでも同じものが動きます。

## 1. これは何か

Cynovela は「社内の資料をためて、質問すると出典つきで答えてくれる」仕組みを、手元の1台だけで動かして確かめるための道具です。動きの検証とデモのためのもので、そのまま業務に使うものではありません。

## 2. 起動のしかた

デモ用の資料が最初から載った状態で立ち上げるには、**--demo を付けて**起動します。

```bash
./launch.sh --demo
```

引数なしは空の状態(本番向け)で立ち上がります。

## 3. 開いてログインする

ブラウザで次のアドレスを開きます。

- http://127.0.0.1:8765

管理者のユーザー名は **cynovela**、閲覧者のユーザー名は **demo** です。最初のパスワードは、**同梱の `STARTUP.md` の「ログイン」の節**に書いてあります。初回ログイン時に、管理者はパスワードの変更を求められますので、新しいものに変えてください。

なお、既定ではこのマシンの外(同じネットワークの別の Mac)からも開ける状態で立ち上がります。自分のマシンだけに絞りたいときは、起動時に `--local-only` を足してください。

## 4. 試す4手

1. **資料の一覧を見る** — 左のメニューから「データカタログ (Data Catalog)」を開きます。デモ用に入っている資料(架空の会社の会社案内や就業規則など)が一覧で見えます。
2. **質問してみる** — 左のメニューから「RAG Chat」を開き、「情報システム担当の受付時間と連絡先を教えてください」と聞いてみます。答えが出そろうまで少し待ってください(初めての質問は十数秒かかることがあります)。答えといっしょに、どの資料をもとにしたか(出典)が表示されることを確かめます。
3. **閲覧者で入り直す** — いったんログアウトし、ユーザー名 **demo** の閲覧者で入り直して、同じ質問をします。今度は、答えの中の**電話番号・メールアドレス・在庫台帳サーバのアドレス**が `[MASKED:PHONE]` のような伏せ字になっていることを確かめます。閲覧者には見せない情報を自動で隠す仕組みが働いています。
4. **記録が残っていることを見る** — 管理者(cynovela)で入り直し、左のメニューから「監査ログ (Audit Log)」を開きます。いま自分がした質問やログインの操作が、記録として残っていることを確かめます。

## 5. うまく行かないときの2点

- **答えが返ってこない** — 答えの文章を作る部分は、別のソフト(推論サーバ。LM Studio など)が受け持ちます。それが http://localhost:1234 で動いている必要があります。接続先は画面の「Settings」にある「LM Studio 接続設定」で確かめられます。
- **自分の資料を入れたい** — 取り込み元の登録は0件から始まります。フォルダの登録のしかたは **GETTING-STARTED.md の 7-1** を見てください。
