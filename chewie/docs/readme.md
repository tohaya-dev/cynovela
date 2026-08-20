# Cynovela

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built by an individual in order to
> understand the concepts of AI infrastructure tools hands-on. It is not a commercial
> product and not an official implementation.
> The implementation is entirely original, and is made of an OSS stack:
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela is a completely unofficial learning tool, created so that an individual can understand the concepts of AI infrastructure tools by working on them hands-on.

---

## 1. Project overview

It is designed so that you can experience "what it is actually like to build one" for features such as the following, which the AI infrastructure tool it refers to provides.

- Data governance (guardrails, PII detection, audit log)
- Data ingest (automatic classification, metadata extraction, difference sync)
- RAG (Retrieval-Augmented Generation) pipeline (hybrid search, Reranker, Multi-Query, CRAG, HyDE)
- Role-based access control (RBAC)
- MCP (Model Context Protocol) integration

The implementation is entirely original and contains no source code of the referenced tool. It is built with OSS only.

---

## 2. Main features

### 2-1. Data ingest (Smart Ingestion)

- Automatic classification into 14 document categories (governance policy, incident report, technical guide, meeting minutes, audit report, and so on)
- 3 classification engines (lightweight rule-based, local LLM, hybrid)
- Automatic tracking of sources by hash difference sync

### 2-2. Guardrails and PII detection

- Detection of 8 PII (personal information) patterns (email, phone, credit card, My Number, IP address, and so on)
- Exit masking by dual-tier storage (raw / masked)
- Protection of the raw text by Fernet encryption
- 3 layers of prompt injection countermeasures

### 2-3. RAG pipeline

- Hybrid merge of BM25 and vector search (RRF or weighted)
- Vector embeddings by BAAI/bge-m3
- Reranker (supports several, including CrossEncoder, FlashRank and Ollama)
- Advanced search features including Multi-Query, CRAG, HyDE, MMR and Parent-Child chunking
- Answer style per role (admin / reader)

### 2-4. RBAC and auditing

- 3 roles (admin / curator / viewer)
- Recording of important operations into the audit_logs table
- Tampering with the audit log via the API is prohibited

### 2-5. External integration

- LM Studio / Ollama / OpenAI-compatible API connection
- MCP server (25 tools; 22 visible by default — 3 admin tools appear only when CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 is set)
- LAN sharing and Tailscale sharing

---

## 3. Technology stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Persistence | SQLite |
| Vector store | ChromaDB |
| Embedding model | BAAI/bge-m3 (default), paraphrase-multilingual-MiniLM-L12-v2, paraphrase-MiniLM-L3-v2, TF-IDF |
| Reranker | BAAI/bge-reranker-v2-m3, CrossEncoder, FlashRank, Ollama |
| LLM | LM Studio, Ollama, OpenAI-compatible API, mock |
| Encryption | cryptography (Fernet) |
| PII detection | Regular expressions, GiNZA NER, Presidio |
| Integration protocol | MCP (Model Context Protocol) |

---

## 4. Quick start

### 4-1. Recommended environment

- macOS (Apple Silicon recommended), Linux, Windows
- Python 3.10 or later
- A conda environment (recommended environment name: `cynovela`)

### 4-2. Starting in demo mode

```bash
python server.py --demo
```

- `--demo`: starts using the demo database `store/db/demo.db` and the index `store/vector/demo/chroma`. Without it, the production `store/db/cynovela.db` and `store/vector/default/chroma` are used. Neither one disappears on restart.

Open `http://127.0.0.1:8765` in a browser and the UI is shown.

### 4-3. Starting in real LLM mode

Start LM Studio, enable its OpenAI-compatible API, and then run the following.

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

### 4-4. Startup modes

`--mode` accepts text / lite / lite-en (the switching is not wired up, so only the displayed name changes).

| mode | Purpose | Required model |
|---|---|---|
| `text` | All text RAG features (default) | BAAI/bge-m3 |
| `lite` | Switching is **not wired up** = actually BAAI/bge-m3 (behaves the same as text; only the displayed name changes) | — |
| `lite-en` | Switching is **not wired up** = actually BAAI/bge-m3 (behaves the same as text; only the displayed name changes) | — |

---

## 5. Document list

The following documents are placed under the `docs/` directory.

| Document | Contents |
|---|---|
| `quickstart.md` | The shortest procedure for startup and initial setup |
| `manual-complete.md` | A single manual covering all features |
| `llm-connection.md` | Details of the LLM connection (LM Studio / Ollama / OpenAI-compatible) |
| `mcp-guide.md` | MCP server integration and the list of exposed tools |
| `lan-sharing.md` | Startup procedure for LAN sharing and Tailscale sharing |
| `security-policy.md` | Known limitations and usage that is not recommended |
| `changelog.md` | Release history |
| `demo-general.html` | Interactive demo for a general audience (just open it in a browser) |
| `demo-tech.html` | Interactive demo for engineers |

---

## 6. License

The implementation code is written on the premise that it will be published as OSS. When you use it, respect the licenses of each dependency library (FastAPI, ChromaDB, BAAI/bge-m3, and so on).

It contains none of the source code, trademarks, logos or official documentation of the AI infrastructure tool it refers to.

---

## 7. Disclaimer

- This tool was created for an individual's learning and verification purposes.
- Business use and production operation are not assumed.
- It does not represent the official position of the referenced company or product.
- The behavior of features, the API and the data structures may change without notice.

---


---

# 日本語

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

Cynovela は、AI 基盤ツールのコンセプトを個人が手を動かして理解するために作成した、完全非公式の学習用ツールです。

