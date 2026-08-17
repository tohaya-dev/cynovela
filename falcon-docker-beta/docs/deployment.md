# デプロイメントガイド

> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

このドキュメントは、Cynovela をローカル環境に展開する手順をまとめたものです。

---

## 1. 動作確認済み環境

Cynovela は個人検証用のツールであり、動作確認している環境は限定的です。以下を参考にしてください。

| 項目 | 確認済みの内容 |
|------|------------|
| OS | macOS（Apple Silicon） |
| Python 実行系 | conda（Miniforge） |
| ローカル LLM | LM Studio（OpenAI 互換 `/v1` API） |
| Embedding | BAAI/bge-m3、paraphrase-multilingual-MiniLM-L12-v2、paraphrase-MiniLM-L3-v2、TF-IDF |

<!-- BACKLOG: Windows / Linux / Docker 環境での動作確認状況は spec-raw に記載がないため未確認 -->
<!-- BACKLOG: GPU 利用時の詳細（CUDA バージョン、メモリ目安）は spec-raw に記載がないため未確認 -->

---

## 2. conda 環境セットアップ

### 環境作成

```bash
conda create -n cynovela python=3.12 -y
conda activate cynovela
```

### 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

主要な依存:

| ライブラリ | 用途 |
|----------|------|
| FastAPI | API サーバー本体 |
| Uvicorn | ASGI サーバー |
| SQLite（標準同梱） | メタデータ・監査ログ・チャンク保存 |
| ChromaDB | ベクター検索 |
| cryptography（Fernet） | raw 本文の暗号化 |
| huggingface_hub | モデルダウンロード |
| BM25Okapi | キーワード検索 |
| fugashi / MeCab | 日本語形態素解析（BM25 トークン化） |

---

## 3. 起動フラグ一覧

`python server.py` に渡せる全フラグです。

| フラグ | 型 | 既定値 | 説明 |
|--------|-----|------|------|
| `--demo` | bool | False | デモのデータベース `store/db/demo.db` とインデックス `store/vector/demo/chroma` を使って起動。付けなければ本番の `store/db/cynovela.db` と `store/vector/default/chroma`。どちらも再起動では消えません |
| `--lmstudio-url` | str | `http://localhost:1234` | LM Studio のベース URL |
| `--mode` | str | `text` | 起動モード（`full` / `text` / `lite` / `lite-en` / `minimal`） |
| `--host` | str | `0.0.0.0` | バインドアドレス（既定は全アドレス。絞るのは `--local-only`） |
| `--lan` | bool | False | LAN 公開（host=0.0.0.0 を明示） |
| `--port` | int | `8765` | ポート番号 |
| `--local-only` | bool | False | 自マシン内だけに絞る（`host=127.0.0.1` で待ち受け） |
| `--allow-tailscale` | bool | False | Tailscale ネットワークからのアクセス許可 |
| `--reset-admin` | bool | False | 管理者パスワードをリセットして表示し終了（デモを直すときは `--demo` を併記） |
| `--ingest PATH` | str（複数指定可） | なし | 取り込み元として許可するフォルダ |
| `--allow-subnet` | list | `[]` | 許可するサブネット（複数指定可） |

### よく使う組み合わせ

```bash
# 通常起動（LM Studio 必要）
python server.py --demo

# LAN 共有 + Tailscale
python server.py --demo --lan --allow-tailscale

# 表示名を変えて起動する例（動作は text と同じ・切替は未配線）
python server.py --demo --mode lite
```

> **PII 検出モード**: `--pii-mode` は CLI 引数として廃止されました。`cynovela.yaml` の `pii_mode` キー（`lite` / `standard` / `quality`）で指定します。

---

## 4. `--mode` 選択ガイド

起動モードによって Embedding と Reranker の構成が変わります。

### モデルサイズ比較表

| `--mode` | Embedding モデル | サイズ目安 | Reranker | 推奨環境 |
|--------|---------------|---------|---------|---------|
| `text`（既定） | BAAI/bge-m3 | 約 2.3GB | 設定で選択可（`reranker.provider`） | GPU 不要・汎用 |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — | — | — |

### 選び方の目安

- 一般的な日本語 RAG: `text`

### Provider 配線の優先順位

2. `cynovela.yaml` の `reranker.provider` の指定（`cross_encoder` / `flashrank` / `mlx` / `http` / `none` ほか）
3. 旧来の `rag.reranker_enabled` + `reranker_url` は `http` 経路として吸収

---

## 5. LM Studio / Ollama との接続

### LM Studio

Cynovela の既定 LLM プロバイダーは LM Studio です。`/v1` 互換 API を持つ任意のサービスにも接続できます。

```bash
python server.py --demo --lmstudio-url http://localhost:1234
```

`cynovela.yaml` での設定例:

```yaml
llm:
  provider: lmstudio
  base_url: http://localhost:1234
  api_key: ""
  model: ""
  max_concurrent: 3
  timeout_seconds: 120
```

> **重要**: LM Studio API には `max_tokens` を渡さないでください。Reasoning モデルで思考用トークン予算が枯渇する原因となります。

### Ollama / OpenRouter / vLLM

`llm.provider` を `openai_compat` にすると、LM Studio 以外の OpenAI 互換エンドポイント（vLLM、Ollama の `/v1` 互換ゲートウェイなど）に切り替えられます。

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:11434/v1   # 例: Ollama
  model: llama3
