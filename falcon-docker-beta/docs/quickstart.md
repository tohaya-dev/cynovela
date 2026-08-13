# クイックスタート

Cynovela を初めて起動し、最初の RAG 質問を投げるまでの最短手順です。対象は版 `1.0.0-alpha`（作業ディレクトリ `<配布物を展開したフォルダ>`）です。

> さらに短い起動メモは [STARTUP.md](../STARTUP.md) を参照してください。

---

## 1. 前提環境

| 項目 | 内容 |
|---|---|
| Python | conda 環境 `cynovela`（Python 3.12 系で検証 / environment.yml は 3.12.13 を固定） |
| ローカル LLM | LM Studio もしくは OpenAI 互換 API |
| 推奨 RAM | 8GB 以上（どの起動モードでも必要なモデルは同じです） |
| ネットワーク | 初回起動時のモデルダウンロードに必要 |

---

## 2. conda 環境のセットアップ

```bash
# conda 環境を作成（例: cynovela）
conda create -n cynovela python=3.12 -y

# 依存ライブラリをインストール
conda run -n cynovela python -m pip install -r requirements.txt
```

主な依存: FastAPI / uvicorn / ChromaDB / sentence-transformers / spaCy + ja-ginza / torch / pypdf ほか（`requirements.txt` 参照）。

---

## 3. SSL_CERT_FILE の注意（重要）

conda 環境では `SSL_CERT_FILE` が誤った証明書パスを指すことがあり、起動時の HuggingFace モデルダウンロードが失敗します。`unset` してシステムデフォルトの証明書を使ってください。

```bash
unset SSL_CERT_FILE
```

同梱の `launch.sh` はこの `unset` を内包しているため、これを使う場合は不要です。**手動で `conda run` を実行する場合のみ**、各自で実行してください。

---

## 4. 起動

### 方法 1: 同梱ランチャー（推奨）

```bash
cd <配布物を展開したフォルダ>

# launch.sh に渡した引数は、そのまま server.py へ届きます
# （実装: launch.sh の `exec "$PY" server.py "${APP_ARGS[@]}"`。2026-08-02 実測）。
# 引数なしは本番（空のデータベース）です。デモを見るなら --demo を明示します。
./launch.sh --demo            # デモデータ + 実 LLM（既定は 0.0.0.0 で待ち受け。自分の機械の中だけに絞るなら --local-only）
./launch.sh --demo --lan      # デモデータ + LAN 公開
./launch.sh --check           # 起動せずに動く条件だけを調べる
```

停止:

```bash
bash stop.sh
```

（中身は `podman stop cynovela-all-in-one` です。別の名前で起動した場合は、その名前を使ってください。）

### 方法 2: 手動起動

```bash
cd <配布物を展開したフォルダ>
unset SSL_CERT_FILE

# デモデータ + 実 LLM（LM Studio を http://localhost:1234 で起動しておく）
conda run -n cynovela python server.py --demo
```

アクセス:

```bash
open http://127.0.0.1:8801
```

（既定の番号は 8801 です。何も付けないときは空いている番号を自分で選ぶため、起動時に表示された番号を使ってください。）

> ⚠️ **実 LLM が要ります**: 質問への答えを作るには LM Studio などの LLM が要ります。以前あった `--mock`（LLM を呼ばずに動かす指定）は撤去済みで、いま指定するとエラーで止まります。

> **コンテナ版（podman）** で動かす場合は `./launch.sh` を使います（取り込みフォルダの詳細は README を参照）。※ コンテナ手順はコンテナ版にのみ同梱されています（ホスト直起動版には `deploy/` はありません）。

---

## 5. 起動モード（`--mode`）と必要モデル

| モード | 必要モデル | サイズ目安 |
|---|---|---|
| `text`（既定） | BAAI/bge-m3 | 約 2.3GB |
| `lite` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — |
| `lite-en` | 切替は**未配線**＝実際は BAAI/bge-m3（動作は text と同じ・表示名が変わるだけです） | — |

初回起動でモデルが未取得の場合、Preflight チェックの対話プロンプト（ダウンロード / 別モードへ切替 / キャンセル）が表示されます。非対話環境では `CYNOVELA_NONINTERACTIVE=1` を設定すると、未キャッシュ時に終了コード 2 で停止します。

```bash
# 例: 表示名を変えて起動する（動作と必要モデルは text と同じ・切替は未配線）
./launch.sh --demo --mode lite
```

