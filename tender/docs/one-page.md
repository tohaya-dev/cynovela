# Cynovela on one page / 1枚でわかる Cynovela

**日本語版はこちら → [日本語](#日本語)**

## English

> For business partners and study sessions; no technical background is assumed. Cynovela is a completely unofficial
> learning tool built by an individual. It is not a commercial product and does not represent any organization or product.

### What it is, and who it is for

Cynovela lets you ask questions about your own documents in plain language and get an answer together with the passages it was based on, while the documents stay on your own Mac. It is a small-scale model of that kind of system, built so that you can understand, by running it yourself, the problems that the AI tools it refers to try to solve. It is meant for personal use, small internal demos, and learning, and it is built with Japanese documents in mind. It looks at three problems:

- A general-purpose AI has not read your organization's rules, procedures or meeting minutes, so it cannot answer "what do our rules say about this?"
- Internal documents often contain personal information and trade secrets, and often must not be sent to an outside service.
- If names, email addresses or phone numbers remain in the search data, they can leak out through answers.

### How it works, from your side

1. **Put documents in.** You add a folder, and Cynovela finds the files inside it. (There is no upload button; documents are read from the folders you add.)
2. **Personal information is masked.** Email addresses, phone numbers and the like are replaced with a mark such as `[MASKED:EMAIL]` before the text is stored. What each person sees depends on their role: an administrator can see the original text, while a viewer sees the masked text.
3. **Ask in plain language.** Type your question on the screen in the browser.
4. **Get an answer with its sources.** Every answer carries numbered citations (`[1]`, `[2]`) pointing to the passage it came from. Open them and check.

### What stays on your Mac

- With the package edition, nothing is installed on the Mac. Cynovela is a folder you keep wherever you like, and everything it writes, documents and settings alike, stays inside it. To remove it, delete the folder.
- The model that turns documents into something searchable runs on the Mac itself.
- Sending anything to the outside happens only if someone deliberately changes the settings to do so.
- The original (unmasked) text is stored encrypted.
- When it starts, you can choose to limit it so that only your own Mac can reach it (see START-HERE).

### What it cannot do, and what to be careful about

- **It is for learning and experimentation, with no warranty.** It is not built to be a production system. Use it at your own risk.
- **Masking is not complete.** Some personal information will be missed. Do not load confidential material on the assumption that it will be masked, and always check the masking result yourself.
- **Answers can be wrong.** It may answer plausibly about things the documents do not say. Always open the citation and check the original text; do not use an answer as the basis for a decision.
- **Check the rights on the material you load**, and follow your organization's rules.
- **Some files cannot be read**, for example a scanned PDF that is only an image, old Office formats such as `.doc` and `.ppt`, and audio or video.

### What you need to try it

- An **Apple silicon Mac** (M1 or later). Intel Macs, Windows and Linux are not verified. 8 GB of memory or more is recommended.
- **Two downloads:** the package edition (about 830 MB) and the AI models (about 3.1 GB). Once unpacked they take about 3.1 GB and 4.84 GB. No Python and no conda are needed.
- **A separate language model that writes the answers.** Cynovela finds the passages; the sentences are written by a language model that runs outside it (by default, one on the same Mac), such as LM Studio or anything with an OpenAI-compatible endpoint. Set that up separately.
- On a company-managed Mac, double-click `check-managed-mac.command` first. It only checks whether the Mac will let you run it.

### Where to go next

| Open | What you get |
|---|---|
| [demo-general.html](demo-general.html) | A walkthrough in the browser, in 8 steps. Nothing needs to be running |
| [concept.md](concept.md) | What Cynovela is for, and how it differs from the AI tools it refers to |
| [getting-started.md](getting-started.md) | From the downloaded file to your first answer, nothing skipped |
| [INDEX.md](INDEX.md) | The list of every document, sorted by reader |

---

# 日本語

> パートナー勉強会など、技術者でない方向けの1枚です。技術の予備知識は要りません。
> Cynovela は個人が作った完全非公式の学習用ツールです。商用製品ではなく、企業・製品の公式見解を一切代表しません。

### これは何か、誰のためのものか

Cynovela は、手元の資料について普段の言葉で質問すると、答えを、その根拠になった箇所と一緒に返す道具です。資料は自分の Mac の中から出しません。参照元のAIツールが解こうとしている課題を、自分で動かして理解するために作った「縮小図」です。個人利用・小さな社内のお披露目・学習のためのもので、日本語の文書を想定して作っています。前提にしている問題は3つです。

- 汎用の AI は組織内の規程・手順・議事録を読んでいません。「うちの規程ではどうなっていますか」には答えられません。
- 組織内の文書は個人情報や営業秘密を含むことが多く、外部のサービスに送れないのが普通です。
- 氏名・メールアドレス・電話番号が検索用のデータに残ると、答えを通して漏れるおそれがあります。

### 使う側から見た流れ

1. **資料を入れる。** フォルダを追加すると、Cynovela がその中のファイルを見つけます（アップロードのボタンはありません。追加したフォルダから読みます）。
2. **個人情報をマスキングする。** メールアドレスや電話番号などは、保存する前に `[MASKED:EMAIL]` のような印に置き換えられます。見えるものは役割で変わり、管理者は原文を、閲覧者はマスキング後の文を見ます。
3. **普段の言葉で質問する。** ブラウザの画面に質問を打ち込みます。
4. **出典つきの答えを受け取る。** どの答えにも、元になった箇所を指す番号（`[1]`・`[2]`）が付きます。開いて確かめてください。

### Mac の中にとどまるもの

- パッケージ版なら、この Mac には何も入れません。Cynovela は好きな場所に置くフォルダで、書き込むもの（資料も設定も）はすべてそのフォルダの中に収まります。消すときはフォルダごと削除します。
- 資料を探せる形に変えるモデルは、その Mac の上で動きます。
- 外部への送信は、誰かが意図して設定を変えない限り起こりません。
- マスキング前の原文は暗号化して保存します。
- 起動のときに、自分の Mac からしか届かないように絞ることもできます（START-HERE を参照）。

### できないこと・気をつけること

- **学習と試用のためのもので、無保証です。** 本番システムとして使うことを想定して作られていません。自己の責任でお使いください。
- **マスキングは完全ではありません。** 取りこぼしは起こります。伏せられることを前提に機密資料を入れず、マスキングの結果は必ずご自身で確かめてください。
- **答えは間違うことがあります。** 資料に書かれていないことを、それらしく答える場合があります。必ず出典を開いて原文で確かめ、そのまま判断の根拠にしないでください。
- **入れる資料の権利はご自身でご確認ください。** 所属の規程に従ってください。
- **読めないファイルがあります。** たとえば画像として作られた（スキャンしただけの）PDF、`.doc`・`.ppt` のような古い Office 形式、音声や動画です。

### 試すのに要るもの

- **Apple シリコン搭載の Mac**（M1 以降）。Intel の Mac・Windows・Linux では動作を確認していません。メモリは 8 GB 以上を推奨します。
- **ダウンロードは2つ:** パッケージ版（約 830 MB）と AIモデル（約 3.1 GB）。展開後はそれぞれ約 3.1 GB と 4.84 GB です。Python も conda も要りません。
- **答えの文章を書く言語モデルを別に用意します。** Cynovela は根拠になる文を見つけるところまでを行い、文章そのものは外で動く言語モデル（既定では同じ Mac の上のもの）が書きます。LM Studio でも、OpenAI と同じ形の口を持つものでも構いません。
- 会社で管理されている Mac では、先に `check-managed-mac.command` をダブルクリックしてください。この Mac で動かせるかを測るだけです。

### 次に開くもの

| 開くもの | 何が得られるか |
|---|---|
| [demo-general.html](demo-general.html) | ブラウザで見て回る8ステップのページ。何も起動していなくても読めます |
| [concept.md](concept.md) | Cynovela が何のためのものか。参照元のAIツールとの違い |
| [getting-started.md](getting-started.md) | 落としたファイルから最初の答えまで。省略なし |
| [INDEX.md](INDEX.md) | すべての文書の一覧。読み手ごとに並べてあります |
