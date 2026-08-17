# Cynovela Release Notes

**日本語版はこちら → [日本語](#日本語)**

## 1.0.3 (2026-08-17)

A fix and usability release. Nothing about your ingested material, settings or
keys changes — a 1.0.2 installation can be replaced in place.

### What changed

**1. Files added after the first publish now reach the search (fix)**

When you added a file to a folder that was already ingested and rescanned it,
the screen said it was detected — but the file never appeared in search or in
answers, and the re-publish button said "no changes since the last publish".
The cause: newly found files were never attached to any collection. The
collections screen now shows a notice — "This collection does not include N
new file(s)" — with an **Add** button, and the re-publish button now states
this as its reason. After adding, press Publish as usual. Nothing is attached
or published automatically: you decide what the tool may read.

**2. Start-up now always asks about your search folders**

`--demo` used to skip the folder question entirely, and then the screen asked
you to add folders — a contradiction. Demo start now asks one question ("add
your own folder too?"). A first-time guide now appears once: in the terminal
just before that question, and in the app as a short four-page tour after the
first sign-in. It explains what will happen, how to connect a language model
(LM Studio or Ollama, both running inside your Mac), what to ask first, and
that a local model can take about 30 seconds before it starts answering.
`--no-prompt` still asks nothing and shows nothing.

**3. The chat workspace list updates without reloading the browser (fix)**

A newly published workspace now appears in the chat selector as soon as you
enter the chat screen.

**4. Initial passwords are no longer written in any file (security)**

The initial passwords are gone from the repository and from the documents.
The package prints the sign-in name and password on the screen at the first
start only, and you are asked to change it at the first sign-in.

**5. Certificate problems on inspected networks are now visible (fix)**

When conda or pip fail behind a company network that replaces certificates,
the raw output is now shown together with concrete instructions for pointing
conda/pip at the company CA. Certificate environment variables
(`SSL_CERT_FILE` and friends) are only dropped when they point at files that
do not exist — a real company certificate is left alone.

**6. Documents**

- Every bundled document is bilingual, **English first and Japanese after**,
  with a link at the top that jumps to the Japanese half.
- The "before you start" notice lives in `docs/NOTICE.md`, and the launcher
  reads it from there.
- `HOW-TO-ASSEMBLE.md` is kept in the repository, so you can read it before
  downloading anything.
- `START-HERE.md` explains the three ways to add search folders.
- Wording: screens and guides now consistently say "search folders"
  (検索の対象フォルダ).

### What has not changed

- Ingested documents, settings, and keys work as they are
- The masking mechanism and the permission mechanism are unchanged

## 1.0.2 (2026-08-17)

A fix to the startup path. **Nothing changes for material you have already
ingested: your documents, settings, and keys are untouched.**
If you are on 1.0.1, you can replace it with 1.0.2 as-is.

### What was fixed

**1. Startup failing with "python not found"**

Right after creating the environment with conda, running `./launch.sh --check`
printed both of these in the same report:

```
python in use: .../envs/cynovela-dist/bin/python
version: Python 3.12.13
python for the backup file: none (no 3.12 or newer found)
```

— saying at once that a python both was and was not present.
The python found on the line above was being looked up a second time further
down, and was missed for no reason other than not being named `python3.12`.

From now on, **the python already found is the one that gets used.** The version
is no longer inferred from the filename; the interpreter itself is asked.

**2. Startup stopping for something that need not stop it**

When 1 above happened, it was listed under "required to run", so **startup itself
stopped.** But the only thing that becomes unreadable is the backup of the
ingest sources; the application itself runs.

From now on it is listed under "worth noting (does not stop startup)", and
**startup proceeds.** The fact that added folders are not loaded is still shown
on screen, as before.

**3. Mismatched dependency versions**

Building the environment from the bundled `environment.yml` did not reach the
versions required by the bundled `requirements.txt`, so **19** "version
mismatch" entries were listed on every `./launch.sh --check`.

The two manifests were reconciled against the versions in `requirements.txt`.
**There are now 0 mismatched dependencies.** To keep them from drifting again,
`tools/check-manifests.py` is bundled to verify the two mechanically.

**4. Corrected guidance text**

On failure, the guidance said "press `Cynovela-start.command` again". That is
**the same entry point that just failed**, and pressing it stops at the same
place.

From now on it shows the operation that actually works at that point: for the
application build `./launch.sh --setup`, and for the container build, how to
install Python.

**5. No longer asking you to install what is already installed**

On a Mac with conda installed, the guidance still said "install conda
(miniforge) and then…" — even though conda's location was displayed a few lines
above in the same report.

From now on the guidance matches what is actually present on that Mac. If conda
is there, it says "run `./launch.sh --setup` to create it".

**6. Aligned the required Python version between the check and the guidance**

It said "no 3.10 or newer found" while telling you to install 3.12. Cynovela
requires **3.12 or newer**. Both the check and the guidance are now 3.12 or
newer.

### What was verified for this release

**Four kinds of clean Mac were built, and the recipient's operating procedure
was run end to end on each.**

| State tested | Result |
|---|---|
| conda only (no Python) | works through startup and search |
| creating Python inside the package | works through startup and search |
| no Python at all | refuses correctly (shows how to install it) |
| container build (Podman) | works through startup and search; if the virtual machine is stopped, names the exact command |

In every case the path was completed: sign in → change password → ingest the
bundled material (7 files, 128 locations) → answers with citations → the
difference in what a viewer sees → stop and start again.

### How to upgrade

The same as before. Unpack it and press `Cynovela-start.command`.
The contents of `store/` (documents, settings, keys) carry over. Move `store/`
from the old folder into the new one before starting.

### What has not changed

- The screens, the operations, and the API are unchanged
- Ingested documents, settings, and keys work as they are
- The masking mechanism and the permission mechanism are unchanged

---

## 1.0.1 (2026-08-14)

- Fixed registration so that the bundled 3.12-series python is used
- Added the container build (Docker Beta)

## 1.0.0 (2026-08-13)

- First general release

---

# 日本語

## 1.0.3 (2026-08-17)

不具合の修正と使い勝手の版です。取り込んだ資料・設定・鍵は何も変わりません。
1.0.2 をお使いの方は、そのまま入れ替えてお使いいただけます。

### 変えたこと

**1. あとから足したファイルが検索に載るようになりました（修正）**

取り込み済みのフォルダにファイルを1つ足して再スキャンすると、画面は
「検知した」と出すのに、そのファイルは検索にも回答にも出てこず、再 Publish の
ボタンは「前回の Publish から変更がありません」と言って押せませんでした。
原因は、見つかった新しいファイルがどのコレクションにも紐づけられないこと
でした。コレクションの一覧に「このコレクションに入っていない新しいファイルが
N 件あります」の知らせと **追加する** ボタンを出し、再 Publish のボタンも
この理由を言うようにしました。追加したら、これまでどおり Publish を押して
ください。勝手に追加も公開もしません。何を読むかは、あなたが決めます。

**2. 起動のとき、検索の対象フォルダを必ず聞くようにしました**

これまで `--demo` を付けるとフォルダの問いが丸ごと飛ばされ、そのあと画面で
「足してください」と促される矛盾がありました。デモ起動でも1問だけ
（「自分のフォルダも足しますか？」）聞きます。あわせて「はじめての方へ」の
案内を初回だけ出します。ターミナルでは問いの直前に、画面では初回ログインの
あとに4枚で、これから進む順番・言語モデルのつなぎ方（LM Studio / Ollama。
どちらも Mac の中で動きます）・最初に試す質問・Mac の中の言語モデルは応答
まで 30 秒ほどかかることを説明します。`--no-prompt` のときは今までどおり
何も聞かず、何も出しません。

**3. チャットのワークスペース一覧が、ブラウザを更新しなくても最新になります（修正）**

新しく公開したワークスペースが、チャット画面へ入り直すだけで選択肢に出ます。

**4. 最初のパスワードを、どのファイルにも書かないようにしました（セキュリティ）**

リポジトリとドキュメントから初期パスワードの平文を消しました。配布物は
はじめて起動したときだけ、ログインの名前とパスワードを画面に出します。
最初のログインで変更を求められます。

**5. 証明書で止まる問題を、見えるようにしました（修正）**

会社のネットワークで証明書が差し替わって conda / pip が失敗したとき、
生の出力と、会社の証明書を conda / pip に教える具体的な手順を出します。
証明書の環境変数（`SSL_CERT_FILE` など）は、指し先が実在しないものだけを
外します。実在する会社の証明書はそのまま使われます。

**6. ドキュメント**

- 同梱のドキュメントは全て日英併記です。**英語が先・日本語が後ろ**で、
  冒頭に日本語の節へ飛ぶリンクがあります。
- 「使う前のご注意」は `docs/NOTICE.md` に置き、起動の画面もそこから
  読みます。
- `HOW-TO-ASSEMBLE.md` をリポジトリに置いたので、ダウンロードする前に
  読めます。
- `START-HERE.md` に、検索の対象フォルダの足し方を3通り書きました。
- 画面と手引きの言い回しを「検索の対象フォルダ」にそろえました。

### 変えていないこと

- 取り込んだ資料、設定、鍵はそのまま使えます
- マスキングの仕組み、権限の仕組みは変わりません

## 1.0.2 (2026-08-17)

起動の入口の直しです。**受け取り手の資料・設定・鍵は何も変わりません。**
1.0.1 をお使いの方は、そのまま 1.0.2 に入れ替えてお使いいただけます。

### 直したこと

**1. 「python が無い」と言われて起動できなかったのを直しました**

conda で環境を作った直後に `./launch.sh --check` を叩くと、同じ画面の中で

```
使う python: .../envs/cynovela-dist/bin/python
版: Python 3.12.13
バックアップに使う python: ありません (3.12 系が見つかりません)
```

と、在るとも無いとも取れることを同時に言っていました。
すぐ上で見つけている python を、下ではもう一度別に探しに行って、
名前が `python3.12` でないという理由だけで見落としていたためです。

これからは、**もう見つけてある python をそのまま使います。**
版は名前で決めつけず、その python 自身に答えさせて確かめます。

**2. 止まる必要のないもので、起動が止まらないようにしました**

上の 1 が起きると「これが無いと動きません」に並び、**起動そのものが止まって**
いました。しかし読めなくなるのは「取り込み元のバックアップ」だけで、本体は動きます。

これからは「気をつけること (止まりはしません)」に並び、**起動は通ります。**
足したフォルダが読み込まれないことは、これまでどおり画面に出ます。

**3. 部品の版の食い違いを無くしました**

同梱の `environment.yml` で環境を作ると、同梱の `requirements.txt` が求める版に
届かず、`./launch.sh --check` のたびに「版が違う部品」が **19 件** 並んでいました。

2 つのマニフェストを突き合わせ、`requirements.txt` の版に揃えました。
**いま「版が違う部品」は 0 件です。** 以後ずれないよう、突き合わせを機械で
確かめる `tools/check-manifests.py` を同梱しました。

**4. ガイドの文言を直しました**

止まったときのガイドが「`Cynovela-start.command` をもう一度押してください」と
出ていました。これは**いま失敗したのと同じ入口**で、押しても同じところで止まります。

これからは、その場で本当に効く操作を出します。
アプリ版は `./launch.sh --setup`、コンテナ版は Python の入れ方を示します。

**5. 在るものを「入れてください」と言わないようにしました**

conda が入っている Mac でも「conda (miniforge) を入れてから…」と出していました。
同じ画面のすぐ上で、conda の保存先を表示していたにもかかわらずです。

これからは、いまその Mac に在るものに合わせて示します。
conda が在るなら「`./launch.sh --setup` を叩けば作れます」と出ます。

**6. 要る Python の版を、判定とガイドで揃えました**

「3.10 以上が見つかりません」と言いながら「3.12 を入れてください」と出していました。
Cynovela が要るのは **3.12 以上**です。判定もガイドも 3.12 以上に揃えました。

### この版で確かめたこと

**何も入っていない Mac を4通り作って、受け取り手の操作手順を最後まで通しました。**

| 試した状態 | 結果 |
|---|---|
| conda だけ在る (Python なし) | 起動〜検索まで通る |
| 配布物の中に Python を作る道 | 起動〜検索まで通る |
| Python が1つも無い | 正しく断る（入れ方を示す） |
| コンテナ版 (Podman) | 起動〜検索まで通る／仮想機械が止まっていれば命令を名指しで示す |

いずれも、ログイン → パスワードの変更 → 同梱資料の取り込み (7件・128 か所) →
出典つきの回答 → 閲覧者の見え方の違い → 止めてもう一度、まで通しています。

### 入れ替え方

これまでと同じです。展開して `Cynovela-start.command` を押してください。
`store/` の中 (資料・設定・鍵) は引き継げます。前の版のフォルダから
`store/` を新しいフォルダへ移してから起動してください。

### 変えていないこと

- 画面・操作・API は変わりません
- 取り込んだ資料、設定、鍵はそのまま使えます
- マスキングの仕組み、権限の仕組みは変わりません

---

## 1.0.1 (2026-08-14)

- 同梱の 3.12 系 python を使うよう登録まわりを修正
- コンテナ版 (Docker Beta) を追加

## 1.0.0 (2026-08-13)

- 最初の正式版
