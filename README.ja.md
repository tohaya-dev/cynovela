**English → [README.md](README.md)**

# Cynovela

企業の AI データパイプラインの「縮小図」です。ファイルを取り込み、個人情報を伏せ、
Publish し、出典つきの答えを返す。そして役割ごとに見えるものを分ける。ここまでを
手元の Mac だけで動かします。

個人利用・限られたお披露目・学び直しのための道具です。売り物ではなく、実務で
そのまま使うことを想定していません。

日本語の文書を想定して作っており、個人情報を伏せる処理も日本語向けに書いて
あります。

名前は造語です。cynosure（導きの星）と Vela（帆座）から。読みは「シノヴェラ」。

<!-- screenshot: place one image here once it has been captured and checked -->

## このリポジトリにある3つの形

| フォルダ | 何か | 配布物 |
|---|---|---|
| `chewie` | Mac の上で直に動く形 | GitHub Releases (v1.1.0) で公開しています |
| `falcon` | コンテナの中で動く形（Podman） | このリポジトリのソースから自分で組み立てる形であり、配布物は用意していません |
| `falcon-docker-beta` | コンテナの中で動く形（Docker・開発中のベータ・モデル同梱なし） | このリポジトリのソースから自分で組み立てる形であり、配布物は用意していません |

使うのはどれか1つだけです。同じものの動かし方が3通りある、という形です。

## 要るもの

- Apple silicon の macOS。
- `chewie` のパッケージ版 ＝ **Python も `conda` も要りません。** フォルダの中に
  自分用の Python を持っており、この Mac には何も入れません。
- `chewie` のソース版 ＝ Python 3.12 以降が要ります。環境は `launch.sh` が作ります。
  `conda` に専用の環境を作る道を用意しており、`conda` が無い場合は配布物の
  フォルダの中に環境を作ります。
- `falcon` ＝ `Podman`。
- `Docker` その他も選べますが、当方では確認していません。利用者が自分で調整する
  必要があります。
- ソース版は初回の起動でそのときに環境を作るため、インターネットが要ります。
- RAM は 8 GB 以上。答えを作るモデルとして LM Studio か OpenAI 互換の API。

## 落とすもの

すべて GitHub Releases (v1.1.0) にあります。
https://github.com/tohaya-dev/cynovela/releases

「どれを落とすか」の1枚での答えは
[chewie/docs/editions.md](chewie/docs/editions.md) にあります。

| 形 | 動き方 | モデルの同梱 | ダウンロードの形 | 要るもの |
|---|---|---|---|---|
| **パッケージ版** `cynovela-chewie-package-1.1.0.tar.gz` | Mac の上で直に | 入っていません。AIモデルも一緒に落とします | 1つのファイル | **Python も `conda` も要りません。** この Mac には何も入れません |
| **ソース版・全部入り** `cynovela-chewie-all-in-one-1.1.0.tar.gz.part00`〜`part02` | Mac の上で直に | 入っています | 分割ファイル（組み立てが要る） | Python 3.12 以降 |
| **ソース版・軽量** `cynovela-chewie-lightweight-1.1.0.tar.gz` | Mac の上で直に | 入っていません。AIモデルも一緒に落とします | 1つのファイル | Python 3.12 以降 |
| **AIモデル** `cynovela-chewie-models-1.1.0.tar.gz.part00`〜`part02` | — | — | 分割ファイル（組み立てが要る） | 名前は models ですが、`conda` のパッケージではなく AIモデル本体です |

要件がいちばん少ないのは **パッケージ版** です。展開し、AIモデルを重ねて
`./launch.sh` を叩きます。

**全部入り**＝モデルも同じダウンロードに入れて、あとから取りに行かせたくない方向け。
**軽量**＝落とすものを小さくしたい方、初回の起動で環境を作ってよい方向け。

リリースには `SHA256SUMS` と `HOW-TO-ASSEMBLE.md` も置いてあります。どの形を選んでも
`SHA256SUMS` は一緒に落としてください。全部入りとAIモデルは1つのファイルに収まらない
大きさのため分割してあります。[HOW-TO-ASSEMBLE.md](HOW-TO-ASSEMBLE.md) のとおりに
つなぎ、`SHA256SUMS` と突き合わせてから起動してください。

`falcon` と `falcon-docker-beta` は、このリポジトリのソースから自分で組み立てる形で
あり、配布物は用意していません。

## はじめての方へ

`chewie` の入口は1つです ＝ **[chewie/START-HERE.md](chewie/START-HERE.md)**。
まずここを開いてください。他の文書の地図もここに入っています。

| 文書 | 何が書いてあるか |
|---|---|
| [chewie/START-HERE.md](chewie/START-HERE.md) | 入口。初回の起動・起こし直し・入れ直し・消し方と、他の文書の在りか |
| [chewie/docs/editions.md](chewie/docs/editions.md) | 4つの落とし物のどれを選ぶか。1枚 |
| [chewie/docs/first-run.md](chewie/docs/first-run.md) | ターミナルを開いたことが無い方へ。落としたファイルから最初の答えまで。省略なし |
| [chewie/docs/restart.md](chewie/docs/restart.md) | 止め方と起こし直し方 |
| [chewie/docs/cli-reference.md](chewie/docs/cli-reference.md) | ターミナルの命令と引数の全数 |
| [chewie/docs/mcp-reference.md](chewie/docs/mcp-reference.md) | MCP の道具の全数。何を渡すと何が返るか |
| [chewie/docs/api-reference.md](chewie/docs/api-reference.md) | HTTP の口の全数。コードから起こしたもの |
| [chewie/docs/quickstart.md](chewie/docs/quickstart.md) | 急ぐ方向けの短い手順 |

`falcon` は [falcon/docs/HAJIMETE.md](falcon/docs/HAJIMETE.md) から読み、そのあと
[falcon/docs/STARTUP.md](falcon/docs/STARTUP.md) へ進んでください。
`falcon-docker-beta` は
[falcon-docker-beta/docs/HAJIMETE.md](falcon-docker-beta/docs/HAJIMETE.md) から読み、
そのあと [falcon-docker-beta/docs/STARTUP.md](falcon-docker-beta/docs/STARTUP.md) へ
進んでください。

手引きはすべて英語と日本語の併記です（英語が先・日本語が後ろ）。どの形でも、
管理者は最初のログインでパスワードの変更を求められます。

## できないこと

- **マスキングには限界があります。** 外へ出す前に型に合わせた置き換えを行いますが、
  取りこぼしは起こります。分かっているものだけでも、ふりがなの氏名、住所の番地
  から先、固定電話の一部の市外局番があります。
- 学びと試しのための道具です。本物の機密の文書を通さないでください。出てきた答えを
  そのまま正しいものとして扱わないでください。
- `Podman` 以外のコンテナエンジンでの動きは、当方では確かめていません。

## ライセンス

MIT。`LICENSE` を見てください。

---

- https://note.com/tocchidegozaru
- https://huggingface.co/tocchitocchi
