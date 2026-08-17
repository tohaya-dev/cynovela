# Cynovela のコンセプト

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool built by an individual to
> understand the concepts of AI infrastructure tools by working on them by hand.
> It is not a commercial product or an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

## The Problems Cynovela Solves

Cynovela is a learning implementation built to assemble and understand, by hand, a pipeline that connects in-house documents to an LLM "safely, reproducibly, and while leaving records." Concretely, it faces the following three problems.

**1. The LLM does not know knowledge specific to the organization**

A general-purpose LLM has not learned an organization's internal rules, procedures, or meeting minutes. To answer questions such as "what do our rules say about this?" or "what policy was decided at last week's meeting?", you need a RAG (Retrieval-Augmented Generation) mechanism that searches the related documents each time and passes them to the LLM as context.

**2. Confidential information cannot be sent to the cloud**

In-house documents often contain personal information and trade secrets, and it is normal that they cannot be sent to an external API. From the standpoint of data sovereignty, audit requirements, and compliance, document text, embedding generation, and LLM inference all have to be completed locally.

**3. You do not want to index documents that contain PII**

If raw personal information remains in the search index, there is a risk of unintended leakage through answers. You need a two-stage design that masks at ingest time to put the search index into a safe state (A-2 Tier1), and additionally passes answers through masking at answer time (A-2 Tier2).

## Design Principles

Cynovela's design follows the principles below.

**Local first**

In the default configuration the FastAPI server binds to `0.0.0.0` and can be reached from other terminals on the same network (original specification). To close it to your own machine only, specify `--local-only` explicitly. The IP allowlist middleware (A-5 §4) works only when `--allow-tailscale` / `--allow-subnet` is passed; when not specified, everything passes through. Embedding (BGE-M3 and so on) runs locally, and the LLM connects to a local inference server with an OpenAI-compatible /v1 API (`http://localhost:1234` by default).

**Two-stage PII protection**

At Tier1 (ingest time), the `raw` and `masked` lines are stored physically separated. The `chunks` table in SQLite gets rows with the `__masked` suffix, and ChromaDB gets two Collections, `{cid}__raw` / `{cid}__masked` (A-2 §6). Tier2 (answer time) is `_mask_for_viewer(text, user)`, which runs at 4 places in the chat response path and forcibly applies masking for anyone other than `admin` (A-2 §7). An administrator sees raw text pass through in the answer display, but when an external (non-local) LLM is used, crag-egress-guard prevents even an administrator's raw preview (context_preview) from being sent outside (locality is judged before sending, and the CRAG preview is skipped for non-local destinations).

**Provider abstraction**

The LLM, Embedding, VectorStore, Reranker, and Classifier layers can each be switched through an abstract base class (A-5 §3, A-6 §1). The defaults are LM Studio + BGE-M3 + ChromaDB + NoReranker + a rule-based classifier, but by editing `cynovela.yaml` you can replace them with other providers. Some of them, such as MLX / Qdrant / LanceDB / GraphRAG, are skeletons only (`NotImplementedError`) and are planned for future implementation.

**Audit logs are mandatory**

Important operations (creation and deletion of Source / Workspace / Collection, Publish, Chat, PII detection, prompt injection blocking, authentication failure) always go through `_log_audit(conn, action, target, detail)` and are recorded in the `audit_logs` table. Deletion and modification via the API are prohibited (CLAUDE.md design constraint).

**Three layers of prompt injection countermeasures**

`routers/chat.py` has a three-stage defense built in: (1) input inspection (14 English and Japanese patterns), (2) exclusion of poison chunks after retrieval, and (3) output inspection (the 4 patterns `HACKED` / `PWNED` / `SECRET-ALPHA-TOKEN` / `[SYSTEM OVERRIDE]`) (A-2 §9). On detection it blocks with HTTP 400 and records `PROMPT_INJECTION_BLOCKED` in the audit log. The principle of placing the system prompt "after" retrieved_content (CLAUDE.md security) is also there to prevent overwrite attacks by documents.

## Basis for the Independent Implementation

Cynovela does not refer to the implementation of the AI infrastructure tools it was inspired by, and there is no compatibility in source code, API specification, or data model. All design decisions are the individual's own responsibility.

**A configuration assembled from OSS only**:

| Part | Role |
|------|------|
| FastAPI + uvicorn | HTTP API server |
| SQLite | Metadata, audit logs, chunk text (foreign keys enabled, `INSERT OR REPLACE` prohibited) |
| ChromaDB | Vector store (two lines of Collections, raw / masked) |
| BGE-M3 | Multilingual embedding (default text mode) |
| BM25Okapi + fugashi/MeCab | Lexical search and Japanese morphological analysis |
| cryptography.fernet | Vault encryption (`enc:` prefix, idempotent) |
| presidio + GiNZA | Secondary path for PII detection (NER family) |
| Local LLM | OpenAI-compatible /v1 API (LM Studio and so on) |

No commercial features, support, or SLA are provided. All implementation decisions and trade-offs are the individual's own.

## What "Local First" Means

In Cynovela, "local first" means the following concrete behavior.

