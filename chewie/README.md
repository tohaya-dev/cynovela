# Cynovela

**日本語版はこちら → [日本語](#日本語)**

**The only entry document is [START-HERE.md](START-HERE.md). Open it first — setup, restart, reinstall and uninstall are all there.**
**最初に開くのは [START-HERE.md](START-HERE.md) だけです（唯一の入口。セットアップ・再起動・再インストール・アンインストールはすべてそこにあります）。**

**Every document bundled here is listed in [docs/INDEX.md](docs/INDEX.md), sorted by reader — using it / installing and running it / looking things up.**
**同梱の文書の全数は [docs/INDEX.md](docs/INDEX.md) に、読み手ごと（使う人 / 入れる人・回す人 / 引く人）に並べてあります。**

## English

<!-- cynovela:welcome-en:start -->
**Cynovela lets you point an AI at the documents already on your Mac and ask about them, in Japanese or English. But answering is not the point.**

**When documents are handed to an AI, what happens in between is normally invisible.** Cynovela makes it visible. Reading, masking and vectorising each show up as they progress, with counts of what was masked and of what kind. Answers cite the passage they came from, and if no supporting passage is found, none is invented. Who looked at what, and when, is recorded.

**Seeing that end to end, on your own machine, is what this tool is for.**

**How your documents are handled**

**Reading, search and answering all happen on your own Mac. Nothing is sent to the internet** — with one exception.
**Exception: API connection.** If you enable a connection to a cloud AI service, your question and the relevant excerpts are sent to that service. It is off by default.
**What is sent is text that has been through the masking step**, and the tool is built so that text which has not been through it is never routed outside. There is no exception by role — the same applies to administrator accounts.
**The masking step is not exhaustive.** Some names and address details are known to slip through. Do not load confidential material on the assumption that it will be protected.

**Before you start**

Requires an Apple silicon Mac. This is a learning and demonstration tool, not a production system. Provided as is, without warranty. Answers can be wrong; always open the cited source and check.
<!-- cynovela:welcome-en:end -->

See [docs/NOTICE.md](docs/NOTICE.md) ("Before You Start") before you rely on it.

**Which package to download**

Everything is on GitHub Releases (v1.1.3): https://github.com/tohaya-dev/cynovela/releases

1. **Package edition** — `cynovela-chewie-package-1.1.3.tar.gz` (1 file, about 800 MB). For Apple silicon Macs. No Python and no conda are needed; extract it and run `./launch.sh`. The AI models are separate: also download the `models` files below and lay them on top.
2. **Source edition** — not a download: the source is this repository. Clone it, or use GitHub's "Download ZIP", take the `chewie/` tree, lay the `models` files below on top, and run `./launch.sh`; the first start builds the environment.

- **AI models only** — `cynovela-chewie-models-1.1.3.tar.gz.part00`–`part02` (3 split files). Despite the name, these split files are not conda packages — they are the AI models themselves. (Byte-identical to the 1.0.7 models — the model weights did not change.)

**Joining, verifying, extracting.** Join the split files in part order into one file: `cat cynovela-chewie-models-1.1.3.tar.gz.part00 cynovela-chewie-models-1.1.3.tar.gz.part01 cynovela-chewie-models-1.1.3.tar.gz.part02 > cynovela-chewie-models-1.1.3.tar.gz` (`cat ...part* > ...` gives the same result). Verify with `shasum -a 256 --ignore-missing -c SHA256SUMS` — every line must say OK. Extract with `tar -xzf`. For the models, run `tar -xzf ../cynovela-chewie-models-1.1.3.tar.gz` inside the extracted chewie folder — `store/models/` is created there. The step-by-step guide, **HOW-TO-ASSEMBLE.md**, sits next to the files on the releases page.

**If unsure:** (1) fetching from outside (conda-forge / PyPI / huggingface.co) is not allowed on your machine, or you are not certain it is — package edition + models. (2) You want to run on your own Python/conda — the source from this repository + models.

**Two short cautions**

- **Do not place the extracted folder under cloud sync** (iCloud Drive, Dropbox, OneDrive, Google Drive). The whole set of files rides the sync, and cleanup or uninstall may never finish. `./launch.sh` detects this and warns before starting (it proceeds without stopping).
- **macOS marks each extracted file with the `com.apple.quarantine` attribute**, which can trigger repeated confirmations or stall loading. `./launch.sh` removes this mark, inside the distribution only, at the start of every launch. To remove it by hand: `xattr -rc <extracted folder>`.

---

# 日本語

<!-- cynovela:welcome:start -->
**Cynovela は、手元の資料を検索の対象にして、その内容を日本語と英語で質問できるようにするツールです。ただし主眼は、答えることではありません。**

**資料をAIに渡すとき、途中で何が起きているのかは、ふつう見えません。** Cynovela は、そこを見えるようにしてあります。**読み込み → マスキング → ベクター化**の各段が進み具合として画面に出て、何をいくつ伏せたかが残ります。答えには根拠にした箇所が付き、根拠が見つからなければ答えを作りません。だれがいつ何を見たかも記録に残ります。

**自分の Mac の中だけで、最初から最後まで手を動かして確かめられること。それがこのツールの目的です。**

**読み込み・検索・回答の生成は、すべてこの Mac の中で行います。インターネットには送信しません。** 例外は、クラウドのAIサービスとつなぐ **API連携** を設定した場合だけです。**最初は入っていません。**

**読み込むときに、氏名・電話番号・住所などを伏せる処理を挟みます。** 閲覧者に返るのはマスキング処理を通したあとの文だけです。API連携で外部へ送るのも、マスキング処理を通したあとの文です。**ただしマスキング処理は完全ではなく、伏せきれずに残るものがあります。**

**学習と試用のためのツールです。** 本番システムとして使うことを想定していません。**先に「使う前のご注意」(同梱の [docs/NOTICE.md](docs/NOTICE.md)) をお読みください。**
<!-- cynovela:welcome:end -->

---

## このツールについて

<!-- cynovela:about:start -->
**何のためのツールか**

手元の資料を検索の対象にして質問できるようにするツールです。**ただし主眼は答えることではなく、その途中で何が起きているかを見えるようにすることにあります。** 資料をAIに渡すとき、どこが伏せられ、何がベクターに変わり、どの根拠で答えが作られ、だれが何を見たのか。**ふだん見えないその過程を、自分の Mac の中で最初から最後まで確かめられます。**

**取り込みのときに見えるもの**

- 読み込み → マスキング → ベクター化 の各段が、進み具合として画面に出ます
- 伏せた件数と、その種別（氏名・電話番号・住所など）が残ります
- いくつの塊に分けたか、いくつをベクターに変えたかが出ます
- 途中で閉じても続きます。あとから同じ記録を開けます

**答えるときに見えるもの**

- 答えには、根拠にした資料と箇所が付きます。開いて原文を確かめられます
- 根拠が見つからないときは、答えを作らずにその旨を返します
- だれがいつ何を見たかが記録に残ります

**だれが何を見られるか**

利用者は**管理者**と**閲覧者**の2種類です。**閲覧者に返るのは、マスキング処理を通したあとの文だけです。** マスキング処理を通す前の文を開けるのは管理者だけで、**この Mac の画面上に限られます。** 読み込むフォルダは複数に分けて登録でき、フォルダごとに見せる相手を変えられます。

**使い方**

フォルダを指定すると、中の文書を読み込んで質問できる状態になります。あとは「去年の契約で、解約の通知は何日前までと書いてあった？」のように、普通の言葉で聞くだけです。

**できないこと**

- **本番システムとして使うことは想定していません。** 可用性・性能・長期の保守は考慮していません
- **マスキング処理は完全ではありません。** ふりがなの氏名や住所の番地から先など、伏せきれずに残るものがあります
- **答えは間違うことがあります。** 必ず出典を開いて原文で確かめてください
<!-- cynovela:about:end -->

---

## 動作環境

<!-- cynovela:env:start -->
| 項目 | 内容 |
|---|---|
| 対応している機種 | **Apple シリコン搭載の Mac のみ**（M1 以降）。Intel の Mac・Windows・Linux では動作を確認していない |
| OS | macOS（アイコンからの起動・フォルダを選ぶ画面が macOS の標準機能に依存） |
| ディスクの空き | **10 GB 以上を推奨。** AIモデル一式で 4.84 GB、配布ファイルが 3.15 GB |
| ブラウザ | Safari / Chrome / Edge のいずれか |
| インターネット | 初回にAIモデルを取得するときのみ必要（精度を優先 4.84 GB／容量を優先 約 2.2 GB／動作確認用 約 2.2 GB）。以降は不要 |
| 費用 | **無償。** API連携を使う場合、連携先の利用料は利用者の負担 |

この配布物はこの Mac の上で直接動きます。コンテナは使いません。
<!-- cynovela:env:end -->

---

## 導入方法

### どれを落とすか

すべて GitHub Releases (v1.1.3) にあります: https://github.com/tohaya-dev/cynovela/releases

1. **パッケージ版** — `cynovela-chewie-package-1.1.3.tar.gz`（1本・約800MB）。Apple silicon の Mac 向け。Python も conda も要らず、展開して `./launch.sh` を叩くだけで動きます。ただし AIモデルは別です: 下の `models` の分割ファイルも落として重ねます。
2. **ソース版** — ダウンロードではありません。ソースはこのリポジトリです。clone するか GitHub の「Download ZIP」で取り、`chewie/` の木に下の `models` を重ねて `./launch.sh` を叩けば、初回の起動が環境を作ります。

- **AIモデルだけ** — `cynovela-chewie-models-1.1.3.tar.gz.part00`〜`part02`（分割3本）。名前は models ですが、この分割ファイルは conda のパッケージではなく **AIモデル本体**です。（1.0.7 のモデルとバイト同一 — モデル本体は変わっていません。）

**つなぐ・確かめる・展開する。** 分割ファイルは part の順に 1 本へつなぎます: `cat cynovela-chewie-models-1.1.3.tar.gz.part00 cynovela-chewie-models-1.1.3.tar.gz.part01 cynovela-chewie-models-1.1.3.tar.gz.part02 > cynovela-chewie-models-1.1.3.tar.gz`（`cat ...part* > ...` でも同じです）。`shasum -a 256 --ignore-missing -c SHA256SUMS` で確かめ、全行 OK であること。展開は `tar -xzf` です。models は、**展開済みの chewie フォルダの中で** `tar -xzf ../cynovela-chewie-models-1.1.3.tar.gz` を実行します（`store/models/` が作られます）。落とし方とつなぎ方の手引き **HOW-TO-ASSEMBLE.md** が、Releases のファイルの並びに一緒に置いてあります。

**迷ったら:** (1) 管理された Mac（MDM 配下）などで外部への取り寄せ（conda-forge / PyPI / huggingface.co）が許可されていない・確信が無い → **パッケージ版 + models**。 (2) 自分の Python/conda で動かしたい → **このリポジトリのソース + models**。

### 短い注意 2 点

- **クラウド同期（iCloud Drive・Dropbox・OneDrive・Google Drive）の下に展開しないでください。** 部品一式が同期に乗り、掃除やアンインストールが終わらないことがあります。`./launch.sh` は同期の下を検知して起動前に注意を出します（止めずに進みます）。
- **展開すると macOS が各ファイルに「印」（`com.apple.quarantine` という拡張属性）を付けます。** 確認が何度も出たり読み込みが止まったりする原因です。`./launch.sh` は起動の最初に、この印を配布物の中だけ全部自分で落とします。手で外すなら `xattr -rc <展開したフォルダ>` です。

### ソース版の環境の作り方（起動時に選びます）

```
  1) conda に専用の環境を作る
  2) この Mac の Python を使い、この配布物のフォルダの中だけに Python の環境を作る
```

### 詳しい比較 — 何がどこに、どれだけ残るか

| | パッケージ版 | ソース版 1) conda の環境 | ソース版 2) 配布物のフォルダ内 |
|---|---|---|---|
| 必要なもの | Apple シリコンの Mac だけ | conda（miniforge など） | Python 3.12 以上 |
| この Mac に Python を入れるか | 入れません（同梱の環境で動きます） | conda の中に専用の環境を作ります | 既存のものを使います |
| 残る場所 | この配布物のフォルダ内だけ | conda の環境フォルダ（専用の名前 `cynovela-dist`） | この配布物のフォルダ内だけ |
| 削除方法 | フォルダごと削除 | 環境を1つ削除（`bash uninstall.sh`） | フォルダごと削除 |
| 他の環境への影響 | ありません | **共有の環境には変更を加えません** | ありません |

