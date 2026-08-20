# 外部の推論サーバ (Mac Accelerator Service) の立て方 — 受け取り手向け 1 ページ

**日本語版はこちら → [日本語](#日本語)**

## English

This package (the host direct-start version) starts up directly on the Mac host with `./launch.sh`.
There is no container.

- **The embedding is by default run by this application itself on the Mac GPU (MPS).** An external inference server is not required.
- **Only the rerank calls an external inference server by default** (`reranker.device: external` in `cynovela.yaml`).
  If there is no external inference server, it automatically falls back to the same model inside the application, so it works even without setting one up.

In other words, an external inference server is not "mandatory"; it is something you set up when you want to
**move the rerank outside / gather the inference onto 1 machine among several Macs**. It is the same way of thinking as
setting up the answering LLM (LM Studio etc.) separately.

## 1. How to set up the external inference server

To run the external inference server, you need a python that has the 4 items `torch` / `sentence-transformers` / `fastapi` / `uvicorn`.
**A bare `python` most often does not have these 4 items.**
Separately from the environment that runs the application body (conda's `cynovela-dist` or `.venv-cynovela`),
please create a place for the external inference server inside this package, and then set it up.

```bash
# アプリと同じ Mac のホスト側で。まず、この配布物のフォルダへ移動します。
cd<この配布物のフォルダ>

# (1) 外部の推論サーバを動かす場所を、この配布物の中に作る。どちらか一方を選びます。
#     conda を使う場合 (共有の環境ではなく、場所を指定して作ります)
conda create -y -p .mas-env python=3.12
#     venv を使う場合 (3.10 以上の python3 を指定してください)
python3.12 -m venv .mas-env

# (2) 部品を入れる
.mas-env/bin/python -m pip install -r mas/mas-requirements.txt

# (3) 立てる
.mas-env/bin/python mas/mas_server.py --preload
```

If you already have a python that has the 4 items, skip (1) and (2) and do (3) with that python.
How to check: `<その python> -c 'import torch, sentence_transformers, fastapi, uvicorn'`

`.mas-env` is created only inside this package. **Nothing is written to conda's shared environments (envs).**
The parts to install are the 4 items written in `mas/mas-requirements.txt`. The `requirements.txt` for the application body
(39 items) and `environment.yml` are not used for the purpose of setting up an external inference server.

- By default it stands at `127.0.0.1:18850` (to change it, use server.host / server.port in `mas/mas.yaml`).
- Check: it is running if `curl http://127.0.0.1:18850/health` returns `"status":"ok"`.
  If you use the rerank too, `"reranker_loaded":true` must also appear in the same response (0.2.0 and later).
- With `curl http://127.0.0.1:18850/capabilities` you can see the model name, the revision, and the device (mps/cpu).
- The application and the external inference server talk **over 127.0.0.1 inside the same Mac**. The application is not
  inside a container, so a rewrite such as `host.containers.internal` is not needed.

## 2. Use "the same revision as the package" of bge-m3 / bge-reranker-v2-m3 for the models

- Embedding model: **BAAI/bge-m3, snapshot revision `5617a9f61b028005a4858fdac845db406aefb181`**
- Rerank model: **BAAI/bge-reranker-v2-m3**
- **If the revision differs, the numbers of the vectors change, they mix with the bundled vector collection, and the search ranking breaks.**
- Where to save: `store/models/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181/` of this package (the HF cache format).
  Under `store/models`, do not place it in any place other than this form.
  When `models.embedding.path` in `mas/mas.yaml` is `''`, it is resolved read-only from this same place as the application.
  Write the path only when you have placed it somewhere else.
- In the unlikely event that the revision differs, at startup and at publish, the warning "ベクターコレクションの埋め込み識別と現在の経路が
  食い違っています" (the embedding identity of the vector collection and the current path disagree) is **explicitly shown on the screen and in the log**
  (§9-4 consistency check). If the warning appears, either align the revisions or rebuild everything.

## 3. How to write the specification of the call destination

The default of `cynovela.yaml` (move only the rerank outside):

```yaml
reranker:
  provider: cross_encoder
  model: BAAI/bge-reranker-v2-m3
  device: external                 # external = 外部の推論サーバへ出す / cpu / mps = アプリ内で回す
  base_url: http://localhost:18850
  top_n: 5

embedding:
  provider: local                  # 既定はアプリ内。外へ出すなら openai_compat
  device: mps                      # local_cpu / mps / external_accelerator
  model: BAAI/bge-m3
  base_url: ''
```

When you want to move the embedding to the external inference server too (to gather the inference onto 1 separate Mac, etc.):

```yaml
embedding:
  provider: openai_compat
  device: external_accelerator
  model: BAAI/bge-m3
  base_url: http://127.0.0.1:18850   # 別の Mac なら その Mac の IP:18850
```

If you changed the port, please match base_url to it. It can also be changed from the administration screen (Settings > Embedding).

**A note for the case of moving it to a separate Mac**: because text will go outside the application, please set
`policy.allow_raw_content: false` in `mas/mas.yaml` on the external inference server side, so that it accepts
only what has already been masked.

## 4. The behavior when the endpoint is not there

- Rerank: when the external inference server cannot be reached, **it falls back to processing with the model inside the application (store/models)**
  (this package is all-in-one and bundles the rerank model). When you have not placed the rerank model,
  it does not rerank and returns the search results as they are. In either case the processing does not stop.
- Embedding (only when you have set it to go outside): when it cannot be reached, **it explicitly falls back to the local processing inside the application**,
  and **"⚠️ 外部の推論サーバに届かないためローカルへ退避中"** (falling back to local because the external inference server cannot be reached) is displayed on the administration screen (Settings > Embedding).
  It never becomes slow silently. If you set the endpoint up again, it automatically returns from the next embedding.

## 5. How to check that it is running

1. External inference server: `curl http://127.0.0.1:18850/health` → `"status":"ok"` (also
   `"reranker_loaded":true` if you use the rerank)
2. Start the application with `./launch.sh` → log in as an administrator
3. Throw 1 question → if `rerank_requests` has increased in `curl http://127.0.0.1:18850/metrics`
   of the external inference server, the rerank is being executed on the external inference server (MPS)
4. If you have also set the embedding to go outside, ingest (publish) 1 document and
   confirm that `embeddings_texts` in the same `/metrics` increases
   (if it is left at the default `provider: local`, it does not increase. This is normal)

Supplement: the image endpoint remains only an entry point for future use and is unimplemented (calling it gives 501).

---

# 日本語

本配布物 (ホスト直起動版) は `./launch.sh` で Mac のホスト上に直接立ち上がります。
コンテナはありません。

- **埋め込みは既定でこのアプリ自身が Mac の GPU (MPS) で回します。** 外部の推論サーバは要りません。
- **再ランクだけは既定で外部の推論サーバを呼びます** (`cynovela.yaml` の `reranker.device: external`)。
  外部の推論サーバが居なければアプリ内の同じモデルへ自動で退避するので、立てなくても動きます。

つまり外部の推論サーバは「必須」ではなく、**再ランクを外へ出す / 複数の Mac で 1 台に推論を寄せる**
ときに立てるものです。回答用 LLM (LM Studio 等) を別に立てるのと同じ考え方です。

## 1. 外部の推論サーバの立て方

外部の推論サーバを動かすには、`torch` / `sentence-transformers` / `fastapi` / `uvicorn` の4件が入った
python が要ります。**裸の `python` にはこの4件が入っていないことがほとんどです。**
アプリ本体を動かす環境 (conda の `cynovela-dist` または `.venv-cynovela`) とは別に、
外部の推論サーバ用の場所をこの配布物の中に作ってから立ててください。

```bash
# アプリと同じ Mac のホスト側で。まず、この配布物のフォルダへ移動します。
cd<この配布物のフォルダ>

# (1) 外部の推論サーバを動かす場所を、この配布物の中に作る。どちらか一方を選びます。
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
(39件) や `environment.yml` は、外部の推論サーバを立てる目的には使いません。

- 既定で `127.0.0.1:18850` に立ちます (変更は `mas/mas.yaml` の server.host / server.port)。
- 確認: `curl http://127.0.0.1:18850/health` が `"status":"ok"` を返せば稼働。
  再ランクまで使うなら同じ応答に `"reranker_loaded":true` が出ていること (0.2.0 以降)。
- `curl http://127.0.0.1:18850/capabilities` で モデル名・版 (revision)・デバイス (mps/cpu) が見えます。
- アプリと外部の推論サーバは**同じ Mac の中で 127.0.0.1 越し**に話します。アプリはコンテナの中に
  居ないので `host.containers.internal` のような読み替えは不要です。

## 2. モデルは bge-m3 / bge-reranker-v2-m3 の「配布物と同一の版」を使うこと

- 埋め込みモデル: **BAAI/bge-m3、snapshot 版 `5617a9f61b028005a4858fdac845db406aefb181`**
- 再ランクモデル: **BAAI/bge-reranker-v2-m3**
- **版が違うとベクトルの数値が変わり、同梱済みのベクターコレクションと混ざって検索順位が壊れます。**
- 保存先: この配布物の `store/models/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181/` (HF キャッシュ形式)。
  `store/models` 配下では、この形以外の場所に置かないでください。
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
  device: external                 # external = 外部の推論サーバへ出す / cpu / mps = アプリ内で回す
  base_url: http://localhost:18850
  top_n: 5

embedding:
  provider: local                  # 既定はアプリ内。外へ出すなら openai_compat
  device: mps                      # local_cpu / mps / external_accelerator
  model: BAAI/bge-m3
  base_url: ''
```

埋め込みも外部の推論サーバへ出したい場合 (推論を別の Mac 1 台に寄せる等):

```yaml
embedding:
  provider: openai_compat
  device: external_accelerator
  model: BAAI/bge-m3
  base_url: http://127.0.0.1:18850   # 別の Mac なら その Mac の IP:18850
```

ポートを変えた場合は base_url を合わせてください。管理画面 (設定 > Embedding) からも変更できます。

**別の Mac へ出す場合の注意**: アプリの外へ文字が出ることになるため、外部の推論サーバ側の
`mas/mas.yaml` で `policy.allow_raw_content: false` にして、マスキング済みのものだけを
受け付ける形にしてください。

## 4. 口が居ないときの振る舞い

- 再ランク: 外部の推論サーバに届かない場合、**アプリ内のモデル (store/models) での処理へ退避**します
  (本配布物は全部入りで、再ランクのモデルを同梱しています)。再ランクのモデルを置いていない
  場合は、再ランクを行わず検索結果をそのまま返します。どちらの場合も処理は止まりません。
- 埋め込み (外へ出す設定にしたときのみ): 届かない場合は**アプリ内のローカル処理へ明示的に退避**し、
  管理画面 (設定 > Embedding) に **「⚠️ 外部の推論サーバに届かないためローカルへ退避中」** と表示されます。
  黙って遅くなることはありません。口を立て直せば次回の埋め込みから自動復帰します。

## 5. 稼働確認のしかた

1. 外部の推論サーバ: `curl http://127.0.0.1:18850/health` → `"status":"ok"` (再ランクを使うなら
   `"reranker_loaded":true` も)
2. `./launch.sh` でアプリを起動 → 管理者でログイン
3. 質問を 1 回投げる → 外部の推論サーバの `curl http://127.0.0.1:18850/metrics` で
   `rerank_requests` が増えていれば、再ランクは外部の推論サーバ (MPS) で実行されています
4. 埋め込みも外へ出す設定にした場合は、資料を 1 本取り込み (publish) して
   同じ `/metrics` の `embeddings_texts` が増えることを確認してください
   (既定の `provider: local` のままなら増えません。これは正常です)

補足: 画像の口は将来用の入口のみで未実装 (呼ぶと 501) のままです。
