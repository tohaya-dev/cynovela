# Document index / 文書の索引

**日本語版はこちら → [日本語](#日本語)**

Every document that ships with Cynovela is listed on this page. If a document is not
linked from here, it does not exist.
Cynovela に同梱される文書は、すべてこのページに並んでいます。ここから辿れない文書はありません。

---

## English

The single entry document is [START-HERE.md](../START-HERE.md). This page is the map of
everything else.

### Where to start

| If this is you | Open |
|---|---|
| You have just downloaded it and want it running | [getting-started.md](getting-started.md) |
| You are still deciding which file to download | [editions.md](editions.md) |
| It is running and you want to try it on the bundled material | [handson.md](handson.md) |
| You are setting it up for other people to use | [operations.md](operations.md), then [security.md](security.md) |
| You want to know whether it can do a particular thing | [limits.md](limits.md), then [faq.md](faq.md) |
| You are looking up an endpoint, a command or a tool | the [Looking things up](#looking-things-up) section below |
| You are about to pass the package on to someone | [READ-BEFORE-DISTRIBUTING.md](READ-BEFORE-DISTRIBUTING.md) |

The three sections below are by reader, not by topic. A document appears in more than one
section when it is useful to more than one reader.

### Using it

For the person who asks it questions.

| Document | What is in it |
|---|---|
| [getting-started.md](getting-started.md) | From the downloaded file to your first answer. The route that needs nothing but the screen is written first; the terminal route is collected after it. Also covers signing in, changing the first password, adding an ingest root, and everyday start and stop. |
| [handson.md](handson.md) | Exercises run against the seven sample files in `dummy-corpus/`: questions one file answers, questions that span several files, questions the material cannot answer, and how the same material looks to an admin and to a viewer. |
| [concept.md](concept.md) | What Cynovela is for, the problems it was built around, what "local first" means here, and how it differs from the AI infrastructure tools it refers to. |
| [readme.md](readme.md) | A one-page summary of the main features and of the OSS stack they are built from. |
| [faq.md](faq.md) | Short answers to the questions asked most often: which file types can be read, how much machine you need, what happens to documents that contain personal information, and which features do not work. |
| [limits.md](limits.md) | What Cynovela cannot do: what masking misses, formats it cannot read, features that are only a skeleton, and the conditions under which sending to the outside stops. Read this before you rely on an answer. |
| [NOTICE.md](NOTICE.md) | The points to accept before you start: learning purpose, no warranty, masking is not complete, answers can be wrong, and checking the rights on the material you load. |
| [demo-general.html](demo-general.html) | An interactive walkthrough for a non-technical audience. Open it in a browser; nothing has to be running. |
| [demo-tech.html](demo-tech.html) | The same walkthrough for engineers, going down to the individual stages of the pipeline. |

### Installing and running it

For the person who puts it on a machine and keeps it going.

| Document | What is in it |
|---|---|
| [editions.md](editions.md) | Which of the four downloads to take, on one page: how many files each is, its size unpacked, whether Python or conda is needed, and whether the AI models are inside. |
| [getting-started.md](getting-started.md) | The first run itself: extracting, building the runtime environment, the model download question, the first sign-in, connecting the LLM, and adding the first ingest root. |
| [operations.md](operations.md) | Keeping it running over time: starting and stopping, where to place it, connecting an LLM provider, driving it from external tools over MCP, sharing over a LAN, backup and restore, logs, exporting the audit log, user management, health checks, notifications, and changing the port. |
| [security.md](security.md) | How access control and the guardrails are actually built: the three roles, how `access_level` and `allowed_roles` decide what a search returns, PII detection and masking, the layers against prompt injection, and the ways of use that are not recommended. |
| [USE-FROM-TERMINAL.txt](USE-FROM-TERMINAL.txt) | Plain text, meant to be read in a terminal. Every `./launch.sh` flag, identical to `./launch.sh --help`. |
| [BUNDLED-DATA.md](BUNDLED-DATA.md) | What the bundled sample material actually contains, counted when the package was built: how many files, chunks and parent chunks, and how many places were masked at ingest. |
| [READ-BEFORE-DISTRIBUTING.md](READ-BEFORE-DISTRIBUTING.md) | Read before you hand the package to anyone: which form of package it is, what starting with and without the demo does, that the bundled material is fictional, and what the receiving machine generates for itself at first startup. |
| [limits.md](limits.md) | The constraints that matter while installing: concurrent use, replacing models, and what is not wired up. |

### Looking things up

For the person who needs an exact name, argument or return value.

| Document | What is in it |
|---|---|
| [reference/api.md](reference/api.md) | Every HTTP endpoint the server answers, read out of the route declarations rather than written by hand, with the method, the path, what it takes and what it returns. |
| [reference/cli.md](reference/cli.md) | Every `cynovela-cli.py` command and every argument it accepts, where it reads the address and the `access_token` from, and what each exit code means. |
| [reference/mcp.md](reference/mcp.md) | All the MCP tools: what you hand each one and what comes back, plus which of them stay hidden until the corresponding environment switch is set. |
| [reference/changelog.md](reference/changelog.md) | What changed in each version, newest first. |
| [architecture.md](architecture.md) | How it works inside: the components, how ingest and classification work, how search works, how to read the scores a search returns, the shape of an answer, and the main categories of endpoint. The overview diagram is [assets/architecture-overview.svg](assets/architecture-overview.svg). |
| [faq.md](faq.md) | When you are not sure which of the four references above holds the answer, the last question of the FAQ says where to look next. |

---

# 日本語

唯一の入口は [START-HERE.md](../START-HERE.md) です。このページは、それ以外のすべての地図です。

### どれから読めばよいか

| こういう方 | 開くもの |
|---|---|
| 落としたばかりで、まず動かしたい | [getting-started.md](getting-started.md) |
| どのファイルを落とすかまだ決めていない | [editions.md](editions.md) |
| 動いたので、同梱の資料で試したい | [handson.md](handson.md) |
| 他の人に使ってもらうために据える | [operations.md](operations.md) → [security.md](security.md) |
| これができるかどうかを知りたい | [limits.md](limits.md) → [faq.md](faq.md) |
| 口・命令・道具の名前を引きたい | 下の[引く人](#引く人)の節 |
| この配布物を誰かに渡す | [READ-BEFORE-DISTRIBUTING.md](READ-BEFORE-DISTRIBUTING.md) |

下の3つの節は、話題ではなく読み手で分けてあります。複数の読み手に要るものは、複数の節に出てきます。

### 使う人

質問を投げる方へ。

| 文書 | 何が書いてあるか |
|---|---|
| [getting-started.md](getting-started.md) | 落としたファイルから最初の答えまで。画面だけで済む道を先に、ターミナルを使う道をその後ろにまとめてあります。ログイン・最初の合言葉の変更・ingest root の追加・毎日の起動と停止も含みます。 |
| [handson.md](handson.md) | `dummy-corpus/` の 7 本の資料を相手にする演習。1 本で答えられる問い・複数の資料をまたぐ問い・答えが無い問い、そして同じ資料が管理者と閲覧者にどう違って見えるか。 |
| [concept.md](concept.md) | Cynovela が何のためのものか、どんな問題を前提に作られたか、ここでいうローカルファーストとは何か、参照元の AI 基盤ツールと何が違うか。 |
| [readme.md](readme.md) | 主な機能と、それを組んでいる OSS スタックの 1 枚まとめ。 |
| [faq.md](faq.md) | よく聞かれることへの短い答え。読める形式・必要なマシンの大きさ・個人情報を含む資料の扱い・動かない機能。 |
| [limits.md](limits.md) | できないこと。マスキングの取りこぼし・読み込めない形式・骨組みだけの機能・外部への送出が止まる条件。答えを頼りにする前に読んでください。 |
| [NOTICE.md](NOTICE.md) | 使う前に受け入れていただく点。学習と試用のためのものであること・無保証・マスキングは完全ではないこと・答えは間違うことがあること・入れる資料の権利の確認。 |
| [demo-general.html](demo-general.html) | 技術者でない方向けの、対話式の見て回るページ。ブラウザで開くだけで、何も起動していなくても読めます。 |
| [demo-tech.html](demo-tech.html) | 同じものの技術者向け。パイプラインの各段まで降ります。 |

### 入れる人・回す人

マシンに据えて、動かし続ける方へ。

| 文書 | 何が書いてあるか |
|---|---|
| [editions.md](editions.md) | 4 つの落とし物のどれを選ぶか、1 枚で。何本あるか・展開後の大きさ・Python や conda が要るか・AIモデルが中に入っているか。 |
| [getting-started.md](getting-started.md) | 初回そのもの。展開・実行環境の作成・モデル取得の問い・最初のログイン・LLM の接続・最初の ingest root の追加。 |
| [operations.md](operations.md) | 使い続けるための運用。起動と停止・置き方・LLM プロバイダの接続・MCP で外部の道具から使う・LAN 共有・backup と restore・ログ・監査ログの Export・利用者の管理・死活確認・通知・番号の変更。 |
| [security.md](security.md) | アクセス制御とガードレールが実際にどう組まれているか。3 つの役割・`access_level` と `allowed_roles` が検索の返りをどう決めるか・PII の検出とマスキング・プロンプトインジェクションへの層・推奨しない使用方法。 |
| [USE-FROM-TERMINAL.txt](USE-FROM-TERMINAL.txt) | 端末で読むためのプレーンテキスト。`./launch.sh` のフラグの全数で、`./launch.sh --help` と同一の内容です。 |
| [BUNDLED-DATA.md](BUNDLED-DATA.md) | 同梱のサンプル資料に実際に何が入っているか。配布物を組んだときに数えた値で、file・chunk・parent chunk の数と、ingest のときに伏せた箇所の数。 |
| [READ-BEFORE-DISTRIBUTING.md](READ-BEFORE-DISTRIBUTING.md) | 誰かに渡す前に読むもの。どの形の配布物か・デモ付きと無しで起動が何が変わるか・同梱資料が架空であること・受け取った機械が初回起動時に自分で作るもの。 |
| [limits.md](limits.md) | 据えるときに効いてくる制約。同時に使うときの制約・モデルの差し替えの制約・配線されていないもの。 |

### 引く人

名前・引数・返り値を正確に引きたい方へ。

| 文書 | 何が書いてあるか |
|---|---|
| [reference/api.md](reference/api.md) | サーバが答える HTTP の口の全数。手で書いたものではなくルート宣言から起こしたもので、メソッド・パス・渡すもの・返るもの。 |
| [reference/cli.md](reference/cli.md) | `cynovela-cli.py` の命令と引数の全数。接続先と `access_token` をどこから読むか、終了コードの意味。 |
| [reference/mcp.md](reference/mcp.md) | MCP の道具の全数。何を渡すと何が返るか、どれが環境の切り替えを立てるまで現れないか。 |
| [reference/changelog.md](reference/changelog.md) | 版ごとの変更点。新しいものが上。 |
| [architecture.md](architecture.md) | 内側の作り。構成要素・取り込みと分類のしくみ・検索のしくみ・検索が返すスコアの読み方・回答のかたち・API の主要カテゴリ。全体図は [assets/architecture-overview.svg](assets/architecture-overview.svg) です。 |
| [faq.md](faq.md) | 上の 4 本のどれに答えがあるか分からないとき、FAQ の最後の問いが次に見る場所を示します。 |