共通で必要なもの（実測済み）: AIモデル一式 **4.84 GB**（別に落とします）。空き容量は **10 GB 以上**を推奨。

## モデル別取得版を受け取った方へ

この配布物には AIモデルが入っていません。ファイルの大きさは約 2.4 MB です。
初回の起動でモデルを取得します。取得には次のものが必要です。

- インターネットにつながること
- 取得する容量: 約 2.2 GB（実測 2,252,964 KB・13ファイル）
- 取得にかかる時間: 目安として数分かかります。回線の速さによって変わります

取得が終わるまで質問はできません。取得の進み具合は画面に出ます。
ネットにつながらない環境で使う場合は、モデル同梱版（約 3.15 GB）をお使いください。

---

## アンインストール

<!-- cynovela:cleanup:start -->
```
＝＝ 止めるだけ ＝＝
bash stop.sh
  本体を止めます。読み込んだ資料と設定はそのまま残ります。

＝＝ 手元から取り除く ＝＝
bash uninstall.sh
  ターミナルから叩きます。次の順で進みます。
    1. 何を取り除くかを画面に出し、1回目の確認をします
    2. 取り返しがつかないことを示し、2回目の確認をします
    3. 以後は一括で行い、途中で問い直しません
```

この形はこの Mac の上で直接動きます。コンテナは使いません。
∴ `uninstall.sh` が扱うのは、この配布物のために作った python の環境と、このフォルダです。

