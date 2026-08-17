# START HERE

**日本語版はこちら → [日本語](#日本語)**

## English

This package is the **container build (Docker, in-development beta)**.

1. **Start it.** Double-click `Cynovela-start.command`.
2. **Sign in.** The user name and the first password are printed on the screen
   when it starts for the first time. You will be asked to change the password
   straight away.
3. **Add search targets.** There are three ways:
   answer the question shown when it starts;
   use "Add a search folder" under "Settings" in the app screen;
   or run `./launch.sh --add` in the terminal (list them with
   `./launch.sh --list`; or double-click `Cynovela-add-folder.command`).
4. **Ask a question.** Open `http://localhost:8801` and type in plain
   language. Every answer carries the passage it came from — open it and check.
5. **Stop it.** Double-click `Cynovela-stop.command`.

**Before you rely on any of it, read these three points.**

- **This is for learning and experimentation.** It is not built to be a
  production system, and it comes with no warranty.
- **Masking is not complete.** Names, phone numbers and the like are masked
  automatically, but some slip through. Do not load confidential material on the
  assumption that it will be protected.
- **Answers can be wrong.** Always open the citation and check the original
  text before acting on an answer.

### If something goes wrong, or you want more detail

| File | What it covers |
|---|---|
| `docs/HAJIMETE.md` | The gentlest walkthrough, from opening it to the first answer |
| `docs/GETTING-STARTED.md` | The same ground in more detail, step by step |
| `docs/quickstart.md` | The short version for people in a hurry |
| `docs/STARTUP.md` | Start-up options, ports, sign-in, and what to do when it will not start |
| `docs/SETUP-ACCELERATOR.md` | Setting up the external inference server (only if you want it) |
| `docs/USE-FROM-TERMINAL.txt` | Running it from the terminal instead of the icons |
| `docs/READ-BEFORE-DISTRIBUTING.md` | Read this before you pass the package on to anyone |
| `docs/NOTICE.md` | Before you start: no warranty, masking limits, checking answers |
| `docs/` | Reference documents: how masking works, permissions, the API, and more |

---

# 日本語

この配布物は **コンテナ版 (Docker・開発中のベータ)** です。

1. **起動する。** `Cynovela-start.command` をダブルクリックします。
2. **ログインする。** ユーザー名と最初のパスワードは、はじめて起動したときに
   画面に出ます。入るとすぐパスワードの変更を求められます。
3. **検索の対象を追加する。** 足し方は3通りあります。
   起動したときに聞かれる画面で足す /
   アプリ画面の「設定」にある「検索の対象フォルダを足す」から足す /
   ターミナルで `./launch.sh --add` を使う (一覧は `./launch.sh --list`。
   アイコンなら `Cynovela-add-folder.command`)。
4. **質問する。** `http://localhost:8801` を開き、普通の言葉で聞きます。
   答えには必ず根拠にした箇所が付きます。開いて原文を確かめてください。
5. **止める。** `Cynovela-stop.command` をダブルクリックします。

**使う前に、次の3つをお読みください。**

- **これは学習と試用のためのものです。** 業務の本番システムとして使うことを
  想定して作られていません。無保証です。
- **マスキングは完全ではありません。** 氏名・電話番号などを自動で伏せますが、
  取りこぼしは起こります。伏せられることを前提に機密資料を入れないでください。
- **答えは間違うことがあります。** 必ず出典を開き、原文で確かめてから
  お使いください。

### うまくいかないとき・もっと詳しく知りたいとき

| ファイル | 何が書いてあるか |
|---|---|
| `docs/HAJIMETE.md` | いちばんやさしいガイド。開いてから最初の答えが返るまで |
| `docs/GETTING-STARTED.md` | 同じ範囲をより詳しく、順を追って |
| `docs/quickstart.md` | 急ぐ方向けの短い手順 |
| `docs/STARTUP.md` | 起動の形・ポート・ログイン・起動しないときの対処 |
| `docs/SETUP-ACCELERATOR.md` | 外部の推論サーバの立て方 (使いたいときだけ) |
| `docs/USE-FROM-TERMINAL.txt` | アイコンではなくターミナルから使う方法 |
| `docs/READ-BEFORE-DISTRIBUTING.md` | 誰かに配る前にお読みください |
| `docs/NOTICE.md` | 使う前のご注意。無保証・マスキングの限界・答えの確かめ方 |
| `docs/` | 参照用の資料。マスキングの仕組み・権限・API など |