---

## 1. プロジェクト概要

参照元の AI 基盤ツールが提供する以下のような機能について、「実際に作るとどうなるか」を体験するために設計されています。

- データガバナンス（ガードレール、PII 検出、監査ログ）
- データ取り込み（自動分類、メタデータ抽出、差分同期）
- RAG（検索拡張生成）パイプライン（ハイブリッド検索、Reranker、Multi-Query、CRAG、HyDE）
- ロールベースアクセス制御（RBAC）
- MCP（Model Context Protocol）連携

実装はすべてオリジナルで、参照元のソースコードは一切含みません。OSS のみで構築されています。

---

## 2. 主な機能

### 2-1. データ取り込み（Smart Ingestion）

- 14 種類のドキュメントカテゴリへの自動分類（ガバナンス・ポリシー、インシデントレポート、技術ガイド、議事録、監査報告書 など）
- 3 種類の分類エンジン（軽量ルールベース、ローカル LLM、ハイブリッド）
- ハッシュ差分同期によるソースの自動追跡

### 2-2. ガードレール・PII 検出

- 8 種類の PII（個人情報）パターン検出（メール、電話、クレジットカード、マイナンバー、IP アドレス 等）
- Dual-tier 保管（raw / masked）による出口マスキング
- Fernet 暗号化による raw 本文保護
- 3 層のプロンプトインジェクション対策

### 2-3. RAG パイプライン

- BM25 + ベクター検索のハイブリッド統合（RRF または重み付け）
- BAAI/bge-m3 によるベクター埋め込み
- Reranker（CrossEncoder、FlashRank、Ollama など複数対応）
- Multi-Query、CRAG、HyDE、MMR、Parent-Child チャンキングを含む高度な検索機能
- ロール別回答スタイル（admin / reader）

### 2-4. RBAC・監査

- 3 ロール（admin / curator / viewer）
- 重要操作の audit_logs テーブルへの記録
- 監査ログの API 経由改ざん禁止

### 2-5. 外部連携

- LM Studio / Ollama / OpenAI 互換 API 接続
- MCP サーバー（25 個の道具。既定で見えるのは 22 個。管理系の 3 個は CYNOVELA_MCP_ALLOW_ADMIN_WRITE=1 を設定したときだけ現れます）
- LAN 共有・Tailscale 共有

---

## 3. 技術スタック

| レイヤー | 技術 |
|---|---|
| Web フレームワーク | FastAPI |
| 永続化 | SQLite |
| ベクターストア | ChromaDB |
| 埋め込みモデル | BAAI/bge-m3（既定）、paraphrase-multilingual-MiniLM-L12-v2、paraphrase-MiniLM-L3-v2、TF-IDF |
| Reranker | BAAI/bge-reranker-v2-m3、CrossEncoder、FlashRank、Ollama |
| LLM | LM Studio、Ollama、OpenAI 互換 API、モック |
| 暗号化 | cryptography（Fernet） |
| PII 検出 | 正規表現、GiNZA NER、Presidio |
| 連携プロトコル | MCP（Model Context Protocol） |

---

## 4. クイックスタート

### 4-1. 推奨環境

- macOS（Apple Silicon 推奨）、Linux、Windows
- Python 3.10 以上
- conda 環境（推奨環境名: `cynovela`）

### 4-2. デモモードで起動

```bash
python server.py --demo
```

- `--demo`: デモのデータベース `store/db/demo.db` とインデックス `store/vector/demo/chroma` を使って起動します。付けなければ本番の `store/db/cynovela.db` と `store/vector/default/chroma` です。どちらも再起動では消えません。

ブラウザで `http://127.0.0.1:8765` を開くと UI が表示されます。

### 4-3. 実 LLM モードで起動

LM Studio を起動して OpenAI 互換 API を有効化した状態で次を実行します。

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

### 4-4. 起動モード

`--mode` は text / lite / lite-en を受け付けます（切替は未配線で、表示名が変わるだけです）。

| mode | 用途 | 必要モデル |
|---|---|---|
| `text` | テキスト RAG 全機能（既定） | BAAI/bge-m3 |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — |

---

## 5. ドキュメント一覧

`docs/` ディレクトリ配下に以下のドキュメントが配置されています。

| ドキュメント | 内容 |
|---|---|
| `quickstart.md` | 起動・初期設定の最短手順 |
| `manual-complete.md` | 全機能を網羅した一冊のマニュアル |
| `llm-connection.md` | LLM 接続の詳細（LM Studio / Ollama / OpenAI 互換） |
| `mcp-guide.md` | MCP サーバー連携と公開ツール一覧 |
| `lan-sharing.md` | LAN 共有・Tailscale 共有の起動手順 |
| `security-policy.md` | 既知制限・推奨しない使用方法 |
| `changelog.md` | リリース履歴 |
| `demo-general.html` | 一般向けインタラクティブデモ（ブラウザで開くだけ） |
| `demo-tech.html` | 技術者向けインタラクティブデモ |

---

## 6. ライセンス

実装コードは OSS として公開する前提で書かれています。利用にあたっては各依存ライブラリのライセンス（FastAPI、ChromaDB、BAAI/bge-m3 等）を尊重してください。

参照元の AI 基盤ツールのソースコード・商標・ロゴ・公式ドキュメントは一切含みません。

---

## 7. 免責

- 本ツールは個人の学習・検証目的で作成されたものです。
- 業務利用・本番運用は想定していません。
- 参照元の会社・製品の公式見解を一切代表しません。
- 機能の挙動・API・データ構造は予告なく変更されることがあります。

---

