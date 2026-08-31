# Which one do I download? / どれを落とせばよいか

**日本語版はこちら → [日本語](#日本語)**

---

## English

The releases page holds **two things**: the package edition, and the AI models
it needs. (The **app edition**, a `.pkg` installer, is **in preparation** and is
not part of this release. The **source edition** is not a download: the source
is this repository — clone it, or use GitHub's "Download ZIP".)

### The one-page answer

| | **App edition** | **Package edition** | **Source edition** | **AI models** |
|---|---|---|---|---|
| File | **In preparation** — not part of this release | `cynovela-chewie-package-1.1.3.tar.gz` | not a download — the source is this repository | `cynovela-chewie-models-1.1.3.tar.gz.part00`–`part02` |
| How many files | — | 1 | — | 3 (join them) |
| Download size | — | about 830 MB | — | about 3.1 GB |
| Size once installed / unpacked | — | about 3.1 GB | about 8 MB before the environment is built | 4.84 GB |
| **Needs Python?** | — | **No** | Yes (3.12 or later), or conda | — |
| **Needs conda?** | — | **No** | No (you may choose it) | — |
| **AI models inside?** | — | **No — download them separately** | **No — download them separately** | this *is* them |
| Needs the network at setup | — | No | Yes | No |
| Where it puts your data | — | inside its own folder | inside its own folder | — |
| Runs on | — | Apple silicon Macs only | Apple silicon Macs | — |
| First start | — | run `./launch.sh` | `./launch.sh` builds an environment first | — |
| Removing it | — | delete the folder | delete the folder | — |

Always download **`SHA256SUMS`** as well, whichever you pick.

### Read the table this way

* **"Python and conda are not needed" is true of the package edition.** It
  carries its own Python inside its folder, in `.condapack-cynovela/`.
* **Neither downloadable form carries the AI models.** Download the `models`
  parts too and unpack them inside the folder. Without them, searching and
  ingesting fail.
* **None of these installs anything on your Mac.** Both are folders you
  keep wherever you like — and can move somewhere else later.
* **The source edition is this repository's `chewie/` tree.** Take the source
  from the repository, add the models, and `./launch.sh` builds the environment
  on the first start.
* The source edition starts small **because** it has neither an environment nor
  the models. It builds the environment on your Mac at first start, which needs
  the network and takes a while.

### Pick like this

* **You want it to behave like any other Mac application.**
  → The app edition (`.pkg`) is being prepared for that; it is not part of this
  release. For now, take the package edition below.
* **You do not want to install anything on this Mac.**
  → Package edition **+** AI models. Two downloads, no build step, and it writes
  only inside its own folder.
* **You already know Python or conda, and you want to see and control what is
  installed.**
  → Source edition (this repository's source) **+** AI models.

### What it is not

None of these contains a language model for writing answers. Cynovela finds
the passages; the sentences are written by a language model that runs outside it
— LM Studio, or anything with an OpenAI-compatible endpoint. Set that up
separately (see `docs/operations.md`, "Connecting an LLM Provider").

The name "models" on the last item means the **embedding and reranking**
models — the ones that turn documents into something searchable. Despite the
file name, those parts are not conda packages.

---

## 日本語

リリースのページには**2つ**置いてあります。パッケージ版と、それに要る AIモデルです。
（**アプリ版**（`.pkg`）は**準備中**で、この版には入っていません。**ソース版**は
ダウンロードではありません。ソースはこのリポジトリです。clone するか、GitHub の
「Download ZIP」で取れます。）

### 1枚での答え

| | **アプリ版** | **パッケージ版** | **ソース版** | **AIモデル** |
|---|---|---|---|---|
| ファイル | **準備中です。** この版には入っていません | `cynovela-chewie-package-1.1.3.tar.gz` | ダウンロードではありません。ソースはこのリポジトリです | `cynovela-chewie-models-1.1.3.tar.gz.part00`〜`part02` |
| 本数 | — | 1本 | — | 3本（つなぐ） |
| 落とす大きさ | — | 約 830 MB | — | 約 3.1 GB |
| 入れた後・展開後の大きさ | — | 約 3.1 GB | 環境を作る前は約 8 MB | 4.84 GB |
| **Python が要るか** | — | **要りません** | 要ります（3.12 以上）。conda でも可 | — |
| **conda が要るか** | — | **要りません** | 要りません（選ぶことはできます） | — |
| **AIモデルが入っているか** | — | **入っていません。別に落とします** | **入っていません。別に落とします** | これが本体 |
| 用意のときに通信が要るか | — | 要りません | 要ります | 要りません |
| 資料と設定の置き場 | — | そのフォルダの中 | そのフォルダの中 | — |
| 動く機械 | — | Apple silicon の Mac だけ | Apple silicon の Mac | — |
| 最初の起動 | — | `./launch.sh` を叩くだけ | `./launch.sh` が先に環境を作ります | — |
| 消し方 | — | フォルダを消す | フォルダを消す | — |

どれを選んでも、**`SHA256SUMS`** も一緒に落としてください。

### この表の読み方

* **「Python も conda も要らない」のはパッケージ版です。**
  自分用の Python をフォルダの中の `.condapack-cynovela/` に持っています。
  `Package edition` に同梱されている環境は、`conda-pack` で固めた `conda` 環境です。
  `Python` の `venv` 機能とは別のものであり、`.condapack-cynovela` という名前で
  区別しています。
* **AIモデルはどちらの形にも入っていません。** `models` の分割ファイルもダウンロードして、
  フォルダの中で展開する必要があります。置かないまま
  起動すると、探すところ・取り込むところで失敗します。
* **どれも、この Mac には何も入れません。** どちらも、好きな場所に置くフォルダです。
  あとから別の場所へ移すこともできます。
* **ソース版は、このリポジトリの `chewie/` の木です。** リポジトリからソースを取り、
  モデルを重ねれば、`./launch.sh` が初回の起動で環境を作ります。
* ソース版が最初は小さいのは、環境もモデルも持っていない**から**です。最初の起動のときに
  この Mac の上で環境を作ります。通信が要り、時間もかかります。

### 選び方

* **ほかの Mac のアプリと同じ扱いにしたい。**
  → そのためのアプリ版（`.pkg`）を準備中です。この版には入っていません。
  いまは下のパッケージ版を選んでください。
* **この Mac には何も入れたくない。**
  → パッケージ版 **＋** AIモデル。落とすのは2つ、組み立ては要らず、書き込みは
  そのフォルダの中で完結します。
* **Python か conda を知っていて、何が入るかを自分で見て決めたい。**
  → ソース版（このリポジトリのソース） **＋** AIモデル。

### これは何ではないか

どれにも、**答えの文章を書く**言語モデルは入っていません。Cynovela は
資料の中から根拠になる文を見つけるところまでを行い、文章そのものは外で動く
言語モデルが書きます。LM Studio でも、OpenAI と同じ形の口を持つものでも構いません。
そちらは別に用意してください（`docs/operations.md` の「LLM プロバイダーを繋ぐ」を参照）。

最後の「models」は、**埋め込みと再並べ替え**のモデルのことです。資料を探せる形に
変えるためのものです。ファイル名は models ですが、conda のパッケージではありません。
