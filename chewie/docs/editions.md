# Which one do I download? / どれを落とせばよいか

**日本語版はこちら → [日本語](#日本語)**

---

## English

The releases page holds **four things**. Three of them are the tool; the fourth
is the AI models, which two of the three do not carry.

### The one-page answer

| | **Package edition** | **Source, all-in-one** | **Source, lightweight** | **AI models** |
|---|---|---|---|---|
| File | `cynovela-chewie-package-1.0.7.tar.gz` | `cynovela-chewie-all-in-one-1.0.7.tar.gz.part00`–`part02` | `cynovela-chewie-lightweight-1.0.7.tar.gz` | `cynovela-chewie-models-1.0.7.tar.gz.part00`–`part02` |
| How many files | 1 | 3 (join them) | 1 | 3 (join them) |
| Download size | about 830 MB | about 3.1 GB | about 2.4 MB | about 3.1 GB |
| Size once unpacked | about 3.1 GB | about 5.2 GB | about 8 MB | 4.84 GB |
| **Needs Python?** | **No** | Yes (3.12 or later), or conda | Yes (3.12 or later), or conda | — |
| **Needs conda?** | **No** | No (you may choose it) | No (you may choose it) | — |
| **AI models inside?** | **No — download them separately** | **Yes** | **No — download them separately** | this *is* them |
| Needs the network at setup | No | Yes | Yes | No |
| Runs on | Apple silicon Macs only | Apple silicon Macs | Apple silicon Macs | — |
| First start | run `./launch.sh` | `./launch.sh` builds an environment first | `./launch.sh` builds an environment first | — |

Always download **`SHA256SUMS`** as well, whichever you pick.

### Read the table this way

* **"Python and conda are not needed" is only true of the package edition.**
  It carries its own Python inside the folder, in `.venv-cynovela/`.
* **Only the all-in-one carries the AI models.** With the package edition and
  the lightweight edition you must download the `models` parts too and unpack
  them inside the folder. Without them, searching and ingesting fail.
* The lightweight edition is small **because** it has neither an environment nor
  the models. It builds the environment on your Mac at first start, which needs
  the network and takes a while.

### Pick like this

* **You just want it to work, and you have an Apple silicon Mac.**
  → Package edition **+** AI models. Two downloads, no build step.
* **You want one download that has everything, and you are happy to let it build
  an environment.**
  → Source edition, all-in-one. One set of parts, models included.
* **You already know Python or conda, and you want to see and control what is
  installed.**
  → Source edition, lightweight **+** AI models.

### What it is not

None of the four contains a language model for writing answers. Cynovela finds
the passages; the sentences are written by a language model that runs outside it
— LM Studio, or anything with an OpenAI-compatible endpoint. Set that up
separately (see `docs/llm-connection.md`).

The name "models" on the fourth item means the **embedding and reranking**
models — the ones that turn documents into something searchable. Despite the
file name, those parts are not conda packages.

---

## 日本語

リリースのページには**4つ**置いてあります。3つが道具そのもので、4つめは AIモデルです。
3つのうち2つは、そのモデルを持っていません。

### 1枚での答え

| | **パッケージ版** | **ソース版・全部入り** | **ソース版・軽量** | **AIモデル** |
|---|---|---|---|---|
| ファイル | `cynovela-chewie-package-1.0.7.tar.gz` | `cynovela-chewie-all-in-one-1.0.7.tar.gz.part00`〜`part02` | `cynovela-chewie-lightweight-1.0.7.tar.gz` | `cynovela-chewie-models-1.0.7.tar.gz.part00`〜`part02` |
| 本数 | 1本 | 3本（つなぐ） | 1本 | 3本（つなぐ） |
| 落とす大きさ | 約 830 MB | 約 3.1 GB | 約 2.4 MB | 約 3.1 GB |
| 展開後の大きさ | 約 3.1 GB | 約 5.2 GB | 約 8 MB | 4.84 GB |
| **Python が要るか** | **要りません** | 要ります（3.12 以上）。conda でも可 | 要ります（3.12 以上）。conda でも可 | — |
| **conda が要るか** | **要りません** | 要りません（選ぶことはできます） | 要りません（選ぶことはできます） | — |
| **AIモデルが入っているか** | **入っていません。別に落とします** | **入っています** | **入っていません。別に落とします** | これが本体 |
| 用意のときに通信が要るか | 要りません | 要ります | 要ります | 要りません |
| 動く機械 | Apple silicon の Mac だけ | Apple silicon の Mac | Apple silicon の Mac | — |
| 最初の起動 | `./launch.sh` を叩くだけ | `./launch.sh` が先に環境を作ります | `./launch.sh` が先に環境を作ります | — |

どれを選んでも、**`SHA256SUMS`** も一緒に落としてください。

### この表の読み方

* **「Python も conda も要らない」のはパッケージ版だけです。**
  フォルダの中の `.venv-cynovela/` に、自分用の Python を持っているからです。
* **AIモデルが入っているのは全部入りだけです。** パッケージ版と軽量版は、
  `models` の片も落として、フォルダの中で展開する必要があります。置かないまま
  起動すると、探すところ・取り込むところで失敗します。
* 軽量版が小さいのは、環境もモデルも持っていない**から**です。最初の起動のときに
  この Mac の上で環境を作ります。通信が要り、時間もかかります。

### 選び方

* **とにかく動けばよい。Apple silicon の Mac である。**
  → パッケージ版 **＋** AIモデル。落とすのは2つ、組み立ては要りません。
* **1回で全部落としたい。環境を作らせるのは構わない。**
  → ソース版・全部入り。片は1組で、モデルも入っています。
* **Python か conda を知っていて、何が入るかを自分で見て決めたい。**
  → ソース版・軽量 **＋** AIモデル。

### これは何ではないか

4つのどれにも、**答えの文章を書く**言語モデルは入っていません。Cynovela は
資料の中から根拠になる文を見つけるところまでを行い、文章そのものは外で動く
言語モデルが書きます。LM Studio でも、OpenAI と同じ形の口を持つものでも構いません。
そちらは別に用意してください（`docs/llm-connection.md` を参照）。

4つめの「models」は、**埋め込みと再並べ替え**のモデルのことです。資料を探せる形に
変えるためのものです。ファイル名は models ですが、conda のパッケージではありません。
