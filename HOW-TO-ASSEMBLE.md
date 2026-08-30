# How to download and assemble / 落とし方とつなぎ方

**日本語版はこちら → [日本語](#日本語)**

## English

**This release (1.1.2) carries the app installer, the package edition and the AI
models.** The two source editions were not rebuilt for it; if you want one of those,
take it from the 1.1.1 release. The table below lists all four forms so that the
names are in one place.

This release has 4 forms of the chewie (application) build. Pick ONE:

| Form | Files to download | AI models |
|---|---|---|
| **App edition** (Apple silicon Macs — installs `Cynovela.app` into `/Applications`) | `Cynovela-1.1.2-macos-arm64.pkg.part00`–`part02` **and** `Cynovela-assemble.command` (split) | already inside |
| **Package edition** (Apple silicon Macs — a folder you run in place, no Python, no conda) | `cynovela-chewie-package-1.1.2.tar.gz` (single file) | **also download the models parts** (below) |
| **Source edition, all-in-one** (on the **1.1.1** release) | `cynovela-chewie-all-in-one-1.1.1.tar.gz.part00`–`part02` (split) | already inside |
| **Source edition, model-separate** (on the **1.1.1** release) | `cynovela-chewie-lightweight-1.1.1.tar.gz` (single file) | **also download the models parts** (below) |

The app edition and the package edition contain the same program. The difference is
where it lives and where it writes. The app edition is installed into
`/Applications` and keeps your data in `~/Library/Application Support/Cynovela/`;
the package edition is a folder you keep wherever you like and it writes inside
that folder. See [chewie/docs/editions.md](https://github.com/tohaya-dev/cynovela/blob/main/chewie/docs/editions.md).

The app edition, the package edition and the AI models are on the
[v1.1.2 release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.1.2). The two
source editions are on the [v1.1.1 release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.1.1),
because they were not rebuilt for 1.1.2.

The AI models: `cynovela-chewie-models-1.1.2.tar.gz.part00`–`part02` (split; byte-identical to the 1.0.7 models).

Always download the matching checksum list into the same folder as well:
`SHA256SUMS` covers the tar.gz editions and the AI models, and
`SHA256SUMS-pkg-assets.txt` covers the app installer's three parts and
`Cynovela-assemble.command`.

### 1. Join the split files (only the ones you downloaded)

**App edition.** Put the three `.part` files and `Cynovela-assemble.command` in the
same folder and double-click `Cynovela-assemble.command`. It checks each part,
joins them, checks the joined file against the whole-file hash, and then opens the
installer. You do not have to run `cat` or `shasum` yourself for this form.

Doing it by hand instead:

    cat Cynovela-1.1.2-macos-arm64.pkg.part00 Cynovela-1.1.2-macos-arm64.pkg.part01 Cynovela-1.1.2-macos-arm64.pkg.part02 > Cynovela-1.1.2-macos-arm64.pkg

**The other forms:**

    cat cynovela-chewie-all-in-one-1.1.1.tar.gz.part00 cynovela-chewie-all-in-one-1.1.1.tar.gz.part01 cynovela-chewie-all-in-one-1.1.1.tar.gz.part02 > cynovela-chewie-all-in-one-1.1.1.tar.gz

    cat cynovela-chewie-models-1.1.2.tar.gz.part00 cynovela-chewie-models-1.1.2.tar.gz.part01 cynovela-chewie-models-1.1.2.tar.gz.part02 > cynovela-chewie-models-1.1.2.tar.gz

(`cat ...part* > ...` does the same, because the shell sorts the part names.)

### 2. Check the result

    shasum -a 256 --ignore-missing -c SHA256SUMS                 # tar.gz editions and the AI models
    shasum -a 256 --ignore-missing -c SHA256SUMS-pkg-assets.txt  # the app installer's parts

Every line it prints should say `OK`. If not, one part did not download completely — download that part again and repeat from step 1. Do not start the tool with a package that failed the check.

(`Cynovela-assemble.command` checks the app installer's parts by itself as well, so
for that form this step is a second, independent check rather than the only one.)

### 3. Install, or unpack

**App edition** — double-click the joined `Cynovela-1.1.2-macos-arm64.pkg`. It
installs `Cynovela.app` into `/Applications`, and asks for an administrator name
and password while doing so, because it writes there.

> 🔴 The installer package is **not signed with an Apple certificate**, so macOS
> will say it "cannot be opened because it is from an unidentified developer". To
> get past that: in Finder, **right-click** the `.pkg` → **Open** → **Open** again.
> Why it is unsigned is explained in
> [MACOS-DISTRIBUTION-STRATEGY.md](https://github.com/tohaya-dev/cynovela/blob/main/MACOS-DISTRIBUTION-STRATEGY.md) §15.7.
> It needs macOS 12 or later on an Apple silicon Mac, and about 8 GB of free space.

**The other forms** — unpack:

    tar -xzf cynovela-chewie-package-1.1.2.tar.gz        # or the form you picked

If you use the **package edition** or the **model-separate edition**, unpack the models **inside the unpacked `chewie` folder**:

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.1.2.tar.gz      # creates store/models/

### 4. What to read next

**App edition** — open `Cynovela.app` from `/Applications` (it always installs
there; the installer offers no other location, and installing it again goes to the
same place). Nothing else has to be downloaded: its Python environment (about
2.3 GB) and the embedded model `bge-m3` (about 4.8 GB) are inside the app. While it
runs it writes only to `~/Library/Application Support/Cynovela/` — the app's own
contents are not changed by a single byte. Quit it with **Cmd+Q**. The first answer
takes about 46 seconds on a cold start and about 26 seconds warm. To remove it, drag
it to the Trash; that removes the program, its Python environment and the AI models
in one go. Your documents and settings live outside it, in
`~/Library/Application Support/Cynovela/`, and are **not** removed with it — see
`START-HERE.md` for how to delete those too.

**The other forms** — open **`START-HERE.md`** in the unpacked folder. It is the only entry document — setup, restart, reinstall and uninstall are all there.

**Signing in, either way.** The administrator user name is `cynovela` and the
viewer account is `demo`. Their first passwords are written **inside the download
itself, in `cynovela.yaml`**: read the value of `auth.admin_initial_password`
(and `auth.viewer_initial_password` for the viewer). Nothing is sent to you
separately. For the package and source editions that file sits in the folder you
unpacked, next to `launch.sh`; for the app edition, right-click
`/Applications/Cynovela.app` in Finder → **Show Package Contents** →
`Contents/Resources/cynovela/cynovela.yaml`. You are asked to change the password
straight after the first sign-in.

If you have never used Terminal before, open **`docs/getting-started.md`** instead. It goes from the downloaded file to your first answer without skipping a keystroke.

> Package edition note: it runs as is with `./launch.sh`. The Python environment it needs is already inside the folder, under `.condapack-cynovela/`. Nothing is installed on your Mac.

---

# 日本語

**この版（1.1.2）に入っているのは、アプリの入れ物（.pkg）とパッケージ版と AIモデルです。**
ソース版の 2 つはこの版では作り直していません。そちらが要る場合は 1.1.1 の
リリースから取ってください。下の表は、名前を 1 か所で見られるように 4 つとも並べています。

このリリースの chewie（アプリ版）は4つの形があります。**どれか1つ**を選んでください。

| 形 | 落とすファイル | AIモデル |
|---|---|---|
| **アプリ版**（M系 Mac・`/Applications` へ `Cynovela.app` を入れる形） | `Cynovela-1.1.2-macos-arm64.pkg.part00`〜`part02` と `Cynovela-assemble.command`（分割） | 入っています |
| **パッケージ版**（M系 Mac・置いた場所でそのまま動くフォルダ。Python も conda も不要） | `cynovela-chewie-package-1.1.2.tar.gz`（1本） | **下の models の片も落とします** |
| **ソース版・全部入り**（**1.1.1** のリリースに在ります） | `cynovela-chewie-all-in-one-1.1.1.tar.gz.part00`〜`part02`（分割） | 入っています |
| **ソース版・モデル別取得版**（**1.1.1** のリリースに在ります） | `cynovela-chewie-lightweight-1.1.1.tar.gz`（1本） | **下の models の片も落とします** |

アプリ版とパッケージ版は、中身のプログラムは同じものです。違うのは「どこに居るか」と
「どこへ書くか」の 2 点です。アプリ版は `/Applications` に入り、資料と設定を
`~/Library/Application Support/Cynovela/` に置きます。パッケージ版は好きな場所に置く
フォルダで、そのフォルダの中へ書きます。詳しくは
[chewie/docs/editions.md](https://github.com/tohaya-dev/cynovela/blob/main/chewie/docs/editions.md) を見てください。

アプリ版・パッケージ版・AIモデルは
[v1.1.2 の release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.1.2) に
あります。ソース版の 2 つは 1.1.2 では作り直していないため、
[v1.1.1 の release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.1.1) に
あります。

AIモデル: `cynovela-chewie-models-1.1.2.tar.gz.part00`〜`part02`（分割。1.0.7 のモデルとバイト同一です）。

突き合わせ用の一覧も、選んだ形を覆うほうを必ず同じフォルダへ落としてください。
tar.gz の各版と AIモデルのぶんが `SHA256SUMS`、アプリ版の入れ物の片3本と
`Cynovela-assemble.command` のぶんが `SHA256SUMS-pkg-assets.txt` です。

### 1. 分割ファイルをつなぐ（落とした形のぶんだけ）

**アプリ版**は、3 つの `.part` と `Cynovela-assemble.command` を同じフォルダに置いて、
`Cynovela-assemble.command` をダブルクリックしてください。片を 1 つずつ確かめ、つなぎ、
つないだものを全体のハッシュと照らし合わせてから、入れる画面を開きます。この形では
`cat` も `shasum` も自分で打つ必要はありません。

手で行う場合は次のとおりです。

    cat Cynovela-1.1.2-macos-arm64.pkg.part00 Cynovela-1.1.2-macos-arm64.pkg.part01 Cynovela-1.1.2-macos-arm64.pkg.part02 > Cynovela-1.1.2-macos-arm64.pkg

**それ以外の形:**

    cat cynovela-chewie-all-in-one-1.1.1.tar.gz.part00 cynovela-chewie-all-in-one-1.1.1.tar.gz.part01 cynovela-chewie-all-in-one-1.1.1.tar.gz.part02 > cynovela-chewie-all-in-one-1.1.1.tar.gz

    cat cynovela-chewie-models-1.1.2.tar.gz.part00 cynovela-chewie-models-1.1.2.tar.gz.part01 cynovela-chewie-models-1.1.2.tar.gz.part02 > cynovela-chewie-models-1.1.2.tar.gz

（`cat ...part* > ...` でも同じです。片の名前の順につながります。）

### 2. つないだ結果を確かめる

    shasum -a 256 --ignore-missing -c SHA256SUMS                 # tar.gz の各版と AIモデル
    shasum -a 256 --ignore-missing -c SHA256SUMS-pkg-assets.txt  # アプリ版の入れ物の片

出てきた行が全部 `OK` なら成功です。`OK` と出ない場合、どれかの片が最後まで落ちていません。その片を落とし直し、1 からやり直してください。確かめに通らなかったものを使い始めないでください。

（アプリ版の片は `Cynovela-assemble.command` 自身も確かめます。∴ この形では、この段は
唯一の確かめではなく、別口からのもう1回の確かめになります。）

### 3. 入れる、または取り出す

**アプリ版**は、つないだ `Cynovela-1.1.2-macos-arm64.pkg` をダブルクリックします。
`/Applications` へ `Cynovela.app` を入れます。そこへ書き込むため、途中で管理者の
名前とパスワードを聞かれます。

> 🔴 この入れ物には **Apple の証明書による署名を付けていません**。そのため macOS が
> 「開発元が未確認のため開けません」と言います。次のようにすると入れられます。
> Finder で `.pkg` を**右クリック** →「**開く**」→ もう一度「**開く**」。
> 署名を付けていない理由は
> [MACOS-DISTRIBUTION-STRATEGY.md](https://github.com/tohaya-dev/cynovela/blob/main/MACOS-DISTRIBUTION-STRATEGY.md) の 15.7 に書いてあります。
> macOS 12 以降の M系 Mac と、8 GB ほどの空きが要ります。

**それ以外の形**は取り出します。

    tar -xzf cynovela-chewie-package-1.1.2.tar.gz        # 選んだ形のファイルで

**パッケージ版**と**モデル別取得版**の方は、models を**取り出した `chewie` フォルダの中で**展開します。

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.1.2.tar.gz      # store/models/ ができます

### 4. 次に読むもの

**アプリ版**は、`/Applications` の `Cynovela.app` を開いてください（入る場所は
`/Applications` に固定です。ほかの場所は選べず、2回目に入れ直しても同じ場所に入ります）。
ほかに落とすものはありません。Python の環境（約 2.3 GB）と埋め込みモデル `bge-m3`
（約 4.8 GB）が中に入っています。動いているあいだ書き込むのは
`~/Library/Application Support/Cynovela/` だけで、**アプリの中身は1バイトも
変わりません**。終わらせるときは **Cmd+Q** です。最初の答えが返るまでは、冷えた状態で
約 46 秒、温まっていれば約 26 秒かかります。消すときはゴミ箱へ入れてください。
プログラムと Python の環境と AIモデルが、まとめて消えます。資料と設定はその外側の
`~/Library/Application Support/Cynovela/` に在るため、**一緒には消えません**。
そちらの消し方は `START-HERE.md` に書いてあります。

**それ以外の形**は、展開したフォルダの **`START-HERE.md`** を開いてください。唯一の入口の文書で、セットアップ・再起動・再インストール・アンインストールはすべてそこにあります。

**入り方（どちらの形でも）。** 管理者のユーザー名は `cynovela`、閲覧者は `demo` です。
最初のパスワードは**落としたもの自身の中の `cynovela.yaml` に書いてあります**。
`auth.admin_initial_password` の値を見てください（閲覧者のぶんは
`auth.viewer_initial_password` です）。別便で届くものはありません。パッケージ版と
ソース版では、そのファイルは展開したフォルダの中、`launch.sh` と同じ場所に在ります。
アプリ版では、Finder で `/Applications/Cynovela.app` を右クリック →
「**パッケージの内容を表示**」→ `Contents/Resources/cynovela/cynovela.yaml` です。
入るとすぐパスワードの変更を求められます。

ターミナルを開いたことが一度も無い方は、代わりに **`docs/getting-started.md`** を開いてください。落としたファイルから最初の答えが返るまでを、打つ文字を省かずに書いてあります。

> パッケージ版の補足: `./launch.sh` だけでそのまま動きます。動かすのに要る Python の環境は、フォルダの中の `.condapack-cynovela/` に既に入っています。この Mac には何も入れません。