| 対象 | 扱い |
|---|---|
| この配布物から起こした本体 | 止めます |
| 外部の推論サーバ (このフォルダの python で動いているもの) | 止めます |
| この配布物のための conda 環境 | 消します |
| ソース版が作った venv (`.venv-cynovela`) | この配布物のフォルダごとゴミ箱へ入ります |
| パッケージ版に同梱の conda-pack 環境 (`.condapack-cynovela`) | この配布物のフォルダごとゴミ箱へ入ります |
| 外部の推論サーバの python の環境 (`.mas-env`) | この配布物のフォルダごとゴミ箱へ入ります |
| この配布物のフォルダ（取り込んだ資料と設定を含みます） | **ゴミ箱へ入れます** |
| conda そのもの | **取り除きません**（他の用途でお使いになるためです） |
| 共有の conda 環境 | **触りません**（この配布物が作っていないものは対象になりません） |

取り除く環境の名前は決め打ちしていません。`cynovela.yaml` に書いてあればそれを、
無ければ `launch.sh` が持っている名前を読みます。
1回目の確認の画面に、読み取った名前と、実際に在るものを並べて出します。
一致しないものは消さず、名前を出して残します。

最後はゴミ箱へ入れるだけです。**ディスクの容量は、ゴミ箱を空にするまで戻りません。**
ゴミ箱から戻すこともできます。
<!-- cynovela:cleanup:end -->

