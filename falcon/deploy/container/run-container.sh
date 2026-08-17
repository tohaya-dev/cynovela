#!/usr/bin/env bash
# ============================================================
#  コンテナ (コンテナ) を組み立てて起動する「部品」。
#
#  entry-unify-20260802 (S-1):
#    これは受け取り手が直接叩くものではありません。入口は ../../launch.sh の1本です。
#    この部品は launch.sh からだけ呼ばれます (launch.sh が --from-entry を渡す)。
#    取り込み元の管理引数 (--add / --add-path / --list / --remove) は launch.sh へ移しました。
#    ここに残るのは、入口から渡されて実際に組み立てる仕事だけです。
#
#  入口から渡される引数: [MODE] [--demo] [--local-only] [--ingest <パス> ...]
#                        [--sync-labels <Bearerトークン>]
#    MODE: full|text|lite|lite-en|minimal (既定 text)
#    --demo: ダミー資料が載ったデモで起動する。付けなければ本番 (空のデータベース)。
#    --local-only: 自マシン内だけに絞る (publish を 127.0.0.1 に限定)。既定は LAN 公開 (元仕様)。
#  決めごとの入手元: cynovela.yaml (server.port / container.name / container.image /
#  container.volume_prefix)。入口からは指定 (--from-entry / --hostport) だけを受ける。
#
# multi-ingest-roots-20260728: 取り込み元はバックアップファイル (store/ingest-roots.json) に登録した
#   複数のルートを /app/ingest/<中の名前> へ読み取り専用 (:ro) で個別マウントする方式。
#   取り込み元はバックアップ (store/ingest-roots.json) から決まる。
# ============================================================
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

# 入口を1本にするための門。直接叩かれたときは、何もせず入口を示す。
# 印は環境変数ではなく指定 (--from-entry) で受ける。
FROM_ENTRY=0
for _a in "$@"; do [ "$_a" = "--from-entry" ] && FROM_ENTRY=1; done
if [ "$FROM_ENTRY" != "1" ]; then
  echo "このスクリプトは単体で使うものではありません。" >&2
  echo "起動の入口は1本です:  $REPO/launch.sh" >&2
  echo "" >&2
  echo "  ./launch.sh              本番 (空のデータベース) で起動" >&2
  echo "  ./launch.sh --demo       同梱のダミー資料が載ったデモで起動" >&2
  echo "  ./launch.sh --help       そのほかの使い方" >&2
  exit 2
fi
# 決めごとは cynovela.yaml 1本から読む。環境変数では受け取らない。
#   コンテナの名前は入口 (launch.sh) と同じ1つの値であり、途中で読み替えない。
CONF_REPO="$REPO"
. "$REPO/tools/conf.sh"
IMG="$(conf_get_or container image "$CONF_DEFAULT_IMAGE")"
NAME="$(conf_get_or container name "$CONF_DEFAULT_CNAME")"
HOSTPORT="$(conf_get_num server port 8801)"
# データ用 named volume の接頭辞 (既定 cyn = 従来名 cyn-db/cyn-vec/cyn-bk)。
VOLPREFIX="$(conf_get_or container volume_prefix "$CONF_DEFAULT_VOLPREFIX")"
# Q-1: モデルの保存先。入口 (tools/launch-body.sh) と同じ1行を読む。
#   空なら従来どおり、この配布物の中の store/models を使う。
MODEL_ROOT="$(conf_get paths models_dir)"
if [ -z "$MODEL_ROOT" ]; then
  MODEL_ROOT="$REPO/store/models"
else
  case "$MODEL_ROOT" in "~/"*) MODEL_ROOT="$HOME/${MODEL_ROOT#\~/}" ;; esac
fi
ROOTS_FILE="$REPO/store/ingest-roots.json"
ROOTS_HELPER="$REPO/scripts/ingest_roots.py"

_roots() { python3 "$ROOTS_HELPER" --file "$ROOTS_FILE" "$@"; }

