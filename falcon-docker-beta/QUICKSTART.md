# QUICKSTART — 5分でひととおり見る

**日本語版はこちら → [日本語](#日本語)**

## English

## 0. The easiest way to start — double-click a file

When you extract the package, it contains 3 files: **`Cynovela-start.command`**, **`Cynovela-stop.command`**,
and **`Cynovela-add-folder.command`**. These 3 are the only ones you touch.

- **Start**: Double-click `Cynovela-start.command`. A terminal opens, and the progress is printed as text
  through checking the conditions for running → assembling → starting.
  When it is done, a browser opens automatically.
- **Stop**: Double-click `Cynovela-stop.command`. A terminal opens, it stops, and the fact that it stopped
  is printed as text.
- **Add a folder to read**: Double-click `Cynovela-add-folder.command`. A folder chooser appears, and when
  you choose one it is written to the backup. The added folder becomes readable only after you start again
  with `Cynovela-start.command`.

> **The first time only, the way it opens may be different.**
> These files are not signed, so if you just open them macOS may block them.
> In that case, **right-click the file (or click while holding control) → "Open"**.
> From the second time on, an ordinary double-click is enough.

### What you need to prepare first — Podman

This form runs on top of a **container**.
For that reason, **Podman is required.** If it is not installed, install it first.

1. Get Podman Desktop from<https://podman.io/> and install it.
2. Open Podman Desktop and start it once by following the on-screen instructions
   (to use it from a terminal, run `podman machine init` and then `podman machine start`).
3. After that, double-click `Cynovela-start.command`.

When Podman is not found, or when it is installed but not yet running,
`Cynovela-start.command` prints the reason and what to do next on the spot and stops.

> **About container platforms other than Podman, such as Docker**
> There is an interface for specifying the executable to use yourself
> (`container.engine` and `container.engine_command` in "For those who want to change the settings" below).
> However, **we have confirmed it only with Podman. Operation with Docker or anything else has not been confirmed.**
> If you use one, you will need to adjust it yourself.

### For those who want to change the settings

All the settings are collected in `cynovela.yaml` in the same folder
(if you do not rewrite it, it runs with the defaults). The frequently used ones are as follows.

```
server:
  port: 8801        ポート番号。ブラウザで開く番号です
  host: 0.0.0.0     外部アクセス。同じネットワーク上の別の Macからも開けます
                    127.0.0.1 にすると、この Mac の中からだけ開けます
container:
  name: cynovela-all-in-one          コンテナの名前
  image: cynovela-all-in-one:latest  組み立てたものに付ける名札
  volume_prefix: cyn-falcon-a-20260809             データの保存領域の名前の頭
  engine: ''                     コンテナに使う実行ファイル（空なら自分で探します）
  engine_command: ''             起動に使うコマンドそのものの差し替え
```

If you want to start from a terminal, see "2. How to start" below. Either way, the same thing runs.

## 1. What this is

Cynovela is a tool for running a mechanism that "stores in-house documents and, when you ask a question,
answers with citations" on a single machine at hand in order to try it out. It is for verifying the behavior
and for demonstration, and is not meant to be used for business work as is.

## 2. How to start

To bring it up with the demo documents already loaded, start it **with --demo**.

> **For those who received the lightweight package**: before starting, place the embedding model into
> `store/models/` following the procedure in `SETUP-ACCELERATOR.md`. If you start without placing it,
> it stops before starting.
> Those who received the all-in-one package have it bundled already, so you can go straight on.

```bash
./launch.sh --demo
```

This form runs in a container. This is the only entry point for starting.

With no arguments it comes up in the empty state (for production).

## 3. Open it and log in

Open the following address in a browser.

- http://127.0.0.1:8801

The administrator user name is **cynovela** and the viewer user name is **demo**. The initial passwords are
written in the **"ログイン" (Login) section of the bundled `STARTUP.md`**. On the first login, the administrator
is asked to change the password, so please change it to a new one.

Note that by default it comes up in a state where it can also be opened from outside this machine (another Mac on
the same network). When you want to limit it to your own machine only, add `--local-only` at startup.

## 4. Four things to try

1. **Look at the list of documents** — Open "データカタログ (Data Catalog)" from the menu on the left. You can see
   the documents included for the demo (a company brochure, work rules, and so on of a fictional company) in a list.
2. **Try asking a question** — Open "RAG Chat" from the menu on the left and try asking
   "情報システム担当の受付時間と連絡先を教えてください" (tell me the reception hours and contact for the information
   systems staff). Wait a little for the answer to be complete (the first question can take a dozen or so seconds).
   Confirm that, together with the answer, which documents it was based on (the citations) is displayed.
3. **Log back in as a viewer** — Log out once, log back in as the viewer with the user name **demo**, and ask the
   same question. This time, confirm that the **phone number, email address, and inventory ledger server address**
   in the answer are masked like `[MASKED:PHONE]`. The mechanism that automatically hides information not shown
   to viewers is at work.
4. **See that the records remain** — Log back in as the administrator (cynovela) and open "監査ログ (Audit Log)"
   from the menu on the left. Confirm that the question you just asked and the login operations remain as records.

## 5. Two things for when it does not work

- **No answer comes back** — The part that writes the answer text is handled by separate software (an inference
  server, such as LM Studio). It needs to be running at http://localhost:1234. You can check the destination in
  "LM Studio 接続設定" (LM Studio connection settings) under "Settings" on the screen.
- **You want to put in your own documents** — The registration of ingest sources starts from 0 entries. For how to
  register a folder, see **7-1 of GETTING-STARTED.md**.

---

# 日本語

## 0. いちばん簡単な始め方 — ファイルをダブルクリック

配布物を展開すると、その中に **`Cynovela-start.command`**・**`Cynovela-stop.command`**・
**`Cynovela-add-folder.command`** という3つのファイルが入っています。触るのはこの3つだけです。

- **始める**: `Cynovela-start.command` をダブルクリックします。ターミナルが開き、
  動く条件の確認 → 組み立て → 起動、まで進み具合が文字で流れます。
  できあがるとブラウザが自動で開きます。
- **止める**: `Cynovela-stop.command` をダブルクリックします。ターミナルが開いて止まり、
  止まったことが文字で出ます。
- **読み込むフォルダを足す**: `Cynovela-add-folder.command` をダブルクリックします。フォルダを
  選ぶ画面が出て、選ぶとバックアップに書かれます。足したフォルダが読めるようになるのは、
  `Cynovela-start.command` で起動し直したあとです。

> **初回だけ、開き方が変わることがあります。**
> このファイルには署名を付けていないため、そのまま開くと macOS が止めることがあります。
> そのときは **ファイルを右クリック（または control を押しながらクリック）→「開く」** と進んでください。
> 2回目からは、ふつうにダブルクリックだけで開きます。

### 先に用意していただくもの — Podman

この形は **コンテナ** の上で動きます。
そのため、**Podman が必要です。** 入っていない場合は、先に入れてください。

1.<https://podman.io/> から Podman Desktop を受け取って入れます。
2. Podman Desktop を開き、画面の指示に従って一度起動します
   （ターミナルから使う場合は `podman machine init` のあと `podman machine start`）。
3. そのあとで `Cynovela-start.command` をダブルクリックします。

Podman が見つからないとき、または入っているのにまだ動いていないときは、
`Cynovela-start.command` がその場で理由と次にすることを画面に出して止まります。

> **Docker など、Podman 以外のコンテナ基盤について**
> 使う実行ファイルを自分で指定する口は用意してあります
> （下の「設定を変えたい方へ」の `container.engine` と `container.engine_command`）。
> ただし **当方では Podman でのみ確認しています。Docker その他での動作は確認していません。**
> 使う場合は、利用者ご自身で調整していただく必要があります。

### 設定を変えたい方へ

同じフォルダの `cynovela.yaml` に、設定はすべてまとまっています
（書き替えなければ既定のまま動きます）。よく使うものは次のとおりです。

```
server:
  port: 8801        ポート番号。ブラウザで開く番号です
  host: 0.0.0.0     外部アクセス。同じネットワーク上の別の Macからも開けます
                    127.0.0.1 にすると、この Mac の中からだけ開けます
container:
  name: cynovela-all-in-one          コンテナの名前
  image: cynovela-all-in-one:latest  組み立てたものに付ける名札
  volume_prefix: cyn-falcon-a-20260809             データの保存領域の名前の頭
  engine: ''                     コンテナに使う実行ファイル（空なら自分で探します）
  engine_command: ''             起動に使うコマンドそのものの差し替え
```

ターミナルから始めたい方は、この下の「2. 起動のしかた」をどうぞ。どちらでも同じものが動きます。

## 1. これは何か

Cynovela は「社内の資料をためて、質問すると出典つきで答えてくれる」仕組みを、手元の1台だけで動かして確かめるための道具です。動きの検証とデモのためのもので、そのまま業務に使うものではありません。

## 2. 起動のしかた

デモ用の資料が最初から載った状態で立ち上げるには、**--demo を付けて**起動します。

> **軽量版を受け取った方へ**: 起動の前に `SETUP-ACCELERATOR.md` の手順で埋め込みモデルを
> `store/models/` へ置いてください。置かずに起動すると、起動する前に止まります。
> 全部入りを受け取った方は同梱済みなので、そのまま進めます。

```bash
./launch.sh --demo
```

この形態はコンテナで動きます。起動の入口はこの1本だけです。

引数なしは空の状態(本番向け)で立ち上がります。

## 3. 開いてログインする

ブラウザで次のアドレスを開きます。

- http://127.0.0.1:8801

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
