# 外の口 (Mac Accelerator Service) の立て方 — 受け取り手向け 1 ページ

本配布物 (ホスト直起動版) は `./launch.sh` で Mac のホスト上に直接立ち上がります。
コンテナはありません。

- **埋め込みは既定でこのアプリ自身が Mac の GPU (MPS) で回します。** 外の口は要りません。
- **再ランクだけは既定で外の口を呼びます** (`cynovela.yaml` の `reranker.device: external`)。
  外の口が居なければアプリ内の同じモデルへ自動で退避するので、立てなくても動きます。

つまり外の口は「必須」ではなく、**再ランクを外へ出す / 複数の Mac で 1 台に推論を寄せる**
ときに立てるものです。回答用 LLM (LM Studio 等) を別に立てるのと同じ考え方です。

## 1. 外の口の立て方

外の口を動かすには、`torch` / `sentence-transformers` / `fastapi` / `uvicorn` の4件が入った
python が要ります。**裸の `python` にはこの4件が入っていないことがほとんどです。**
アプリ本体を動かす環境 (conda の `cynovela-dist` または `.venv-cynovela`) とは別に、
外の口用の場所をこの配布物の中に作ってから立ててください。

```bash
# アプリと同じ Mac のホスト側で。まず、この配布物のフォルダへ移動します。
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

既に4件が入っている python をお持ちの場合は、(1) と (2) を飛ばし、その python で (3) を
行ってください。確かめ方: `<その python> -c 'import torch, sentence_transformers, fastapi, uvicorn'`

`.mas-env` はこの配布物の中だけに作られます。**conda の共有の環境 (envs) には何も書きません。**
入れる部品は `mas/mas-requirements.txt` に書いた4件です。本体アプリ用の `requirements.txt`
(39件) や `environment.yml` は、外の口を立てる目的には使いません。

- 既定で `127.0.0.1:18850` に立ちます (変更は `mas/mas.yaml` の server.host / server.port)。
- 確認: `curl http://127.0.0.1:18850/health` が `"status":"ok"` を返せば稼働。
  再ランクまで使うなら同じ応答に `"reranker_loaded":true` が出ていること (0.2.0 以降)。
- `curl http://127.0.0.1:18850/capabilities` で モデル名・版 (revision)・デバイス (mps/cpu) が見えます。
- アプリと外の口は**同じ Mac の中で 127.0.0.1 越し**に話します。アプリはコンテナの中に
  居ないので `host.containers.internal` のような読み替えは不要です。

## 2. モデルは bge-m3 / bge-reranker-v2-m3 の「配布物と同一の版」を使うこと

- 埋め込みモデル: **BAAI/bge-m3、snapshot 版 `5617a9f61b028005a4858fdac845db406aefb181`**
- 再ランクモデル: **BAAI/bge-reranker-v2-m3**
- **版が違うとベクトルの数値が変わり、同梱済みのベクターコレクションと混ざって検索順位が壊れます。**
- 置き場所: この配布物の `store/models/models--BAAI--bge-m3/snapshots/<版>/` (HF キャッシュ形式)。
  `mas/mas.yaml` の `models.embedding.path` が `''` のときは、アプリと同じこの場所から
  読み取り専用で解決します。別の場所に置いたときだけパスを書いてください。
- 万一版が違う場合、起動時とpublish時に「ベクターコレクションの埋め込み識別と現在の経路が
  食い違っています」と **画面とログに明示的に警告**が出ます (§9-4 整合チェック)。
  警告が出たら版を揃えるか全再構築してください。

## 3. 呼び先の指定の書き方

`cynovela.yaml` の既定 (再ランクだけ外へ出す):

```yaml
reranker:
  provider: cross_encoder
  model: BAAI/bge-reranker-v2-m3
  device: external                 # external = 外の口へ出す / cpu / mps = アプリ内で回す
  base_url: http://localhost:18850
  top_n: 5

embedding:
  provider: local                  # 既定はアプリ内。外へ出すなら openai_compat
  device: mps                      # local_cpu / mps / external_accelerator
  model: BAAI/bge-m3
  base_url: ''
```

埋め込みも外の口へ出したい場合 (推論を別の Mac 1 台に寄せる等):

```yaml
embedding:
  provider: openai_compat
  device: external_accelerator
  model: BAAI/bge-m3
  base_url: http://127.0.0.1:18850   # 別の Mac なら その Mac の IP:18850
```

ポートを変えた場合は base_url を合わせてください。管理画面 (設定 > Embedding) からも変更できます。

**別の Mac へ出す場合の注意**: アプリの外へ文字が出ることになるため、外の口側の
`mas/mas.yaml` で `policy.allow_raw_content: false` にして、伏字済みのものだけを
受け付ける形にしてください。

## 4. 口が居ないときの振る舞い

- 再ランク: 外の口に届かない場合、**アプリ内のモデル (store/models) での処理へ退避**します
  (本配布物は全部入りで、再ランクのモデルを同梱しています)。再ランクのモデルを置いていない
  場合は、再ランクを行わず検索結果をそのまま返します。どちらの場合も処理は止まりません。
- 埋め込み (外へ出す設定にしたときのみ): 届かない場合は**アプリ内のローカル処理へ明示的に退避**し、
  管理画面 (設定 > Embedding) に **「⚠️ 外の口に届かないためローカルへ退避中」** と表示されます。
  黙って遅くなることはありません。口を立て直せば次回の埋め込みから自動復帰します。

## 5. 稼働確認のしかた

1. 外の口: `curl http://127.0.0.1:18850/health` → `"status":"ok"` (再ランクを使うなら
   `"reranker_loaded":true` も)
2. `./launch.sh` でアプリを起動 → 管理者でログイン
3. 質問を 1 回投げる → 外の口の `curl http://127.0.0.1:18850/metrics` で
   `rerank_requests` が増えていれば、再ランクは外の口 (MPS) で実行されています
4. 埋め込みも外へ出す設定にした場合は、資料を 1 本取り込み (publish) して
   同じ `/metrics` の `embeddings_texts` が増えることを確認してください
   (既定の `provider: local` のままなら増えません。これは正常です)

補足: 画像の口は将来用の入口のみで未実装 (呼ぶと 501) のままです。