# バックアップの roots 配列を PUT /api/settings 用の {"ingest.roots": "<JSON文字列>"} に整形する
# portable-roots-20260808 (F-2): 生の JSON を直に読むと、配布物のルートディレクトリからの
#   相対の書き方 ("@app/…") がそのまま画面の表示写像へ流れる。∴ バックアップを読む側は
#   scripts/ingest_roots.py に一本化し、解いたホスト側の絶対パスだけを送る。
_roots_payload() {
  _roots list | python3 -c '
import json, sys
roots = json.load(sys.stdin) or []
print(json.dumps({"ingest.roots": json.dumps(roots, ensure_ascii=False)}, ensure_ascii=False))
'
}

# ingest.roots を PUT する。$1=Bearer トークン。HTTP コードを echo し、200 なら 0 を返す。
_put_roots() {
  local _tok="$1" _code
  _code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -X PUT \
    -H "Authorization: Bearer ${_tok}" -H 'Content-Type: application/json' \
    -d "$(_roots_payload)" "http://127.0.0.1:${HOSTPORT}/api/settings" 2>/dev/null || true)
  echo "$_code"
  [ "$_code" = "200" ]
}

MODE="text"
LOCAL_ONLY=0
DEMO=0
INGEST_ADDS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --from-entry) : ;;
    --hostport)
      [ $# -ge 2 ] || { echo "usage: --hostport <番号>" >&2; exit 2; }
      HOSTPORT="$2"; shift ;;
    --local-only) LOCAL_ONLY=1 ;;
    --demo) DEMO=1 ;;
    full|text|lite|lite-en|minimal) MODE="$1" ;;
    --ingest)
      [ $# -ge 2 ] || { echo "usage: --ingest <パス>" >&2; exit 2; }
      INGEST_ADDS+=("$2"); shift ;;
    # entry-unify-20260802: --add / --add-path / --list / --remove は launch.sh へ移した。
    #   受け取り手が2本のスクリプトを使い分ける形をやめ、入口を1本にするため。
    --sync-labels)
      [ $# -ge 2 ] || { echo "usage: --sync-labels <Bearerトークン>" >&2; exit 2; }
      if _c=$(_put_roots "$2"); then
        echo "[roots] ingest.roots を送信しました (HTTP ${_c})"
        exit 0
      else
        echo "[roots] 送信に失敗しました (HTTP ${_c})。トークンと起動状態を確認してください" >&2
        exit 1
      fi ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

# --ingest <パス>: バックアップに登録してから通常起動へ進む
for _p in ${INGEST_ADDS[@]+"${INGEST_ADDS[@]}"}; do
  _name=$(_roots add "$_p")
  echo "[roots] 登録: ${_name} <- ${_p}"
done

# KEY-PERSIST 20260724: 鍵はコンテナの外 (ホスト側 $REPO/keys/secret.key) に置き、読み取り専用で
# つなぐ。イメージ/コンテナ内に鍵を生成させない (コンテナ再作成で鍵消失した 2026-07 事故の再演防止)。
KEYFILE="$REPO/keys/secret.key"
if [ ! -f "$KEYFILE" ]; then
  mkdir -p "$REPO/keys"
  if [ -f "$REPO/store/secret.key" ]; then
    # bundled-config-20260731: 同梱の金庫鍵 (dist-vault-key-20260729 で store/secret.key に
    #   置かれる) を初期値にする。従来はここで必ず新しい乱数鍵を作っていたため、同梱デモの
    #   本文がその鍵では復号できず、**管理者でも原文が読めない** 状態で配っていた
    #   (役割による見え方が成立しない)。鍵をホスト側に置いて読み取り専用でつなぐという
    #   KEY-PERSIST 20260724 の作りは変えていない。変えたのは最初に書く中身だけ。
    cp "$REPO/store/secret.key" "$KEYFILE"
    echo "[key] seeded keys/secret.key from bundled store/secret.key"
  else
    # 同梱鍵が無い場合 (自分でツリーから起動する開発時など) は従来どおり新規生成する。
    # Fernet 鍵 = 32byte の urlsafe base64 (44 文字)
    openssl rand 32 | base64 | tr '+/' '-_' > "$KEYFILE"
    echo "[key] generated new secret.key at $KEYFILE (mode 600)"
  fi
  chmod 600 "$KEYFILE"
fi

# bundled-config-20260731: モデル保存先が無いまま podman へ渡すと、bind 元不在で
#   'Error: statfs ... no such file or directory' という素の失敗になり、受け取り手には
#   何をすればよいか分からない。軽量版は store/models を同梱しないため必ずここに当たる。
#   先に自分で検出して、docs/SETUP-ACCELERATOR.md の手順を名指しで示す。
if [ ! -d "$MODEL_ROOT" ]; then
  echo "[models] 埋め込みモデルの保存先がありません: $MODEL_ROOT" >&2
  echo "[models] この配布物はモデルを同梱していません。次のどちらかで進められます。" >&2
  echo "[models]   A) ダウンロードする:  ./launch.sh --fetch-model" >&2
  echo "[models]      ※ ダウンロード元とネットの具合によっては失敗することがあります。" >&2
  echo "[models]   B) 持っているフォルダをつなぐ: cynovela.yaml の paths: の models_dir: に" >&2
  echo "[models]      models--BAAI--bge-m3 が入っているフォルダの場所を書く" >&2
  echo "[models] 保存先の形は docs/SETUP-ACCELERATOR.md の手順に合わせてください。" >&2
  exit 2
fi

echo "[build] context=$REPO"
podman build -t "$IMG" -f "$REPO/deploy/container/Containerfile" "$REPO"

echo "[run] mode=$MODE port=$HOSTPORT"
# bundled-config-20260731: 既定では受け取り手の持ち物を消さない。
#   従来はここで `podman rm -f "$NAME"` を無条件に実行していた。$NAME の既定は当時
#   1つの固定値だったので、受け取り手が同じ名前のコンテナを既に持っていると、文書どおりの
#   起動をしただけで確認も無く消えた (2>/dev/null || true で消したことすら見えない)。
#   置き換えるのは、この配布物が作ったコンテナ (Containerfile のマーカーつき) だけにする。
#   マーカーの無い同名のコンテナが在るときは消さずに止め、別の名前で起動する方法を示す。
if podman container exists "$NAME" 2>/dev/null; then
  _owner="$(podman inspect "$NAME" --format '{{index .Config.Labels "org.cynovela.artifact"}}' 2>/dev/null || true)"
  if [ "$_owner" = "cynovela-container" ]; then
    # 同じ名前のコンテナが在るときは消さない。
    #   以前はここで podman rm -f して作り直していた。持ち主が同じでも、消せばそのコンテナに
    #   付いていたものは戻せない。止まっているだけなら、そのまま起こす (掛け直しはこの道)。
    _st="$(podman inspect "$NAME" --format '{{.State.Running}}' 2>/dev/null || echo false)"
    if [ "$_st" = "true" ]; then
      echo "'$NAME' は既に動いています。二重には起動しません。"
      echo "  開く場所: http://127.0.0.1:${HOSTPORT}/"
      exit 0
    fi
    # 束縛 (取り込み元・口) はコンテナを作ったときにしか張れない。
    # いまの決めと食い違うまま起こすと、足したはずの取り込み元が読めないなど、
    # 画面と実体がずれる。食い違うときは消さずに、消し方を添えて知らせる。
    _now_port="$(podman inspect "$NAME" --format '{{range $p, $c := .HostConfig.PortBindings}}{{range $c}}{{.HostPort}}{{end}}{{end}}' 2>/dev/null || true)"
    _now_roots="$(podman inspect "$NAME" --format '{{json .Mounts}}' 2>/dev/null | python3 -c "
import json,sys
try:
    ms = json.load(sys.stdin) or []
except Exception:
    ms = []
print(''.join(sorted(
    str(m.get('Destination','')) + '=' + str(m.get('Source',''))
    for m in ms if str(m.get('Destination','')).startswith('/app/ingest/'))))
" 2>/dev/null || true)"
    _want_roots="$(_roots list 2>/dev/null | python3 -c "
import json,sys
try:
    rs = json.load(sys.stdin) or []
except Exception:
    rs = []
print(''.join(sorted(
    '/app/ingest/' + str(r.get('name','')) + '=' + str(r.get('host_path',''))
    for r in rs)))
" 2>/dev/null || true)"
    if [ "$_now_port" != "$HOSTPORT" ] || [ "$_now_roots" != "$_want_roots" ]; then
      echo "エラー: '$NAME' という名前のコンテナが既にありますが、いまの決めと食い違います。" >&2
      [ "$_now_port" != "$HOSTPORT" ] && echo "       ポート番号: いまのコンテナ=$_now_port / 設定=$HOSTPORT" >&2
      [ "$_now_roots" != "$_want_roots" ] && echo "       取り込み元の顔ぶれが変わっています。" >&2
      echo "       束縛はコンテナを作るときにしか張れないため、そのままでは反映できません。" >&2
      echo "       消さずに止めました。反映するには、そのコンテナを片づけてから、もう一度お試しください:" >&2
      echo "         podman rm -f '$NAME'" >&2
      echo "       ※ 読み込んだ資料と設定は保存領域 (${VOLPREFIX}-db ほか) に残るため、片づけても消えません。" >&2
      exit 2
    fi
    echo "[run] 以前の $NAME (この配布物が作ったもの) を、消さずにそのまま起こします"
    podman start "$NAME" >/dev/null || {
      echo "エラー: '$NAME' を起こせませんでした。" >&2
      echo "       中身を確かめる:  podman logs '$NAME'" >&2
      exit 2
    }
    echo "[wait] http://127.0.0.1:${HOSTPORT}/"
    for i in $(seq 1 60); do
      code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 4 "http://127.0.0.1:${HOSTPORT}/" 2>/dev/null || true)
      [ "$code" = "200" ] && { echo "ready ($((i*3))s)"; break; }
      sleep 3
    done
    echo "[hint] 開く場所と口の決めは、このコンテナを作ったときのものが続きます。"
    echo "       設定 (cynovela.yaml) を変えたものを効かせるには、いったん片づけてください:"
    echo "         podman rm -f '$NAME'"
    exit 0
  else
    echo "エラー: '$NAME' という名前のコンテナが既にあります。" >&2
    echo "       この配布物が作ったものではないため、消さずに止めました。" >&2
    echo "       別の名前で起動するには: cynovela.yaml の container.name を変えてください。" >&2
    echo "       そのコンテナが不要な場合は、ご自身で podman rm -f '$NAME' を実行してください。" >&2
    exit 2
  fi