- **Data stays on the local disk**: SQLite and ChromaDB are created under `~/.cynovela/` by default (can be overridden with the `CYNOVELA_DB` / `CYNOVELA_CHROMA` environment variables, A-1 §5).
- **Embedding runs on the local CPU/GPU**: Nominally you can choose from BGE-M3 (default text mode), MiniLM (lite / lite-en modes), and TF-IDF (minimal mode) (A-1 §2), but switching to `lite` / `lite-en` / `minimal` is **not wired up**, and in practice BGE-M3 is used whichever one you specify. A preflight check runs at first startup and asks for confirmation before fetching not-yet-downloaded models from HuggingFace (with `CYNOVELA_NONINTERACTIVE=1` it stops immediately without a prompt, A-1 §6).
- **LLM inference goes through a local server**: `http://localhost:1234` (LM Studio) by default. With `--lmstudio-url` you can also connect to an OpenAI-compatible server on another machine, but explicit specification is required.
- **External transmission requires explicit configuration**: switching `reranker.provider` to `cohere` or similar, setting `execution.llm_provider` to `openrouter` / `claude_api`, adding `--lan` / `--allow-tailscale` — none of these happen unless the user changes them intentionally.

## Current Standing

Cynovela is a learning-purpose verification implementation at the  stage.

- **The core flow (Source registration → Scan → Workspace → Collection → Publish → RAG Chat) works**: a smoke test completes in about 2 seconds.
- **The test suite has 14 PHASEs / 405+ assertions**: it can be run all at once with `scripts/run_all_tests.sh`. It covers static analysis, extended APIs, GUI Playwright, security, consistency, CASCADE deletion, SSE error cases, chat error cases, scan error cases, embedding compatibility, DB migration, GUI recovery, and audit_log (CLAUDE.md).
- **Unimplemented features**: MLX Embedding / MLX Reranker / Qdrant VectorStore / LanceDB / GraphRAG are skeletons only (A-6 §1). The structured answer template is unimplemented, and the exclusion logic of `confidence_threshold` is only partially integrated (A-3 §6, §11). Authentication is enforced even when starting with `--demo` (the fixed token in the form `Bearer demo-token-<user_id>` was abolished on 2026-07-29).
- **Commercial use is out of scope**: this is a personal implementation for learning purposes. It does not represent the official position of the AI infrastructure tools it was inspired by.

---

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

## Cynovela が解く問題

Cynovela は、社内ドキュメントを LLM に「安全に・再現可能に・記録を残しながら」つなぐパイプラインを、自分の手で組み立てて理解するために作った学習用の実装です。具体的には次の 3 つの問題に向き合っています。

**1. 社内固有の知識を LLM が知らない**

汎用 LLM は社内の規程・手順・議事録を学習していません。「うちの規程ではどうなっていますか」「先週の会議で決まった方針は何ですか」といった問いに答えるには、関連文書を都度検索して文脈として LLM に渡す RAG（Retrieval-Augmented Generation: 検索拡張生成）の仕組みが必要です。

**2. 機密情報をクラウドに送れない**

社内文書は個人情報や営業秘密を含むことが多く、外部 API に送信できないケースが普通です。データ主権・監査要件・コンプライアンスの観点から、文書本文・Embedding 生成・LLM 推論のすべてをローカルで完結させる必要があります。

**3. PII を含む文書をインデックス化したくない**

検索インデックスに生の個人情報が残ると、回答経由で意図せず漏れるリスクがあります。取り込み時にマスクして検索インデックスを安全な状態にし（A-2 Tier1）、さらに回答時にもマスクを通す（A-2 Tier2）二段構えの設計が必要です。

## 設計思想

Cynovela の設計は次の原則に従っています。

**ローカルファースト**

既定構成では FastAPI サーバーが `0.0.0.0` にバインドされ、同じネットワークの他の端末から到達できます（元仕様）。自分のマシンの中だけに閉じるには `--local-only` を明示します。IP アローリストミドルウェア（A-5 §4）は `--allow-tailscale` / `--allow-subnet` を渡したときだけ働き、未指定のときは全通過します。Embedding（BGE-M3 等）はローカル実行、LLM は OpenAI 互換 /v1 API を持つローカル推論サーバー（既定 `http://localhost:1234`）に接続します。

**二段構えの PII 保護**

Tier1（取込時）で `raw` / `masked` の両系統を物理的に分離して保存します。SQLite の `chunks` テーブルは `__masked` サフィックス付きの行を、ChromaDB は `{cid}__raw` / `{cid}__masked` の 2 Collection を作ります（A-2 §6）。Tier2（回答時）は `_mask_for_viewer(text, user)` がチャット応答経路 4 箇所で動き、`admin` 以外には強制的にマスクを掛けます（A-2 §7）。admin は回答表示で raw を素通ししますが、外部（非ローカル）LLM を使う場合は crag-egress-guard により admin でも raw の下読み（context_preview）を外部へ送出しません（送信前にローカル判定し、非ローカル宛は CRAG 下読みをスキップ）。

**プロバイダー抽象化**

