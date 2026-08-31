# Read Before Distributing

**日本語は下 → [日本語](#配布前にお読みくださいread-before-distributing)**

## English

This document is for whoever receives this package, and for whoever passes it
on. Read it first.

A package comes in one of two forms — the **package edition** (a single file,
about 800MB; no Python and no conda needed: unpack it and run `./launch.sh`)
and the **source edition** (not a download: the source is the repository —
clone it or use GitHub's "Download ZIP" and take the `chewie/` tree) — plus the
**models split files** (`cynovela-chewie-models-1.1.3.tar.gz.part00`–`part02`).
Neither form contains the AI models:
download the models parts too, join them in part order with `cat`, and run
`tar -xzf ../cynovela-chewie-models-1.1.3.tar.gz` inside the unpacked chewie
folder — that alone places them in the correct shape under `store/models/`
(`models--BAAI--bge-m3/snapshots/<rev>/`; nowhere else). The joining and
verification guide is `HOW-TO-ASSEMBLE.md`, published next to the files.
All forms are version `1.1.3`. Where the forms differ, this document states so.
The `store/` folder holds the ingested material's index, the database, the
settings and the key files — back it up as a whole. The token-signing key
(`store/db/jwt/secret.key`) is newly generated on the receiving machine at
first startup; it is not in the package.

1. **What this package is for.** It is for verification and demonstration —
   checking that it works, evaluating it, showing it. It is not meant to be run
   in production as it stands.
2. **There are two ways to start it.** With no arguments it starts in
   production mode (an empty database, into which you ingest your own
   material); with **`--demo`** it starts with the bundled sample material
   already loaded. If this is your first time, try `--demo` first. The two keep
   their databases and indexes in separate locations, so nothing from the demo
   mixes into production.
3. **All bundled material is fictional.** The seven files under `dummy-corpus/`
   describe a fictional organization. Every person, organisation, address, phone
   number and email address in them is invented and bears no relation to anyone
   real.
4. **The initial passwords are fixed values, written into this package's own
   `cynovela.yaml`** (`auth.admin_initial_password` /
   `auth.viewer_initial_password`, next to `launch.sh`). Nothing is delivered
   separately, and they are not written into any of the documents. `launch.sh`
   also prints them on the screen on the ordinary first start — but **not** on
   the `--demo` start, where the bundled sample database makes that route count
   as "not the first start"; reading `cynovela.yaml` works either way. **The
   administrator is required to change the password at first sign-in** — tell
   the recipient to do that first.
5. **In production mode, no ingest source is registered.** You must register one
   before your own material can be read. See `getting-started.md`. With
   `--demo`, one source is already registered.
6. **Note the default listen address.** The server listens on **all addresses
   (0.0.0.0)** by default, so it is visible from other machines on the same
   network. Pass **`--local-only`** to confine it to your own machine.

---

# 配布前にお読みください（READ BEFORE DISTRIBUTING）

この文書は、本配布物を受け取った方・配布する方に最初に読んでいただくガイドです。

配布物には**パッケージ版**（1本・約800MB。Python も conda も不要で、展開して `./launch.sh` だけで動く形）と**ソース版**（ダウンロードではなく、リポジトリのソースを clone か「Download ZIP」で取り、`chewie/` の木から始める形）の 2 つの形があり、これに **AIモデルだけの分割ファイル（models）** が加わります。どちらの形にも AIモデルは入っていないので、models も落として重ねます。形によって話が違うところは、そのつど明記します。版はいずれも `1.1.3` です。

## 1. この配布物の位置づけ

本配布物は**検証・デモ用**です。動作確認・評価・デモンストレーションを目的としており、そのままの形での本番運用を想定したものではありません。

## 2. 起動は 2 通りあります

引数なしで起動すると**本番**（空のデータベースから始まり、自分の資料を取り込んで使う）、**`--demo`** を付けると同梱のダミー資料が載った**デモ**で起動します。はじめての方はまず `--demo` で試してください。

この 2 つは、データベースとインデックスの場所が分かれています。

| 起動のしかた | データベース | インデックス（ベクター） |
|---|---|---|
| 引数なし（本番） | `store/db/cynovela.db` | `store/vector/default/chroma` |
| `--demo`（デモ） | `store/db/demo.db` | `store/vector/demo/chroma` |

**どちらも再起動して消えることはありません。**場所が分かれているので、デモで試したあとに本番を使い始めても、デモの中身が本番に混ざることはありません。

> **起動の前にモデルを置いてください。**
> どちらの形にも、検索に使う埋め込みモデルは入っていません。models の分割ファイル（`cynovela-chewie-models-1.1.3.tar.gz.part00`〜`part02`）を part の順に `cat` で 1 本につないだうえで、**展開済みの chewie フォルダの中で `tar -xzf ../cynovela-chewie-models-1.1.3.tar.gz` を実行**してください。それだけで `store/models/` の正しい形（`models--BAAI--bge-m3/snapshots/<版>/`）に置かれます。宛先は `store/models/` 配下だけです。つなぎ方と検証の手引きは、Releases に一緒に置いてある `HOW-TO-ASSEMBLE.md` にあります。置かないまま起動すると、検索や取り込みをしようとしたところで失敗します。
>
> なお `store/` フォルダには、取り込んだ資料の索引・データベース・設定・鍵ファイルが入っています。控えを取るなら `store/` ごと取ってください。通行証のトークン署名用の鍵（`store/db/jwt/secret.key`）は初回起動時にその機械で新しく作られます（配布物には入っていません）。

## 3. 同梱資料はすべて架空のサンプルです

同梱の `dummy-corpus/` にある 7 ファイル（ガイド 1 本+資料 6 本）は、すべて架空の企業**「アオゾラ商事」**を題材にした説明用サンプルです。文中に登場する人物・組織・住所・電話番号・メールアドレスなどの連絡先は**すべて実在しません**。実在の人物・団体とは一切関係ありません。

同梱のデータベースとインデックスは、**配布物を作るときに、この配布物の中の `dummy-corpus/` から作っています**。作る側の作業用の資料やインデックスは入っていません。コンテナ版には、実際に入っているものを配布物を作るときに数えた内訳が `BUNDLED-DATA.md` として同梱されます。

## 4. 初期パスワードは固定値で、この配布物自身の `cynovela.yaml` に書いてあります

管理者と閲覧者の初期パスワードは**固定値**で、**この配布物の `cynovela.yaml`**（`launch.sh` と同じ場所）の `auth.admin_initial_password` / `auth.viewer_initial_password` に書き込まれています。同梱の文書には書かれていません。**別便で渡すファイルはありません**（2026-08-02 に、乱数を作って別便で渡す形から変えました。受け取り手が入れない配布物を作らないためです）。

普通の初回起動では `launch.sh` が画面にも出します（`tools/launch-body.sh` の `print_first_login`。2 回目からは出ません）。ただし **`--demo` の起動では出ません**。同梱のデモ用データベースが最初から入っているため、その経路は「初回ではない」と判定されるからです。`cynovela.yaml` を見る道は、どちらでも使えます。

平文はこのリポジトリには置いていません。配布物を作るときに `tools/dist-initial-credentials.local`（git 追跡外・0600）から読み込み、同梱の `cynovela.yaml` の `auth.admin_initial_password` / `auth.viewer_initial_password` へ書き込みます。このファイルが無いと配布物は作れません（途中で止まります）。

**管理者は初回ログインでパスワードの変更を求められます。** 受け取った方には、まず管理者のパスワードを変えるようにお伝えください。

初回ログイン時に**管理者パスワードの変更が必須**です。画面のガイドに従って新しいパスワードを設定してください。

## 5. 本番で起動すると、取り込み元（ソースのルート）は登録 0 件から始まります

**引数なしで起動した場合（本番）**、取り込み元（ソースのルート）は登録 0 件です。自分の資料を取り込むには、**最初に取り込み元を 1 つ登録する必要があります**。登録するまで、外部のフォルダは読み取れません。

登録手順は、同梱の **getting-started.md の「取り込み元を足す」の節** を参照してください。

**`--demo` で起動した場合**はこの作業は要りません。同梱のダミー資料が取り込み済みの状態で入っており、取り込み元も `./dummy-corpus` の 1 件が最初から登録されています。そのまま検索や質問を試せます。

## 6. 待ち受けアドレスの既定値に注意してください

サーバを直接起動した場合、待ち受けは**既定で全アドレス（0.0.0.0）**です。つまり、**同一ネットワークの別の Macからも見える**状態で起動します。自分のマシンの中だけに閉じたい場合は、起動時に **`--local-only`** を付けてください。

**ここからはコンテナ版だけの話です。**コンテナで起動する `deploy/container/run-container.sh` を使う場合も、既定は全アドレス公開です。自分のマシンの中だけに閉じるには、同じく `--local-only` を付けてください。

アプリ版にはコンテナで起動する道具は入っていません（`deploy/` そのものがありません）。アプリ版を受け取った方は、この節の後半は読み飛ばしてください。