fi
# LAN-RESTORE 20260724: 既定=全アドレス向け公開。
# 外部アクセスは cynovela.yaml の server.host で決まる。
#   0.0.0.0 (既定) = 同じネットワークの他の端末からも開ける
#   127.0.0.1      = この Mac の中からだけ開ける
#   --local-only の指定は、設定より強く効く (その場だけ絞る指定として残す)。
PUBLISH="${HOSTPORT}:8765"
_bind="$(conf_get_or server host 0.0.0.0)"
case "$_bind" in
  127.0.0.1|localhost) PUBLISH="127.0.0.1:${HOSTPORT}:8765" ;;
esac
[ "$LOCAL_ONLY" = "1" ] && PUBLISH="127.0.0.1:${HOSTPORT}:8765"

# C-B3 20260729: 起動引数をイメージへ焼き込まない方式へ移行した。Containerfile の ENTRYPOINT は
#   python server.py --host 127.0.0.1 --port 8765 だけになり、従来イメージに焼き込まれていた
#   --demo / --lan / --allow-subnet ×3 はここから明示的に渡す。引数なしで本スクリプトを実行した
#   ときの渡し値は従来の焼き込み値と同一 (同梱デモ・全アドレス待ち受け・コンテナ網3件の許可)。
#   --host は後勝ち (append ではない) なので、ENTRYPOINT の 127.0.0.1 を 0.0.0.0 で上書きできる。
#   --lan は渡さない: server.py の --lan は「host が 127.0.0.1 のときだけ 0.0.0.0 に上げる」後方互換の
#   分岐 (server.py:3519) であり、--host 0.0.0.0 を明示する本方式では効果がないため。
BINDHOST="0.0.0.0"
ALLOW_SUBNETS=(10.0.0.0/8 172.16.0.0/12 192.168.0.0/16)
# --local-only の効き方について (実測 2026-07-29・podman 5.8.2 / applehv):
#   コンテナ内の待ち受けを 127.0.0.1 に絞ると publish が中まで届かない (ENTRYPOINT 既定のまま
#   -p 19060:8765 で公開して 120 秒間 HTTP 000)。中への転送先はコンテナ側アドレスであって
#   コンテナ内 loopback ではないため、両立しない。
#   また API ガードから見える送信元は publish の絞りに関わらず 192.168.127.1 (VM ゲートウェイ) で、
#   -p 127.0.0.1:… でも -p 0.0.0.0:… でも同じ値だった。よって許可サブネットを絞ると
#   --local-only のときだけ 403 になり publish が届かなくなる。
#   したがって自マシン内へ絞る境界は publish 側 (上の PUBLISH) が受け持ち、コンテナ内の待ち受けは
#   常に 0.0.0.0、許可サブネットも共通とする (「publish が届く方を優先」)。
# startup-default-20260730: コンテナ形態も「引数なし=本番 / --demo=デモ」の2通りに揃える。
#   従来はここで --demo を無条件に付けており「コンテナだけは常にデモ」の例外だった。
APP_ARGS=(--mode "$MODE" --host "$BINDHOST")
if [ "$DEMO" = "1" ]; then APP_ARGS=(--demo "${APP_ARGS[@]}"); fi
for _sn in "${ALLOW_SUBNETS[@]}"; do APP_ARGS+=(--allow-subnet "$_sn"); done
echo "[run] publish=$PUBLISH args=${APP_ARGS[*]}"

