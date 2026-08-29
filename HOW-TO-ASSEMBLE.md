# How to download and assemble / 落とし方とつなぎ方

**日本語版はこちら → [日本語](#日本語)**

## English

**This release (1.1.2) carries the package edition and the AI models only.**
The two source editions were not rebuilt for it; if you want one of those, take it
from the 1.1.1 release. The table below lists all three forms so that the names are
in one place.

This release has 3 forms of the chewie (application) build. Pick ONE:

| Form | Files to download | AI models |
|---|---|---|
| **Package edition** (Apple silicon Macs — ready to use, no Python, no conda) | `cynovela-chewie-package-1.1.2.tar.gz` (single file) | **also download the models parts** (below) |
| **Source edition, all-in-one** | `cynovela-chewie-all-in-one-1.1.2.tar.gz.part00`–`part02` (split) | already inside |
| **Source edition, model-separate** | `cynovela-chewie-lightweight-1.1.2.tar.gz` (single file) | **also download the models parts** (below) |

Every file above and below is on the same [v1.1.2 release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.1.2).

The AI models: `cynovela-chewie-models-1.1.2.tar.gz.part00`–`part02` (split; byte-identical to the 1.0.7 models).

Always download `SHA256SUMS` into the same folder as well.

### 1. Join the split files (only the ones you downloaded)

    cat cynovela-chewie-all-in-one-1.1.2.tar.gz.part00 cynovela-chewie-all-in-one-1.1.2.tar.gz.part01 cynovela-chewie-all-in-one-1.1.2.tar.gz.part02 > cynovela-chewie-all-in-one-1.1.2.tar.gz

    cat cynovela-chewie-models-1.1.2.tar.gz.part00 cynovela-chewie-models-1.1.2.tar.gz.part01 cynovela-chewie-models-1.1.2.tar.gz.part02 > cynovela-chewie-models-1.1.2.tar.gz

(`cat ...part* > ...` does the same, because the shell sorts the part names.)

### 2. Check the result

    shasum -a 256 --ignore-missing -c SHA256SUMS

Every line it prints should say `OK`. If not, one part did not download completely — download that part again and repeat from step 1. Do not start the tool with a package that failed the check.

### 3. Unpack

    tar -xzf cynovela-chewie-package-1.1.2.tar.gz        # or the form you picked

If you use the **package edition** or the **model-separate edition**, unpack the models **inside the unpacked `chewie` folder**:

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.1.2.tar.gz      # creates store/models/

### 4. What to read next

Open **`START-HERE.md`** in the unpacked folder. It is the only entry document — setup, restart, reinstall and uninstall are all there.

If you have never used Terminal before, open **`docs/first-run.md`** instead. It goes from the downloaded file to your first answer without skipping a keystroke.

> Package edition note: it runs as is with `./launch.sh`. The Python environment it needs is already inside the folder, under `.condapack-cynovela/`. Nothing is installed on your Mac.

---

# 日本語

**この版（1.1.2）に入っているのは、パッケージ版と AIモデルだけです。**
ソース版の 2 つはこの版では作り直していません。そちらが要る場合は 1.1.1 の
リリースから取ってください。下の表は、名前を 1 か所で見られるように 3 つとも並べています。

このリリースの chewie（アプリ版）は3つの形があります。**どれか1つ**を選んでください。

| 形 | 落とすファイル | AIモデル |
|---|---|---|
| **パッケージ版**（M系 Mac・すぐ使える形。Python も conda も不要） | `cynovela-chewie-package-1.1.2.tar.gz`（1本） | **下の models の片も落とします** |
| **ソース版・全部入り** | `cynovela-chewie-all-in-one-1.1.2.tar.gz.part00`〜`part02`（分割） | 入っています |
| **ソース版・モデル別取得版** | `cynovela-chewie-lightweight-1.1.2.tar.gz`（1本） | **下の models の片も落とします** |

上と下のファイルは、すべて同じ [v1.1.2 の release](https://github.com/tohaya-dev/cynovela/releases/tag/v1.1.2) にあります。

AIモデル: `cynovela-chewie-models-1.1.2.tar.gz.part00`〜`part02`（分割。1.0.7 のモデルとバイト同一です）。

`SHA256SUMS` も必ず同じフォルダへ落としてください。

### 1. 分割ファイルをつなぐ（落とした形のぶんだけ）

    cat cynovela-chewie-all-in-one-1.1.2.tar.gz.part00 cynovela-chewie-all-in-one-1.1.2.tar.gz.part01 cynovela-chewie-all-in-one-1.1.2.tar.gz.part02 > cynovela-chewie-all-in-one-1.1.2.tar.gz

    cat cynovela-chewie-models-1.1.2.tar.gz.part00 cynovela-chewie-models-1.1.2.tar.gz.part01 cynovela-chewie-models-1.1.2.tar.gz.part02 > cynovela-chewie-models-1.1.2.tar.gz

（`cat ...part* > ...` でも同じです。片の名前の順につながります。）

### 2. つないだ結果を確かめる

    shasum -a 256 --ignore-missing -c SHA256SUMS

出てきた行が全部 `OK` なら成功です。`OK` と出ない場合、どれかの片が最後まで落ちていません。その片を落とし直し、1 からやり直してください。確かめに通らなかったものを使い始めないでください。

### 3. 取り出す

    tar -xzf cynovela-chewie-package-1.1.2.tar.gz        # 選んだ形のファイルで

**パッケージ版**と**モデル別取得版**の方は、models を**取り出した `chewie` フォルダの中で**展開します。

    cd chewie
    tar -xzf ../cynovela-chewie-models-1.1.2.tar.gz      # store/models/ ができます

### 4. 次に読むもの

展開したフォルダの **`START-HERE.md`** を開いてください。唯一の入口の文書で、セットアップ・再起動・再インストール・アンインストールはすべてそこにあります。

ターミナルを開いたことが一度も無い方は、代わりに **`docs/first-run.md`** を開いてください。落としたファイルから最初の答えが返るまでを、打つ文字を省かずに書いてあります。

> パッケージ版の補足: `./launch.sh` だけでそのまま動きます。動かすのに要る Python の環境は、フォルダの中の `.condapack-cynovela/` に既に入っています。この Mac には何も入れません。
