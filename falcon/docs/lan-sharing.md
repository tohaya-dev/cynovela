# LAN 共有・Tailscale 共有ガイド

**日本語版はこちら → [日本語](#日本語)**

## English

> **About this document**
> Cynovela is a completely unofficial learning tool, built so that one individual could
> understand the concepts behind AI infrastructure tools by working through them by hand.
> It is not a commercial product and not an official implementation.
> The implementation is entirely original, built on an OSS stack of
> FastAPI / SQLite / ChromaDB / BGE-M3 / a local LLM.
> It does not represent the official position of any company or product.

Cynovela listens on `0.0.0.0` by default. That means other machines on the same LAN (local
network) can reach it with no extra flags (original specification). If you want to close it off
to your own machine only, add `--local-only`. For access via Tailscale (a VPN service), or to
narrow down where access may come from, use the flags below.

---

## 1. Default behaviour (safest)

```bash
python server.py
```

- **Bind address**: `0.0.0.0` (`127.0.0.1` only when `--local-only` is added)
- **Clients that can access it**: only browsers and CLIs on the same machine
- **Seen from outside**: the port appears to be closed

Operated in this state, access over the network cannot occur in principle. This configuration
is recommended for verification and personal use.

---

## 2. LAN sharing mode

If you want to access Cynovela from another machine on the same LAN, add the `--lan` flag.

### 2-1. Startup command

```bash
python server.py --lan
```

This flag switches the bind address to `0.0.0.0` (all interfaces), making it connectable from
other machines on the LAN.

### 2-2. Connection example

If the LAN IP of the server machine is `192.168.1.20`, connect from a browser on another
machine as follows.

```
http://192.168.1.20:8765
```

### 2-3. IP allowlist

Cynovela has an IP allowlist feature. `127.0.0.1` and `localhost` are always permitted, but any
other source must be permitted explicitly. You can add source subnets with `--allow-subnet`.

```bash
python server.py --lan --allow-subnet 192.168.1.0/24
```

To specify more than one, repeat `--allow-subnet`.

```bash
python server.py --lan --allow-subnet 192.168.1.0/24 --allow-subnet 10.0.0.0/24
```

Requests from a source that is not permitted receive HTTP 403 Forbidden.

---

## 3. Tailscale sharing mode

With Tailscale you can connect over a VPN even between separate networks, such as home and a
remote location. Cynovela has an `--allow-tailscale` flag that automatically permits the
Tailscale subnet (`100.64.0.0/10`).

### 3-1. Preconditions

- The Tailscale client is installed on the server machine and logged in
- The connecting machine is logged in to the same Tailscale account
- The `tailscale ip -4` command returns a Tailscale IP on the server side

### 3-2. Startup command

```bash
python server.py --lan --allow-tailscale
```

### 3-3. Behaviour

- At startup it runs `tailscale ip -4` to detect the assigned Tailscale IP (3 second timeout).
- It automatically adds the `100.64.0.0/10` subnet to the IP allowlist.
- Clients connecting via Tailscale become able to connect.

To display the Tailscale name or IP of a source, run `tailscale status` on the Tailscale client
side.

---

## 4. Changing the port number

The default port is `8765`. You can change it with `--port`.

```bash
python server.py --lan --port 9000
```

Using a privileged port such as 80 or 443 requires administrator privileges, so going through a
reverse proxy (nginx, etc.) is recommended.

---

## 5. Security notes

LAN sharing and Tailscale sharing are convenient, but there are several risks to be aware of.

### 5-1. Communication is plaintext HTTP

The Cynovela main body listens over HTTP. HTTPS is not built in, so the contents of
communication travel as plaintext within the network. If you handle highly confidential
documents, consider one of the following.

- Access only over an encrypted VPN such as Tailscale
- Terminate TLS at a reverse proxy (nginx, etc.)

### 5-2. Direct exposure to the internet is prohibited

Given the incompleteness of authentication and the lack of encryption, you must absolutely
avoid exposing it directly to the internet side while bound to `0.0.0.0`.

### 5-3. Constraints of authentication

Authentication is JWT (issued by `POST /api/auth/login`), and is required even when started
with `--demo`. The legacy `Bearer demo-token-<user_id>` form has been abolished and is not
accepted. When sharing over a LAN, operate on the premise that only trusted users are on the
network.

### 5-4. Permission for file upload

Because the configuration can end up accepting file uploads from any user on the LAN, always
check the validation of the `path` argument of `/api/sources` and the upload limit setting
(`CYNOVELA_MAX_UPLOAD_BYTES`, default 100 MB).

### 5-5. Recommended configurations

Even for verification and learning use, one of the following is recommended.

- Fully local: add no flags and operate on `127.0.0.1` only
- Personal VPN: add only `--allow-tailscale` and avoid exposure to the LAN
- Restricted LAN: narrow the sources strictly with `--lan --allow-subnet`

---

## 6. Summary of related startup flags

| Flag | Default | Description |
|---|---|---|
| `--host` | `0.0.0.0` | Bind address (all addresses by default; narrow it with `--local-only`) |
| `--port` | `8765` | Port number |
| `--lan` | disabled | Explicitly set `host=0.0.0.0` and listen on all interfaces |
| `--allow-tailscale` | disabled | Permit the Tailscale subnet (`100.64.0.0/10`) |
| `--allow-subnet` | empty | Add a custom subnet (can be specified multiple times) |

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

Cynovela は既定で `0.0.0.0` で待ち受けます。つまり同じ LAN（ローカルネットワーク）内の他のマシンからは、追加のフラグ無しで到達できます（元仕様）。自分のマシンの中だけに閉じたい場合は `--local-only` を付けてください。Tailscale（VPN サービス）経由のアクセスや、アクセス元を絞りたい場合は、以下のフラグを使います。

---

## 1. 既定の動作（最も安全）

```bash
python server.py
```

- **バインドアドレス**: `0.0.0.0`（`--local-only` を付けたときだけ `127.0.0.1`）
- **アクセス可能なクライアント**: 同じマシン上のブラウザ・CLI のみ
- **外部から見ると**: ポートが閉じているように見える

この状態で運用すると、ネットワーク経由でのアクセスは原理的に発生しません。検証や個人利用にはこの構成が推奨です。

---

## 2. LAN 共有モード

同じ LAN 内の別マシンから Cynovela にアクセスしたい場合は `--lan` フラグを付けます。

### 2-1. 起動コマンド

```bash
python server.py --lan
```

このフラグはバインドアドレスを `0.0.0.0`（すべてのインターフェイス）に切り替え、LAN 内の他のマシンから接続可能になります。

### 2-2. 接続例

サーバー側マシンの LAN IP が `192.168.1.20` の場合、別マシンのブラウザから次のように接続します。

```
http://192.168.1.20:8765
```

### 2-3. IP アローリスト

Cynovela には IP アローリスト機能があり、`127.0.0.1` と `localhost` は常に許可されますが、それ以外の接続元は明示的に許可する必要があります。`--allow-subnet` で接続元サブネットを追加できます。

```bash
python server.py --lan --allow-subnet 192.168.1.0/24
```

複数指定する場合は `--allow-subnet` を繰り返します。

```bash
python server.py --lan --allow-subnet 192.168.1.0/24 --allow-subnet 10.0.0.0/24
```

許可されていない接続元からのリクエストには HTTP 403 Forbidden を返します。

---

## 3. Tailscale 共有モード

Tailscale を使えば、自宅と外出先など離れたネットワーク間でも VPN 経由で接続できます。Cynovela は Tailscale サブネット（`100.64.0.0/10`）を自動的に許可する `--allow-tailscale` フラグを備えています。

### 3-1. 前提

- Tailscale クライアントがサーバー側マシンにインストール・ログイン済みであること
- 接続元マシンも同じ Tailscale アカウントでログインしていること
- サーバー側で `tailscale ip -4` コマンドが Tailscale IP を返すこと

### 3-2. 起動コマンド

```bash
python server.py --lan --allow-tailscale
```

### 3-3. 動作

- 起動時に `tailscale ip -4` を実行して Tailscale 割り当て IP を検出します（タイムアウト 3 秒）。
- IP アローリストに `100.64.0.0/10` サブネットを自動追加します。
- Tailscale 経由のクライアントから接続できるようになります。

接続元の Tailscale 名や IP を表示するには、`tailscale status` を Tailscale クライアント側で実行してください。

---

## 4. ポート番号の変更

既定ポートは `8765` です。`--port` で変更できます。

```bash
python server.py --lan --port 9000
```

ポート 80 や 443 など特権ポートを使う場合は管理者権限が必要なため、リバースプロキシ（nginx 等）経由を推奨します。

---

## 5. セキュリティ上の注意

LAN 共有・Tailscale 共有は便利な反面、注意すべきリスクが複数あります。

### 5-1. 通信は HTTP 平文

Cynovela 本体は HTTP で待ち受けています。HTTPS 化は組み込まれていないため、通信内容はネットワーク内で平文流通します。機密性の高い文書を扱う場合は次のいずれかを検討してください。

- Tailscale など暗号化された VPN 経由でのみアクセスする
- リバースプロキシ（nginx 等）で TLS を終端する

### 5-2. インターネットへの直接公開は禁止

`0.0.0.0` でバインドしたままインターネット側に直接公開することは、認証の不完全さや暗号化の欠如を考慮すると、絶対に避けてください。

### 5-3. 認証の制約

認証は JWT（`POST /api/auth/login` が発行）で、`--demo` 起動でも必要です。旧 `Bearer demo-token-<user_id>` 形式は廃止済みで受理しません。LAN 共有時は信頼できるユーザーのみがネットワーク上にいる前提で運用してください。

### 5-4. ファイルアップロードの権限

LAN 内の任意のユーザーからファイルアップロードを受け付ける構成になり得るため、`/api/sources` の path 引数のバリデーションやアップロード上限の設定値（`CYNOVELA_MAX_UPLOAD_BYTES`、既定 100 MB）を必ず確認してください。

### 5-5. 推奨構成

検証・学習用途であっても、以下のいずれかを推奨します。

- 完全ローカル: 何もフラグを付けず `127.0.0.1` のみで運用
- 個人 VPN: `--allow-tailscale` のみ付与、LAN への暴露は避ける
- 限定 LAN: `--lan --allow-subnet` で接続元を厳密に絞る

---

## 6. 関連する起動フラグまとめ

| フラグ | 既定 | 説明 |
|---|---|---|
| `--host` | `0.0.0.0` | バインドアドレス（既定は全アドレス。絞るのは `--local-only`） |
| `--port` | `8765` | ポート番号 |
| `--lan` | 無効 | `host=0.0.0.0` を明示してすべてのインターフェイスで待ち受け |
| `--allow-tailscale` | 無効 | Tailscale サブネット（`100.64.0.0/10`）を許可 |
| `--allow-subnet` | 空 | カスタムサブネットを追加（複数指定可） |

---

最終更新: 2026-05-26 / Alpha GA 対応版