# multi-ingest-roots-20260728: 取り込み元マウントの決め方。
#   tmpfs を /app/ingest に重ね (イメージ焼き込みの ingest/ を隠す)、
#      バックアップの各 root を /app/ingest/<中の名前> へ :ro で子マウント。ルート0件なら tmpfs のみ (空)。
# B3/B4:
#   B3 = ルートが1件も無いときは、この配布物の中のダミー資料 (dummy-corpus) をルートにする (決定 9-3)。
#        場所は起動のたびに $REPO から解き直す。バックアップへ展開先の絶対の場所を焼き付けない。
#   B4 = 画面からルートを足せるようにするため、バックアップそのものをコンテナへ読み書きで渡す。
#        (コンテナの中の /app/store/ingest-roots.json = ホストの $ROOTS_FILE)
#        新しく足したルートが実際に読めるようになるのは、次に ./launch.sh を叩いたときである
#        (コンテナへの束縛は起動時にしか張れないため)。画面にもその旨を出す。
python3 - "$ROOTS_FILE" <<'PYEOF'
import json, os, sys
p = sys.argv[1]
os.makedirs(os.path.dirname(p), exist_ok=True)
if not os.path.isfile(p):
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "roots": [], "used_names": {}}, f, ensure_ascii=False, indent=2)
PYEOF

