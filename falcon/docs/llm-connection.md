# LLM 接続ガイド

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool built by an individual to
> understand the concepts of AI platform tools hands-on. It is not a commercial
> product nor an official implementation.
> The implementation is entirely original, built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela connects over HTTP to an external LLM (large language model) server to generate answers. This document explains the representative connection methods and the procedure for switching between them.

---

## 1. Connection Architecture

Cynovela's LLM connection layer (`llm_adapter.py`) is designed to connect to any service that has an OpenAI-compatible `/v1/chat/completions` endpoint. With `LMStudioAdapter` (an OpenAI-compatible adapter) as the mainstay, replacing the URL lets it support several local LLM runners.

```
Cynovela server
  ↓ HTTP POST /v1/chat/completions
LLM runner (LM Studio / Ollama / vLLM, etc.)
  ↓ streamed response
Cynovela server (guardrails → returned to the user)
```

---

## 2. Connecting to LM Studio

LM Studio is a desktop LLM runner with a GUI. It is Cynovela's default connection target.

### 2-1. Startup option

```bash
python server.py --lmstudio-url http://localhost:1234
```

`--lmstudio-url` is optional, and the default value is `http://localhost:1234`.

### 2-2. Preparation on the LM Studio side

1. Start LM Studio and load any model (for example, a Japanese-capable model).
2. In the "Local Server" tab, enable the OpenAI-compatible API and put it in a listening state on port 1234.
3. When you start the Cynovela server, it connects via `/v1/chat/completions`.

### 2-3. URL normalization behavior

The LLM adapter normalizes the URL by automatically removing a trailing `/` and `/v1`. All of the following are treated as the same connection target.

- `http://localhost:1234`
- `http://localhost:1234/`
- `http://localhost:1234/v1`

---

## 3. Connecting to Ollama

Ollama is a CLI-centric local LLM runner. Because it provides an OpenAI-compatible API, you can connect simply by specifying Ollama's OpenAI-compatible endpoint in `--lmstudio-url`.

### 3-1. Startup example

```bash
python server.py --lmstudio-url http://localhost:11434
```

### 3-2. Using Ollama as a Reranker

Ollama can be connected not only for LLM inference but also as a Reranker provider. Configure it in `cynovela.yaml` as follows.

```yaml
reranker:
  provider: ollama
  base_url: http://localhost:11434
  model: bge-reranker-v2-m3
```

---

## 4. Connecting to an LLM on a Remote Machine

You can also run LM Studio / Ollama on another machine and connect to it from Cynovela over the network. This is useful when you want to consolidate GPUs on a separate machine.

```bash
python server.py --lmstudio-url http://192.168.1.50:1234
```

On the target machine, you need to configure LM Studio or Ollama to listen on "all interfaces".

> **Security note**: LLM communication is plaintext HTTP. Exposing it outside the LAN is not recommended. We recommend connecting over a VPN such as Tailscale.

> **Egress block for the CRAG preview (crag-egress-guard)**: When a remote / non-local LLM endpoint is specified, the CRAG (self-corrective RAG) preview (`context_preview`) is not sent outside. Before sending, it determines whether the endpoint is local, and if it is non-local (including cases where it cannot be determined) it does not send the preview and skips CRAG. This prevents fragments of raw body text from leaking to an external LLM even for an administrator. With a local LLM (LM Studio / Ollama running locally), CRAG remains enabled as before.

---

## 5. List of Supported Providers

Switch with the `llm.provider` key in `cynovela.yaml`.

| Provider | Value | Description |
|---|---|---|
| LM Studio | `lmstudio` | Connects to LM Studio's OpenAI-compatible API (default) |
| OpenAI-compatible (generic) | `openai_compat` | Any service that has an OpenAI-compatible `/v1` API (vLLM / OpenRouter / Ollama, etc.) |
| Mock | `mock` | Returns a fixed string without calling the LLM (for testing) |

### 5-1. Configuration example for an OpenAI-compatible connection

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:8000
  model: meta-llama/Llama-3-8B-Instruct
  api_key: ""          # 設定UIで入力（このセッションのみ保持・保存しない）
  max_concurrent: 3
  timeout_seconds: 120
