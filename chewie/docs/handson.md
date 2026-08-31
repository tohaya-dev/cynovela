# ハンズオン / Hands-on

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual to
> understand the concepts of AI infrastructure tools by actually running them.
> It is not a commercial offering and not an official implementation.
> The implementation is entirely original, and consists of an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any organization.

This document is a set of exercises you run against the sample material that ships
inside this package. You ask real questions, look at the answers, and check them
against the file the answer actually came from.

Every exercise below uses only the seven files under `dummy-corpus/`. They describe a
fictional firm; the people, organizations, addresses, phone numbers, and mail
addresses in them do not exist.

---

**Contents**

- [1. Getting ready](#1-getting-ready)
- [2. What is inside the sample material](#2-what-is-inside-the-sample-material)
- [3. Exercise A — questions one file can answer](#3-exercise-a--questions-one-file-can-answer)
- [4. Exercise B — questions that span more than one file](#4-exercise-b--questions-that-span-more-than-one-file)
- [5. Exercise C — questions the material does not answer](#5-exercise-c--questions-the-material-does-not-answer)
- [6. Exercise D — how the same material looks to different roles](#6-exercise-d--how-the-same-material-looks-to-different-roles)
- [7. Exercise E — ingest and publish material of your own](#7-exercise-e--ingest-and-publish-material-of-your-own)
- [8. Questions and expected answers](#8-questions-and-expected-answers)
  - [(a) Answerable from a single file](#a-answerable-from-a-single-file)
  - [(b) Needs two or more files](#b-needs-two-or-more-files)
  - [(c) Not written anywhere](#c-not-written-anywhere)

## 1. Getting ready

The exercises assume Cynovela is already running with the bundled demo data.

- For how to start it, see [getting-started.md](getting-started.md).
- Start with the demo data, open `http://127.0.0.1:8765` in a browser, and log in.
  The user names and passwords are the ones described in
  [getting-started.md](getting-started.md).
- On a demo start, one workspace holding the bundled sample material is present, and
  one source named `src-dummy` pointing at the ingest root `./dummy-corpus` is already
  registered. The collection under it is already published, so you can ask questions
  right away.

Two things are worth turning on before you begin.

- In RAG Chat, the display mode can be switched between **Standard** (`normal`),
  **Explain** (`explain`), and **Developer** (`developer`). In `developer` you can see
  the vector score / BM25 score / hybrid score of each chunk. Exercises A to C are
  much easier to read in `developer`.
- The audit log screen (admin only) shows what the server recorded for each question.
  Exercises C and D end by looking at it.

How to read the scores. The vector score is a cosine similarity against the
Embedding model that Cynovela uses by default (`BAAI/bge-m3`, BGE-M3).

| Score band | Interpretation |
|---|---|
| 0.35 to 0.45 | Noise floor. Appears even for an unrelated question |
| 0.40 | The effective default of the confidence threshold (`confidence_threshold`) |
| 0.55 to 0.75 | The usual band for a question the material really answers |
| 0.75 and above | Very strongly related |

For the search itself (hybrid of vector and BM25, RRF, MMR, and the rest), see
[architecture.md](architecture.md) §4 "How search works".

---

## 2. What is inside the sample material

`dummy-corpus/` holds seven files. Knowing what is in which file is the whole point
of the exercises: you can check every answer against the source yourself.

| File | What it is | Used in |
|---|---|---|
| `00-はじめに.md` | A short guide to the other six files | Exercise A (as an orientation, not as an answer source) |
| `01-company-overview.md` | Profile of the firm: outline, product categories, locations, history, management | Exercises A, B, C |
| `02-work-rules.md` | Work rules (excerpt): working hours, holidays, leave, pay, expenses | Exercises A, B, C |
| `03-system-guide.md` | Operating guide for the internal inventory system: login, goods receipt, stocktaking, monthly closing | Exercises A, B, D |
| `04-faq.md` | 20 internal questions and answers, summarizing the three files above | Exercises A, B |
| `05-meeting-notes.md` | Minutes of three monthly meetings (May, June, July 2026) | Exercises B, C |
| `06-company-overview-en.md` | The firm's profile in English | Exercises A, B, C |

Note that `04-faq.md` restates content that also lives in `01`, `02`, and `03`. That
overlap is deliberate: it is what makes the citation list in the answer interesting
to look at.

---

## 3. Exercise A — questions one file can answer

**What you are checking**: that a question whose answer sits in a single file is
answered from that file, and that the citation points at it.

Ask these in RAG Chat, one at a time.

1. 就業時間は何時から何時までですか
2. 年次有給休暇は何日もらえますか
3. 有給休暇はいつまでに届け出ればよいですか
4. 従業員は何名ですか
5. 支社はどこにありますか
6. 給与の支払日はいつですか
7. 在庫台帳のログインに何回失敗するとロックされますか
8. 入庫登録はいつまでに行いますか

And in English, against `06-company-overview-en.md`:

9. How many employees does the firm have, and when was it founded?
10. What are the four product categories?
11. When was the Fukuoka branch opened?

**How to check**: the expected answer and the place it comes from are in the table in
section 8. Open the file named there and compare. In `developer` mode, the top chunk
for these questions usually lands in the 0.55 to 0.75 band.

A thing worth noticing: for questions 1 to 8 the citation list often contains **two**
files — the original one and `04-faq.md`, which restates it. That is the hybrid search
finding both, not a mistake.

---

## 4. Exercise B — questions that span more than one file

**What you are checking**: that a question no single file answers is still answered,
by pulling chunks out of several files at once.

1. 在庫台帳の月次締めと経費精算の締めは同じものですか。それぞれいつ行いますか
2. 差異報告の登録漏れが問題になったのはどの支社ですか。差異報告の正しい手順も教えてください
3. 社長は誰ですか。2026年6月の会議には出席しましたか
4. 「アオゾラ在庫台帳」はいつ導入され、その月次締めは毎月何日ですか
5. 季節雑貨はどの棚に保管しますか。2026年7月の会議では季節雑貨について何が報告されましたか
6. 経費精算の締めについて、規則の定めと、会議で出た運用上の課題を教えてください

And one in English, deliberately asked against material that is mostly Japanese:

7. Which branch offices does the firm have, and which branch had the most errors in the pre-closing check?

**How to check**: for each of these, the table in section 8 names **two or more**
files. Confirm that the citation list contains more than one file. Question 7 is the
interesting one: the branch list is in the English file, but the error counts exist
only in the Japanese minutes, so an answer that covers both had to cross the language
boundary. BGE-M3 is a multilingual Embedding model, which is why this can work at all.

Question 1 is the trap the sample material was built around. Two different closing
dates exist on purpose — the inventory monthly closing on the 25th and the expense
closing at month end. An answer that merges them into one is wrong, and you can see
it is wrong by opening the two files.

---

## 5. Exercise C — questions the material does not answer

**What you are checking**: what comes back when the material simply does not contain
the answer. This is the exercise that matters most.

1. 退職金はいくら支払われますか
2. 名古屋支社の住所を教えてください
3. アオゾラ商事の株価はいくらですか
4. 2026年8月の月次業務改善会議の決定事項を教えてください

And in English:

5. What is the retail price of the cooling goods?
6. Who is the president of Aozora Trading's largest supplier?

**How the current build behaves**: search still returns chunks for these questions —
something is always the nearest neighbour. What the build does is look at the highest
**vector** score among them, and compare it with `confidence_threshold`, whose
effective default is **0.40**. When the highest score falls below that threshold, the
LLM is not called at all; instead a low-confidence reply is returned, saying that no
reliable answer was found and naming the score and the threshold, together with a few
suggested rephrasings built from the headings of the chunks that were found. The
server also records a `LOW_CONFIDENCE_FALLBACK` entry in the audit log.

So the reply you get is not the LLM guessing. It is the pipeline declining to guess.

**How to check**:

1. Ask one of the six questions above in `developer` mode and read the top score.
2. Open the audit log screen as `admin` and look for the `LOW_CONFIDENCE_FALLBACK`
   entry for that question. The detail line carries the score and the threshold.
3. Verify the claim yourself: `grep -i 退職 dummy-corpus/*.md` and the equivalent for
   the other five return nothing. The words are genuinely absent from all seven files.

Do not expect this to fire every single time. Whether a given question lands above or
below 0.40 depends on the wording, and a question that is *near* the material (for
example asking about parental leave, when the work rules do mention leave for a
spouse giving birth) can score high enough to be answered from the closest thing
present. The six above were chosen because the subject matter is absent outright.

---

## 6. Exercise D — how the same material looks to different roles

**What you are checking**: that the role you logged in with changes both which vault
is searched and what the answer is allowed to show.

The effective roles that the database holds are the two values `admin` and `viewer`.
Names such as `curator` are normalized to `viewer`.

| Role | Vault searched | Exit mask on the answer |
|---|---|---|
| `admin` | raw (the original text) | Not applied |
| `viewer` | masked | Applied |

The sample material contains contact details on purpose, which is what makes this
exercise possible without preparing anything:

- `01-company-overview.md` — two mail addresses in "5. 経営体制とお問い合わせ"
- `03-system-guide.md` — a phone number, a mail address, and an IPv4 address in
  "情報システム担当の連絡先"
- `05-meeting-notes.md` — mail addresses inside two of the decisions

**Steps**:

1. Log in as `admin` and ask 情報システム担当の連絡先を教えてください. The phone
   number, the mail address, and the IP address appear as written.
2. Log out, log in as `viewer`, and ask exactly the same question. The same fields
   come back as `[MASKED:PHONE]`, `[MASKED:EMAIL]`, `[MASKED:IP]`.
3. Ask 会社案内の問い合わせ先を教えてください under both roles and compare in the same way.
4. Still as `viewer`, try to open the audit log screen. It is rejected with
   403 Forbidden — the admin-only endpoints are closed to `viewer` outright, not
   merely hidden in the GUI.
5. Go back to `admin`, open the audit log, and find the `pii_detected` entries left by
   the questions you just asked.

For what is detected and how the two tiers of masking work, see
[security.md](security.md) §5 "PII detection and masking". For the permissions of each role, see
[security.md](security.md) §3 "Roles and permissions".

**Going further — workspace boundaries**: a collection lives under a workspace, and a
user sees only the collections of the workspaces they belong to. Create a second
workspace, put a user in one but not the other, and confirm from the collection list
that the visible set differs. Note that in ChromaDB this boundary is a logical one by
collection name; a physical boundary is not implemented. See
[limits.md](limits.md).

---

## 7. Exercise E — ingest and publish material of your own

**What you are checking**: the path a file takes from disk to being answerable —
ingest root → source → scan → file → collection → publish → chunk.

1. Create a workspace, and pick one of the seed guardrail policies for it
   (`pol-pii`, `pol-strict`, `pol-log`). The differences are in
   [security.md](security.md) §4 "Guardrails".
2. Add an ingest root and register it as a source, or reuse the existing `src-dummy`
   source, which points at `./dummy-corpus`.
3. Run a scan on the source. The files under the root are enumerated and appear as
   file rows.
4. Create a collection under the workspace and link the files you want into it.
5. Press publish. Each file is split into chunks, each chunk is embedded, and both a
   raw and a masked copy are written. When it finishes, the collection turns `ready`.
6. Open the file list and look at the category and the confidence assigned to each
   file. The classification runs at ingest time and sorts each document into one of
   the fourteen categories — you should see `meeting_minutes` for `05-meeting-notes.md`
   and `faq` for `04-faq.md`. For the categories and the three classification engines,
   see [architecture.md](architecture.md) §3 "How ingest and classification work".
7. Ask a question from exercise A against your own collection and confirm you get the
   same answer as from the demo collection.

**A worthwhile variation**: write a small text file of your own containing a mail
address and a phone number, publish it, and then run exercise D against it. You will
see the masking applied to text you wrote yourself.

**Before you throw the workspace away**: take an Export of the collection, or a Full
Export, and try an Import into a fresh collection. Together with backup and restore,
that is the round trip described in [operations.md](operations.md).

---

## 8. Questions and expected answers

Every question used above, with the answer and the exact place the answer is written.
Each entry was checked by reading the file.

### (a) Answerable from a single file

| Question | Expected answer | Where the answer is |
|---|---|---|
| 就業時間は何時から何時までですか | 始業 9:00、終業 18:00。休憩は 60 分で、原則 12:00 から 13:00 の間に取る | `02-work-rules.md`, 第2章 第4条（勤務時間） |
| 年次有給休暇は何日もらえますか | 勤続 1 年以上に年間 20 日。入社初年度は入社 6 か月経過時点で 10 日、以後段階的に増加 | `02-work-rules.md`, 第3章 第8条（年次有給休暇） |
| 有給休暇はいつまでに届け出ればよいですか | 原則、取得日の 3 営業日前までに所属長へ届け出る | `02-work-rules.md`, 第8条 第3項（`04-faq.md` Q8 にも同内容） |
| 従業員は何名ですか | 142 名（2026年4月1日現在） | `01-company-overview.md`, 「1. 会社概要」（`04-faq.md` Q3、`06-company-overview-en.md` にも同内容） |
| 支社はどこにありますか | 大阪支社と福岡支社の 2 か所 | `01-company-overview.md`, 「1. 会社概要」および「3. 拠点」 |
| 給与の支払日はいつですか | 毎月末日締め、翌月 25 日に指定口座へ支払う | `02-work-rules.md`, 第5章 第14条（給与の支払） |
| 在庫台帳のログインに何回失敗するとロックされますか | 5 回連続で失敗するとロック。解除は情報システム担当に依頼する | `03-system-guide.md`, 「2. ログイン手順」の 5 |
| 入庫登録はいつまでに行いますか | 商品が到着した当日中が原則。できない事情があれば所属長に報告のうえ翌営業日の午前中 | `03-system-guide.md`, 「3. 入庫登録の手順」冒頭と「入庫登録の注意事項」 |
| How many employees does the firm have, and when was it founded? | 142 employees as of April 1, 2026; founded in April 1998 | `06-company-overview-en.md`, "1. About Us" |
| What are the four product categories? | Kitchenware / Bath and Toiletries / Storage and Organization / Seasonal Goods | `06-company-overview-en.md`, "2. Product Categories" |
| When was the Fukuoka branch opened? | 2012, as the sales base for the Kyushu region | `06-company-overview-en.md`, "3. Locations" and "4. History" |

### (b) Needs two or more files

| Question | Expected answer | Where the answer is |
|---|---|---|
| 在庫台帳の月次締めと経費精算の締めは同じものですか。それぞれいつ行いますか | 別のもの。在庫台帳の月次締めは毎月 25 日（25 日が休日なら直前の営業日）、経費精算は月末締め・翌月 15 日払い | `03-system-guide.md` 「5. 月次締めの手順」＋ `02-work-rules.md` 第15条（経費精算）。`04-faq.md` Q20 にも要約 |
| 差異報告の登録漏れが問題になったのはどの支社ですか。差異報告の正しい手順も教えてください | 大阪支社（5 月度のエラー 5 件のうち 4 件）。手順は、再確認しても差異が解消しない場合に「差異報告」画面から登録し所属長の確認を受ける | `05-meeting-notes.md` 「議事録2」討議内容 ＋ `03-system-guide.md` 「4. 棚卸しの手順」の 6 |
| 社長は誰ですか。2026年6月の会議には出席しましたか | 代表取締役社長は山田花子。6 月 11 日の会議は出張のため欠席 | `01-company-overview.md` 「5. 経営体制とお問い合わせ」＋ `05-meeting-notes.md` 「議事録2」出席者・欠席 |
| 「アオゾラ在庫台帳」はいつ導入され、その月次締めは毎月何日ですか | 2020 年に導入。月次締めは毎月 25 日 | `01-company-overview.md` 「4. 沿革」（英語なら `06-company-overview-en.md` "4. History"）＋ `03-system-guide.md` 「5. 月次締めの手順」 |
| 季節雑貨はどの棚に保管しますか。2026年7月の会議では季節雑貨について何が報告されましたか | 保管は S で始まる専用棚で、通常棚と混在させない。7 月の会議では夏物の出荷が好調で冷感グッズの一部に欠品、追加発注済みで 7 月下旬に入庫予定と報告 | `03-system-guide.md` 「入庫登録の注意事項」＋ `05-meeting-notes.md` 「議事録3」討議内容 |
| 経費精算の締めについて、規則の定めと、会議で出た運用上の課題を教えてください | 規則は月末締め・翌月 15 日払いで、締め日を過ぎた申請は翌月分として処理。課題は締め日直前に申請が集中して経理の確認作業が逼迫していることで、営業部門へ都度申請を依頼することにした | `02-work-rules.md` 第15条 ＋ `05-meeting-notes.md` 「議事録2」討議内容・決定事項 2 |
| Which branch offices does the firm have, and which branch had the most errors in the pre-closing check? | Osaka and Fukuoka. The Fukuoka branch had 12 errors at the April closing; of the 5 errors in May, 4 were at the Osaka branch | `06-company-overview-en.md` "3. Locations" (English) + `05-meeting-notes.md` 「議事録1」「議事録2」(Japanese) — the answer has to cross the language boundary |

### (c) Not written anywhere

For these, the build is expected to return a low-confidence reply rather than to
answer, because the highest vector score falls below the `confidence_threshold` of
0.40 and the LLM is therefore not called.

| Question | Expected answer | Why nothing answers it |
|---|---|---|
| 退職金はいくら支払われますか | Cannot be answered from the material | `02-work-rules.md` is an excerpt running from 第1条 to 第18条 plus 附則, and none of them covers 退職金. The word does not appear in any of the seven files |
| 名古屋支社の住所を教えてください | Cannot be answered from the material | The branch offices are Osaka and Fukuoka only (`01-company-overview.md` 「3. 拠点」). 名古屋 appears nowhere in the seven files |
| アオゾラ商事の株価はいくらですか | Cannot be answered from the material | Nothing about listing or share price exists; `01-company-overview.md` gives revenue and headcount but no capital-market information |
| 2026年8月の月次業務改善会議の決定事項を教えてください | Cannot be answered from the material | `05-meeting-notes.md` holds exactly three sets of minutes — May, June, and July 2026. There is no August record |
| What is the retail price of the cooling goods? | Cannot be answered from the material | Cooling goods appear in `01-company-overview.md`, `06-company-overview-en.md`, and `05-meeting-notes.md`, but no price is given anywhere |
| Who is the president of Aozora Trading's largest supplier? | Cannot be answered from the material | `06-company-overview-en.md` states that the firm sources from approximately 320 suppliers, but no supplier is named and no supplier's management is described |

---

---

# 日本語

> **この文書について**
> Cynovela は、AI 基盤ツールの考え方を実際に動かして理解するために個人が作った、
> 完全に非公式の学習用ツールです。商用のものでも公式の実装でもありません。
> 実装はすべて独自で、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカル LLM という
> OSS のスタックで構成されています。いかなる企業の公式見解も表しません。

この文書は、この配布物に同梱されているサンプル資料を相手に、実際に手を動かして
確かめるための演習集です。実際に質問し、返ってきた答えを見て、その答えがどのファイル
から来たのかを自分で突き合わせます。

以下の演習は、すべて `dummy-corpus/` の 7 本のファイルだけを使います。7 本は架空の
企業を題材にしたもので、登場する人物・組織・住所・電話番号・メールアドレスは
すべて実在しません。

---

**目次**

- [1. 準備](#1-準備)
- [2. サンプル資料には何が入っているか](#2-サンプル資料には何が入っているか)
- [3. 演習A: 1 本で答えられる問い](#3-演習a-1-本で答えられる問い)
- [4. 演習B: 複数の文書をまたぐ問い](#4-演習b-複数の文書をまたぐ問い)
- [5. 演習C: 答えが無い問い](#5-演習c-答えが無い問い)
- [6. 演習D: 役割による見え方の違い](#6-演習d-役割による見え方の違い)
- [7. 演習E: 自分の資料を取り込んで publish する](#7-演習e-自分の資料を取り込んで-publish-する)
- [8. 設問と正解の対応表](#8-設問と正解の対応表)
  - [(a) 1 本で答えられるもの](#a-1-本で答えられるもの)
  - [(b) 2 本以上をまたぐもの](#b-2-本以上をまたぐもの)
  - [(c) どこにも書いていないもの](#c-どこにも書いていないもの)

## 1. 準備

演習は、同梱のデモデータで Cynovela が動いていることを前提にします。

- 起動のしかたは [getting-started.md](getting-started.md) を見てください。
- デモデータで起動し、ブラウザで `http://127.0.0.1:8765` を開いてログインします。
  ユーザー名とパスワードは [getting-started.md](getting-started.md) に書いてあるものです。
- デモ起動では、同梱のサンプル資料が入った workspace が 1 件入っており、ingest root
  `./dummy-corpus` を指す source が `src-dummy` という名前で最初から登録されています。
  その下の collection は publish 済みなので、そのまま質問を試せます。

始める前に、2 つだけ入れておくとよいものがあります。

- RAG Chat の表示モードは、**標準**（`normal`）・**解説**（`explain`）・**開発者**
  （`developer`）に切り替えられます。`developer` にすると、各 chunk のベクタースコア /
  BM25 スコア / ハイブリッドスコアが見えます。演習 A から C は `developer` のほうが
  格段に読みやすくなります。
- 監査ログの画面（`admin` のみ）には、質問ごとにサーバが記録した内容が並びます。
  演習 C と D は、最後にここを見て終わります。

スコアの読み方です。ベクタースコアは、Cynovela が既定で使う Embedding モデル
（`BAAI/bge-m3`、BGE-M3）に対するコサイン類似度です。

| スコア帯 | 意味 |
|---|---|
| 0.35〜0.45 | ノイズ床。関係のない質問でもこのあたりは出る |
| 0.40 | 信頼度しきい値（`confidence_threshold`）の実効既定値 |
| 0.55〜0.75 | 資料が本当に答えを持っている質問で通常出る帯 |
| 0.75 以上 | 非常に強く関連している |

検索そのもの（ベクターと BM25 のハイブリッド、RRF、MMR など）については
[architecture.md](architecture.md) §4「検索のしくみ」 を見てください。

---

## 2. サンプル資料には何が入っているか

`dummy-corpus/` には 7 本のファイルが入っています。どのファイルに何が書いてあるかを
把握しておくことが演習の要です。そうすれば、返ってきた答えを自分で突き合わせられます。

| ファイル | 内容 | 使う演習 |
|---|---|---|
| `00-はじめに.md` | 残り 6 本の案内 | 演習 A（案内としてのみ。答えの出どころには使わない） |
| `01-company-overview.md` | 会社案内。概要・取扱品目・拠点・沿革・経営体制 | 演習 A・B・C |
| `02-work-rules.md` | 就業規則（抜粋）。勤務時間・休日・休暇・給与・経費 | 演習 A・B・C |
| `03-system-guide.md` | 組織内の在庫システムの利用手順。ログイン・入庫・棚卸し・月次締め | 演習 A・B・D |
| `04-faq.md` | 組織内からの 20 問。上の 3 本の内容を要約したもの | 演習 A・B |
| `05-meeting-notes.md` | 2026 年 5 月・6 月・7 月の定例会議 3 本の議事録 | 演習 B・C |
| `06-company-overview-en.md` | 会社案内の英語版 | 演習 A・B・C |

`04-faq.md` は `01` `02` `03` にもある内容を言い直しています。この重なりは意図的な
もので、答えに付く出典の一覧を見るときに面白くなるのはそのためです。

---

## 3. 演習A: 1 本で答えられる問い

**何を確かめるか**: 答えが 1 本のファイルの中にある質問が、そのファイルから答えられ、
出典がそのファイルを指すこと。

RAG Chat で 1 問ずつ聞いてみてください。

1. 就業時間は何時から何時までですか
2. 年次有給休暇は何日もらえますか
3. 有給休暇はいつまでに届け出ればよいですか
4. 従業員は何名ですか
5. 支社はどこにありますか
6. 給与の支払日はいつですか
7. 在庫台帳のログインに何回失敗するとロックされますか
8. 入庫登録はいつまでに行いますか

英語では、`06-company-overview-en.md` を相手にこう聞きます。

9. How many employees does the firm have, and when was it founded?
10. What are the four product categories?
11. When was the Fukuoka branch opened?

**確かめかた**: 期待される答えと、その答えが書かれている場所は 8 節の表にあります。
そこに書かれたファイルを開いて突き合わせてください。`developer` モードで見ると、
これらの質問の最上位 chunk はたいてい 0.55〜0.75 の帯に入ります。

見ておくとよいところ。1〜8 の質問では、出典の一覧に**2 本**のファイルが並ぶことが
よくあります。元のファイルと、それを言い直している `04-faq.md` です。これは
ハイブリッド検索が両方を見つけているということで、誤りではありません。

---

## 4. 演習B: 複数の文書をまたぐ問い

**何を確かめるか**: 1 本だけでは答えられない質問でも、複数のファイルから同時に
chunk を引いてきて答えられること。

1. 在庫台帳の月次締めと経費精算の締めは同じものですか。それぞれいつ行いますか
2. 差異報告の登録漏れが問題になったのはどの支社ですか。差異報告の正しい手順も教えてください
3. 社長は誰ですか。2026年6月の会議には出席しましたか
4. 「アオゾラ在庫台帳」はいつ導入され、その月次締めは毎月何日ですか
5. 季節雑貨はどの棚に保管しますか。2026年7月の会議では季節雑貨について何が報告されましたか
6. 経費精算の締めについて、規則の定めと、会議で出た運用上の課題を教えてください

もう 1 問は英語です。相手にする資料はほとんど日本語であるのに、あえて英語で聞きます。

7. Which branch offices does the firm have, and which branch had the most errors in the pre-closing check?

**確かめかた**: どの質問についても、8 節の表は**2 本以上**のファイルを挙げています。
出典の一覧に 2 本以上並ぶことを確認してください。7 番目が面白いところです。支社の
一覧は英語のファイルにありますが、エラーの件数は日本語の議事録にしかないので、
両方を含む答えは言語の境をまたいだことになります。BGE-M3 が多言語の Embedding
モデルであることが、これが成立しうる理由です。

1 番目は、このサンプル資料がそのために作られた罠です。締め日が 2 つ、意図的に
書き分けられています。在庫の月次締めは毎月 25 日、経費精算の締めは月末です。
この 2 つを 1 つに混ぜた答えは誤りであり、2 本のファイルを開けば誤りだと分かります。

---

## 5. 演習C: 答えが無い問い

**何を確かめるか**: 資料が答えを持っていないとき、何が返ってくるか。これがいちばん
大事な演習です。

1. 退職金はいくら支払われますか
2. 名古屋支社の住所を教えてください
3. アオゾラ商事の株価はいくらですか
4. 2026年8月の月次業務改善会議の決定事項を教えてください

英語では次の 2 問です。

5. What is the retail price of the cooling goods?
6. Who is the president of Aozora Trading's largest supplier?

**現在の作り**: これらの質問でも検索は chunk を返します。いちばん近いものは必ず
存在するからです。この作りがやっていることは、その中で最も高い**ベクター**スコアを
見て、`confidence_threshold`（実効の既定値は **0.40**）と比べることです。最も高い
スコアがしきい値を下回ると、LLM はそもそも呼ばれません。代わりに低信頼の返しが
返り、確かな答えが見つからなかったこと、そのスコアとしきい値、そして見つかった
chunk の見出しから作った言い換えの候補がいくつか示されます。サーバは監査ログに
`LOW_CONFIDENCE_FALLBACK` の記録も残します。

つまり返ってくるのは、LLM が当てずっぽうで答えた結果ではありません。パイプラインが
当てずっぽうの回答を避けた結果です。

**確かめかた**:

1. 上の 6 問のどれかを `developer` モードで聞き、最上位のスコアを読む。
2. `admin` で監査ログの画面を開き、その質問の `LOW_CONFIDENCE_FALLBACK` の記録を
   探す。詳細の行にスコアとしきい値が入っています。
3. 主張そのものを自分で検証する。`grep -i 退職 dummy-corpus/*.md` は何も返しません。
   残る 5 問も同様で、これらの語は 7 本のどこにも本当に存在しません。

毎回必ずこうなると考えないでください。ある質問が 0.40 の上に出るか下に出るかは
言い回しに左右されますし、資料の*近く*にある質問（たとえば育児休業について聞くと、
就業規則には配偶者の出産に伴う特別休暇の定めがある）は、いちばん近いものから
答えられる程度に高いスコアを取ることがあります。上の 6 問は、題材そのものが
まったく存在しないという理由で選んであります。

---

## 6. 演習D: 役割による見え方の違い

**何を確かめるか**: ログインした役割によって、検索する保管庫と、答えに出してよい
ものの両方が変わること。

データベースが保持する実効の役割は `admin` と `viewer` の 2 値です。`curator` の
ような名前は `viewer` に正規化されます。

| 役割 | 検索する保管庫 | 答えへの出口マスク |
|---|---|---|
| `admin` | raw（原文） | 適用しない |
| `viewer` | masked | 適用する |

サンプル資料には、意図的に連絡先が入れてあります。だからこの演習は何も準備せずに
始められます。

- `01-company-overview.md` —「5. 経営体制とお問い合わせ」にメールアドレスが 2 件
- `03-system-guide.md` —「情報システム担当の連絡先」に電話番号・メールアドレス・
  IPv4 アドレス
- `05-meeting-notes.md` — 決定事項 2 か所の中にメールアドレス

**手順**:

1. `admin` でログインし、情報システム担当の連絡先を教えてください と聞く。電話番号・
   メールアドレス・IP アドレスが書かれたとおりに出ます。
2. ログアウトして `viewer` でログインし、まったく同じ質問をする。同じ箇所が
   `[MASKED:PHONE]` `[MASKED:EMAIL]` `[MASKED:IP]` になって返ります。
3. 会社案内の問い合わせ先を教えてください を両方の役割で聞き、同じように比べる。
4. `viewer` のまま、監査ログの画面を開こうとする。403 Forbidden で拒否されます。
   `admin` 専用の口は `viewer` に対して端から閉じており、画面上で隠しているだけでは
   ありません。
5. `admin` に戻って監査ログを開き、いま聞いた質問が残した `pii_detected` の記録を
   見つける。

何が検出され、2 段のマスキングがどう働くかは [security.md](security.md) §5「PII の検出とマスキング」 を、
役割ごとの権限は [security.md](security.md) §3「役割と権限」 を見てください。

**発展 — workspace の境界**: collection は workspace の下にあり、利用者は自分が
属する workspace の collection しか見えません。もう 1 つ workspace を作り、片方だけに
利用者を入れて、collection の一覧で見える範囲が変わることを確かめてください。なお
ChromaDB におけるこの境界は collection 名による論理的なもので、物理的な境界は
実装されていません。[limits.md](limits.md) を見てください。

---

## 7. 演習E: 自分の資料を取り込んで publish する

**何を確かめるか**: ファイルがディスクから「質問に答えられる状態」へ至るまでの道筋。
ingest root → source → scan → file → collection → publish → chunk です。

1. workspace を作り、シードのガードレール方針から 1 つを選ぶ（`pol-pii`・`pol-strict`・
   `pol-log`）。違いは [security.md](security.md) §4「ガードレール」 にあります。
2. ingest root を足して source として登録するか、`./dummy-corpus` を指す既存の
   `src-dummy` の source をそのまま使う。
3. source に対して scan を走らせる。root の下のファイルが数え上げられ、file の行として
   並びます。
4. workspace の下に collection を作り、入れたい file を結び付ける。
5. publish を押す。各 file が chunk に分割され、各 chunk が埋め込まれ、raw と masked の
   両方の写しが書かれます。終わると collection は `ready` になります。
6. file の一覧を開き、各 file に付いた分類と確信度を見る。分類は取り込みのときに走り、
   各文書を 14 の分類のどれかに振り分けます。`05-meeting-notes.md` には
   `meeting_minutes`、`04-faq.md` には `faq` が付くはずです。分類と 3 種類の分類エンジンに
   ついては [architecture.md](architecture.md) §3「取り込みと分類のしくみ」 を見てください。
7. 演習 A の質問を自分の collection に対して聞き、デモの collection と同じ答えが返る
   ことを確かめる。

**やってみる価値のある変え方**: メールアドレスと電話番号を含む小さなテキストファイルを
自分で書いて publish し、それに対して演習 D をやってみてください。自分で書いた文章に
マスキングが掛かるのが見えます。

**workspace を捨てる前に**: その collection の Export、あるいは Full Export を取り、
空の collection への Import を試してください。backup と restore と合わせて、
[operations.md](operations.md) に書かれている一巡りになります。

---

## 8. 設問と正解の対応表

上で使った質問の全数と、その答え、そして答えが書かれている正確な場所です。各項目は
実際にファイルを読んで確かめてあります。

### (a) 1 本で答えられるもの

| 設問 | 期待される答え | 答えの所在 |
|---|---|---|
| 就業時間は何時から何時までですか | 始業 9:00、終業 18:00。休憩は 60 分で、原則 12:00 から 13:00 の間に取る | `02-work-rules.md` 第2章 第4条（勤務時間） |
| 年次有給休暇は何日もらえますか | 勤続 1 年以上に年間 20 日。入社初年度は入社 6 か月経過時点で 10 日、以後段階的に増加 | `02-work-rules.md` 第3章 第8条（年次有給休暇） |
| 有給休暇はいつまでに届け出ればよいですか | 原則、取得日の 3 営業日前までに所属長へ届け出る | `02-work-rules.md` 第8条 第3項（`04-faq.md` Q8 にも同内容） |
| 従業員は何名ですか | 142 名（2026年4月1日現在） | `01-company-overview.md`「1. 会社概要」（`04-faq.md` Q3、`06-company-overview-en.md` にも同内容） |
| 支社はどこにありますか | 大阪支社と福岡支社の 2 か所 | `01-company-overview.md`「1. 会社概要」および「3. 拠点」 |
| 給与の支払日はいつですか | 毎月末日締め、翌月 25 日に指定口座へ支払う | `02-work-rules.md` 第5章 第14条（給与の支払） |
| 在庫台帳のログインに何回失敗するとロックされますか | 5 回連続で失敗するとロック。解除は情報システム担当に依頼する | `03-system-guide.md`「2. ログイン手順」の 5 |
| 入庫登録はいつまでに行いますか | 商品が到着した当日中が原則。できない事情があれば所属長に報告のうえ翌営業日の午前中 | `03-system-guide.md`「3. 入庫登録の手順」冒頭と「入庫登録の注意事項」 |
| How many employees does the firm have, and when was it founded? | 142 employees as of April 1, 2026; founded in April 1998 | `06-company-overview-en.md` "1. About Us" |
| What are the four product categories? | Kitchenware / Bath and Toiletries / Storage and Organization / Seasonal Goods | `06-company-overview-en.md` "2. Product Categories" |
| When was the Fukuoka branch opened? | 2012 年、九州エリアの営業拠点として開設 | `06-company-overview-en.md` "3. Locations" および "4. History" |

### (b) 2 本以上をまたぐもの

| 設問 | 期待される答え | 答えの所在 |
|---|---|---|
| 在庫台帳の月次締めと経費精算の締めは同じものですか。それぞれいつ行いますか | 別のもの。在庫台帳の月次締めは毎月 25 日（25 日が休日なら直前の営業日）、経費精算は月末締め・翌月 15 日払い | `03-system-guide.md`「5. 月次締めの手順」＋ `02-work-rules.md` 第15条（経費精算）。`04-faq.md` Q20 にも要約 |
| 差異報告の登録漏れが問題になったのはどの支社ですか。差異報告の正しい手順も教えてください | 大阪支社（5 月度のエラー 5 件のうち 4 件）。手順は、再確認しても差異が解消しない場合に「差異報告」画面から登録し所属長の確認を受ける | `05-meeting-notes.md`「議事録2」討議内容 ＋ `03-system-guide.md`「4. 棚卸しの手順」の 6 |
| 社長は誰ですか。2026年6月の会議には出席しましたか | 代表取締役社長は山田花子。6 月 11 日の会議は出張のため欠席 | `01-company-overview.md`「5. 経営体制とお問い合わせ」＋ `05-meeting-notes.md`「議事録2」出席者・欠席 |
| 「アオゾラ在庫台帳」はいつ導入され、その月次締めは毎月何日ですか | 2020 年に導入。月次締めは毎月 25 日 | `01-company-overview.md`「4. 沿革」（英語なら `06-company-overview-en.md` "4. History"）＋ `03-system-guide.md`「5. 月次締めの手順」 |
| 季節雑貨はどの棚に保管しますか。2026年7月の会議では季節雑貨について何が報告されましたか | 保管は S で始まる専用棚で、通常棚と混在させない。7 月の会議では夏物の出荷が好調で冷感グッズの一部に欠品、追加発注済みで 7 月下旬に入庫予定と報告 | `03-system-guide.md`「入庫登録の注意事項」＋ `05-meeting-notes.md`「議事録3」討議内容 |
| 経費精算の締めについて、規則の定めと、会議で出た運用上の課題を教えてください | 規則は月末締め・翌月 15 日払いで、締め日を過ぎた申請は翌月分として処理。課題は締め日直前に申請が集中して経理の確認作業が逼迫していることで、営業部門へ都度申請を依頼することにした | `02-work-rules.md` 第15条 ＋ `05-meeting-notes.md`「議事録2」討議内容・決定事項 2 |
| Which branch offices does the firm have, and which branch had the most errors in the pre-closing check? | 大阪と福岡。福岡支社は 4 月度の締めで 12 件、5 月度の 5 件のうち 4 件は大阪支社 | `06-company-overview-en.md` "3. Locations"（英語）＋ `05-meeting-notes.md`「議事録1」「議事録2」（日本語）。答えは言語の境をまたぐ |

### (c) どこにも書いていないもの

これらでは、最も高いベクタースコアが `confidence_threshold` の 0.40 を下回るため
LLM は呼ばれず、答えるのではなく低信頼の返しが返ることを期待します。

| 設問 | 期待される答え | なぜどこにも無いのか |
|---|---|---|
| 退職金はいくら支払われますか | 資料からは答えられない | `02-work-rules.md` は第1条から第18条と附則までの抜粋で、退職金を扱う条文が無い。この語は 7 本のどこにも現れない |
| 名古屋支社の住所を教えてください | 資料からは答えられない | 支社は大阪と福岡の 2 か所だけ（`01-company-overview.md`「3. 拠点」）。名古屋は 7 本のどこにも現れない |
| アオゾラ商事の株価はいくらですか | 資料からは答えられない | 上場や株価に関する記述が無い。`01-company-overview.md` に年商と従業員数はあるが資本市場の情報は無い |
| 2026年8月の月次業務改善会議の決定事項を教えてください | 資料からは答えられない | `05-meeting-notes.md` に入っている議事録は 2026 年 5 月・6 月・7 月のちょうど 3 本。8 月の記録は無い |
| What is the retail price of the cooling goods? | 資料からは答えられない | 冷感グッズは `01-company-overview.md`・`06-company-overview-en.md`・`05-meeting-notes.md` に出てくるが、価格はどこにも書かれていない |
| Who is the president of Aozora Trading's largest supplier? | 資料からは答えられない | `06-company-overview-en.md` は仕入先が約 320 社であると述べるだけで、個々の社名も、その経営陣も書かれていない |