INGEST_MOUNTS=()
if true; then
  # notmpcopyup: podman は既定でイメージ側 /app/ingest の中身 (焼き込みの ingest/) を tmpfs へ
  # コピーする (tmpcopyup)。余分なルートに見えるためコピーを止める (実測 2026-07-28: 無指定だと sub1 等が出た)。
  INGEST_MOUNTS+=(--mount "type=tmpfs,destination=/app/ingest,notmpcopyup")
  _root_n=0
  while IFS=$'\t' read -r _rname _rpath; do
    [ -n "$_rname" ] && [ -n "$_rpath" ] || continue
    INGEST_MOUNTS+=(-v "${_rpath}:/app/ingest/${_rname}:ro")
    echo "[roots] mount: /app/ingest/${_rname} <- ${_rpath} (:ro)"
    _root_n=$((_root_n + 1))
  done < <(_roots mount-args)
  # B3: 1件も足されていないときは、同梱のダミー資料をそのままルートにする。
  if [ "$_root_n" = "0" ]; then
    if [ -d "$REPO/dummy-corpus" ]; then
      INGEST_MOUNTS+=(-v "$REPO/dummy-corpus:/app/ingest/dummy-corpus:ro")
      DEFAULT_INGEST_USED=1
      echo "[roots] 取り込み元が1件も足されていないので、同梱のダミー資料をルートにします"
      echo "[roots] mount: /app/ingest/dummy-corpus <- $REPO/dummy-corpus (:ro)"
    else
      DEFAULT_INGEST_USED=0
      echo "[roots] 取り込み元が1件もありません。画面の 設定 → 取り込み元、または"
      echo "[roots] ./launch.sh --add で足してください"
    fi
  fi
