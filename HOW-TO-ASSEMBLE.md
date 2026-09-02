# How to download and assemble / 落とし方とつなぎ方

**日本語版はこちら → [日本語](#日本語)**

## 最短の手順 / The short version

**1. リリースのページから5つ落とす**（同じフォルダへ）

    cynovela-chewie-package-1.2.0.tar.gz
    cynovela-chewie-models-1.2.0.tar.gz.part00
    cynovela-chewie-models-1.2.0.tar.gz.part01
    cynovela-chewie-models-1.2.0.tar.gz.part02
    SHA256SUMS

**2. つなげる**

    cat cynovela-chewie-models-1.2.0.tar.gz.part00 cynovela-chewie-models-1.2.0.tar.gz.part01 cynovela-chewie-models-1.2.0.tar.gz.part02 > cynovela-chewie-models-1.2.0.tar.gz

**3. 確かめる**（全部 `OK` になること）

    shasum -a 256 --ignore-missing -c SHA256SUMS

**4. 展開する**

    tar -xzf cynovela-chewie-package-1.2.0.tar.gz
    cd chewie
    tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz

**5. 展開したフォルダの `QUICKSTART.md` を開く。**
起動・ログイン・モデルのつなぎ方・最初の質問まで、そこに続きがあります。

---

以下は、形ごとの一覧とくわしい手順です。上の5つで足りる方は読まなくてかまいません。

## English

**This release (1.2.0) carries the package edition and the AI models.** The app
edition (`.pkg`) is **in preparation** and is not part of this release. No
source archive is distributed on the releases page: the source is this
repository — clone it, or use GitHub's "Download ZIP", and start from the
`chewie/` tree with `./launch.sh`. The table below lists the forms so that the
names are in one place.

Pick ONE:

| Form | Files to download | AI models |
|---|---|---|
| **App edition** (`.pkg`) | **In preparation.** Not part of this release | — |
| **Package edition** (Apple silicon Macs — a folder you run in place, no Python, no conda) | `cynovela-chewie-package-1.2.0.tar.gz` (single file) | **also download the models parts** (below) |
| **Source edition** | not a download — the source is this repository | **also download the models parts** (below) |

The package edition and the AI models are on the
[v1.2.0 release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.2.0).

The AI models: `cynovela-chewie-models-1.2.0.tar.gz.part00`–`part02` (split; byte-identical to the 1.1.3 and 1.0.7 models).

Always download the checksum list `SHA256SUMS` into the same folder as well; it
covers the package edition and the AI models.

On a managed Mac (under MDM), the release also carries
`check-managed-mac.command` — download it and double-click it first. It only
measures whether this Mac will let you run the tool; it changes no setting.

### 1. Join the split files (only the ones you downloaded)

    cat cynovela-chewie-models-1.2.0.tar.gz.part00 cynovela-chewie-models-1.2.0.tar.gz.part01 cynovela-chewie-models-1.2.0.tar.gz.part02 > cynovela-chewie-models-1.2.0.tar.gz

(`cat ...part* > ...` does the same, because the shell sorts the part names.)

### 2. Check the result

    shasum -a 256 --ignore-missing -c SHA256SUMS                 # the package edition and the AI models

Every line it prints should say `OK`. If not, one part did not download completely — download that part again and repeat from step 1. Do not start the tool with a package that failed the check.

### 3. Unpack

Unpack:

    tar -xzf cynovela-chewie-package-1.2.0.tar.gz

Unpack the models **inside the unpacked `chewie` folder** (the source edition
needs this step too):

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz      # creates store/models/

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

---

# 日本語

**この版（1.2.0）に入っているのは、パッケージ版と AIモデルです。** アプリ版（`.pkg`）は
**準備中**で、この版には入っていません。ソースの書庫はリリースのページに置いて
いません。ソースはこのリポジトリです。clone するか GitHub の「Download ZIP」で取り、
`chewie/` の木から `./launch.sh` で始めてください。下の表は、名前を 1 か所で
見られるように並べています。

**どれか1つ**を選んでください。

| 形 | 落とすファイル | AIモデル |
|---|---|---|
| **アプリ版**（`.pkg`） | **準備中です。** この版には入っていません | — |
| **パッケージ版**（M系 Mac・置いた場所でそのまま動くフォルダ。Python も conda も不要） | `cynovela-chewie-package-1.2.0.tar.gz`（1本） | **下の models の分割ファイルもダウンロードします** |
| **ソース版** | ダウンロードではありません。ソースはこのリポジトリです | **下の models の分割ファイルもダウンロードします** |

パッケージ版・AIモデルは
[v1.2.0 の release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.2.0) に
あります。

AIモデル: `cynovela-chewie-models-1.2.0.tar.gz.part00`〜`part02`（分割。1.1.3・1.0.7 のモデルとバイト同一です）。

突き合わせ用の一覧 `SHA256SUMS`（パッケージ版と AIモデルのぶん）も、必ず同じ
フォルダへ落としてください。

管理された Mac（MDM 配下）で使う場合は、リリースに置いてある
`check-managed-mac.command` を先に落としてダブルクリックしてください。この Mac で
動かせるかを測るだけの診断で、設定は何も変えません。

### 1. 分割ファイルをつなぐ（落とした形のぶんだけ）

    cat cynovela-chewie-models-1.2.0.tar.gz.part00 cynovela-chewie-models-1.2.0.tar.gz.part01 cynovela-chewie-models-1.2.0.tar.gz.part02 > cynovela-chewie-models-1.2.0.tar.gz

（`cat ...part* > ...` でも同じです。分割ファイルの名前の順につながります。）

### 2. つないだ結果を確かめる

    shasum -a 256 --ignore-missing -c SHA256SUMS                 # パッケージ版と AIモデル

出てきた行が全部 `OK` なら成功です。`OK` と出ない場合、どれかの分割ファイルが最後までダウンロードできていません。そのファイルをダウンロードし直し、1 からやり直してください。確かめに通らなかったものを使い始めないでください。

### 3. 取り出す

取り出します。

    tar -xzf cynovela-chewie-package-1.2.0.tar.gz

models は**取り出した `chewie` フォルダの中で**展開します（ソース版の方も、この段は同じです）。

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.2.0.tar.gz      # store/models/ ができます

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
