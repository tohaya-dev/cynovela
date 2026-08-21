# Stopping and starting again / 止め方と、起こし直し方

**日本語版はこちら → [日本語](#日本語)**

---

## English

### Part 1 — the steps

#### Stop it

Open Terminal, go into the folder you unpacked, and run one line:

```
cd ~/Downloads/chewie
bash stop.sh
```

It prints one of these:

```
Cynovela を停止します (PID: 12345)...
停止完了
```

```
PIDファイル(/Users/…/store/server.pid)がありません。停止対象なし。
```

The second one means it was not running. Nothing is wrong.

If you prefer clicking: double-click **`Cynovela-stop.command`** in the folder.

#### Start it again

```
cd ~/Downloads/chewie
./launch.sh --demo
```

Leave off `--demo` if you are using your own folders instead of the bundled
sample documents. **Use the same choice every time** — see Part 2.

Or double-click **`Cynovela-start.command`**.

Starting again takes **20 to 60 seconds**, not the three to eight minutes the
very first start took.

#### If something else is already running

`./launch.sh` looks first, and if it finds a running copy it shows you this:

```
先に、いま動いているものを調べました。
  server.py（PID 12345）  : 動いています（待ち受け 8765）
このまま新しく起こすと、同じものが二重に立ち上がります。
どうしますか。
  1) 動いているものを止めて、新しく起こす
  2) 止まっているものを、そのまま起こし直す
  3) 動いているものへ、そのままつなぐ
  4) 動いているものを止めて、終わる
  5) 何もせずに終わる
番号を入れてください [1/2/3/4/5]:
```

* Pick **3** if you just want the address of the copy that is already up.
* Pick **1** if you changed a setting and want a fresh start.
* Pick **4** to stop it and go away.

None of these delete anything.

#### After restarting your Mac

The tool does not start itself. Do the "start it again" steps above.

---

### Part 2 — what is going on

#### Why `--demo` has to be the same every time

`--demo` does not mean "with sample data on top of my data". It selects a
**different database and a different index**:

| Started with | Database it uses | Index it uses |
|---|---|---|
| `./launch.sh` | `store/db/cynovela.db` | `store/vector/default/chroma` |
| `./launch.sh --demo` | `store/db/demo.db` | `store/vector/demo/chroma` |

So a folder you added while running with `--demo` is not there when you start
without it, and the other way round. Nothing was lost — you are looking at the
other set. Start it again the way you started it before and your work is back.

The two never mix, which is the point: the sample documents cannot end up in
your real answers.

#### Why `stop.sh` is safe

It reads the process number out of `store/server.pid`, checks that the process
with that number really is `server.py`, and only then stops it. It never
searches for something listening on a port and never uses `pkill`, so it cannot
stop a different program that happens to be using port 8765.

If it says the PID file is missing, the tool had already stopped and cleaned up
after itself.

#### Why closing the Terminal window does not stop it

`./launch.sh` detaches the program from the window before it finishes. That is
deliberate: the tool is meant to keep running while you use the browser, and
people close Terminal windows. `bash stop.sh` is the way back.

#### What survives a stop

Everything: documents you ingested, the search index, users, settings, the
audit log. They all live in `store/` inside the folder. Stopping only ends the
process.

The only thing that goes away is anything that was still running when you
stopped it — a scan or a publish in progress. Start those again from the screen
or with `cynovela-cli scan start` / `cynovela-cli publish start`.

#### When the environment itself is broken

If it refuses to start and complains that something is missing:

```
./launch.sh --setup
```

That rebuilds the Python environment and does not start the tool. Then start
normally. Your documents and settings are untouched.

---

## 日本語

### 前半 — 手順

#### 止める

ターミナルを開き、取り出したフォルダへ移って、1行打ちます。

```
cd ~/Downloads/chewie
bash stop.sh
```

次のどちらかが出ます。

```
Cynovela を停止します (PID: 12345)...
停止完了
```

```
PIDファイル(/Users/…/store/server.pid)がありません。停止対象なし。
```

2つめは「そもそも動いていなかった」という意味です。異常ではありません。

クリックで済ませたい方は、フォルダの中の **`Cynovela-stop.command`** を
ダブルクリックしてください。

#### もう一度起こす

```
cd ~/Downloads/chewie
./launch.sh --demo
```

同梱のお試し資料ではなく自分のフォルダを使っているなら `--demo` は付けません。
**毎回同じ形で起こしてください。** 理由は後半にあります。

**`Cynovela-start.command`** のダブルクリックでも同じです。

起こし直しは **20〜60秒** です。いちばん最初の3〜8分はかかりません。

#### もう動いているものが在るとき

`./launch.sh` は先に調べます。動いているものが在れば、次を出します。

```
先に、いま動いているものを調べました。
  server.py（PID 12345）  : 動いています（待ち受け 8765）
このまま新しく起こすと、同じものが二重に立ち上がります。
どうしますか。
  1) 動いているものを止めて、新しく起こす
  2) 止まっているものを、そのまま起こし直す
  3) 動いているものへ、そのままつなぐ
  4) 動いているものを止めて、終わる
  5) 何もせずに終わる
番号を入れてください [1/2/3/4/5]:
```

* いま動いているものの開き先を知りたいだけなら **3** です。
* 設定を変えたので入れ直したいなら **1** です。
* 止めて終わりたいなら **4** です。

どれを選んでも、何も消えません。

#### Mac を再起動したあと

この道具は自分では起き上がりません。上の「もう一度起こす」を行ってください。

---

### 後半 — 何が起きているのか

#### なぜ `--demo` を毎回そろえる必要があるのか

`--demo` は「自分のデータの上にお試し資料を重ねる」という意味ではありません。
**別のデータベースと別の索引**を選ぶ指定です。

| 起こし方 | 使うデータベース | 使う索引 |
|---|---|---|
| `./launch.sh` | `store/db/cynovela.db` | `store/vector/default/chroma` |
| `./launch.sh --demo` | `store/db/demo.db` | `store/vector/demo/chroma` |

∴ `--demo` を付けて動かしているときに足したフォルダは、付けずに起こすと在りません。
逆も同じです。消えたのではなく、もう一方を見ています。前と同じ形で起こし直せば
戻ってきます。

2つは決して混ざりません。それがこの作りの狙いです。お試しの資料が、あなたの
本当の答えの中に紛れ込むことはありません。

#### なぜ `stop.sh` は安全なのか

`store/server.pid` から番号を読み、その番号のプロセスが本当に `server.py` かを
確かめてから止めます。待ち受けの番号から探すことも `pkill` を使うこともしません。
∴ たまたま 8765 を使っている別のプログラムを巻き込むことはありません。

「PIDファイルがありません」と出たときは、既に止まっていて、後片づけも済んでいた
ということです。

#### なぜターミナルの窓を閉じても止まらないのか

`./launch.sh` は、終わる前に本体を窓から切り離します。わざとそうしています。
ブラウザを使っているあいだ動き続けてほしいものであり、窓は閉じられるものだからです。
戻る道が `bash stop.sh` です。

#### 止めても残るもの

全部です。読み込んだ資料・索引・利用者・設定・監査の記録。どれもフォルダの中の
`store/` に在ります。止めるのはプロセスを終わらせるだけです。

消えるのは、止めた時点でまだ走っていたものだけです。走査や公開の途中がそれに
当たります。画面から、または `cynovela-cli scan start` / `cynovela-cli publish start`
で始め直してください。

#### 環境そのものが壊れたとき

足りないものが在ると言って起き上がらないときは、次を1回叩きます。

```
./launch.sh --setup
```

Python の環境を作り直すだけで、起動はしません。そのあと普通に起こしてください。
読み込んだ資料と設定には触りません。
