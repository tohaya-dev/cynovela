# Cynovela

**日本語版はこちら → [日本語](#日本語)**

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

See docs/NOTICE.md ("Before You Start") before you rely on it.

---

# 日本語

全部入り版 = cynovela-<形態>-all-in-one-<日付>.tar.gz ／ 軽量版 = cynovela-falcon-lightweight-<日付>.tar.gz

<!-- cynovela:welcome:start -->
**Cynovela は、手元の資料をAIに読ませて、その内容を日本語と英語で質問できるようにするツールです。ただし主眼は、答えることではありません。**

**資料をAIに渡すとき、途中で何が起きているのかは、ふつう見えません。** Cynovela は、そこを見えるようにしてあります。**読み込み → マスキング → ベクター化**の各段が進み具合として画面に出て、何をいくつ伏せたかが残ります。答えには根拠にした箇所が付き、根拠が見つからなければ答えを作りません。だれがいつ何を見たかも記録に残ります。

**自分の Mac の中だけで、最初から最後まで手を動かして確かめられること。それがこのツールの目的です。**

**読み込み・検索・回答の生成は、すべてこの Mac の中で行います。インターネットには送信しません。** 例外は、クラウドのAIサービスとつなぐ **API連携** を設定した場合だけです。**最初は入っていません。**

**読み込むときに、氏名・電話番号・住所などを伏せる処理を挟みます。** 閲覧者に返るのはマスキング処理を通したあとの文だけです。API連携で外部へ送るのも、マスキング処理を通したあとの文です。**ただしマスキング処理は完全ではなく、伏せきれずに残るものがあります。**

**学習と試用のためのツールです。** 業務の本番システムとして使うことを想定していません。**先に「使う前のご注意」(同梱の docs/NOTICE.md) をお読みください。**
<!-- cynovela:welcome:end -->

---

## このツールについて

<!-- cynovela:about:start -->
**何のためのツールか**

手元の資料をAIに読ませて質問できるようにするツールです。**ただし主眼は答えることではなく、その途中で何が起きているかを見えるようにすることにあります。** 資料をAIに渡すとき、どこが伏せられ、何がベクターに変わり、どの根拠で答えが作られ、だれが何を見たのか。**ふだん見えないその過程を、自分の Mac の中で最初から最後まで確かめられます。**

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

- **業務の本番システムとして使うことは想定していません。** 可用性・性能・長期の保守は考慮していません
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
| コンテナで動かす場合 | **Podman。** 初回のビルドに 5〜20 分。**Docker その他は当方では確認しておらず、利用者ご自身での調整が必要** |
| ディスクの空き | **10 GB 以上を推奨。** AIモデル一式で 4.84 GB、配布ファイルが 3.15 GB |
| ブラウザ | Safari / Chrome / Edge のいずれか |
| インターネット | 初回にAIモデルを取得するときのみ必要（精度を優先 4.84 GB／容量を優先 約 2.2 GB／動作確認用 約 2.2 GB）。以降は不要 |
| 費用 | **無償。** API連携を使う場合、連携先の利用料は利用者の負担 |

動作の確認は Podman で行っています。Docker では確認していません。
使う実行ファイルは設定で指定できます。
<!-- cynovela:env:end -->

---

## 導入方法

この Mac に何が残るかが変わります。あとから削除できます。

- **方法A. コンテナで動かす（この Mac への影響が最も少ない）**
  Python をインストールしません。必要なのは Podman だけです。使い終わったらコンテナごと削除できます。
  残るもの: お使いのコンテナ基盤 ＋ コンテナイメージ。初回のビルドに 5〜20 分。
- **方法B. 配布物のフォルダ内だけに作る（conda を使わない）**
  Python の実行環境を、この配布物のフォルダ内だけに作ります。他の場所には変更を加えません。
  削除するときは、このフォルダを削除するだけです。**Python がインストール済みである必要があります。**
- **方法C. conda の環境を新しく作る**
  すでに conda をお使いの方向けです。環境が1つ増えます（名前は変更できます）。
  **既存の環境には変更を加えません。**

**迷ったら方法A です。** この Mac に Python をインストールせずに済み、削除も最も簡単です。

### 詳しい比較 — 何がどこに、どれだけ残るか

| | 方法A コンテナ | 方法B 配布物のフォルダ内 | 方法C conda の環境 |
|---|---|---|---|
| 必要なもの | Podman（未導入なら入れ方を示します） | Python 3.12 以上 | conda（miniforge など） |
| この Mac に Python を入れるか | 入れません | 既存のものを使います | conda の中に作ります |
| 残る場所 | コンテナ基盤の管理領域 | この配布物のフォルダ内だけ | conda の環境フォルダ |
| 削除方法 | コンテナとイメージを削除 | フォルダごと削除 | 環境を1つ削除 |
| 他の環境への影響 | ありません | ありません | 既存の環境には変更を加えません |
| 初回の待ち時間 | 5〜20 分（ビルド） | 未実測 | 未実測 |
| 使用する容量 | 未実測 | 未実測 | 未実測 |

共通で必要なもの（実測済み）: AIモデル一式 **4.84 GB**／配布ファイル **3.15 GB**／初回の通信 **約 2.2 GB**。空き容量は **10 GB 以上**を推奨。

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
  コンテナを止めます。読み込んだ資料と設定はそのまま残ります。

＝＝ 手元から取り除く ＝＝
bash uninstall.sh
  ターミナルから叩きます。次の順で進みます。
    1. 何を取り除くかを画面に出し、1回目の確認をします
    2. 取り返しがつかないことを示し、2回目の確認をします
    3. 以後は一括で行い、途中で問い直しません
```

`uninstall.sh` が扱うのは、この配布物が手元に残すもの全部です。

| 対象 | 扱い |
|---|---|
| 外部アクセラレータ (このフォルダの python で動いているもの) | 止めます |
| コンテナ | 止めて消します |
| 名前つきの保存領域 | 消します（読み込んだ資料と設定も一緒に無くなります） |
| イメージ | 消します |
| 外部の推論サーバの python の環境 (`.mas-env`) | この配布物のフォルダごとゴミ箱へ入ります |
| この配布物のフォルダ | **ゴミ箱へ入れます** |
| Podman | **取り除きません**（他の用途でお使いになるためです） |

取り除く相手の名前は `cynovela.yaml` から読みます。別の Cynovela をお持ちでも、そちらは対象になりません。
1回目の確認の画面に、読み取った名前と、実際に在るものを並べて出します。
一致しないものは消さず、名前を出して残します。

最後はゴミ箱へ入れるだけです。**ディスクの容量は、ゴミ箱を空にするまで戻りません。**
ゴミ箱から戻すこともできます。
<!-- cynovela:cleanup:end -->

---

## ターミナルから使う

コマンド一覧は同梱の「docs/USE-FROM-TERMINAL.txt」にあります。

---

## 第三者への参照

- `LICENSE` — 本体のライセンス（MIT）
- `LICENSES-MODELS.md` — 同梱・参照するAIモデルのライセンス表記
- `THIRD_PARTY_NOTICES.md` — 画面側の部品とマスキングの仕組みが使う第三者ソフトウェアのライセンス表記
- `docs/BUNDLED-DATA.md` — 同梱データについての説明
- `docs/NOTICE.md` — 使う前のご注意（免責）
- `SECURITY.md` — セキュリティについて

---

## この配布物でできないこと

- 画面の表示は日本語のみです。英語には切り替わりません。
- はじめての方へのガイドは、起動時に自動では出ません。最初の画面の「このツールについて」からいつでも開けます。
- 環境の準備（--setup）は起動の画面から呼べません。ターミナルから実行してください。手順は同梱の「docs/USE-FROM-TERMINAL.txt」にあります。
- コンテナで動かす形では、データの保存先を起動の画面から変えられません。保存先はコンテナの保存領域です。
- この Mac に直接入れる形では、データの保存先を変えても、資料の中身そのものは元の場所に残ります。
- 資料のフォルダを足したあと、起動し直す前に外そうとすると失敗します。起動し直してから外してください。
- 構成の「動作確認用」は、いまは「容量を優先」と同じモデルを使います。容量は変わりません。

## 何も入れずに始めた場合の、閲覧者の作り方

何も入れずに始めた場合、最初に居るのは管理者だけです。閲覧者はご自身で作ります。
管理者で入り、利用者の管理から新しい利用者を追加し、役割に閲覧者を選んでください。
お試しの資料で始めた場合は、閲覧者があらかじめ用意されています。
