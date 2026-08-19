# START HERE

**日本語版はこちら → [日本語](#日本語)**

## English

**This is the only entry document. You can get started with this document alone.**
Everything else under `docs/` is reference material — open it only when you need it (the list is at the end).

This package is the **application build (runs on macOS directly, no container)**.

---

### 1. Which package did you download?

```
1) Package edition (for Apple silicon Macs — ready to use)
     Extract it and run one line. No Python and no conda are needed.
     Nothing is installed on this Mac. To remove it, delete the folder.
2) Source edition (for everyone else, or those who want to build the environment themselves)
     At startup you choose one of 2 ways to build the environment:
       1) create a dedicated conda environment (name: cynovela-dist), or
       2) use this Mac's Python (3.12 or later) and build a venv only inside this folder.
```

**The AI models are downloaded separately** (a separate file on the release page, or the first start offers to fetch them). Neither package contains them.

---

### 2. System requirements

| Item | Requirement |
|---|---|
| macOS | Apple silicon Mac (M1 or later). Intel Macs, Windows and Linux are not verified. **The package edition runs on Apple silicon only.** |
| Python | **3.12 or later** (`pyproject.toml` declares `requires-python = ">=3.12"`; `environment.yml` pins 3.12.13). **3.10 and 3.11 cannot be used.** Not needed for the package edition, nor for source-edition choice 1 (conda fetches its own). |
| conda | **Miniforge recommended** (its default channel is conda-forge). **Not required** — the package edition and source-edition choice 2 work without it. |
| Free disk space | Package edition expanded: **about 3.1 GB** (measured). Source edition expanded: all-in-one **about 5.2 GB** / model-separate edition **about 8 MB** (measured). AI models: **4.84 GB** (separate download for the package and model-separate editions; already inside the all-in-one). |
| Memory | 8 GB or more recommended (existing record; not re-measured). |
| Network | Package edition: not needed to run — only to fetch the AI models. Source edition setup fetches from: conda-forge / PyPI / github.com (2 wheels) / huggingface.co (models). |
| LLM for answers | LM Studio or an OpenAI-compatible API (answers need a real LLM). |

**Installing by hand, without the launch sequence** (only if you cannot use `./launch.sh`): you need Python **3.12 or later** yourself; create a dedicated environment (conda name `cynovela-dist`, or a venv inside this folder — never create or modify a shared environment), run `pip install -r requirements.txt` in it, place the models, and start with `python server.py`. The requirements above still apply unchanged.

---

### 3. Set up and start for the first time

**Package edition:** extract the archive, then in Terminal run:

```
./launch.sh
```

Nothing is installed on this Mac; the bundled environment inside the folder is used as is.

**Source edition:** extract the archive, then run `./launch.sh` (or double-click `Cynovela-start.command`). On the first run it asks which of the 2 ways to build the environment (see section 1) and builds it. **Either way, the shared conda environment is never created and never modified.**

Then:

1. **Sign in.** The user name and the first password are printed on the screen at the first start. You will be asked to change the password straight away.
2. **Add search targets.** Answer the question shown at startup; or use "Add a search folder" under "Settings" in the app screen; or run `./launch.sh --add` (list with `./launch.sh --list`; icon: `Cynovela-add-folder.command`).
3. **Ask a question.** Open `http://localhost:8765` and type in plain language. Every answer carries the passage it came from — open it and check.
4. **Stop it.** Double-click `Cynovela-stop.command` (or run `bash stop.sh`).

---

### 4. Starting it again later (the next day, after a reboot)

Setup is needed only once. From then on:

- **Start:** double-click `Cynovela-start.command` (or `./launch.sh`). The environment is reused; nothing is rebuilt.
- **Stop:** double-click `Cynovela-stop.command` (or `bash stop.sh`). Your documents and settings remain.
- If it says something is missing and refuses to start, run `./launch.sh --setup` once, then start again.

---

### 5. Reinstalling

Two different situations, two different routes:

- **Rebuild only the environment** (it broke, or you want it fresh — your ingested documents and settings are kept):
  1. Remove the old environment: conda form → `conda env remove -n cynovela-dist`; in-folder form → delete the `.venv-cynovela` folder.
  2. Run `./launch.sh --setup`, then start as usual.
- **Reinstall from scratch** (everything goes, including ingested documents and settings):
  1. Run `bash uninstall.sh` (see section 6 — the folder goes to the Trash).
  2. Extract the downloaded archive again and do section 3 from the top.

---

### 6. Uninstalling

`bash uninstall.sh` — it confirms twice, then:

| It removes / stops | It does NOT touch |
|---|---|
| The running Cynovela started from this folder | conda itself (kept for your other uses) |
| The dedicated conda environment (`cynovela-dist`) | **Shared conda environments — never** |
| This folder, including ingested documents and settings (moved to the **Trash**, not deleted) | Anything whose name does not match |

Disk space returns only after you empty the Trash. You can restore from the Trash.

---

### 7. What each script is (the names alone do not tell you)

| File | What it does |
|---|---|
| `Cynovela-start.command` | **Starts it. Double-click.** |
| `Cynovela-stop.command` | **Stops it. Double-click.** |
| `Cynovela-add-folder.command` | **Adds a folder to be ingested. Double-click.** |
| `launch.sh` | **What the three above call internally. Use this one from the terminal.** |
| `uninstall.sh` | **Removes what this package created.** |

`launcher-core.sh` and `tools/launch-body.sh` are internal parts. You never need to touch them.

---

### 8. Before you rely on any of it, read these three points

- **This is for learning and experimentation.** It is not built to be a production system, and it comes with no warranty.
- **Masking is not complete.** Names, phone numbers and the like are masked automatically, but some slip through. Do not load confidential material on the assumption that it will be protected.
- **Answers can be wrong.** Always open the citation and check the original text before acting on an answer.

---

### 9. Open only when you need it

| File | What it covers (how it differs from the others) |
|---|---|
| `README.md` | What this tool is, what it can and cannot do, and the environment it runs in |
| `docs/HAJIMETE.md` | The gentlest walkthrough, from opening the package to the first answer (screen-first) |
| `docs/GETTING-STARTED.md` | The same first run in more detail, step by step, with what each step prints |
| `docs/quickstart.md` | The short version for people in a hurry (includes the manual, non-launcher route) |
| `docs/STARTUP.md` | Day-to-day start/stop, ports, sign-in, and what to do when it will not start |
| `docs/manual-complete.md` | The complete reference manual for every feature |
| `docs/operations.md` | Operating it over time: logs, backups, maintenance |
| `docs/deployment.md` | Deployment details behind the setup |
| `docs/SETUP-ACCELERATOR.md` | Setting up the external inference server (only if you want it) |
| `docs/USE-FROM-TERMINAL.txt` | Running it from the terminal instead of the icons (same as `./launch.sh --help`) |
| `docs/READ-BEFORE-DISTRIBUTING.md` | Read this before you pass the package on to anyone |
| `docs/NOTICE.md` | Before you start: no warranty, masking limits, checking answers |
| `docs/` | Further reference: how masking works, permissions, the API, and more |

---

# 日本語

**この文書が唯一の入口です。この文書だけで始められます。**
`docs/` 配下の他の文書は参照用です。必要になったときだけ開いてください（一覧は末尾）。

この配布物は **アプリ版（Mac の上で直に動く形。コンテナは使いません）** です。

---

### 1. どちらの配布物を落としましたか

```
1) パッケージ版（M系 Mac の方はこちら・すぐ使える形）
     展開して1行叩くだけで動きます。Python も conda も要りません。
     この Mac には何も入れません。消すときはフォルダごと削除します。
2) ソース版（上記以外の方、または自分で環境を作りたい方）
     起動時に、環境の作り方を2つから選びます:
       1) conda に専用の環境を作る（名前: cynovela-dist）
       2) この Mac の Python（3.12 以上）を使い、このフォルダの中だけに venv を作る
```

**AIモデルは別に落とします**（リリースページの別ファイル、または初回起動が取得を提案します）。どちらの配布物にも入っていません。

---

### 2. システム要件

| 項目 | 要件 |
|---|---|
| macOS | Apple シリコン搭載の Mac（M1 以降）。Intel の Mac・Windows・Linux では動作を確認していません。**パッケージ版は Apple シリコン専用です。** |
| Python | **3.12 以上**（`pyproject.toml` が `requires-python = ">=3.12"` を宣言。`environment.yml` は 3.12.13 を固定）。**3.10・3.11 は使えません。** パッケージ版と、ソース版の選択肢1（conda）では、事前の Python は不要です。 |
| conda | **Miniforge を推奨**（既定のチャネルが conda-forge のため）。**必須ではありません** — パッケージ版とソース版の選択肢2 は conda 無しで動きます。 |
| ディスクの空き | パッケージ版の展開後: **約 3.1 GB**（実測）。ソース版の展開後: 全部入り **約 5.2 GB**／モデル別取得版 **約 8 MB**（実測）。AIモデル: **4.84 GB**（パッケージ版とモデル別取得版は別に落とします。全部入りには入っています）。 |
| メモリ | 8 GB 以上を推奨（既存の記録による値。今回は測り直していません）。 |
| ネットワーク | パッケージ版: 動かすのに不要。AIモデルの取得時のみ必要。ソース版のセットアップは次から取り寄せます: conda-forge / PyPI / github.com（wheel 2本）/ huggingface.co（モデル）。 |
| 回答用の LLM | LM Studio もしくは OpenAI 互換 API（答えを作るには実 LLM が要ります）。 |

**起動シークエンスを使わずに手で入れる場合**（`./launch.sh` を使えないときのみ）: Python は **3.12 以上**をご自身で用意し、専用の環境を作り（conda なら名前 `cynovela-dist`、またはこのフォルダの中の venv。共有の環境は作らない・書き換えない）、その中で `pip install -r requirements.txt` を実行し、モデルを配置して `python server.py` で起動します。上の要件はそのまま適用されます。

---

### 3. セットアップと初回の起動

**パッケージ版:** 展開して、ターミナルで次の1行を叩きます。

```
./launch.sh
```

この Mac には何も入れません。フォルダの中に同梱された環境をそのまま使います。

**ソース版:** 展開して `./launch.sh` を叩きます（または `Cynovela-start.command` をダブルクリック）。初回に、環境の作り方（1節の2択）を聞かれ、作られます。**どちらを選んでも、共有の conda 環境は作りません・書き換えません。**

そのあとは:

1. **ログインする。** ユーザー名と最初のパスワードは、はじめて起動したときに画面に出ます。入るとすぐパスワードの変更を求められます。
2. **検索の対象を足す。** 起動したときに聞かれる画面で足す / アプリ画面の「設定」の「検索の対象フォルダを足す」から足す / ターミナルで `./launch.sh --add`（一覧は `./launch.sh --list`。アイコンなら `Cynovela-add-folder.command`）。
3. **質問する。** `http://localhost:8765` を開き、普通の言葉で聞きます。答えには必ず根拠にした箇所が付きます。開いて原文を確かめてください。
4. **止める。** `Cynovela-stop.command` をダブルクリックします（または `bash stop.sh`）。

---

### 4. 途中から起動し直すには（翌日・再起動のあと）

セットアップは最初の1回だけです。以後は:

- **起動:** `Cynovela-start.command` をダブルクリック（または `./launch.sh`）。環境はそのまま使われ、作り直しは起きません。
- **停止:** `Cynovela-stop.command` をダブルクリック（または `bash stop.sh`）。資料と設定はそのまま残ります。
- 「足りないものがあるので起動しません」と出たときは、`./launch.sh --setup` を1回実行してから、もう一度起動してください。

---

### 5. 再インストールするには

状況が2つ、道も2つあります。

- **環境だけ作り直す**（環境が壊れた・作り直したい。取り込んだ資料と設定は残ります）:
  1. 古い環境を消します。conda の形 → `conda env remove -n cynovela-dist`。フォルダ内の形 → `.venv-cynovela` フォルダを削除。
  2. `./launch.sh --setup` を実行し、あとは普段どおり起動します。
- **まっさらから入れ直す**（取り込んだ資料・設定も含めて全部消えます）:
  1. `bash uninstall.sh` を実行します（6節参照。フォルダはゴミ箱へ入ります）。
  2. 落とした配布物をもう一度展開し、3節を最初からやり直します。

---

### 6. 消すには

`bash uninstall.sh` — 2回確認したあと、次を行います。

| 消す・止めるもの | 触らないもの |
|---|---|
| このフォルダから起こした稼働中の Cynovela | conda そのもの（他の用途のため残します） |
| 専用の conda 環境（`cynovela-dist`） | **共有の conda 環境 — 決して消しません** |
| このフォルダ全体（取り込んだ資料・設定を含む。削除ではなく**ゴミ箱へ**） | 名前が一致しないもの |

ディスクの容量は、ゴミ箱を空にするまで戻りません。ゴミ箱から戻すこともできます。

---

### 7. スクリプトの名前の対応表（名前だけでは分からないため）

| ファイル | 何をするもの |
|---|---|
| `Cynovela-start.command` | **起動する。ダブルクリック** |
| `Cynovela-stop.command` | **止める。ダブルクリック** |
| `Cynovela-add-folder.command` | **読み込むフォルダを足す。ダブルクリック** |
| `launch.sh` | **上の3つが内側で呼んでいるもの。ターミナルから使うときはこれ** |
| `uninstall.sh` | **この配布物が作ったものを消す** |

`launcher-core.sh` と `tools/launch-body.sh` は内側の部品です。触る必要はありません。

---

### 8. 使う前に、次の3つをお読みください

- **これは学習と試用のためのものです。** 業務の本番システムとして使うことを想定して作られていません。無保証です。
- **マスキングは完全ではありません。** 氏名・電話番号などを自動で伏せますが、取りこぼしは起こります。伏せられることを前提に機密資料を入れないでください。
- **答えは間違うことがあります。** 必ず出典を開き、原文で確かめてからお使いください。

---

### 9. 必要になったときに開くもの

| ファイル | 何が書いてあるか（他とどう違うか） |
|---|---|
| `README.md` | このツールが何か・できること できないこと・動作環境 |
| `docs/HAJIMETE.md` | いちばんやさしいガイド。開いてから最初の答えが返るまで（画面中心） |
| `docs/GETTING-STARTED.md` | 同じ初回の道のりをより詳しく、順を追って。各段で画面に出るものつき |
| `docs/quickstart.md` | 急ぐ方向けの短い手順（launch.sh を使わない手動の道も含む） |
| `docs/STARTUP.md` | 日常の起動と停止・ポート・ログイン・起動しないときの対処 |
| `docs/manual-complete.md` | 全機能の完全マニュアル（リファレンス） |
| `docs/operations.md` | 使い続けるための運用: ログ・バックアップ・保守 |
| `docs/deployment.md` | セットアップの裏側にある導入の詳細 |
| `docs/SETUP-ACCELERATOR.md` | 外部の推論サーバの立て方（使いたいときだけ） |
| `docs/USE-FROM-TERMINAL.txt` | アイコンではなくターミナルから使う方法（`./launch.sh --help` と同一） |
| `docs/READ-BEFORE-DISTRIBUTING.md` | 誰かに配る前にお読みください |
| `docs/NOTICE.md` | 使う前のご注意。無保証・マスキングの限界・答えの確かめ方 |
| `docs/` | さらに参照用: マスキングの仕組み・権限・API など |