```

### 5-2. Mock mode

The former `--mock` (a verification mode that did not call the LLM at all) has been removed. Specifying it now stops with an error.

```bash
python server.py --demo
```

In this mode the Embedding also switches to TF-IDF (a lightweight vocabulary-frequency-based embedding), and no external model download occurs. It is not suitable for checking RAG (retrieval-augmented generation) quality, but it is useful for verifying the UI and the flow.

---

## 6. Related Environment Variables

The main environment variables available for the LLM connection are as follows.

| Environment variable | Purpose |
|---|---|
| `CYNOVELA_LLM_BASE_URL` | Overrides the LLM base URL |
| _(no environment variable)_ | The LLM API key is entered in the settings UI (kept for this session only, never saved) |
| `CYNOVELA_LLM_MODEL` | LLM model name (used only for OpenAI-compatible connections) |
| `CYNOVELA_LLM_PROVIDER` | LLM provider name |
| `CYNOVELA_LLM_MAX_CONCURRENT` | Upper limit of concurrent calls |

---

## 7. Reranker Providers

Apart from the LLM, the Reranker that reorders the search results is also replaceable. Specify it with `reranker.provider` in `cynovela.yaml`.

| Provider | Value | Description |
|---|---|---|
| Disabled | `none` | Does not use a Reranker |
| CrossEncoder | `cross_encoder` | A local CrossEncoder model (the default high-quality configuration) |
| FlashRank | `flashrank` | A lightweight Reranker library |
| MLX | `mlx` | A skeleton implementation for Apple Silicon (the actual body is a future item) |
| Ollama | `ollama` | A Reranker via Ollama |
| HTTP | `http` | Any HTTP endpoint |

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

Cynovela は外部の LLM（大規模言語モデル）サーバーに HTTP 経由で接続して回答生成を行います。本ドキュメントでは、代表的な接続方法と切り替え手順を説明します。

---

## 1. 接続アーキテクチャ

Cynovela の LLM 接続層（`llm_adapter.py`）は、OpenAI 互換の `/v1/chat/completions` エンドポイントを持つ任意のサービスに接続できる設計です。`LMStudioAdapter`（OpenAI 互換アダプター）を主軸として、URL を差し替えることで複数のローカル LLM ランナーに対応します。

```
Cynovela サーバー
  ↓ HTTP POST /v1/chat/completions
LLM ランナー（LM Studio / Ollama / vLLM 等）
  ↓ ストリーム応答
Cynovela サーバー（ガードレール → ユーザーへ返却）
```

---

## 2. LM Studio との接続

LM Studio はデスクトップ向けの GUI 付き LLM ランナーです。Cynovela の既定接続先になっています。

### 2-1. 起動時オプション

```bash
python server.py --lmstudio-url http://localhost:1234
```

`--lmstudio-url` は省略可能で、既定値は `http://localhost:1234` です。

### 2-2. LM Studio 側の準備

1. LM Studio を起動して任意のモデル（例: 日本語対応モデル）をロードします。
2. 「Local Server」タブで OpenAI 互換 API を有効化し、ポート 1234 で待ち受け状態にします。
3. Cynovela サーバーを起動すると、`/v1/chat/completions` 経由で接続されます。

### 2-3. URL 正規化の挙動

LLM アダプターは URL 末尾の `/` および `/v1` を自動的に除去して正規化します。以下はいずれも同じ接続先として扱われます。

- `http://localhost:1234`
- `http://localhost:1234/`
- `http://localhost:1234/v1`

---

## 3. Ollama との接続

Ollama は CLI 中心のローカル LLM ランナーです。OpenAI 互換 API を提供しているため、`--lmstudio-url` に Ollama の OpenAI 互換エンドポイントを指定するだけで接続できます。

### 3-1. 起動例

```bash
python server.py --lmstudio-url http://localhost:11434
```

### 3-2. Reranker としての Ollama 利用

Ollama は LLM 推論だけでなく、Reranker（再ランク付け）プロバイダーとしても接続できます。`cynovela.yaml` で次のように設定します。

