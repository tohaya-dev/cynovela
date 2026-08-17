# 外部アクセラレータ (Mac Accelerator Service) の立て方 — 受け取り手向け 1 ページ

**日本語版はこちら → [日本語](#日本語)**

## English

**If you received the lightweight package, this procedure is mandatory.** The lightweight package does not bundle
the embedding model, and if you run the startup script without placing the model, it stops before starting
(it prints "埋め込みモデルの保存先がありません" = there is no location for the embedding model).
If you received the all-in-one package, the model is already bundled, so this procedure is not needed
(read it only if you want to use the external accelerator).
The container stays a light single image, and the embedding calls the
**Mac Accelerator Service (external accelerator)** that runs on the host side of the same Mac. It is the same
idea as the LLM used for answers (LM Studio and so on).

## 1. Bring up the external accelerator first

### 1-A. Leave it to the startup script (this is the default path)

When you run `./launch.sh`, a stage for the "external inference server" comes in before you choose the container
executable. What this stage does is the following.

1. It looks at whether `127.0.0.1:18850` responds. If it does, it goes straight on to the next step.
2. If not, it asks whether to create a place to run the external inference server **inside this package**.
   There are 5 choices: create it with `conda` / create it with `venv` / specify the location of python yourself /
   go on without using an external inference server / quit.
3. It creates the place by the chosen path, brings up the external inference server, and prints the `device` from `/health` on the screen.
4. If it could not bring it up, it prints what is missing on the screen and stops.
   It is not built to end up running on CPU without you noticing.

The place it creates is `.mas-env` (inside this package). **It writes nothing into conda's shared environments (envs).**
The components it installs are the 4 items written in `mas/mas-requirements.txt`.

You can also choose to go on without using an external inference server. In that case, the embedding is done on the CPU inside the container.

### 1-B. Bring it up by hand

This is the procedure for bringing it up without using the startup script.

```bash
# ホスト側 (コンテナの外) で。まず、この配布物のフォルダへ移動します。
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

If you already have a python that has the 4 items (`torch` / `sentence-transformers` / `fastapi` / `uvicorn`),
skip (1) and (2) and do (3) with that python.

- By default it comes up on `127.0.0.1:18850` (change it with server.host / server.port in `mas/mas.yaml`).
- To confirm: it is running if `curl http://127.0.0.1:18850/health` returns `"status":"ok"`.
- With `curl http://127.0.0.1:18850/capabilities` you can see the model name, the revision, and the device (mps/cpu).
- The records are written to `store/mas.log` (when brought up from the startup script).

### 1-C. About the components

`mas/mas-requirements.txt` contains 4 items. The `requirements.txt` for the main application (39 items) and
`environment.yml` are not used for the purpose of bringing up the external inference server. `environment.yml`
creates something in conda's shared location in the `name: cynovela` form, which is a different thing from the
path that creates it inside this package.

## 2. Use the "same revision as the package" of the bge-m3 embedding model

- Model: **BAAI/bge-m3, snapshot revision `5617a9f61b028005a4858fdac845db406aefb181`**
- **If the revision differs, the vector values change, they get mixed with the bundled vector collection
  (for 30 documents), and the search ranking breaks.**
- Location: **`store/models/models--BAAI--bge-m3/snapshots/<revision>/` (HF cache format) in this package is mandatory.**
  Because the startup script mounts `store/models` as read-only, it cannot start without this location.
  Which directory the external accelerator side reads can be specified separately with
  `models.embedding.path` in `mas/mas.yaml`.
- In the unlikely event that the revision differs, a warning to the effect of "the embedding identity and the current
  path do not match" is printed **explicitly on the screen and in the log** at startup and at publish time.
  If the warning appears, align the revision or rebuild everything.

## 3. How to write the destination

`cynovela.yaml` for the container form (the default of this package):

```yaml
embedding:
  provider: openai_compat
  device: external_accelerator     # 指定できる値: local_cpu / local_mps / external_accelerator
  model: BAAI/bge-m3
  base_url: http://host.containers.internal:18850   # コンテナから見たホスト側の宛先
```

- **When calling from the container**: `http://host.containers.internal:18850` (the bundled default value).
- **When starting server.py directly on the host**: change it to `http://127.0.0.1:18850`.
  `host.containers.internal` cannot be resolved outside the container.
- If you changed the port, match base_url to it.
  It can also be changed from the admin screen (Settings > Embedding).

## 4. Behavior when the accelerator is not there

- When the external accelerator cannot be reached, the embedding **explicitly falls back to the CPU inside the container**
  (the processing does not stop).
- While it is falling back, the admin screen (Settings > Embedding) shows
  **"⚠️ …(アクセラレータ)に届かないため、埋め込みはローカル(cpu)へ退避中です"**
  (the accelerator cannot be reached, so the embedding is falling back to local (cpu)). It never silently becomes slow.
  If you bring it up again, it automatically returns from the next embedding onward.

## 5. How to confirm it is running

1. Accelerator: `curl http://127.0.0.1:18850/health` → `"status":"ok"`
2. After starting the application, log in as an administrator → Settings > Embedding shows
   **"✅ …(アクセラレータ)接続中 (device: mps)"** (accelerator connected)
3. Ingest (publish) one document → if `embeddings_texts` has increased in
   `curl http://127.0.0.1:18850/metrics`, the embedding is being executed on the external accelerator (MPS)

Note: `/v1/rerank` is implemented (from 0.2.0 onward. It runs BAAI/bge-reranker-v2-m3 on MPS, and
`"reranker_loaded":true` appears in `/health`). When the accelerator can be reached, the rerank is also
executed externally (MPS). **The fallback destination when it cannot be reached differs by package type**:
the all-in-one uses the bundled rerank model (store/models) and reranks inside the container.
**The lightweight package does not have a rerank model** (what you place with this procedure is only the
bge-m3 for embedding, and the bge-reranker-v2-m3 for rerank is not included), so it does not rerank and
returns the search results as they are. In either case the processing does not stop (measured: when
`ExternalAcceleratorReranker._ensure_local()` in providers/reranker.py confirms there are no weights, it
treats it as having no fallback destination).
The image intake path is only defined for future use and is still unimplemented (calling it returns 501).

---

# 日本語

**軽量版を受け取った場合、この手順は必須です。** 軽量版は埋め込みモデルを同梱しておらず、
モデルを置かないまま起動用スクリプトを実行すると、起動する前に止まります
(「埋め込みモデルの保存先がありません」と表示されます)。
全部入りを受け取った場合はモデルが同梱済みなので、この手順は不要です
(外部アクセラレータを使いたい場合のみ読んでください)。
コンテナは軽い単一イメージのままで、埋め込みは同一 Mac のホスト側で動く
**Mac Accelerator Service (外部アクセラレータ)** を呼びます。回答用 LLM (LM Studio 等) と
同じ考え方です。

## 1. 外部アクセラレータを先に立てる

### 1-A. 起動用スクリプトに任せる (こちらが既定の道です)

`./launch.sh` を叩くと、コンテナの実行ファイルを選ぶ前に「外部の推論サーバ」の段が入ります。
この段が行うのは次のことです。

1. `127.0.0.1:18850` に応答があるかを見ます。あればそのまま次へ進みます。
2. 無ければ、外部の推論サーバを動かす場所を**この配布物の中に**作るかどうかを尋ねます。
   選べるのは `conda` で作る / `venv` で作る / 自分で python の場所を指定する /
   外部の推論サーバを使わずに進む / やめる の5つです。
3. 選ばれた道で場所を作り、外部の推論サーバを立て、`/health` の `device` を画面に出します。
4. 立てられなかったときは、何が足りないかを画面に出して止まります。
   気づかないまま CPU で動く形にはしていません。

作る場所は `.mas-env`（この配布物の中）です。**conda の共有の環境 (envs) には何も書きません。**
入れる部品は `mas/mas-requirements.txt` に書いた4件です。

外部の推論サーバを使わずに進むことも選べます。その場合、埋め込みはコンテナ内 CPU で行われます。

### 1-B. 手で立てる

起動用スクリプトを使わずに立てる場合の手順です。

```bash
# ホスト側 (コンテナの外) で。まず、この配布物のフォルダへ移動します。
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

既に4件 (`torch` / `sentence-transformers` / `fastapi` / `uvicorn`) が入っている python を
お持ちの場合は、(1) と (2) を飛ばし、その python で (3) を行ってください。

- 既定で `127.0.0.1:18850` に立ちます (変更は `mas/mas.yaml` の server.host / server.port)。
- 確認: `curl http://127.0.0.1:18850/health` が `"status":"ok"` を返せば稼働。
- `curl http://127.0.0.1:18850/capabilities` で モデル名・版 (revision)・デバイス (mps/cpu) が見えます。
- 記録は `store/mas.log` へ書かれます (起動用スクリプトから立てた場合)。

### 1-C. 部品について

`mas/mas-requirements.txt` の中身は4件です。本体アプリ用の `requirements.txt` (39件) や
`environment.yml` は、外部の推論サーバを立てる目的には使いません。`environment.yml` は
`name: cynovela` の形で conda の共有の場所へ作るものであり、この配布物の中に作る道とは別のものです。

## 2. 埋め込みモデルは bge-m3 の「配布物と同一の版」を使うこと

- モデル: **BAAI/bge-m3、snapshot 版 `5617a9f61b028005a4858fdac845db406aefb181`**
- **版が違うとベクトルの数値が変わり、同梱済みのベクターコレクション (資料30本ぶん) と
  混ざって検索順位が壊れます。**
- 保存先: **この配布物の `store/models/models--BAAI--bge-m3/snapshots/<版>/` (HF キャッシュ形式) は必須です。**
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
