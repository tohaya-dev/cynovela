# Which one do I download? / どれを落とせばよいか

**日本語版はこちら → [日本語](#日本語)**

---

## English

The releases page holds **five things**. Four of them are the tool; the fifth
is the AI models, which two of the four do not carry.

The first two — the app edition and the package edition — hold exactly the same
program. They differ in where it lives and where it writes.

### The one-page answer

| | **App edition** | **Package edition** | **Source, all-in-one** | **Source, lightweight** | **AI models** |
|---|---|---|---|---|---|
| File | `Cynovela-1.1.2-macos-arm64.pkg.part00`–`part02` | `cynovela-chewie-package-1.1.2.tar.gz` | `cynovela-chewie-all-in-one-1.1.1.tar.gz.part00`–`part02` | `cynovela-chewie-lightweight-1.1.1.tar.gz` | `cynovela-chewie-models-1.1.2.tar.gz.part00`–`part02` |
| How many files | 3 + `Cynovela-assemble.command` (it joins them) | 1 | 3 (join them) | 1 | 3 (join them) |
| Download size | 3.88 GB | about 830 MB | about 3.1 GB | about 2.4 MB | about 3.1 GB |
| Size once installed / unpacked | 7.1 GB in `/Applications` | about 3.1 GB | about 5.2 GB | about 8 MB | 4.84 GB |
| **Needs Python?** | **No** | **No** | Yes (3.12 or later), or conda | Yes (3.12 or later), or conda | — |
| **Needs conda?** | **No** | **No** | No (you may choose it) | No (you may choose it) | — |
| **AI models inside?** | **Yes** | **No — download them separately** | **Yes** | **No — download them separately** | this *is* them |
| Needs the network at setup | No | No | Yes | Yes | No |
| Where it puts your data | `~/Library/Application Support/Cynovela/` | inside its own folder | inside its own folder | inside its own folder | — |
| Runs on | Apple silicon, macOS 12 or later | Apple silicon Macs only | Apple silicon Macs | Apple silicon Macs | — |
| First start | open `Cynovela.app` | run `./launch.sh` | `./launch.sh` builds an environment first | `./launch.sh` builds an environment first | — |
| Removing it | drag to the Trash (takes the environment and the models with it) | delete the folder | delete the folder | delete the folder | — |

Always download **`SHA256SUMS`** as well, whichever you pick.

### Read the table this way

* **"Python and conda are not needed" is true of the app edition and the package
  edition.** Each carries its own Python: the app edition inside the bundle, the
  package edition inside its folder, in `.condapack-cynovela/`.
* **The app edition and the all-in-one carry the AI models.** With the package
  edition and the lightweight edition you must download the `models` parts too and
  unpack them inside the folder. Without them, searching and ingesting fail.
* **Only the app edition installs anything on your Mac.** It writes
  `Cynovela.app` into `/Applications`, which is why it asks for an administrator
  password. The other three are folders you keep wherever you like.
* **The app edition's installer is not signed with an Apple certificate.** The
  first double-click is refused; right-click the `.pkg` → Open → Open. The
  reasoning is in `MACOS-DISTRIBUTION-STRATEGY.md` §15.7.
* **The two source editions were not rebuilt for 1.1.2.** Take them from the
  1.1.1 release.
* The lightweight edition is small **because** it has neither an environment nor
  the models. It builds the environment on your Mac at first start, which needs
  the network and takes a while.

### Pick like this

* **You want it to behave like any other Mac application.**
  → App edition. One install, models included; drag it to the Trash to remove the
  program, its Python environment and the models together. Needs an administrator
  password once, at install time.
* **You do not want to install anything on this Mac.**
  → Package edition **+** AI models. Two downloads, no build step, and it writes
  only inside its own folder.
* **You want one download that has everything, and you are happy to let it build
  an environment.**
  → Source edition, all-in-one. One set of parts, models included.
* **You already know Python or conda, and you want to see and control what is
  installed.**
  → Source edition, lightweight **+** AI models.

### What it is not

None of the five contains a language model for writing answers. Cynovela finds
the passages; the sentences are written by a language model that runs outside it
— LM Studio, or anything with an OpenAI-compatible endpoint. Set that up
separately (see `docs/operations.md`, "Connecting an LLM Provider").

The name "models" on the last item means the **embedding and reranking**
models — the ones that turn documents into something searchable. Despite the
file name, those parts are not conda packages.

---

## 日本語

リリースのページには**5つ**置いてあります。4つが道具そのもので、5つめは AIモデルです。
4つのうち2つは、そのモデルを持っていません。

はじめの2つ ― アプリ版とパッケージ版 ― は、中身のプログラムがまったく同じものです。
違うのは「どこに居るか」と「どこへ書くか」の2点だけです。

### 1枚での答え

| | **アプリ版** | **パッケージ版** | **ソース版・全部入り** | **ソース版・軽量** | **AIモデル** |
|---|---|---|---|---|---|
| ファイル | `Cynovela-1.1.2-macos-arm64.pkg.part00`〜`part02` | `cynovela-chewie-package-1.1.2.tar.gz` | `cynovela-chewie-all-in-one-1.1.1.tar.gz.part00`〜`part02` | `cynovela-chewie-lightweight-1.1.1.tar.gz` | `cynovela-chewie-models-1.1.2.tar.gz.part00`〜`part02` |
| 本数 | 3本 ＋ `Cynovela-assemble.command`（これがつなぎます） | 1本 | 3本（つなぐ） | 1本 | 3本（つなぐ） |
| 落とす大きさ | 3.88 GB | 約 830 MB | 約 3.1 GB | 約 2.4 MB | 約 3.1 GB |
| 入れた後・展開後の大きさ | `/Applications` に 7.1 GB | 約 3.1 GB | 約 5.2 GB | 約 8 MB | 4.84 GB |
| **Python が要るか** | **要りません** | **要りません** | 要ります（3.12 以上）。conda でも可 | 要ります（3.12 以上）。conda でも可 | — |
| **conda が要るか** | **要りません** | **要りません** | 要りません（選ぶことはできます） | 要りません（選ぶことはできます） | — |
| **AIモデルが入っているか** | **入っています** | **入っていません。別に落とします** | **入っています** | **入っていません。別に落とします** | これが本体 |
| 用意のときに通信が要るか | 要りません | 要りません | 要ります | 要ります | 要りません |
| 資料と設定の置き場 | `~/Library/Application Support/Cynovela/` | そのフォルダの中 | そのフォルダの中 | そのフォルダの中 | — |
| 動く機械 | Apple silicon・macOS 12 以降 | Apple silicon の Mac だけ | Apple silicon の Mac | Apple silicon の Mac | — |
| 最初の起動 | `Cynovela.app` を開く | `./launch.sh` を叩くだけ | `./launch.sh` が先に環境を作ります | `./launch.sh` が先に環境を作ります | — |
| 消し方 | ゴミ箱へ入れる（環境もモデルも一緒に消えます） | フォルダを消す | フォルダを消す | フォルダを消す | — |

どれを選んでも、**`SHA256SUMS`** も一緒に落としてください。

### この表の読み方

* **「Python も conda も要らない」のはアプリ版とパッケージ版です。**
  どちらも自分用の Python を持っています。アプリ版はアプリの中に、パッケージ版は
  フォルダの中の `.condapack-cynovela/` にあります。
  `Package edition` に同梱されている環境は、`conda-pack` で固めた `conda` 環境です。
  `Python` の `venv` 機能とは別のものであり、`.condapack-cynovela` という名前で
  区別しています。
* **AIモデルが入っているのはアプリ版と全部入りです。** パッケージ版と軽量版は、
  `models` の片も落として、フォルダの中で展開する必要があります。置かないまま
  起動すると、探すところ・取り込むところで失敗します。
* **この Mac に何かを入れるのはアプリ版だけです。** `/Applications` へ
  `Cynovela.app` を書き込むため、入れるときに管理者のパスワードを聞きます。
  ほかの3つは、好きな場所に置くフォルダです。
* **アプリ版の入れ物には Apple の証明書による署名を付けていません。** 最初の
  ダブルクリックは断られます。`.pkg` を右クリック →「開く」→「開く」で入れられます。
  考え方は `MACOS-DISTRIBUTION-STRATEGY.md` の 15.7 に書いてあります。
* **ソース版の2つは 1.1.2 では作り直していません。** 1.1.1 のリリースから取ってください。
* 軽量版が小さいのは、環境もモデルも持っていない**から**です。最初の起動のときに
  この Mac の上で環境を作ります。通信が要り、時間もかかります。

### 選び方

* **ほかの Mac のアプリと同じ扱いにしたい。**
  → アプリ版。1回入れれば中に全部入っており、ゴミ箱へ入れればプログラムと
  Python の環境と AIモデルがまとめて消えます。入れるときに一度だけ管理者の
  パスワードが要ります。
* **この Mac には何も入れたくない。**
  → パッケージ版 **＋** AIモデル。落とすのは2つ、組み立ては要らず、書き込みは
  そのフォルダの中で完結します。
* **1回で全部落としたい。環境を作らせるのは構わない。**
  → ソース版・全部入り。片は1組で、モデルも入っています。
* **Python か conda を知っていて、何が入るかを自分で見て決めたい。**
  → ソース版・軽量 **＋** AIモデル。

### これは何ではないか

5つのどれにも、**答えの文章を書く**言語モデルは入っていません。Cynovela は
資料の中から根拠になる文を見つけるところまでを行い、文章そのものは外で動く
言語モデルが書きます。LM Studio でも、OpenAI と同じ形の口を持つものでも構いません。
そちらは別に用意してください（`docs/operations.md` の「LLM プロバイダーを繋ぐ」を参照）。

最後の「models」は、**埋め込みと再並べ替え**のモデルのことです。資料を探せる形に
変えるためのものです。ファイル名は models ですが、conda のパッケージではありません。