```yaml
reranker:
  provider: ollama
  base_url: http://localhost:11434
  model: bge-reranker-v2-m3
```

---

## 4. リモートマシン上の LLM への接続

LM Studio / Ollama を別マシンで動かして、Cynovela からネットワーク経由で接続することもできます。これは GPU を別マシンに集約したい場合に有用です。

```bash
python server.py --lmstudio-url http://192.168.1.50:1234
```

接続先マシン側で、LM Studio または Ollama を「すべてのインターフェイス」で待ち受けるよう設定しておく必要があります。

> **セキュリティ上の注意**: LLM 通信は HTTP 平文です。LAN 外への公開は推奨しません。Tailscale などの VPN 経由で接続することを推奨します。

> **CRAG 下読みの egress 封鎖（crag-egress-guard）**: リモート／非ローカルの LLM エンドポイントを指定した場合、CRAG（自己修正 RAG）の下読み（`context_preview`）は外部へ送出されません。送信前にエンドポイントがローカルかを判定し、非ローカル（判定不能を含む）なら下読みを送らず CRAG をスキップします。これにより admin であっても raw 本文の断片が外部 LLM へ漏れることを防ぎます。ローカル LLM（LM Studio / Ollama をローカルで実行）では従来どおり CRAG が有効です。

---

## 5. 対応プロバイダー一覧

`cynovela.yaml` の `llm.provider` キーで切り替えます。

| プロバイダー | 値 | 説明 |
|---|---|---|
| LM Studio | `lmstudio` | LM Studio の OpenAI 互換 API へ接続（既定） |
| OpenAI 互換（汎用） | `openai_compat` | OpenAI 互換 `/v1` API を持つ任意のサービス（vLLM / OpenRouter / Ollama 等） |
| モック | `mock` | LLM を呼び出さず、固定文字列を返す（テスト用） |

### 5-1. OpenAI 互換接続の設定例

```yaml
llm:
  provider: openai_compat
  base_url: http://localhost:8000
  model: meta-llama/Llama-3-8B-Instruct
  api_key: ""          # 設定UIで入力（このセッションのみ保持・保存しない）
  max_concurrent: 3
  timeout_seconds: 120
```

### 5-2. モックモード

以前あった `--mock`（LLM を全く呼び出さない検証モード）は撤去済みです。いま指定するとエラーで止まります。

```bash
python server.py --demo
```

このモードでは Embedding（埋め込み）も TF-IDF（語彙頻度ベースの軽量埋め込み）に切り替わり、外部モデルのダウンロードも発生しません。RAG（検索拡張生成）の品質確認には適しませんが、UI とフロー検証には有用です。

---

## 6. 関連する環境変数

LLM 接続関係で使用できる主な環境変数は以下です。

| 環境変数 | 用途 |
|---|---|
| `CYNOVELA_LLM_BASE_URL` | LLM ベース URL を上書き |
| _(環境変数なし)_ | LLM API キーは設定UIで入力（このセッションのみ保持・保存しない） |
| `CYNOVELA_LLM_MODEL` | LLM モデル名（OpenAI 互換時のみ使用） |
| `CYNOVELA_LLM_PROVIDER` | LLM プロバイダー名 |
| `CYNOVELA_LLM_MAX_CONCURRENT` | 同時実行数の上限 |

---

## 7. Reranker（再ランク付け）プロバイダー

LLM とは別に、検索結果の並び替えを担う Reranker も差し替え可能です。`cynovela.yaml` の `reranker.provider` で指定します。

| プロバイダー | 値 | 説明 |
|---|---|---|
| 無効 | `none` | Reranker を使わない |
| CrossEncoder | `cross_encoder` | ローカルの CrossEncoder モデル（既定の高品質構成） |
| FlashRank | `flashrank` | 軽量 Reranker ライブラリ |
| MLX | `mlx` | Apple Silicon 向けの骨格実装（実体は将来対応） |
| Ollama | `ollama` | Ollama 経由の Reranker |
| HTTP | `http` | 任意の HTTP エンドポイント |

---

最終更新: 2026-05-26 / Alpha GA 対応版