fi

# この Mac が使っている時間帯を、そのままコンテナへ渡す。
#   なぜ要るか: コンテナは自分の中に「いま何時か」を持つ。何も渡さなければ世界標準時になる。
#   画面に出る時刻には2種類あり、ブラウザが直して出すものは機材の時間になるが、
#   コンテナが自分の時計で文字にしたもの (ワークスペースの名前に焼き付く時刻など) は
#   世界標準時のまま出る。∴ 同じ出来事が、時間帯の差だけずれた2つの顔を持つ。
#   読み出すのは機材の設定そのものであり、特定の国を書き込んでいない。
#   ∴ 海外で使う受け取り手なら、その国の時間になる。
#   読み出せなかったときは何も渡さない。世界標準時のまま動くだけで、止まらない。
TZ_ARGS=()
_host_tz="$(readlink /etc/localtime 2>/dev/null | sed -n 's|.*/zoneinfo/||p')"
if [ -n "$_host_tz" ]; then
  TZ_ARGS=(-e "TZ=${_host_tz}")
  echo "[tz] この Mac の時間帯をコンテナへ渡します: ${_host_tz}"
else
  echo "[tz] この Mac の時間帯を読み出せませんでした。渡さずに起こします (コンテナの中は世界標準時になります)"
fi

# models mounted read-only (9GB, not in image); data dirs are NAMED volumes (VM fs => SQLite WAL OK, NOT bind mounts)
podman run -d --name "$NAME" \
  -p "$PUBLISH" \
  ${TZ_ARGS[@]+"${TZ_ARGS[@]}"} \
  -v "$KEYFILE:/app/store/secret.key:ro" \
  -v "$MODEL_ROOT:/app/store/models:ro" \
  -v "${VOLPREFIX}-db:/app/store/db" \
  -v "${VOLPREFIX}-vec:/app/store/vector" \
  -v "${VOLPREFIX}-bk:/app/store/backups" \
  -v "$ROOTS_FILE:/app/store/ingest-roots.json" \
  ${INGEST_MOUNTS[@]+"${INGEST_MOUNTS[@]}"} \
  "$IMG" "${APP_ARGS[@]}"

echo "[wait] http://127.0.0.1:${HOSTPORT}/"
READY=0
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 4 "http://127.0.0.1:${HOSTPORT}/" 2>/dev/null || true)
  [ "$code" = "200" ] && { echo "ready ($((i*3))s)"; READY=1; break; }
  sleep 3
done

# C-B5 20260729: 固定トークンでの自動同期は廃止した。固定のパスワードは起動形態によらず
# 受け付けなくなったため (core/auth.py)、ここで自動同期を試みても必ず 401 になる。
# 取り込み元の表示写像は、ログインして得たトークンで --sync-labels を実行して合わせる。
if [ "$READY" = "1" ]; then
  echo "[hint] 取り込み元の表示写像は未同期です。画面にログインしたあと、"
  echo "       ./launch.sh --sync-labels <ログインで得たトークン> を実行してください"
fi

# 回答を作る LLM のつなぎ先。コンテナからホストの LLM へは host.containers.internal で届く。
# localhost 以外を宛先にするときは api_key にダミー文字列が要る。
# LM Studio は "Serve on Local Network" を有効にする (Ollama を使う場合は OLLAMA_HOST=0.0.0.0)。
echo "[hint] 回答を作る LLM は画面の Settings で設定します (Base URL と Model)。"
echo "       同梱の既定は LM Studio (http://host.containers.internal:1234)。"
echo "       Model は空欄 (auto) にせず、一覧から実在するチャット用モデルを選んでください。"
echo "       API から設定する場合のトークンは POST /api/auth/login で発行されたものを使います。"