---

## 6. デモアカウントでログイン

ブラウザで `http://127.0.0.1:8801` を開きます（起動時に別の番号が表示されたときは、その番号）。`--demo` ではデモ用ユーザーが自動投入されますが、認証は通常どおり強制されます（ユーザー名とパスワードの入力が要ります）。DB が保持するロールは **`admin` / `viewer` の 2 値**です。

| ロール | 権限 | 検索対象 |
|---|---|---|
| `admin` | 全機能 | raw 保管庫（出力マスクなし） |
| `viewer` | 閲覧中心 | masked 保管庫（出口マスクあり） |

> `curator` / `data-scientist` 等の名称は内部的に `viewer` へ正規化されます。

出荷 `demo.db` の実ログイン情報:

| ユーザー名（既定。`admin` ではありません） | ロール | パスワード |
|---|---|---|
| `cynovela` | admin | 初回ログイン時に変更を強制（固定 PW は配布しません） |
| `demo` | viewer | 同梱の資格情報ファイル（配布物の tar とは別便で受け取る `*.admin-password.txt`）の `viewer_password` を参照。固定 PW は配布しません |

---

## 7. 最初のファイル取り込みと Publish

1. `--demo` 起動では、**同梱のダミー資料が入ったワークスペースが 1 件だけ**入っています（空のシード WS 3 件は 2026-07-30 に撤去済みで、起動時に取り除かれます。2026-08-02 実測: `--demo` 起動直後の `/api/workspaces` は「デモワークスペース」のみ）。自分用のワークスペースは「新しいワークスペースを作成」から作ります。
2. 「コレクション作成」で名前と RAG 戦略を指定
3. ファイルをアップロード
4. 「Publish（公開）」を実行し `ready` 状態にする

Publish では テキスト抽出 → チャンク分割 → PII 検出/マスキング → Embedding 生成（ChromaDB 保存）→ BM25 インデックス構築 が行われます。進捗は SSE で返り、完了時に `publish_history` へ件数・所要時間が記録されます。

---

## 8. 最初の質問

`ready` 状態のコレクションに対し、RAG Chat 画面から質問します。

```
このドキュメントで扱われている主なトピックは何ですか？
```

回答には出典として `[1][2]` の引用番号付きでチャンクが表示されます。`admin` は raw 本文、`viewer` はマスク済み本文を検索し、`viewer` では LLM 出力にも出口マスクが適用されます。

---

## 9. 動作確認（テスト）

> **配布物には `tests/` は入っていません**（梱包時に外されます）。受け取った配布物では `pytest` / `make test` は実行できません。
> 動作を確かめるには `conda run -n cynovela python scripts/test_comprehensive_e2e.py` を使ってください。

```bash
# 開発ツリー（tests/ が在る側）での実行

# 手動 pytest（軽量・最初の失敗で停止）
cd <開発ツリーのフォルダ>
unset SSL_CERT_FILE
conda run -n cynovela python -m pytest -x -q
```

`Makefile` の `make test` / `make test-quick` / `make verify-live` も利用できます。`live` 系はサーバが `http://127.0.0.1:8801`（起動時に表示された番号）で稼働していることが前提です。

---

## 次のステップ

- [architecture.md](architecture.md) — システム構成を理解する
- [handson-basic.md](handson-basic.md) — 基本操作を試す
- [rag-pipeline.md](rag-pipeline.md) — RAG パイプラインを理解する

---

## トラブルシューティング

- **モデルダウンロードや HTTPS が SSL で失敗** → `unset SSL_CERT_FILE` してから起動・テストしてください（ランチャー使用時は不要）。
- **LAN の他の端末から開けない** → 既定で `0.0.0.0` 待ち受けなので、まずポートと接続先 IP を確認してください（`--local-only` を付けていると自マシン内に絞られます）。
- **品質が安定しない** → LM Studio 側のモデルと設定を確認してください。
- **admin パスワードを忘れた** → `conda run -n cynovela python server.py --reset-admin` で再発行できます。
- **ポート 8801 が使用中** → `lsof -i :8801` で確認します。何も付けないときは空いている番号を自分で選ぶため、そのまま起動できます。止めるときは `bash stop.sh` です（中身は `podman stop cynovela-all-in-one`。別の名前で起動した場合は、その名前を使ってください）。

その他は [faq.md](faq.md) を参照してください。
