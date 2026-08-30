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
| `chewie` | Mac の上で直に動く形 | GitHub Releases (v1.1.2) で公開しています |
| `falcon` | コンテナの中で動く形（Podman） | このリポジトリのソースから自分で組み立てる形であり、配布物は用意していません |
| `falcon-docker-beta` | コンテナの中で動く形（Docker・開発中のベータ・モデル同梱なし） | このリポジトリのソースから自分で組み立てる形であり、配布物は用意していません |

使うのはどれか1つだけです。同じものの動かし方が3通りある、という形です。

## 要るもの

- Apple silicon の macOS。
- `chewie` のアプリ版（`.pkg`）＝ **準備中です。** この版には入っていません。
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

すべて GitHub Releases (v1.1.2) にあります。
https://github.com/tohaya-dev/cynovela/releases

「どれを落とすか」の1枚での答えは
[chewie/docs/editions.md](chewie/docs/editions.md) にあります。

| 形 | 動き方 | モデルの同梱 | ダウンロードの形 | 要るもの |
|---|---|---|---|---|
| **アプリ版**（`.pkg`） | — | — | **準備中です。** この版には入っていません | — |
| **パッケージ版** `cynovela-chewie-package-1.1.2.tar.gz` | 置いた場所のフォルダで直に | 入っていません。AIモデルも一緒に落とします | 1つのファイル | **Python も `conda` も要りません。** この Mac には何も入れません |
| **ソース版・全部入り** `cynovela-chewie-all-in-one-1.1.1.tar.gz.part00`〜`part02` | 置いた場所のフォルダで直に | 入っています | 分割ファイル（組み立てが要る） | Python 3.12 以降 |
| **ソース版・軽量** `cynovela-chewie-lightweight-1.1.1.tar.gz` | 置いた場所のフォルダで直に | 入っていません。AIモデルも一緒に落とします | 1つのファイル | Python 3.12 以降 |
| **AIモデル** `cynovela-chewie-models-1.1.2.tar.gz.part00`〜`part02` | — | — | 分割ファイル（組み立てが要る） | 名前は models ですが、`conda` のパッケージではなく AIモデル本体です |

**アプリ版**（`.pkg`）＝ **準備中です。** この版には入っていません。

**パッケージ版**＝この Mac に何も入れたくない方向け。展開し、AIモデルを重ねて
`./launch.sh` を叩きます。書き込みはそのフォルダの中で完結します。展開したフォルダは
あとから別の場所へ移せます。移した先でも同じ `./launch.sh` で起こしてください。

**全部入り**＝モデルも同じダウンロードに入れて、あとから取りに行かせたくない方向け。
**軽量**＝落とすものを小さくしたい方、初回の起動で環境を作ってよい方向け。ソース版の
2 つは 1.1.2 では作り直していないため、1.1.1 のリリースに在ります。

リリースには `HOW-TO-ASSEMBLE.md` と、突き合わせ用の一覧 `SHA256SUMS`（tar.gz の
各版と AIモデルのぶん）、そして `check-managed-mac.command`（会社から渡された Mac で
動かせるかを、設定を変えずに測るだけの診断）を置いてあります。リリースの1ファイルは
2 GiB までのため、全部入りと AIモデルは片に分けてあります。
[HOW-TO-ASSEMBLE.md](HOW-TO-ASSEMBLE.md) のとおりにつなぎ、`SHA256SUMS` と
突き合わせてから起動してください。

`falcon` と `falcon-docker-beta` は、このリポジトリのソースから自分で組み立てる形で
あり、配布物は用意していません。

## はじめての方へ

`chewie` の入口は1つです ＝ **[chewie/START-HERE.md](chewie/START-HERE.md)**。
まずここを開いてください。他の文書の地図もここに入っています。

| 文書 | 何が書いてあるか |
|---|---|
| [chewie/START-HERE.md](chewie/START-HERE.md) | 入口。初回の起動・起こし直し・入れ直し・消し方と、他の文書の在りか |
| [chewie/docs/editions.md](chewie/docs/editions.md) | 4つの落とし物のどれを選ぶか。1枚 |
| [chewie/docs/getting-started.md](chewie/docs/getting-started.md) | ターミナルを開いたことが無い方へ。落としたファイルから最初の答えまで。省略なし |
| [chewie/docs/operations.md](chewie/docs/operations.md) | 動かし続けるために。止め方と起こし直し方、LLM のつなぎ方、控えと戻し方、利用者、記録 |
| [chewie/docs/reference/cli.md](chewie/docs/reference/cli.md) | ターミナルの命令と引数の全数 |
| [chewie/docs/reference/mcp.md](chewie/docs/reference/mcp.md) | MCP の道具の全数。何を渡すと何が返るか |
| [chewie/docs/reference/api.md](chewie/docs/reference/api.md) | HTTP の口の全数。コードから起こしたもの |
| [chewie/docs/handson.md](chewie/docs/handson.md) | 動き出したあと、同梱の資料で試すための練習 |

`falcon` は [falcon/docs/HAJIMETE.md](falcon/docs/HAJIMETE.md) から読み、そのあと
[falcon/docs/STARTUP.md](falcon/docs/STARTUP.md) へ進んでください。
`falcon-docker-beta` は
[falcon-docker-beta/docs/HAJIMETE.md](falcon-docker-beta/docs/HAJIMETE.md) から読み、
そのあと [falcon-docker-beta/docs/STARTUP.md](falcon-docker-beta/docs/STARTUP.md) へ
進んでください。

手引きはすべて英語と日本語の併記です（英語が先・日本語が後ろ）。

**最初のパスワードについて。** 管理者のユーザー名は `cynovela`、閲覧者は `demo` です。
最初のパスワードは**落としたもの自身の中の `cynovela.yaml` に書いてあります**。
`auth.admin_initial_password` の値を見てください（閲覧者のぶんは
`auth.viewer_initial_password` です）。別便で届くものはなく、この一連の文書にも
パスワードは書いてありません。

- **パッケージ版・ソース版:** `cynovela.yaml` は展開したフォルダの中、`launch.sh` と
  同じ場所に在ります。

起動の画面にも、普通の `./launch.sh` の起動のときには1回だけ出ます。ただしデモ起動
（`./launch.sh --demo`）では出ません。同梱のデモ用データベースが最初から入っている
ため、その経路は「初回ではない」と判定されるからです。どの形でも、管理者は最初の
ログインでパスワードの変更を求められます。

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
