# Cynovela Release Notes

**日本語版はこちら → [日本語](#日本語)**

## 1.1.2 (2026-08-29)

A release that rebuilds what is distributed, and adds a second way to install it.
Nothing happens to ingested material, settings or keys; a 1.1.1 installation can
be replaced in place.

- **New: an app edition.** `Cynovela-1.1.2-macos-arm64.pkg` installs
  `Cynovela.app` into `/Applications`. Double-click it like any other Mac
  application — no terminal, no Python, no conda. Its Python environment and the
  AI models are inside the app, so dragging the app to the Trash removes all
  three together. Your documents, index, settings and keys are kept outside it,
  in `~/Library/Application Support/Cynovela/`, so they survive an upgrade; the
  app's menu has an entry for deleting them when you do want them gone. The
  package edition is unchanged and remains the way to run it without installing
  anything.
  - It always installs into `/Applications`; the installer offers no other
    location, and installing it again goes to the same place. While it runs it
    writes only to `~/Library/Application Support/Cynovela/` — the app's own
    contents are not changed by a single byte. Quit it with **Cmd+Q** (the
    package edition still uses `bash stop.sh`). Measured first answer: about 46
    seconds on a cold start, about 26 seconds warm.
  - The installer is too large for a single release file, so it is split into
    three parts — `Cynovela-1.1.2-macos-arm64.pkg.part00`–`part02`.
    `Cynovela-assemble.command` joins them, checks them and opens the installer.
    `SHA256SUMS-pkg-assets.txt` lists those files so you can check them yourself
    as well.
  - 🔴 It is **not signed with an Apple certificate.** macOS refuses the first
    double-click and calls it "from an unidentified developer". Right-click the
    `.pkg` → Open → Open. Signing an installer package requires an Apple
    Developer Program certificate this project does not have.
- The distributables carried a folder name from the machine they were built on.
  It did no harm in use, but it does not belong in something handed to other
  people, so the contents were rebuilt without it.
- The way the distributables are assembled was changed to build everything from
  scratch every time. Previously a locally prepared copy was carried in, and that
  is how the above got in.
- A gate now checks, before anything is published, that nothing identifying the
  person who built it remains. A single hit stops the build.

## 1.0.7 (2026-08-22)

A fix release. Nothing about your ingested material, settings or keys changes —
a 1.0.6 installation can be replaced in place.

### Read this first if you are on 1.0.6

**1.0.6 could be stopped by a single API call.** Registering an ingest folder
whose name could not be assigned made the server exit — one ordinary
`POST /api/ingest-roots` was enough, and the whole server went down with it,
taking any scan or publish in flight with it. If you run 1.0.6 with the API or
the CLI reachable by anyone else, replace it. This release fixes it.

**1.0.6 showed a `confidential` collection to a viewer.** The collection list did
not filter by access level for non-administrators, and a search restricted to
particular collections could still reach outside that set through its keyword
half. Both are fixed here.

### What changed

**1. A single API call could stop the server (fix)**

Names for ingest folders are now assigned so that the part that makes a name
unique always survives the 32-character limit. When no name is free, the request
is refused with a readable message instead of the server exiting.

**2. A `confidential` collection was visible to a viewer (fix)**

Collections marked `confidential` are no longer listed to non-administrators,
and a search restricted to given collections stays inside that set.

**3. The pass no longer expires after 8 hours**

Signing in used to hand you a pass that stopped working 8 hours later, with no
way to ask for anything else. Now the pass has no expiry unless you ask for one
(`expires_in_hours` or `expires_in_seconds` on sign-in). If you hand a pass to
something you do not control, ask for an expiry. Note that signing out does not
make an already-issued pass stop working — the pass is checked by its signature
alone. This is written up in "What this tool cannot do", section 11.

**4. Signing in from the terminal**

`cynovela-cli login` signs you in and remembers the pass for you, in a file only
you can read. The password is taken from standard input or from the terminal, so
it does not sit in your shell history, and the pass is never printed.
`cynovela-cli logout` forgets it again.

**5. Exporting a workspace could produce an empty package (fix)**

If a collection held files from a folder that was not linked to the workspace,
the export wrote the file ids but not the files themselves. Importing that
package produced a collection with nothing in it — and said it had succeeded.
The export now collects the files a collection holds, wherever they came from,
and an import that ends up with an empty collection says so instead of
reporting success.

**6. An imported workspace can be asked questions straight away (fix)**

Importing restores the search vectors, but the identifiers stored inside them
still pointed at the workspace they were exported from, and searching filters on
exactly those. So an imported workspace answered nothing until it was published
again — which the note on screen said was unnecessary. The identifiers are now
rewritten during the import.

**7. Removing a person for good**

Deleting a user used to switch the account off and leave the row in place. You
can now remove it for good, from the screen's API, from the terminal
(`users delete --purge`) and from MCP. Audit log entries are kept either way.

**8. The same folder can no longer be registered twice**

Registering a folder that is already registered under another name is refused,
comparing the real path.

**9. Two scans of the same folder can no longer run at once**

The check used to be on one entry point only. It now sits in the scan itself, so
the synchronous route, the automatic scan when a folder is registered, and the
scan at start-up are all covered.

**10. The timeout message now says what happened**

It used to suggest reducing a number of referenced documents that has no setting
anywhere. It now says the wait is 120 seconds per call, that this cannot be
changed, and what you can actually do about it.

**11. Source numbers match the answer**

The `[1]`, `[2]` markers in an answer and the numbered list of sources beneath it
are now the same numbers in the terminal and over MCP, as they already were on
the screen.

**12. Documents**

New: how to run it for the first time if you have never opened Terminal; how to
stop and start it again; which of the four downloads to take; a full reference
for every terminal command; a full reference for all 25 MCP tools. The API
reference was replaced by a list of every endpoint, read out of the code rather
than written by hand. "What this tool cannot do" gained a new section covering
restoring a backup, what a backup does and does not hold, the fixed dimension
number in an export, the context length with Ollama, and what an imported
workspace cannot do.

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

The initial passwords are gone from the repository and from the documents. They
are written into each package's own `cynovela.yaml` when that package is built,
under `auth.admin_initial_password` and `auth.viewer_initial_password` — read
them there. You are asked to change the password at the first sign-in.

(Correction, recorded in 1.1.2: this entry originally said the package prints the
name and password on the screen at the first start. That happens on the ordinary
`./launch.sh` start, but **not** on the demo start (`./launch.sh --demo`), because
the sample database ships inside the package and the check for "is this the first
start" looks for that database. `cynovela.yaml` is the reliable place to read it.)

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

## 1.1.2 (2026-08-29)

配布物の中身を作り直し、入れ方をもう1つ増やした版です。読み込んだ資料・設定・鍵には
何も起きません。1.1.1 の入れ物はそのまま置き換えられます。

- **新しく「アプリ版」を用意しました。** `Cynovela-1.1.2-macos-arm64.pkg` を開くと、
  `/Applications` に `Cynovela.app` が入ります。ほかの Mac のアプリと同じように
  ダブルクリックで起動します。ターミナルも Python も conda も要りません。Python の
  環境と AIモデルはアプリの中に入っているため、アプリをゴミ箱へ入れれば3つとも
  まとめて消えます。資料・索引・設定・鍵はアプリの外の
  `~/Library/Application Support/Cynovela/` に置くので、入れ替えても残ります。
  そちらも消したいときのための項目を、アプリのメニューに用意しました。
  パッケージ版はこれまでどおりで、この Mac に何も入れずに使う道として残ります。
  - 入る場所は `/Applications` に固定です。ほかの場所は選べず、2回目に入れ直しても
    同じ場所に入ります。動いているあいだ書き込むのは
    `~/Library/Application Support/Cynovela/` だけで、アプリの中身は1バイトも
    変わりません。終わらせるときは **Cmd+Q** です（パッケージ版はこれまでどおり
    `bash stop.sh`）。最初の答えが返るまでの実測は、冷えた状態で約 46 秒、
    温まっていれば約 26 秒でした。
  - 入れ物は1つのファイルに収まらない大きさのため、3つに分けてあります
    （`Cynovela-1.1.2-macos-arm64.pkg.part00`〜`part02`）。
    `Cynovela-assemble.command` がつなぎ、確かめ、入れる画面まで開きます。
    自分でも確かめられるように、その3本の一覧を `SHA256SUMS-pkg-assets.txt` に
    載せてあります。
  - 🔴 この入れ物には **Apple の証明書による署名を付けていません。** macOS は最初の
    ダブルクリックを断り、「開発元が未確認」と言います。`.pkg` を右クリック →
    「開く」→「開く」で入れられます。入れ物に署名を付けるには Apple Developer
    Program の証明書が要り、この企画は持っていません。
- 配布物の中に、作った人の機械のフォルダ名が残っていました。使う分には支障は
  ありませんでしたが、配るものに載せるべきものではないため、中身を作り直して
  取り除きました。
- 配布物を組み立てる手順を改め、毎回まっさらな状態から作るようにしました。
  これまでは手元で用意したものを持ち込んでおり、そこに上の情報が紛れ込んでいました。
- 配るものを世に出す前に、作った人の情報が残っていないかを機械で確かめる関門を
  設けました。1 件でも残っていれば、そこで止まります。

## 1.0.7（2026-08-22）

不具合を直す版です。読み込んだ資料・設定・鍵には何も起きません。1.0.6 の入れ物は
そのまま置き換えられます。

### 1.0.6 をお使いの方は先にこれを

**1.0.6 は、API を1回叩くだけで止まることがありました。** 取り込み元のフォルダを
登録するとき、名前を割り当てられないとサーバーが終了していました。ふつうの
`POST /api/ingest-roots` 1回で足り、サーバー全体が落ち、走っていた走査や公開も
道連れになりました。API や CLI に他の人が届く形で 1.0.6 を動かしているなら、
置き換えてください。この版で直っています。

**1.0.6 は、`confidential` のまとまりを閲覧者に見せていました。** まとまりの一覧が
管理者以外に対して公開の度合いで絞っておらず、まとまりを指定した検索でも、
キーワード側だけがその外へ届く経路が残っていました。どちらもこの版で直っています。

### 変わったこと

**1. API を1回叩くだけでサーバーが止まる件（修正）**

取り込み元の名前の付け方を改め、名前を一意にするための部分が32文字の枠から
必ず落ちないようにしました。空きが無いときは、サーバーが終了するのではなく、
読める文言で断ります。

**2. `confidential` のまとまりが閲覧者に見えていた件（修正）**

`confidential` の印が付いたまとまりは管理者以外の一覧に出さなくなりました。
まとまりを指定した検索も、その集合の外へは出ません。

**3. 通行証が8時間で切れなくなりました**

これまでは、ログインすると8時間で使えなくなる通行証が渡され、それ以外を頼む道が
ありませんでした。いまは、頼まないかぎり期限がつきません（ログインのときに
`expires_in_hours` か `expires_in_seconds` を渡すと、その長さで切れます）。
自分の手の届かないところへ渡すときは、期限を頼んでください。
なお、ログアウトしても、既に出ている通行証は使えなくなりません。通行証は署名だけで
確かめられるためです。これは「このツールにできないこと」の第11節に書いてあります。

**4. ターミナルからのログイン**

`cynovela-cli login` でログインでき、通行証は自分だけが読めるファイルに覚えさせます。
合言葉は標準入力かターミナルから受け取るので、ターミナルの履歴には残りません。
通行証そのものは画面に出しません。`cynovela-cli logout` で忘れさせます。

**5. 作業場所の書き出しが空の包みになることがあった件（修正）**

まとまりが持つ資料の出どころのフォルダが、その作業場所に結ばれていない場合、
書き出しには資料の番号だけが入り、資料そのものが入りませんでした。その包みを
取り込むと、中身の空のまとまりができ、しかも成功と表示していました。
書き出しは、まとまりが持つ資料をどこから来たものでも集めるようになり、
取り込みは、中身が空になったときにそう言うようになりました。

**6. 取り込んだ作業場所にすぐ質問できる件（修正）**

取り込みは探すためのベクターを戻しますが、その中に残っている番号は書き出し元の
作業場所を指したままでした。探す側はまさにその番号で絞ります。∴ 取り込んだ作業場所は、
もう一度公開するまで何も答えませんでした。画面の知らせは「公開は要りません」と
言っていたのにです。取り込みのときに番号を書き換えるようにしました。

**7. 利用者を完全に消す**

これまでの削除は、その利用者を使えなくして行を残すだけでした。いまは行そのものを
消せます。画面の API からも、ターミナル（`users delete --purge`）からも、MCP からも
できます。監査の記録はどちらの場合も残ります。

**8. 同じフォルダを二重に登録できなくなりました**

既に登録されているフォルダを別の名前で登録しようとすると断ります。見分けは
実体のパスで行います。

**9. 同じフォルダの走査が2本同時に走らなくなりました**

これまで確かめていたのは入口の1つだけでした。走査そのものの中で確かめるようにしたので、
同期の道も、フォルダを登録したときの自動の走査も、起動のときの走査も、すべて覆います。

**10. 時間切れの知らせが、起きたことを言うようになりました**

これまでは、どこにも設定の無い「参照ドキュメント数」を減らせと言っていました。
いまは、待ち時間が1回の呼び出しにつき 120秒 であること、それは変えられないこと、
そして実際に打てる手を言います。

**11. 出典の番号が本文と合うようになりました**

答えの中の `[1]`・`[2]` と、その下に並ぶ出典の番号が、ターミナルでも MCP でも
同じ番号になりました（画面では前から同じでした）。

**12. 文書**

新しく用意したもの: ターミナルを開いたことが無い方のための、はじめての起動の手順。
止め方と起こし直し方。4つの落とし物のどれを選ぶか。ターミナルの命令の全数の一覧。
MCP の道具25件の全数の一覧。API の一覧は、手で書いたものではなく、コードから
起こした全ての口の一覧に差し替えました。「このツールにできないこと」には、
控えへの戻し方、控えに入るもの・入らないもの、書き出しに書かれる決め打ちの次元の数、
Ollama を使うときの文脈の長さ、取り込んだ作業場所にできないことを、新しい節として
足しました。

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
説明を初回だけ出します。ターミナルでは問いの直前に、画面では初回ログインの
あとに4枚で、これから進む順番・言語モデルのつなぎ方（LM Studio / Ollama。
どちらも Mac の中で動きます）・最初に試す質問・Mac の中の言語モデルは応答
まで 30 秒ほどかかることを説明します。`--no-prompt` のときは今までどおり
何も聞かず、何も出しません。

**3. チャットのワークスペース一覧が、ブラウザを更新しなくても最新になります（修正）**

新しく公開したワークスペースが、チャット画面へ入り直すだけで選択肢に出ます。

**4. 最初のパスワードを、どのファイルにも書かないようにしました（セキュリティ）**

リポジトリとドキュメントから初期パスワードの平文を消しました。値は、配布物を
組み立てるときにその配布物自身の `cynovela.yaml` へ書き込まれます
（`auth.admin_initial_password` と `auth.viewer_initial_password`）。
受け取り手はそこを見てください。最初のログインで変更を求められます。

（1.1.2 で記録した訂正: この項目はもともと「はじめて起動したときだけ、ログインの
名前とパスワードを画面に出します」と書いていました。それが起きるのは普通の
`./launch.sh` の起動のときで、デモ起動（`./launch.sh --demo`）では出ません。
同梱のデモ用データベースが最初から入っており、「初回かどうか」の判定がその
データベースの有無を見ているためです。確実に読めるのは `cynovela.yaml` です。）

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