```

Reranker は別系統で、`reranker.provider` を `ollama` に設定すると Ollama を Reranker として利用できます。

### モック LLM

以前あった `--mock`（LLM 呼び出しをモックに置き換える指定）は撤去済みです。いま指定するとエラーで止まります。

---

## 6. 初回モデルダウンロード手順

### Preflight チェック

`--mode minimal` でない場合、起動時に必要モデルの存在を確認します。

スキップ条件:

- `--mode minimal`
- そのモードの必要モデルリストが空

### 不足時のプロンプト

不足モデルがあると、対話プロンプトが表示されます。

```
[1] 今すぐダウンロードして起動する
[2] 代替モードで起動する（例: text / lite / mock）
[3+] キャンセル
```

| 選択 | 動作 |
|------|------|
| `[1]` | HuggingFace Hub から `~/.cynovela/models/` 配下にダウンロード |
| `[2]` | 代替モードを提示（`full → text → lite → lite-en → mock` の順） |
| `[3+]` | 起動キャンセル |

### 非対話環境での起動中止

CI などで対話プロンプトを出したくない場合は、環境変数 `CYNOVELA_NONINTERACTIVE=1` を設定します。モデル不在時は即座に終了します。

```bash
CYNOVELA_NONINTERACTIVE=1 python server.py --mode text
```

### 保存先

- ダウンロード先: `~/.cynovela/models/`
- 命名規則: HuggingFace のリポジトリ名のスラッシュを `__` に置換（例: `BAAI__bge-m3`）

### モデルパスの上書き

OneDrive 等の同期フォルダにモデルを置きたい場合は `cynovela.yaml` の `models` セクションでパスを指定できます。

```yaml
models:
  embedding:
    path: "/path/to/bge-m3"
    name: "BAAI/bge-m3"
  reranker:
    path: ""
    name: "BAAI/bge-reranker-v2-m3"
```

---

## 7. 主要な環境変数

機密情報は `cynovela.yaml` に直書きせず、環境変数で渡すことを推奨します。

### データ・パス

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_DB` | SQLite DB パス（既定は `~/.cynovela/db/...`） |
| `CYNOVELA_CHROMA` | ChromaDB ディレクトリ |
| `CYNOVELA_BACKUP_DIR` | バックアップディレクトリ |
| `CYNOVELA_LOG_DIR` | ログディレクトリ |
| `CYNOVELA_DATA_DIR` | アプリデータルート |

### LLM / Embedding / Reranker

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_LLM_BASE_URL` | LLM ベース URL |
| _(環境変数なし)_ | LLM API キーは設定UIで入力（このセッションのみ保持・保存しない） |
| `CYNOVELA_LLM_MODEL` | LLM モデル名 |
| `CYNOVELA_LLM_PROVIDER` | LLM プロバイダー |
| `CYNOVELA_LLM_MAX_CONCURRENT` | LLM 同時実行数上限 |
| `CYNOVELA_EMBEDDING_PROVIDER` | Embedding プロバイダー |
| `CYNOVELA_EMBEDDING_MODEL` | Embedding モデル名 |
| `CYNOVELA_EMBEDDING_BASE_URL` | Embedding ベース URL |
| `CYNOVELA_EMBEDDING_API_KEY` | Embedding API キー |
| `CYNOVELA_RERANKER_API_KEY` | Reranker API キー |
| `CYNOVELA_CLASSIFIER_API_KEY` | 分類器 API キー |

### 運用

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_NONINTERACTIVE` | `1` で Preflight 対話をスキップして即終了 |
| `CYNOVELA_DISABLE_RATE_LIMIT` | レートリミット無効化 |
| `CYNOVELA_MAX_UPLOAD_BYTES` | ファイルアップロード最大サイズ（既定 100MB） |
| `CYNOVELA_MCP_PYTHON` | MCP サーバー実行用 Python パス |
| `CYNOVELA_SECRET_KEY` | Fernet 暗号化鍵（本番推奨） |

### 初期化

| 環境変数 | 用途 |
|---------|------|
| `CYNOVELA_ADMIN_INITIAL_PASSWORD` | 初回起動時の admin パスワード |
| `CYNOVELA_ADMIN_USERNAME` | 初回起動時の admin ユーザー名（既定: `cynovela`） |
| `CYNOVELA_SMTP_PASSWORD` | SMTP パスワード |

---

## 8. 起動フロー全体図

```
main() 呼び出し
  ↓
argparse で CLI 引数パース
  ↓
Preflight チェック（必要モデルの存在確認）
  ├─ モデル不足 → ユーザー選択（DL / 代替 mode / キャンセル）
  └─ 戻り値 False なら起動中止
  ↓
LLM アダプター取得
  └─ それ以外 → LM Studio など
  ↓
AppConfig 構築（mode / demo / mock 反映）
  ↓
cynovela.yaml 読み込み
  ├─ CYNOVELA_* 環境変数で上書き
  └─ CircuitBreaker / Semaphore 初期化
  ↓
Provider 配線（Embedding / Reranker）
  ↓
PII 検出モード設定（yaml.pii_mode）
  ↓
DB 初期化（--demo なら store/db/demo.db、付けなければ store/db/cynovela.db）
  ↓
Uvicorn で FastAPI 起動
```

---

## 9. ポートとアクセス制御

| 既定値 | 内容 |
|------|------|
| 8765 | サーバーポート |
| 0.0.0.0 | バインドアドレス（`--local-only` で 127.0.0.1 に絞る） |
| 許可 IP | 既定は制限なし（`--allow-subnet` / `--allow-tailscale` 指定時のみ適用） |

LAN や Tailscale からのアクセスを許可するには、`--lan` / `--allow-tailscale` / `--allow-subnet` を併用します（操作ガイド・ハンズオン応用編を参照）。

---
最終更新: 2026-05-26 / Alpha GA 対応版
