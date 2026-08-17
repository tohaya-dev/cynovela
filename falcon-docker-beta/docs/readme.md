> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# Cynovela

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
- MCP サーバー（11 ツール）
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

最終更新: 2026-05-26 / Alpha GA 対応版
