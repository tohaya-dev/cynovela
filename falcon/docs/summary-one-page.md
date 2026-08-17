# Cynovela 概要（1ページ版）

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool built by an individual to
> understand the concepts of AI infrastructure tools by working on them by hand.
> It is not a commercial product or an official implementation.
> The implementation is entirely original, and is built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

## Core Message

Cynovela is a learning-purpose verification implementation that keeps a RAG (Retrieval-Augmented Generation) pipeline for in-house documents entirely within a local environment. The whole flow — document ingest, PII (personal information) detection, vector search, and answer generation by a local LLM — is built from OSS parts only. Its purpose is to understand, by running it yourself, the problems that the referenced AI infrastructure tools try to solve.

## Problems It Solves

1. **In-house documents do not reach the LLM's context**
   A general-purpose LLM does not know in-house terms, rules, or operating procedures. Having a person copy and paste a summary by hand every time they ask a question is not realistic.
2. **Documents cannot be sent to the cloud**
   Sending in-house documents that contain confidential information to an external API creates constraints from the standpoint of data sovereignty, audit requirements, and compliance. A RAG that runs fully locally is needed.
3. **You do not want documents containing PII to go into the search index as they are**
   If personal names, email addresses, phone numbers and the like are indexed without masking, there is a risk of leakage through answers. A two-stage design is needed: masking at ingest time (Tier1) and masking at answer time (Tier2).

## How It Works (3 Steps)

1. **Register a Source → Scan**
   When you register a local directory as a Source, the target files are detected recursively and registered in the `files` table. Because a deterministic file_id derived from the path is used even on a re-scan, the impact on existing Collections is minimized.
2. **Workspace → Collection → Publish**
   Under a Workspace (the unit of permission and policy management) you create a Collection (a set of files plus a chunking strategy), and at Publish time the documents are split into chunks, embedded, and loaded into ChromaDB. At the same time PII is detected, and both lines, `tier="raw"` and `tier="masked"`, are generated.
3. **RAG Chat**
   For a user's question, related chunks are retrieved by a hybrid of BM25 and vector search (RRF: Reciprocal Rank Fusion by default), and passed as context to the local LLM to generate an answer. Citation numbers, a low-confidence fallback, prompt injection countermeasures, and output-time masking are built in.

## List of OSS Parts

| Part | Role |
|------|------|
| **FastAPI** | The HTTP API server itself (started with uvicorn) |
| **SQLite** | Persistence of metadata, audit logs, and chunk text (foreign keys enabled) |
| **ChromaDB** | Vector store (creates two lines of Collections, raw / masked) |
| **BGE-M3** | Multilingual embedding model (the default text mode) |
| **Local LLM** | To avoid the external transmission that the referenced AI infrastructure tools assume, a local inference server with an OpenAI-compatible /v1 API is used |

As supporting parts, BM25Okapi (keyword search), fugashi/MeCab (Japanese morphological analysis), cryptography.fernet (vault encryption), and presidio + GiNZA (the secondary path for PII detection) are used.

## Disclaimer

Cynovela is a personal implementation for learning purposes; commercial use and production use are not assumed. It does not represent the official position of the referenced AI infrastructure tools, and it contains no company or product names. All implementation decisions and design trade-offs are the individual's own.

---
Last updated: 2026-05-26 / Alpha GA edition

---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

## 核心メッセージ

Cynovela は、社内ドキュメントを対象とした RAG（Retrieval-Augmented Generation: 検索拡張生成）パイプラインを、すべてローカル環境で完結させる学習用の検証実装です。文書の取り込み、PII（個人情報）検出、ベクター検索、ローカル LLM による回答生成までの一連の流れを、OSS 部品のみで構築しました。参照元の AI 基盤ツールが解こうとしている課題を、自分の手で動かして理解することを目的としています。

## 解決する問題

1. **社内ドキュメントが LLM の文脈に届かない**
   汎用 LLM は社内固有の用語・規程・運用手順を知りません。質問するたびに人間が手で要約をコピー＆ペーストするのは現実的ではありません。
2. **クラウドに文書を送信できない**
   機密情報を含む社内文書を外部 API に送ると、データ主権・監査要件・コンプライアンスの観点で制約が生じます。完全ローカルで動く RAG が必要です。
3. **PII を含む文書をそのまま検索インデックスに乗せたくない**
   個人名・メールアドレス・電話番号などをマスクしないままインデックス化すると、回答経由で漏れるリスクがあります。取り込み時のマスク（Tier1）と回答時のマスク（Tier2）の二段構えが必要です。

## 動き方（3ステップ）

1. **Source 登録 → Scan**
   ローカルディレクトリを Source として登録すると、対象ファイルを再帰的に検出して `files` テーブルに登録します。再スキャンしてもパス由来の決定論的 file_id を使うため、既存 Collection への影響を最小化します。
2. **Workspace → Collection → Publish**
   Workspace（権限・ポリシー管理単位）の下に Collection（ファイル群＋チャンク戦略）を作成し、Publish 時に文書をチャンク分割・Embedding 化して ChromaDB に投入します。同時に PII を検出し、`tier="raw"` と `tier="masked"` の両系統を生成します。
3. **RAG Chat**
   ユーザーの質問に対し、BM25 とベクター検索のハイブリッド（既定は RRF: 相互順位融合）で関連チャンクを取得し、ローカル LLM に文脈として渡して回答を生成します。引用番号・低信頼度フォールバック・プロンプトインジェクション対策・出力時マスクが組み込まれています。

## OSS 部品一覧

| 部品 | 役割 |
|------|------|
| **FastAPI** | HTTP API サーバー本体（uvicorn で起動） |
| **SQLite** | メタデータ・監査ログ・チャンク本文の永続化（外部キー有効） |
| **ChromaDB** | ベクター ストア（raw / masked の二系統 Collection を作成） |
| **BGE-M3** | 多言語対応の Embedding（埋め込み）モデル（既定の text モード） |
| **ローカル LLM** | 参照元の AI 基盤ツールが想定する外部送信を避けるため、OpenAI 互換 /v1 API を持つローカル推論サーバーを利用 |

補助部品として、BM25Okapi（キーワード検索）、fugashi/MeCab（日本語形態素解析）、cryptography.fernet（保管庫暗号化）、presidio + GiNZA（PII 検出の二次経路）を利用します。

## 免責

Cynovela は学習目的の個人実装であり、商用利用・本番利用は想定していません。参照元の AI 基盤ツールの公式見解を代表せず、会社・製品名も含みません。実装の判断・設計上のトレードオフはすべて個人によるものです。

---
最終更新: 2026-05-26 / Alpha GA 対応版
