# First run — from the downloaded file to your first answer / はじめての起動 — 落としたファイルから最初の答えまで

**日本語版はこちら → [日本語](#日本語)**

This page is for the **package edition** (`cynovela-chewie-package-1.1.1.tar.gz`).
It assumes you have never opened Terminal. Nothing is skipped.

---

## English

### Read this first: two things that will look wrong, and are not

1. **Most of these steps print nothing when they work.** A command that succeeds
   usually says nothing at all and just gives you a new line to type on. Silence
   is success here. Only failures talk.
2. **Some steps take minutes with no sign of life.** Joining the model files and
   the first start are the slow ones. Nothing is frozen. Leave it alone.

---

### Part 1 — the steps

Do these in order. Do not read ahead for reasons; the reasons are in Part 2.

#### Step 1. Download five files

On the releases page, download these into your **Downloads** folder:

```
cynovela-chewie-package-1.1.1.tar.gz
cynovela-chewie-models-1.1.1.tar.gz.part00
cynovela-chewie-models-1.1.1.tar.gz.part01
cynovela-chewie-models-1.1.1.tar.gz.part02
SHA256SUMS
```

Together they are about 5.4 GB. Wait until all five have finished.

#### Step 2. Open Terminal

Press **⌘ (command) + space**. A search box appears in the middle of the screen.
Type `terminal` and press **return**.

A window opens with white or black text and a blinking cursor. That is Terminal.
Everything below is typed into that window. After each line, press **return**.

#### Step 3. Go to the Downloads folder

Type this line and press return:

```
cd ~/Downloads
```

Nothing will be printed. That is correct.

#### Step 4. Join the three model parts into one file

Type this as **one line** and press return:

```
cat cynovela-chewie-models-1.1.1.tar.gz.part* > cynovela-chewie-models-1.1.1.tar.gz
```

This takes **one to three minutes** and prints nothing while it works. When the
cursor comes back, it is done.

#### Step 5. Check that the files arrived intact

```
shasum -a 256 --ignore-missing -c SHA256SUMS
```

This takes **one to three minutes**. It then prints one line per file. Every line
must end in `OK`:

```
cynovela-chewie-models-1.1.1.tar.gz: OK
cynovela-chewie-package-1.1.1.tar.gz: OK
```

If any line says `FAILED`, download that file again and repeat from step 4. Do
not go on.

#### Step 6. Unpack the program

```
tar -xzf cynovela-chewie-package-1.1.1.tar.gz
```

This takes **three to ten minutes** and prints nothing. A folder named `chewie`
appears in Downloads.

#### Step 7. Go into that folder

```
cd chewie
```

Nothing is printed.

#### Step 8. Unpack the AI models inside it

```
tar -xzf ../cynovela-chewie-models-1.1.1.tar.gz
```

This takes **two to five minutes** and prints nothing.

#### Step 9. Start it

```
./launch.sh --demo
```

`--demo` starts it with the sample documents that came in the package, so you
have something to ask about on the very first day. Without `--demo` it starts
empty and you must add a folder of your own first.

Now it talks to you. What you will see, in order — all of it in Japanese,
because the startup messages are only in Japanese:

```
先に、いま動いているものを調べました。
  動いているものは 0個 でした。
このまま進みます。

同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました。選択の画面は出さず、これを使って起動します。
記録はこのファイルへ書きます: /Users/…/Downloads/chewie/store/launch-app.log
起動しています (本体はこのターミナルから切り離して動かします)
```

The second line means "the bundled environment was found, so the screen that
asks how to build one is not shown". You are not being asked anything here.

**The first start takes three to eight minutes.** Nothing appears during that
time. When it is ready you will see:

```
立ち上がりました。
  開くところ : http://127.0.0.1:8765/
  記録       : /Users/…/Downloads/chewie/store/launch-app.log
止めるときは、次のように叩いてください。
  bash stop.sh
```

#### Step 10. Open it in your browser

Hold **⌘** and click `http://127.0.0.1:8765/`, or type that address into Safari
or Chrome yourself.

A sign-in screen appears.

#### Step 11. Sign in

* **User name:** `cynovela`
* **Password:** it is written in the file `cynovela.yaml` inside the folder you
  unpacked, on the line that begins `admin_initial_password:`. To see it, type
  this in Terminal:

  ```
  grep admin_initial_password cynovela.yaml
  ```

It will ask you to choose a new password straight away. Do that.

#### Step 12. Ask your first question

Because you started with `--demo`, the sample documents are already loaded and searchable. Type a question in plain language into
the box and press return, for example:

```
特別休暇は結婚のとき何日もらえますか
```

**The first answer takes one to four minutes** — the AI model has to be loaded
into memory first. Later answers are much faster.

Under every answer there is a list of the passages the answer came from. Open
one and check it against the answer. That is the point of this tool.

#### Step 13. Stop it when you are done

In Terminal:

```
bash stop.sh
```

It prints:

```
Cynovela を停止します (PID: 12345)...
停止完了
```

Your documents and settings stay where they are.

---

### Part 2 — why each of those steps is there

#### Why five files instead of one

GitHub refuses to host a single file larger than a few gigabytes, so the AI
models are cut into three pieces of 1.5 GB. Step 4 glues them back together.
`SHA256SUMS` is a list of fingerprints; step 5 recomputes the fingerprint of
what landed on your disk and compares it. A download that stopped halfway looks
like a normal file until you try to use it, which is why the check is worth the
three minutes.

#### Why `cd ~/Downloads`

Terminal always has one folder it is "standing in". `cd` moves it. `~` is
shorthand for your home folder — the one with your name on it in Finder. So
`~/Downloads` is the same Downloads folder Finder shows you. Every later command
acts on files in the folder Terminal is standing in, which is why step 7 moves
into `chewie` before unpacking the models: the models must land inside the
program's folder, not next to it.

#### Why nothing is printed

Unix commands were written to be chained together, so they stay quiet unless
something is wrong. `cd`, `cat` and `tar` all follow that habit. This is the
single most common reason people think the tool is broken when it is not.

#### Why the package edition needs no Python and no conda

The folder you unpacked already contains its own Python and every library it
needs, in a directory called `.condapack-cynovela`. It starts with a dot, so Finder
hides it — that is a macOS convention for "not for you to touch", not a sign
that something went wrong. (Press **⌘ + shift + .** in Finder to show hidden
items, and again to hide them.) Because everything lives inside the folder,
nothing is written anywhere else on your Mac, and deleting the folder removes
the tool completely.

That is also why step 9 prints *"同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました"*
and does **not** ask you to choose how to build an environment. The source
editions do ask, because they have no environment yet.

#### Why the first start is slow, and later ones are not

On the first start the tool reads the AI model off the disk, builds its search
index over the bundled demo documents, and prepares its database. From then on
all three already exist and are reused.

#### Why the first answer is slow

Answering needs a language model, which runs outside Cynovela (LM Studio, or any
OpenAI-compatible service). The first question makes that service load the model
into memory — several gigabytes — before a single word comes back. The tool
waits up to 120 seconds per request for that. If you get a message about a
timeout, load the model in LM Studio first and ask again.

#### Why the password is in a file

Each package is built with a different first password, written into
`cynovela.yaml` at packaging time. If it were the same for everyone, anyone who
had downloaded the tool would know yours. Changing it on first sign-in is
required for the same reason: administrator actions are refused until you do.

#### Why you should not put the folder in iCloud Drive, Dropbox or OneDrive

Those services copy every file to a server and can replace local files with
placeholders. Several gigabytes of libraries would be uploaded, and a
placeholder cannot be executed, so the tool stops working in ways that are hard
to diagnose. `./launch.sh` warns you if it detects one of those folders, but it
lets you go on. Put the folder somewhere plain instead — `~/Downloads` or
directly in your home folder is fine.

#### Why the terminal can be closed

`./launch.sh` detaches the program from the Terminal window before it finishes.
Closing the window does not stop it. That is why there is a separate
`bash stop.sh`.

---

## 日本語

このページは**パッケージ版**（`cynovela-chewie-package-1.1.1.tar.gz`）向けです。
ターミナルを一度も開いたことが無い方を想定して書いています。省略はしていません。

---

### 先に読んでください: 壊れて見えるが壊れていない2つのこと

1. **ここに出てくる命令は、うまくいったときほど何も出しません。** 成功すると、
   何も言わずに次の行を打てる状態に戻るだけです。ここでは沈黙が成功です。
   しゃべるのは失敗したときだけです。
2. **数分のあいだ、まったく反応が無い場面があります。** モデルのファイルをつなぐ
   ところと、最初の起動がそれです。固まっていません。触らずに待ってください。

---

### 前半 — 手順

上から順に行ってください。理由は後半にあります。先に読む必要はありません。

#### 手順1. ファイルを5つ落とす

リリースのページから、次の5つを**ダウンロード**フォルダへ落とします。

```
cynovela-chewie-package-1.1.1.tar.gz
cynovela-chewie-models-1.1.1.tar.gz.part00
cynovela-chewie-models-1.1.1.tar.gz.part01
cynovela-chewie-models-1.1.1.tar.gz.part02
SHA256SUMS
```

合わせて約 5.4 GB です。5つとも終わるまで待ってください。

#### 手順2. ターミナルを開く

**⌘（コマンド）キーと スペースキー**を同時に押します。画面の真ん中に検索の枠が
出ます。`terminal` と打ち、**return** を押します。

白か黒の文字とカーソルが点滅する窓が開きます。これがターミナルです。
以下はすべてこの窓に打ちます。1行打つごとに **return** を押します。

#### 手順3. ダウンロードのフォルダへ移る

次の1行を打って return を押します。

```
cd ~/Downloads
```

何も出ません。それで合っています。

#### 手順4. モデルの3つの片を1本につなぐ

次を**1行で**打って return を押します。

```
cat cynovela-chewie-models-1.1.1.tar.gz.part* > cynovela-chewie-models-1.1.1.tar.gz
```

**1〜3分**かかります。そのあいだ何も出ません。カーソルが戻ってきたら終わりです。

#### 手順5. ちゃんと落ちているかを確かめる

```
shasum -a 256 --ignore-missing -c SHA256SUMS
```

**1〜3分**かかります。そのあとファイルごとに1行ずつ出ます。全部の行が `OK` で
終わっていなければなりません。

```
cynovela-chewie-models-1.1.1.tar.gz: OK
cynovela-chewie-package-1.1.1.tar.gz: OK
```

`FAILED` と出た行があれば、そのファイルを落とし直して手順4からやり直します。
先へ進まないでください。

#### 手順6. 本体を取り出す

```
tar -xzf cynovela-chewie-package-1.1.1.tar.gz
```

**3〜10分**かかります。何も出ません。ダウンロードの中に `chewie` という名前の
フォルダができます。

#### 手順7. そのフォルダの中へ移る

```
cd chewie
```

何も出ません。

#### 手順8. その中で AIモデルを取り出す

```
tar -xzf ../cynovela-chewie-models-1.1.1.tar.gz
```

**2〜5分**かかります。何も出ません。

#### 手順9. 起こす

```
./launch.sh --demo
```

`--demo` を付けると、配布物に入っているお試しの資料が載った状態で立ち上がります。
初日から質問できる材料が入っている、ということです。付けないと中身が空の状態で
立ち上がるので、先に自分のフォルダを足す必要があります。

ここからは向こうがしゃべります。出てくる順に書きます。

```
先に、いま動いているものを調べました。
  動いているものは 0個 でした。
このまま進みます。

同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました。選択の画面は出さず、これを使って起動します。
記録はこのファイルへ書きます: /Users/…/Downloads/chewie/store/launch-app.log
起動しています (本体はこのターミナルから切り離して動かします)
```

2行目は「同梱の環境が見つかったので、環境の作り方を聞く画面は出しません」という
意味です。ここでは何も聞かれません。

**最初の起動は3〜8分かかります。** そのあいだ何も出ません。用意ができると
次が出ます。

```
立ち上がりました。
  開くところ : http://127.0.0.1:8765/
  記録       : /Users/…/Downloads/chewie/store/launch-app.log
止めるときは、次のように叩いてください。
  bash stop.sh
```

#### 手順10. ブラウザで開く

**⌘** を押しながら `http://127.0.0.1:8765/` をクリックします。または Safari や
Chrome のアドレス欄にそのまま打ち込みます。

ログインの画面が出ます。

#### 手順11. ログインする

* **利用者の名前:** `cynovela`
* **合言葉:** 取り出したフォルダの中の `cynovela.yaml` というファイルの、
  `admin_initial_password:` で始まる行に書いてあります。見るには、ターミナルで
  次を打ちます。

  ```
  grep admin_initial_password cynovela.yaml
  ```

入るとすぐに、新しい合言葉を決めるよう求められます。決めてください。

#### 手順12. 最初の質問をする

`--demo` で起こしたので、お試しの資料が最初から入っていて、探せる状態になっています。ふつうの言葉で枠に打ち込んで return を
押します。たとえば次のようにです。

```
特別休暇は結婚のとき何日もらえますか
```

**最初の答えは1〜4分かかります。** AIモデルをいったん記憶に読み込む必要が
あるためです。2回目からはずっと速くなります。

答えの下には、その答えの元になった文の断片が並びます。開いて、答えと突き合わせて
ください。この道具はそのために在ります。

#### 手順13. 終わったら止める

ターミナルで次を打ちます。

```
bash stop.sh
```

次が出ます。

```
Cynovela を停止します (PID: 12345)...
停止完了
```

読み込んだ資料と設定はそのまま残ります。

---

### 後半 — なぜその手順なのか

#### なぜ1本ではなく5つなのか

GitHub は数ギガバイトを超える1本のファイルを置かせてくれません。∴ AIモデルは
1.5 GB ずつ3つに切ってあります。手順4がそれを貼り合わせています。
`SHA256SUMS` は指紋の一覧です。手順5は、あなたのディスクに落ちたものの指紋を
その場で計算し直して突き合わせています。途中で止まったダウンロードは、使おうと
するまで普通のファイルに見えます。∴ この3分は払う価値があります。

#### なぜ `cd ~/Downloads` なのか

ターミナルには「いま立っているフォルダ」が1つあります。`cd` はそれを移す命令です。
`~` は自分のホームフォルダ（Finder で自分の名前が付いているところ）の略記です。
∴ `~/Downloads` は Finder で見えているダウンロードと同じ場所です。
以降の命令は、ターミナルが立っているフォルダのファイルに対して働きます。
手順7で `chewie` の中へ移ってからモデルを取り出しているのはそのためです。
モデルは本体のフォルダの**中**に置かれなければならず、隣ではいけません。

#### なぜ何も出ないのか

Unix の命令は互いにつなぎ合わせて使うために作られたので、異常が無いかぎり黙って
います。`cd` も `cat` も `tar` もその流儀です。壊れていないのに壊れたと思われる
いちばんの理由がこれです。

#### なぜパッケージ版は Python も conda も要らないのか

取り出したフォルダの中に、そのフォルダ専用の Python と、必要な部品一式が
`.condapack-cynovela` という入れ物で既に入っているからです。名前が点で始まるので
Finder は隠します。これは「触らなくてよいもの」という macOS の決まりであって、
何かがおかしい印ではありません。（Finder で **⌘ + shift + .** を押すと隠れている
ものが出ます。もう一度押すと戻ります。）
全部がフォルダの中で完結しているので、この Mac の他の場所には何も書きません。
フォルダごと消せば、それで完全に取り除いたことになります。

手順9で *「同梱の conda-pack 環境 (.condapack-cynovela) が見つかりました」* と出て、環境の作り方を
**聞かれない**のもこれが理由です。ソース版は環境をまだ持っていないので聞きます。

#### なぜ最初の起動だけ遅いのか

最初の起動では、AIモデルをディスクから読み、同梱のデモ資料に対する索引を作り、
データベースを用意します。2回目からは3つとも既に在るので、そのまま使われます。

#### なぜ最初の答えが遅いのか

答えを作るには言語モデルが要ります。これは Cynovela の外で動いています
（LM Studio や、OpenAI と同じ形の口を持つもの）。最初の質問で、その向こう側が
モデルを記憶へ読み込みます。数ギガバイトです。1語も返らないうちにその時間が
かかります。Cynovela は1回の呼び出しにつき 120秒 まで待ちます。時間切れの
知らせが出たときは、先に LM Studio でモデルを読み込んでから、もう一度
聞いてください。

#### なぜ合言葉がファイルに書いてあるのか

配布物は1本ごとに違う最初の合言葉を持って作られ、梱包のときに `cynovela.yaml`
へ書き込まれます。全員同じだったら、この道具を落とした人は誰でもあなたの
合言葉を知っていることになります。最初のログインで変えるよう求めるのも同じ
理由です。変えるまで、管理の操作は通しません。

#### なぜ iCloud Drive・Dropbox・OneDrive の中に置いてはいけないのか

これらは全てのファイルを向こうのサーバへ写し、手元のファイルを「印」だけに
置き換えることがあります。数ギガバイトの部品がまるごと送られますし、
「印」は実行できないので、原因の分かりにくい形で動かなくなります。
`./launch.sh` はそういう場所を見つけると知らせますが、止めはしません。
`~/Downloads` かホームフォルダの直下のような、素直な場所へ置いてください。

#### なぜターミナルを閉じてよいのか

`./launch.sh` は、終わる前に本体をターミナルの窓から切り離します。窓を閉じても
本体は止まりません。∴ 止めるための `bash stop.sh` が別に在ります。
