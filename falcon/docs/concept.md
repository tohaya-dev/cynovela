> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# Cynovela のコンセプト

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

Cynovela は Alpha GA 段階の学習用検証実装です。

- **コア フロー（Source 登録 → Scan → Workspace → Collection → Publish → RAG Chat）は動作**: スモークテストで 2 秒程度で完了します。
- **テスト スイートは 14 PHASE / 405+ アサーション**: `scripts/run_all_tests.sh` で一括実行可能。静的解析・拡張 API・GUI Playwright・セキュリティ・整合性・CASCADE 削除・SSE 異常系・チャット異常系・スキャン異常系・Embedding 互換・DB マイグレーション・GUI 回復・audit_log を網羅（CLAUDE.md）。
- **未実装機能**: MLX Embedding / MLX Reranker / Qdrant VectorStore / LanceDB / GraphRAG は骨格のみ（A-6 §1）。構造化回答テンプレートは未実装、`confidence_threshold` の除外ロジックは部分統合（A-3 §6, §11）。認証は `--demo` 起動でも強制されます（`Bearer demo-token-<user_id>` 形式の固定トークンは 2026-07-29 に廃止）。
- **商用利用は想定外**: 学習目的の個人実装です。参照元の AI 基盤ツールの公式見解を代表しません。

---
最終更新: 2026-05-26 / Alpha GA 対応版
