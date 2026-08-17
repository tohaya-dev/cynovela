# Read Before Distributing

**日本語は下 → [日本語](#配布前にお読みくださいread-before-distributing)**

This document is for whoever receives this package, and for whoever passes it
on. Read it first.

A package comes in one of two forms: the **container build** and the
**application build**. The `track:` line of the bundled `VERSION` tells you
which one you have. Where the two differ, this document says so.

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
   describe a fictional company. Every person, organisation, address, phone
   number and email address in them is invented and bears no relation to anyone
   real.
4. **The initial passwords are fixed values, written in the bundled
   `STARTUP.md`.** Nothing is delivered separately. **The administrator is
   required to change the password at first sign-in** — tell the recipient to
   do that first.
5. **In production mode, no ingest source is registered.** You must register one
   before your own material can be read. See `GETTING-STARTED.md`. With
   `--demo`, one source is already registered.
6. **Note the default listen address.** The server listens on **all addresses
   (0.0.0.0)** by default, so it is visible from other machines on the same
   network. Pass **`--local-only`** to confine it to your own machine.

---

# 配布前にお読みください（READ BEFORE DISTRIBUTING）

この文書は、本配布物を受け取った方・配布する方に最初に読んでいただく案内です。

配布物には**コンテナ版**と**アプリ版**の 2 つの形があります。どちらを受け取ったかは、同梱の `VERSION` の `track:` の行で分かります。形によって話が違うところは、そのつど断ります。版はどちらも `1.0.2` です。

## 1. この配布物の位置づけ

本配布物は**検証・デモ用**です。動作確認・評価・デモンストレーションを目的としており、そのままの形での本番運用を想定したものではありません。

## 2. 起動は 2 通りあります

引数なしで起動すると**本番**（空のデータベースから始まり、自分の資料を取り込んで使う）、**`--demo`** を付けると同梱のダミー資料が載った**デモ**で起動します。はじめての方はまず `--demo` で試してください。

この 2 つは、データベースと索引の場所が分かれています。

| 起動のしかた | データベース | 索引（ベクター） |
|---|---|---|
| 引数なし（本番） | `store/db/cynovela.db` | `store/vector/default/chroma` |
| `--demo`（デモ） | `store/db/demo.db` | `store/vector/demo/chroma` |

**どちらも再起動して消えることはありません。**場所が分かれているので、デモで試したあとに本番を使い始めても、デモの中身が本番に混ざることはありません。

> **軽量版を受け取った方は、起動の前にモデルを置いてください。**
> 軽量版（tar.gz が数 MB のもの）には、検索に使う埋め込みモデルが入っていません。同梱の `SETUP-ACCELERATOR.md` の手順に従って `store/models/` へモデルを置いてから起動してください。置かないままだと、コンテナ版は**起動する前に止まります**。アプリ版は起動そのものはできますが、検索や取り込みをしようとしたところで失敗します。全部入り（tar.gz が数 GB のもの）はモデルを同梱済みなので、そのまま起動できます。

## 3. 同梱資料はすべて架空のサンプルです

同梱の `dummy-corpus/` にある 7 ファイル（案内 1 本+資料 6 本）は、すべて架空の企業**「アオゾラ商事」**を題材にした説明用サンプルです。文中に登場する人物・組織・住所・電話番号・メールアドレスなどの連絡先は**すべて実在しません**。実在の人物・団体とは一切関係ありません。

同梱のデータベースと索引は、**配布物を作るときに、この配布物の中の `dummy-corpus/` から作っています**。作る側の作業用の資料や索引は入っていません。コンテナ版には、実際に入っているものを配布物を作るときに数えた内訳が `BUNDLED-DATA.md` として同梱されます。

## 4. 初期パスワードは固定値で、同梱の案内に書いてあります

管理者と閲覧者の初期パスワードは**固定値**で、tar の中の `STARTUP.md` の「ログイン」の節に書かれています。**別便で渡すファイルはありません**（2026-08-02 に、乱数を作って別便で渡す形から変えました。受け取り手が入れない配布物を作らないためです）。

平文はこのリポジトリには置いていません。配布物を作るときに `tools/dist-initial-credentials.local`（git 追跡外・0600）から読み込み、同梱の `STARTUP.md` と `cynovela.yaml` へ書き込みます。このファイルが無いと配布物は作れません（途中で止まります）。

**管理者は初回ログインでパスワードの変更を求められます。** 受け取った方には、まず管理者のパスワードを変えるようにお伝えください。

初回ログイン時に**管理者パスワードの変更が必須**です。画面の案内に従って新しいパスワードを設定してください。

## 5. 本番で起動すると、取り込み元（ソースの根）は登録 0 件から始まります

**引数なしで起動した場合（本番）**、取り込み元（ソースの根）は登録 0 件です。自分の資料を取り込むには、**最初に取り込み元を 1 つ登録する必要があります**。登録するまで、外部のフォルダは読み取れません。

登録手順は、同梱の **GETTING-STARTED.md の「7. 自分の資料を取り込む」（7-1. 取り込み元のフォルダを登録する）** を参照してください。

**`--demo` で起動した場合**はこの作業は要りません。同梱のダミー資料が取り込み済みの状態で入っており、取り込み元も `./dummy-corpus` の 1 件が最初から登録されています。そのまま検索や質問を試せます。

## 6. 待ち受けアドレスの既定値に注意してください

サーバを直接起動した場合、待ち受けは**既定で全アドレス（0.0.0.0）**です。つまり、**同一ネットワークの別の Macからも見える**状態で起動します。自分のマシンの中だけに閉じたい場合は、起動時に **`--local-only`** を付けてください。

**ここからはコンテナ版だけの話です。**コンテナで起動する `./launch.sh` を使う場合も、既定は全アドレス公開です。自分のマシンの中だけに閉じるには、同じく `--local-only` を付けてください。

アプリ版にはコンテナで起動する道具は入っていません（`deploy/` そのものがありません）。アプリ版を受け取った方は、この節の後半は読み飛ばしてください。