---

## ターミナルから使う

コマンド一覧は同梱の [docs/USE-FROM-TERMINAL.txt](docs/USE-FROM-TERMINAL.txt) にあります（`./launch.sh` の指定の全数。`./launch.sh --help` でも同じ一覧が見られます）。
`cynovela-cli.py` の命令と引数の全数は [docs/reference/cli.md](docs/reference/cli.md) にあります。

---

## 第三者への参照

- `LICENSE` — 本体のライセンス（MIT）
- `LICENSES-MODELS.md` — 同梱・参照するAIモデルのライセンス表記
- `THIRD_PARTY_NOTICES.md` — 画面側の部品とマスキングの仕組みが使う第三者ソフトウェアのライセンス表記
- [`docs/BUNDLED-DATA.md`](docs/BUNDLED-DATA.md) — 同梱データについての説明
- [`docs/NOTICE.md`](docs/NOTICE.md) — 使う前のご注意（免責）
- `SECURITY.md` — セキュリティについて

---

## この配布物でできないこと

- 画面の表示は日本語のみです。英語には切り替わりません。
- はじめての方へのガイドは、起動時に自動では出ません。最初の画面の「このツールについて」からいつでも開けます。
- 環境の準備（--setup）は起動の画面から呼べません。ターミナルから実行してください。手順は同梱の [docs/USE-FROM-TERMINAL.txt](docs/USE-FROM-TERMINAL.txt) にあります。
- データの保存先を変えても、資料の中身そのものは元の場所に残ります。
- 資料のフォルダを足したあと、起動し直す前に外そうとすると失敗します。起動し直してから外してください。
- 構成の「動作確認用」は、いまは「容量を優先」と同じモデルを使います。容量は変わりません。

## 何も入れずに始めた場合の、閲覧者の作り方

何も入れずに始めた場合、最初に居るのは管理者だけです。閲覧者はご自身で作ります。
管理者で入り、利用者の管理から新しい利用者を追加し、役割に閲覧者を選んでください。
お試しの資料で始めた場合は、閲覧者があらかじめ用意されています。