LLM・Embedding・VectorStore・Reranker・Classifier の各層は抽象基底クラスを介して切り替え可能です（A-5 §3、A-6 §1）。既定は LM Studio + BGE-M3 + ChromaDB + NoReranker + ルールベース分類器ですが、`cynovela.yaml` を編集することで他のプロバイダーへ差し替えられます。MLX / Qdrant / LanceDB / GraphRAG など一部は骨格のみ（`NotImplementedError`）で、将来実装予定です。

**監査ログを必須に**

重要操作（Source / Workspace / Collection の作成・削除、Publish、Chat、PII 検出、プロンプトインジェクション遮断、認証失敗）は必ず `_log_audit(conn, action, target, detail)` を通り、`audit_logs` テーブルに記録されます。API 経由での削除・変更は禁止されています（CLAUDE.md 設計制約）。

**3 層のプロンプトインジェクション対策**

`routers/chat.py` には、(1) 入力検査（英日 14 パターン）、(2) retrieval 後の poison chunk 除外、(3) 出力検査（`HACKED` / `PWNED` / `SECRET-ALPHA-TOKEN` / `[SYSTEM OVERRIDE]` の 4 パターン）の 3 段防御が組み込まれています（A-2 §9）。検出時は HTTP 400 で遮断し、`PROMPT_INJECTION_BLOCKED` を監査ログに記録します。システムプロンプトを retrieved_content の「後」に配置する原則（CLAUDE.md セキュリティ）も、文書による上書き攻撃を防ぐためのものです。

## 独自実装の根拠

Cynovela は参照元の AI 基盤ツールの実装を参照しておらず、ソースコード・API 仕様・データモデルに互換性はありません。すべての設計判断は個人の責任です。

**OSS だけで組み立てた構成**:

| 部品 | 役割 |
|------|------|
| FastAPI + uvicorn | HTTP API サーバー |
| SQLite | メタデータ・監査ログ・チャンク本文（外部キー有効、`INSERT OR REPLACE` 禁止） |
| ChromaDB | ベクター ストア（raw / masked の二系統 Collection） |
| BGE-M3 | 多言語 Embedding（既定 text モード） |
| BM25Okapi + fugashi/MeCab | 語彙的検索と日本語形態素解析 |
| cryptography.fernet | 保管庫暗号化（`enc:` プレフィックス、冪等） |
| presidio + GiNZA | PII 検出の二次経路（NER 系） |
| ローカル LLM | OpenAI 互換 /v1 API（LM Studio など） |

商用機能・サポート・SLA は提供しません。実装の判断・トレードオフはすべて個人によるものです。

## ローカルファーストの意味

「ローカルファースト」は、Cynovela において次の具体的な動作を意味します。

- **データはローカル ディスクに留まる**: SQLite と ChromaDB は既定で `~/.cynovela/` 配下に作られます（`CYNOVELA_DB` / `CYNOVELA_CHROMA` 環境変数で上書き可、A-1 §5）。
- **Embedding はローカル CPU/GPU で実行**: 名目上は BGE-M3（既定 text モード）、MiniLM（lite / lite-en モード）、TF-IDF（minimal モード）から選択できます（A-1 §2）が、`lite` / `lite-en` / `minimal` への切替は**未配線**で、実際にはどの指定でも BGE-M3 が使われます。初回起動時に preflight チェックが走り、未ダウンロード モデルは HuggingFace からの取得を確認します（`CYNOVELA_NONINTERACTIVE=1` で対話なし即停止、A-1 §6）。
- **LLM 推論はローカル サーバー経由**: 既定 `http://localhost:1234`（LM Studio）。`--lmstudio-url` で別マシン上の OpenAI 互換サーバーにも繋げますが、明示指定が必要。
- **外部送信は明示設定が必要**: `reranker.provider` を `cohere` 等に切り替える、`execution.llm_provider` を `openrouter` / `claude_api` にする、`--lan` / `--allow-tailscale` を付ける——いずれもユーザーが意図的に変更しない限り発生しません。

## 現在の位置づけ

Cynovela は  段階の学習用検証実装です。

- **コア フロー（Source 登録 → Scan → Workspace → Collection → Publish → RAG Chat）は動作**: スモークテストで 2 秒程度で完了します。
- **テスト スイートは 14 PHASE / 405+ アサーション**: `scripts/run_all_tests.sh` で一括実行可能。静的解析・拡張 API・GUI Playwright・セキュリティ・整合性・CASCADE 削除・SSE 異常系・チャット異常系・スキャン異常系・Embedding 互換・DB マイグレーション・GUI 回復・audit_log を網羅（CLAUDE.md）。
- **未実装機能**: MLX Embedding / MLX Reranker / Qdrant VectorStore / LanceDB / GraphRAG は骨格のみ（A-6 §1）。構造化回答テンプレートは未実装、`confidence_threshold` の除外ロジックは部分統合（A-3 §6, §11）。認証は `--demo` 起動でも強制されます（`Bearer demo-token-<user_id>` 形式の固定トークンは 2026-07-29 に廃止）。
- **商用利用は想定外**: 学習目的の個人実装です。参照元の AI 基盤ツールの公式見解を代表しません。

---
