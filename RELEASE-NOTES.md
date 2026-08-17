# Cynovela Release Notes

**日本語版はこちら → [日本語](#日本語)**

## 1.0.3 (2026-08-17)

A documentation release. **Nothing in the program changes**, and nothing about
your ingested material, settings or keys changes. If you are on 1.0.2, you only
need this if you want the English documentation.

### What changed

**1. Every bundled document is now bilingual**

Until 1.0.2, only the README was in English; everything else — the startup
guide, the getting-started guide, the reference documents under `docs/`, the
slide decks — was Japanese only. All of it now carries English as well, with
**English first and Japanese after**, and a link at the top of each file that
jumps to the Japanese half.

**2. `HOW-TO-ASSEMBLE.md` is now in the repository**

The guide for joining the split all-in-one packages used to exist only as a
release attachment. It is now kept in the repository as well, in both
languages, so you can read it before downloading anything.

**3. The README now links to the first-time guide**

`README.md` and `README.ja.md` link to `HAJIMETE.md` and to
`HOW-TO-ASSEMBLE.md`, so the cover page leads to both.

### What has not changed

- The screens, the operations, and the API are unchanged
- Ingested documents, settings, and keys work as they are
- The masking mechanism and the permission mechanism are unchanged
- The Japanese text of every document is unchanged; it only moved down the page

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

ドキュメントだけの版です。**プログラムは何も変わりません。** 取り込んだ資料・
設定・鍵も変わりません。1.0.2 をお使いの方は、英語のドキュメントが要るとき
だけ入れ替えてください。

### 変えたこと

**1. 同梱のドキュメントを全て日英併記にしました**

1.0.2 までは英語があるのは README だけで、起動の手引きも、はじめての方への
ガイドも、`docs/` の下の資料も、スライドも日本語だけでした。これらすべてに
英語を足し、**英語が先・日本語が後ろ**に並べました。各ファイルの冒頭には
日本語の節へ飛ぶリンクを置いてあります。

**2. `HOW-TO-ASSEMBLE.md` をリポジトリに置きました**

分割した全部入りをつなぐ手引きは、これまでリリースの添付ファイルとしてしか
ありませんでした。リポジトリにも日英併記で置いたので、ダウンロードする前に
読めます。

**3. 表紙から、はじめての方へのガイドへ行けるようにしました**

`README.md`・`README.ja.md` から `HAJIMETE.md` と `HOW-TO-ASSEMBLE.md` へ
リンクを張りました。

### 変えていないこと

- 画面・操作・API は変わりません
- 取り込んだ資料、設定、鍵はそのまま使えます
- マスキングの仕組み、権限の仕組みは変わりません
- 各ドキュメントの日本語の本文は書き換えていません。位置が後ろへ移っただけです

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
