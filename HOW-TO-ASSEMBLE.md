# How to download and assemble / 落とし方とつなぎ方

**日本語版はこちら → [日本語](#日本語)**

## 最短の手順 / The short version

**1. リリースのページから5つ落とす**（同じフォルダへ）

    cynovela-tender-package-2.0.1.tar.gz
    cynovela-tender-models-2.0.1.tar.gz.part00
    cynovela-tender-models-2.0.1.tar.gz.part01
    cynovela-tender-models-2.0.1.tar.gz.part02
    SHA256SUMS

**2. つなげる**

    cat cynovela-tender-models-2.0.1.tar.gz.part00 cynovela-tender-models-2.0.1.tar.gz.part01 cynovela-tender-models-2.0.1.tar.gz.part02 > cynovela-tender-models-2.0.1.tar.gz

**3. 確かめる**（全部 `OK` になること）

    shasum -a 256 --ignore-missing -c SHA256SUMS

**4. 展開する**

    tar -xzf cynovela-tender-package-2.0.1.tar.gz
    cd tender
    tar -xzf ../cynovela-tender-models-2.0.1.tar.gz

**5. 展開したフォルダの `QUICKSTART.md` を開く。**
起動・ログイン・モデルのつなぎ方・最初の質問まで、そこに続きがあります。

1.2.0 から入れ替える場合は、先に [1.2.0 から入れ替える](#120-から入れ替える) を読んでください。
2.0.0 から入れ替える場合は、先に [2.0.0 から入れ替える](#200-から入れ替える) を読んでください。
Upgrading from 1.2.0? Read [Upgrading from 1.2.0](#upgrading-from-120) first.
Upgrading from 2.0.0? Read [Upgrading from 2.0.0](#upgrading-from-200) first.

---

以下は、形ごとの一覧とくわしい手順です。上の5つで足りる方は読まなくてかまいません。

## English

**This release (2.0.1) carries the package edition and the AI models.** The app
edition (`.pkg`) is **in preparation** and is not part of this release. No
source archive is distributed on the releases page: the source is this
repository — clone it, or use GitHub's "Download ZIP", and start from the
`tender/` tree with `./launch.sh`. The table below lists the forms so that the
names are in one place.

Pick ONE:

| Form | Files to download | AI models |
|---|---|---|
| **App edition** (`.pkg`) | **In preparation.** Not part of this release | — |
| **Package edition** (Apple silicon Macs — a folder you run in place, no Python, no conda) | `cynovela-tender-package-2.0.1.tar.gz` (single file) | **also download the models parts** (below) |
| **Source edition** | not a download — the source is this repository | **also download the models parts** (below) |

The package edition and the AI models are on the
[v2.0.1 release](https://github.com/tohaya-dev/cynovela/releases/tag/v2.0.1).
The previous version, v1.2.0, remains available on the releases page.

The AI models: `cynovela-tender-models-2.0.1.tar.gz.part00`–`part02` (split; the same content as the 1.2.0, 1.1.3 and 1.0.7 models, under a new name).

Always download the checksum list `SHA256SUMS` into the same folder as well; it
covers the package edition and the AI models.

On a managed Mac (under MDM), the release also carries
`check-managed-mac.command` — download it and double-click it first. It only
measures whether this Mac will let you run the tool; it changes no setting.

### 1. Join the split files (only the ones you downloaded)

    cat cynovela-tender-models-2.0.1.tar.gz.part00 cynovela-tender-models-2.0.1.tar.gz.part01 cynovela-tender-models-2.0.1.tar.gz.part02 > cynovela-tender-models-2.0.1.tar.gz

(`cat ...part* > ...` does the same, because the shell sorts the part names.)

### 2. Check the result

    shasum -a 256 --ignore-missing -c SHA256SUMS                 # the package edition and the AI models

Every line it prints should say `OK`. If not, one part did not download completely — download that part again and repeat from step 1. Do not start the tool with a package that failed the check.

### 3. Unpack

Unpack:

    tar -xzf cynovela-tender-package-2.0.1.tar.gz

Unpack the models **inside the unpacked `tender` folder** (the source edition
needs this step too):

    cd tender
    tar -xzf ../cynovela-tender-models-2.0.1.tar.gz      # creates store/models/

### 4. What to read next

If this is your first time, open **`QUICKSTART.md`** in the unpacked folder — it takes you from starting the tool to your first answer. For the details, open **`START-HERE.md`** — setup, restart, reinstall and uninstall are all there.

**First sign-in. You do not need to look for the password.**
**It is printed on screen, once, the first time you start.**

    ────────────────────────────────────────────────
      First login / はじめてのログイン
        Open / ひらく          : http://localhost:8765
        User name / ユーザー名 : cynovela
        Password / パスワード  : (it appears here)
      You will be asked to change it on the first sign-in.
      Shown only this once.
    ────────────────────────────────────────────────

- **Shown on the first start only.** It does not appear again.
- **The administrator is `cynovela`; the viewer account is `demo`.**
- **The administrator is asked to change the password on first sign-in.** The viewer is not.
- **Nothing is sent to you separately.**
- **If you missed that screen**, the same value is in `cynovela.yaml` in the folder you
  unpacked, next to `launch.sh`: `auth.admin_initial_password`
  (`auth.viewer_initial_password` for the viewer).

If you have never used Terminal before, open **`docs/getting-started.md`** instead. It goes from the downloaded file to your first answer without skipping a keystroke.

> Package edition note: it runs as is with `./launch.sh`. The Python environment it needs is already inside the folder, under `.condapack-cynovela/`. Nothing is installed on your Mac.

### Upgrading from 1.2.0

2.0.1 unpacks into a folder named `tender`; 1.2.0 unpacked into `chewie`. The
new folder does not read `chewie/store/`, which holds the database, the search
index, the key files, the list of ingest roots (`ingest-roots.json`) and the AI
models. To carry them over:

1. **Stop 1.2.0.** In the `chewie` folder, run `bash stop.sh`, or double-click
   `Cynovela-stop.command`.
2. **Unpack 2.0.1 next to it**, in the folder that holds `chewie`. Do not start
   it yet.

       tar -xzf cynovela-tender-package-2.0.1.tar.gz      # creates tender/

3. **Before the first start of 2.0.1, copy the old `store/` into the new one:**

       cp -Rp chewie/store/. tender/store/

   A freshly unpacked `tender/store/` holds only `ingest-roots.json`, which
   registers the bundled sample folder under the name `tender-dummy-corpus`.
   Let the copy overwrite it with your old `ingest-roots.json`: material you
   already ingested is found through the root names recorded in that file.
   The old file's sample root, `chewie-dummy-corpus`, is recorded relative to
   the app folder, so after the copy it points at `tender/dummy-corpus`.
   `store/models/` is copied as well, so you do not need to download or
   assemble the models parts.
4. **Start from `tender/`:** `cd tender`, then `./launch.sh` (or
   `./launch.sh --demo`, or the `.command` files in that folder). Your existing
   user names and passwords work, and tokens issued by 1.2.0 keep working.
5. **Check your ingest roots.** A folder you added yourself is recorded by its
   full path. If it was inside the old `chewie/` folder, it still points there.
   Keep the `chewie` folder until you have added those folders again from
   `tender/`, and remove it only after that.

If you changed `cynovela.yaml` in the `chewie` folder, make the same changes in
`tender/cynovela.yaml` by hand; do not copy the old file over the new one.

### Upgrading from 2.0.0

2.0.1 is the same program as 2.0.0; only comments and documents differ. Both
unpack into a folder named `tender`, so move the old folder aside first. The old
`tender/store/` holds the database, the search index, the key files, the list of
ingest roots (`ingest-roots.json`) and the AI models. To carry them over:

1. **Stop 2.0.0.** In the `tender` folder, run `bash stop.sh`, or double-click
   `Cynovela-stop.command`.
2. **Rename the old folder** so that 2.0.1 does not unpack over it:

       mv tender tender-2.0.0

3. **Unpack 2.0.1** in the same place. Do not start it yet.

       tar -xzf cynovela-tender-package-2.0.1.tar.gz      # creates tender/

4. **Before the first start of 2.0.1, copy the old `store/` into the new one:**

       cp -Rp tender-2.0.0/store/. tender/store/

   A freshly unpacked `tender/store/` holds only `ingest-roots.json`. Let the
   copy overwrite it with your old one: material you already ingested is found
   through the root names recorded in that file. `store/models/` is copied as
   well, so you do not need to download or assemble the models parts.
5. **Start from `tender/`:** `cd tender`, then `./launch.sh`. Your existing user
   names, passwords and tokens keep working.

A folder you added yourself inside the old `tender` folder is recorded by its
full path, which now leads into the new folder. Add it again, and keep
`tender-2.0.0` until you have done so. If you changed `cynovela.yaml`, make the
same changes in the new `tender/cynovela.yaml` by hand.

---

# 日本語

**この版（2.0.1）に入っているのは、パッケージ版と AIモデルです。** アプリ版（`.pkg`）は
**準備中**で、この版には入っていません。ソースの書庫はリリースのページに置いて
いません。ソースはこのリポジトリです。clone するか GitHub の「Download ZIP」で取り、
`tender/` の木から `./launch.sh` で始めてください。下の表は、名前を 1 か所で
見られるように並べています。

**どれか1つ**を選んでください。

| 形 | 落とすファイル | AIモデル |
|---|---|---|
| **アプリ版**（`.pkg`） | **準備中です。** この版には入っていません | — |
| **パッケージ版**（M系 Mac・置いた場所でそのまま動くフォルダ。Python も conda も不要） | `cynovela-tender-package-2.0.1.tar.gz`（1本） | **下の models の分割ファイルもダウンロードします** |
| **ソース版** | ダウンロードではありません。ソースはこのリポジトリです | **下の models の分割ファイルもダウンロードします** |

パッケージ版・AIモデルは
[v2.0.1 の release](https://github.com/tohaya-dev/cynovela/releases/tag/v2.0.1) に
あります。前の版 v1.2.0 も、リリースのページに残っています。

AIモデル: `cynovela-tender-models-2.0.1.tar.gz.part00`〜`part02`（分割。中身は 1.2.0・1.1.3・1.0.7 のモデルと同じで、名前だけが変わりました）。

突き合わせ用の一覧 `SHA256SUMS`（パッケージ版と AIモデルのぶん）も、必ず同じ
フォルダへ落としてください。

管理された Mac（MDM 配下）で使う場合は、リリースに置いてある
`check-managed-mac.command` を先に落としてダブルクリックしてください。この Mac で
動かせるかを測るだけの診断で、設定は何も変えません。

### 1. 分割ファイルをつなぐ（落とした形のぶんだけ）

    cat cynovela-tender-models-2.0.1.tar.gz.part00 cynovela-tender-models-2.0.1.tar.gz.part01 cynovela-tender-models-2.0.1.tar.gz.part02 > cynovela-tender-models-2.0.1.tar.gz

（`cat ...part* > ...` でも同じです。分割ファイルの名前の順につながります。）

### 2. つないだ結果を確かめる

    shasum -a 256 --ignore-missing -c SHA256SUMS                 # パッケージ版と AIモデル

出てきた行が全部 `OK` なら成功です。`OK` と出ない場合、どれかの分割ファイルが最後までダウンロードできていません。そのファイルをダウンロードし直し、1 からやり直してください。確かめに通らなかったものを使い始めないでください。

### 3. 取り出す

取り出します。

    tar -xzf cynovela-tender-package-2.0.1.tar.gz

models は**取り出した `tender` フォルダの中で**展開します（ソース版の方も、この段は同じです）。

    cd tender
    tar -xzf ../cynovela-tender-models-2.0.1.tar.gz      # store/models/ ができます

### 4. 次に読むもの

はじめてなら、展開したフォルダの **`QUICKSTART.md`** を開いてください。起動から最初の答えまでを案内します。くわしくは **`START-HERE.md`** へ。セットアップ・再起動・再インストール・アンインストールはすべてそこにあります。

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

ターミナルを開いたことが一度も無い方は、代わりに **`docs/getting-started.md`** を開いてください。落としたファイルから最初の答えが返るまでを、打つ文字を省かずに書いてあります。

> パッケージ版の補足: `./launch.sh` だけでそのまま動きます。動かすのに要る Python の環境は、フォルダの中の `.condapack-cynovela/` に既に入っています。この Mac には何も入れません。

### 1.2.0 から入れ替える

2.0.1 は `tender` というフォルダへ展開されます（1.2.0 は `chewie` でした）。新しい
フォルダは `chewie/store/` を読みません。`chewie/store/` には、データベース・検索用
インデックス・鍵ファイル・取り込み元の一覧（`ingest-roots.json`）・AIモデルが
入っています。引き継ぐには、次の順に進めます。

1. **1.2.0 を止めます。** `chewie` フォルダで `bash stop.sh` を叩くか、
   `Cynovela-stop.command` をダブルクリックします。
2. **2.0.1 を隣に展開します。** `chewie` のあるフォルダで展開します。まだ起動しません。

       tar -xzf cynovela-tender-package-2.0.1.tar.gz      # tender/ ができます

3. **2.0.1 をはじめて起動する前に、古い `store/` の中身を新しい方へコピーします。**

       cp -Rp chewie/store/. tender/store/

   展開したばかりの `tender/store/` には `ingest-roots.json` だけが入っており、
   同梱のサンプル資料のフォルダを `tender-dummy-corpus` という名前で登録しています。
   これは古い `ingest-roots.json` で上書きしてください。取り込み済みの資料は、この
   ファイルに書かれたルートの名前でたどるためです。古いファイルのサンプル資料のルート
   `chewie-dummy-corpus` は本体のフォルダからの相対で書かれているので、コピーしたあとは
   `tender/dummy-corpus` を指します。
   `store/models/` も一緒にコピーされるため、AIモデルの分割ファイルを落としてつなぐ手順は
   要りません。
4. **`tender/` から起動します。** `cd tender` のあと `./launch.sh`（または
   `./launch.sh --demo`、そのフォルダの `.command`）。これまでの利用者名とパスワードで
   ログインでき、1.2.0 が出したトークンもそのまま使えます。
5. **取り込み元を確かめます。** 自分で足したフォルダは、フルパスで記録されています。
   古い `chewie/` フォルダの中にあったものは、そのまま古い場所を指します。
   `tender/` から足し直すまで `chewie` フォルダは残し、足し直してから消してください。

`chewie` フォルダの `cynovela.yaml` を書き換えていた場合は、同じ変更を
`tender/cynovela.yaml` へ手で入れてください。古いファイルで上書きはしません。

### 2.0.0 から入れ替える

2.0.1 は 2.0.0 と同じプログラムで、違うのはコメントと文書だけです。どちらも
`tender` というフォルダへ展開されるので、先に古いフォルダの名前を変えておきます。
古い `tender/store/` には、データベース・検索用インデックス・鍵ファイル・
取り込み元の一覧（`ingest-roots.json`）・AIモデルが入っています。引き継ぐには、
次の順に進めます。

1. **2.0.0 を止めます。** `tender` フォルダで `bash stop.sh` を叩くか、
   `Cynovela-stop.command` をダブルクリックします。
2. **古いフォルダの名前を変えます。** 2.0.1 が上に重なって展開されないようにします。

       mv tender tender-2.0.0

3. **2.0.1 を同じ場所に展開します。** まだ起動しません。

       tar -xzf cynovela-tender-package-2.0.1.tar.gz      # tender/ ができます

4. **2.0.1 をはじめて起動する前に、古い `store/` の中身を新しい方へコピーします。**

       cp -Rp tender-2.0.0/store/. tender/store/

   展開したばかりの `tender/store/` には `ingest-roots.json` だけが入っています。
   これは古い `ingest-roots.json` で上書きしてください。取り込み済みの資料は、この
   ファイルに書かれたルートの名前でたどるためです。`store/models/` も一緒にコピー
   されるため、AIモデルの分割ファイルを落としてつなぐ手順は要りません。
5. **`tender/` から起動します。** `cd tender` のあと `./launch.sh`。これまでの
   利用者名・パスワード・トークンはそのまま使えます。

古い `tender` フォルダの中に自分で足したフォルダは、フルパスで記録されており、
今は新しいフォルダの中を指します。足し直してください。足し直すまで `tender-2.0.0`
は残しておきます。`cynovela.yaml` を書き換えていた場合は、同じ変更を新しい
`tender/cynovela.yaml` へ手で入れてください。
