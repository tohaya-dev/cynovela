# 外部アクセラレータ (Mac Accelerator Service) の立て方 — 受け取り手向け 1 ページ

**軽量版を受け取った場合、この手順は必須です。** 軽量版は埋め込みモデルを同梱しておらず、
モデルを置かないまま起動用スクリプトを実行すると、起動する前に止まります
(「埋め込みモデルの置き場がありません」と表示されます)。
全部入りを受け取った場合はモデルが同梱済みなので、この手順は不要です
(外部アクセラレータを使いたい場合のみ読んでください)。
コンテナは軽い単一イメージのままで、埋め込みは同一 Mac のホスト側で動く
**Mac Accelerator Service (外部アクセラレータ)** を呼びます。回答用 LLM (LM Studio 等) と
同じ考え方です。

## 1. 外部アクセラレータを先に立てる

### 1-A. 起動用スクリプトに任せる (こちらが既定の道です)

`./launch.sh` を叩くと、コンテナの実行ファイルを選ぶ前に「外の口」の段が入ります。
この段が行うのは次のことです。

1. `127.0.0.1:18850` に応答があるかを見ます。あればそのまま次へ進みます。
2. 無ければ、外の口を動かす場所を**この配布物の中に**作るかどうかを尋ねます。
   選べるのは `conda` で作る / `venv` で作る / 自分で python の場所を指定する /
   外の口を使わずに進む / やめる の5つです。
3. 選ばれた道で場所を作り、外の口を立て、`/health` の `device` を画面に出します。
4. 立てられなかったときは、何が足りないかを画面に出して止まります。
   気づかないまま CPU で動く形にはしていません。

作る場所は `.mas-env`（この配布物の中）です。**conda の共有の環境 (envs) には何も書きません。**
入れる部品は `mas/mas-requirements.txt` に書いた4件です。

外の口を使わずに進むことも選べます。その場合、埋め込みはコンテナ内 CPU で行われます。

### 1-B. 手で立てる

起動用スクリプトを使わずに立てる場合の手順です。

```bash
# ホスト側 (コンテナの外) で。まず、この配布物のフォルダへ移動します。
cd <この配布物のフォルダ>

# (1) 外の口を動かす場所を、この配布物の中に作る。どちらか一方を選びます。
#     conda を使う場合 (共有の環境ではなく、場所を指定して作ります)
conda create -y -p .mas-env python=3.12
#     venv を使う場合 (3.10 以上の python3 を指定してください)
python3.12 -m venv .mas-env

# (2) 部品を入れる
.mas-env/bin/python -m pip install -r mas/mas-requirements.txt

# (3) 立てる
.mas-env/bin/python mas/mas_server.py --preload
```

既に4件 (`torch` / `sentence-transformers` / `fastapi` / `uvicorn`) が入っている python を
お持ちの場合は、(1) と (2) を飛ばし、その python で (3) を行ってください。

- 既定で `127.0.0.1:18850` に立ちます (変更は `mas/mas.yaml` の server.host / server.port)。
- 確認: `curl http://127.0.0.1:18850/health` が `"status":"ok"` を返せば稼働。
- `curl http://127.0.0.1:18850/capabilities` で モデル名・版 (revision)・デバイス (mps/cpu) が見えます。
- 記録は `store/mas.log` へ書かれます (起動用スクリプトから立てた場合)。

### 1-C. 部品について

`mas/mas-requirements.txt` の中身は4件です。本体アプリ用の `requirements.txt` (39件) や
`environment.yml` は、外の口を立てる目的には使いません。`environment.yml` は
`name: cynovela` の形で conda の共有の場所へ作るものであり、この配布物の中に作る道とは別のものです。

## 2. 埋め込みモデルは bge-m3 の「配布物と同一の版」を使うこと

- モデル: **BAAI/bge-m3、snapshot 版 `5617a9f61b028005a4858fdac845db406aefb181`**
- **版が違うとベクトルの数値が変わり、同梱済みのベクターコレクション (資料30本ぶん) と
  混ざって検索順位が壊れます。**
- 置き場所: **この配布物の `store/models/models--BAAI--bge-m3/snapshots/<版>/` (HF キャッシュ形式) は必須です。**
  起動用スクリプトが `store/models` を読み取り専用でつなぐため、この場所が無いと起動できません。
  外部アクセラレータ側にどのディレクトリを読ませるかは、別途 `mas/mas.yaml` の
  `models.embedding.path` で指定できます。
- 万一版が違う場合、起動時と publish 時に「埋め込みの識別と現在の経路が食い違っています」
  という趣旨の警告が**画面とログに明示的に**出ます。
  警告が出たら版を揃えるか、全再構築してください。

## 3. 呼び先の指定の書き方

コンテナ形態 (本配布物の既定) の `cynovela.yaml`:

```yaml
embedding:
  provider: openai_compat
  device: external_accelerator     # 指定できる値: local_cpu / local_mps / external_accelerator
  model: BAAI/bge-m3
  base_url: http://host.containers.internal:18850   # コンテナから見たホスト側の宛先
```

- **コンテナから呼ぶ場合**: `http://host.containers.internal:18850`（同梱の既定値）。
- **ホストから直接 server.py を起動している場合**: `http://127.0.0.1:18850` に変えてください。
  `host.containers.internal` はコンテナの外では名前解決できません。
- ポートを変えた場合は base_url を合わせてください。
  管理画面 (Settings > Embedding) からも変更できます。

## 4. アクセラレータが居ないときの振る舞い

- 外部アクセラレータに届かない場合、埋め込みは**コンテナ内 CPU へ明示的に退避**します
  (処理は止まりません)。
- 退避中は管理画面 (Settings > Embedding) に
  **「⚠️ …(アクセラレータ)に届かないため、埋め込みはローカル(cpu)へ退避中です」**
  と表示されます。黙って遅くなることはありません。
  立て直せば次回の埋め込みから自動復帰します。

## 5. 稼働確認のしかた

1. アクセラレータ: `curl http://127.0.0.1:18850/health` → `"status":"ok"`
2. アプリ起動後、管理者でログイン → Settings > Embedding に
   **「✅ …(アクセラレータ)接続中 (device: mps)」** が出る
3. 資料を1本取り込み (publish) → `curl http://127.0.0.1:18850/metrics` で
   `embeddings_texts` が増えていれば、埋め込みは外部アクセラレータ (MPS) で実行されています

補足: `/v1/rerank` は実装済みです (0.2.0 以降。MPS で BAAI/bge-reranker-v2-m3 を実行し、
`/health` に `"reranker_loaded":true` が出ます)。アクセラレータに接続できている場合、再ランクも
外部 (MPS) で実行されます。**届かない場合の退避先は配布の種類で変わります**:
全部入りは同梱の再ランクモデル (store/models) を使ってコンテナの中で再ランクします。
**軽量版は再ランクのモデルを持たない** (この手順で置くのは埋め込みの bge-m3 だけで、
再ランクの bge-reranker-v2-m3 は含みません) ため、再ランクを行わず検索結果をそのまま返します。
どちらの場合も処理は止まりません (実測: providers/reranker.py の
`ExternalAcceleratorReranker._ensure_local()` が重み無しを確認したら退避先を持たない扱いにする)。
画像の受け付け経路は将来用に定義されているだけで未実装 (呼ぶと 501) のままです。
