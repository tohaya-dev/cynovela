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

## まず動かす

はじめての方は、ここだけ上から順にやってください。くわしい話はあとから
[`chewie/QUICKSTART.md`](chewie/QUICKSTART.md) と
[`chewie/START-HERE.md`](chewie/START-HERE.md) にあります。

**Apple シリコンの Mac 専用です。Python も conda も要りません。この Mac には何も入れません。**

> 🔴 **これは、試して確かめるための道具です。**実務のサイトに置くものではありません。
> 本物の機密の資料を通さないでください。出てきた答えをそのまま正しいものとして
> 扱わないでください。**この節に書いてある初期の利用者名とパスワードは、
> すぐ試せるようにするためのものです。**

### 1. 落とす（5つ・同じフォルダへ）

[リリースのページ](https://github.com/tohaya-dev/cynovela/releases) から落とします。

| ファイル | 何か |
|---|---|
| `cynovela-chewie-package-1.2.0.tar.gz` | **Cynovela 本体。**`package` と付いているものが本体です |
| `cynovela-chewie-models-1.2.0.tar.gz.part00`〜`part02` | **Cynovela が使う AIモデル。**資料をベクターにする埋め込みモデル（BGE-M3 ほか）と、検索結果を並べ替えるモデルです。**答えを作る LLM は入っていません**（5節で別に用意します）。GitHub は1ファイル 2 GiB までのため、3つに分けてあります |
| `SHA256SUMS` | 壊れていないか確かめる一覧 |

会社から貸与された Mac をお使いの方は、先に `check-managed-mac.command` を落として
ダブルクリックしてください。動かせる状態かどうかだけを調べます。設定は何も変えません。

### 2. AIモデルをつないで、本体の中へ入れる

ターミナルを開き（`アプリケーション` → `ユーティリティ` → `ターミナル`）、落としたフォルダで
順に叩きます。

**2-1. 3つをつなぎます。**

    cd ~/Downloads
    cat cynovela-chewie-models-1.2.0.tar.gz.part00 cynovela-chewie-models-1.2.0.tar.gz.part01 cynovela-chewie-models-1.2.0.tar.gz.part02 > cynovela-chewie-models-1.2.0.tar.gz

**2-2. 壊れていないか確かめます。**出た行が全部 `OK` なら成功です。

    shasum -a 256 --ignore-missing -c SHA256SUMS

**2-3. 本体を展開します。**`chewie` フォルダができます。

    tar -xzf cynovela-chewie-package-1.2.0.tar.gz

**2-4. AIモデルを、本体の中で展開します。**

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz

**`chewie/store/models/` ができます。この場所でないと見つけられません。**
先に別の場所で展開してしまった場合は、できた `models` フォルダを `chewie/store/` の中へ
移してください。

**クラウド同期のフォルダ（iCloud Drive・Dropbox・OneDrive・Google Drive）の中には
置かないでください。**ファイルが実行できない形に置き換えられます。

### 3. 起動する

    ./launch.sh

ブラウザが自動で開きます。開かないときは、ターミナルの画面に出ている場所を自分で
開いてください。**`http://localhost:8765` です。8765 がふさがっていれば別の番号が
選ばれ、画面に出ます。**

### 4. ログインして、パスワードを変える

| 役割 | 利用者名 | 最初のパスワード |
|---|---|---|
| **管理者**（全部できる） | `cynovela` | `Cynovela1!` |
| **閲覧者**（見るだけ） | `demo` | `demo1234` |

**同じ値が、はじめて起動したときにターミナルの画面へ1回だけ出ます。**
展開したフォルダの `cynovela.yaml`（`launch.sh` と同じ場所）の `auth:` にもあります。

🔴 **管理者は、最初のログインでパスワードの変更を求められます。**変えるまで管理の操作は
できません。**必ず変えてください。**

**閲覧者（`demo`）には変更を求めません。**そして **Cynovela は既定で、同じネットワークの
他の端末からも開けます。**これは、別の Mac から試せるようにするための既定です。
**共有のネットワークで試すときは、`Settings` から閲覧者のパスワードも変えてください。**
この Mac の中だけに閉じたい場合は `./launch.sh --local-only` で起動します。

### 5. 答えを作る LLM をつなぐ

🔴 **ここを飛ばすと、質問しても答えが返りません。先にやってください。**

つなぐ先を先に動かしておきます（**この Mac の中で動かすもの**＝LM Studio・Ollama、
**外のサービス**＝OpenAI と同じ形の口を持つもの。OpenRouter などはここに入ります。
API キーが要ります）。

そのうえで、画面の `Settings` で**この順に**押します。

1. **プロバイダを選ぶ** — `LM Studio` / `Ollama` / `OpenAI 互換` のいずれか
2. **Base URL を入れる** — LM Studio は `http://localhost:1234`、
   Ollama は `http://localhost:11434`。外のサービスはその案内に従います
3. **`🔌 接続テスト`** を押して、成功することを確かめます
4. **`📋 モデル一覧を取得`** を押し、**使うモデルを選びます**
5. **`💾 LLM 設定をまとめて適用`** を押します

🔴 **5 を押すまで設定は保存されません。**途中に出る `保存` や `✅ 適用完了` は別の項目の
ものです。**モデルを変えるときも、3〜5 を同じ順でやり直してください。**

### 6. 試す

    ./launch.sh --demo

**同梱のサンプル資料21件が初回に取り込まれ、すぐ `RAG Chat` で質問できます**
（取り込みは約39秒。M4 Max での実測）。まず「この資料の概要を教えてください」と
聞いてみてください。**ローカルの LLM は答えが返るまで時間がかかります。**待ってください。

**起動の仕方は2通りだけです。**

| 叩くもの | どうなるか |
|---|---|
| `./launch.sh` | **本番。中身は空です。**自分の資料を入れて使います |
| `./launch.sh --demo` | **サンプル資料が入った状態。**試すのはこちら |

**どちらも別々のデータベースを持ちます。**デモで試しても本番の中身は混ざりません。
ダブルクリックで起動したい方は `Cynovela-start.command`（本番）と
`Cynovela-demo.command`（デモ）があります。

### 7. 自分の資料を読ませる

どちらでもできます。

    ./launch.sh --add               フォルダを選ぶ画面が出ます
    ./launch.sh --add-path <パス>   場所を文字で指定します

画面からは `Settings` の **「検索の対象フォルダを足す」**です。

- 🔴 **足せるのはフォルダ単位です。ファイルを1つだけ指定することはできません。**
- 🔴 **何も足さない状態では、同梱のサンプル資料だけが対象です。**
  自分の資料について聞くには、そのフォルダを足す必要があります。
- 足したあと、資料を読み込んで `Publish` すると検索の対象になります。
  **取り込みは裏で動きます。ブラウザを閉じても止まりません。**

## このリポジトリにある3つの形

| フォルダ | 何か | 配布物 |
|---|---|---|
| `chewie` | Mac の上で直に動く形 | GitHub Releases (v1.2.0) で公開しています |
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

すべて GitHub Releases (v1.2.0) にあります。
https://github.com/tohaya-dev/cynovela/releases

「どれを落とすか」の1枚での答えは
[chewie/docs/editions.md](chewie/docs/editions.md) にあります。

| 形 | 動き方 | モデルの同梱 | ダウンロードの形 | 要るもの |
|---|---|---|---|---|
| **アプリ版**（`.pkg`） | — | — | **準備中です。** この版には入っていません | — |
| **パッケージ版** `cynovela-chewie-package-1.2.0.tar.gz` | 置いた場所のフォルダで直に | 入っていません。AIモデルも一緒に落とします | 1つのファイル | **Python も `conda` も要りません。** この Mac には何も入れません |
| **ソース版** | 置いた場所のフォルダで直に | 入っていません。AIモデルも一緒に落とします | ダウンロードではありません。ソースはこのリポジトリです（clone するか、GitHub の「Download ZIP」で取れます） | Python 3.12 以降、または conda |
| **AIモデル** `cynovela-chewie-models-1.2.0.tar.gz.part00`〜`part02` | — | — | 分割ファイル（組み立てが要る） | 名前は models ですが、`conda` のパッケージではなく AIモデル本体です |

**アプリ版**（`.pkg`）＝ **準備中です。** この版には入っていません。

**パッケージ版**＝この Mac に何も入れたくない方向け。展開し、AIモデルを
`chewie/store/models/` へ展開して `./launch.sh` を叩きます。書き込みはそのフォルダの中で完結します。展開したフォルダは
あとから別の場所へ移せます。移した先でも同じ `./launch.sh` で起こしてください。

**ソース版**＝何が入るかを自分で見て決めたい方向け。ソースはこのリポジトリです。
`chewie/` の木を取り、AIモデルを重ねて `./launch.sh` を叩けば、初回の起動が環境を
作ります。リリースのページにソースの書庫は置いていません。

リリースには `HOW-TO-ASSEMBLE.md` と、突き合わせ用の一覧 `SHA256SUMS`（パッケージ版
と AIモデルのぶん）、そして `check-managed-mac.command`（管理された Mac〔MDM 配下〕で
動かせるかを、設定を変えずに測るだけの診断）を置いてあります。リリースの1ファイルは
2 GiB までのため、AIモデルは分割ファイルに分けてあります。
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
| [chewie/docs/editions.md](chewie/docs/editions.md) | どの形を選ぶか。1枚 |
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

**最初のログイン。パスワードを探す必要はありません。**
**はじめて起動したとき、ターミナルの画面に1回だけ出ます。**

    ────────────────────────────────────────────────
      First login / はじめてのログイン
        Open / ひらく          : http://localhost:8765
        User name / ユーザー名 : cynovela
        Password / パスワード  : （ここに出ます）
      最初のログインで変更を求められます。
      この表示が出るのは初回だけです。
    ────────────────────────────────────────────────

- **出るのは初回だけです。**2回目からは出ません。
- **管理者は `cynovela`、閲覧者は `demo` です。**
- **管理者は最初のログインでパスワードの変更を求められます。**閲覧者には求めません。
- **別便で届くものはありません。**
- **この画面を見逃した場合**は、展開したフォルダの `cynovela.yaml`
  （`launch.sh` と同じ場所）の `auth.admin_initial_password` に同じ値が書いてあります
  （閲覧者のぶんは `auth.viewer_initial_password`）。

| 役割 | 利用者名 | 最初のパスワード |
|---|---|---|
| **管理者**（全部できる） | `cynovela` | `Cynovela1!` |
| **閲覧者**（見るだけ） | `demo` | `demo1234` |

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
