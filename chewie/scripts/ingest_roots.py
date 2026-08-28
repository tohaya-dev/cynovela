#!/usr/bin/env python3
"""multi-ingest-roots-20260728: 取り込み元のバックアップファイル (store/ingest-roots.json) の操作。

標準ライブラリのみ。falcon / chewie で同一ファイルを保つこと (書式・命名規則の一致が要件)。

バックアップファイル書式 (JSON):
  {"version": 1,
   "roots": [{"name": "<中の名前>", "host_path": "<Mac 側の実際の場所>",
              "label": "<画面に出す名前>"}],
   "used_names": {"<中の名前>": "<その名前を割り当てた host_path>"}}

中の名前の作り方:
  1. パスの末尾2階層から英小文字・数字・ハイフンのみを残し "-" で連結する。
  2. 空または既存と重複した場合はパス全体の sha256 先頭8文字を足す (空なら "src-" + 符号)。
  3. 32文字で打ち切る。
一度使った名前は used_names に残し、別のフォルダへは割り当てない (名前の使い回し禁止)。
root-name-reuse-20260729: ただし同じ host_path を外して再び追加したときだけは前と同じ名前に
戻す。既に登録済みのルートの name は決して付け替えない (取り込み済みの資料のパス解決が壊れるため)。
used_names は旧形式 (名前だけの文字列配列) も読み込める。旧形式の項目は対応先不明として
名前の予約だけを引き継ぎ、現に登録されているルートからは対応を補う。番号や符号を詰め直さない。

portable-roots-20260808 (F-2 / 決定 9-3):
  バックアップに書く host_path には、配布物のルートディレクトリからの相対の書き方 "@app/<以下の道>" を置ける。
  パッケージングの場で書き込む**既定の取り込み元だけ**がこの形になる (tools/build-dist.sh が
  add --portable で書く)。受け取り手が自分で足したものは、従来どおりその機材の絶対パスで
  保存する (決定 9-3 の運用と、既に足してあるバックアップの読み替えを起こさないため)。

  読み書きの境目はこの 1 ファイルに閉じている:
    _load()  … "@app/…" を、この機材での**絶対パス**へ解いて返す。
    _save()  … 読んだときに "@app/…" だった項目だけを、書き戻すときに再び "@app/…" に畳む。
  ∴ バックアップを読むすべての側 (server.py / routers/ / run-container.sh / launch.sh) は
    従来どおり絶対パスだけを見る。この仕組みのために 1 行も直していない。

  配布物のルートディレクトリの決め方は、この助っ人ファイル自身の保存先から解く
  (<配布物のルートディレクトリ>/scripts/ingest_roots.py)。保存先 (paths.data_dir) を移しても、
  コンテナの中 (/app/scripts/…) でも、同じ答えになる。--repo で明示もできる。
"""
import argparse
import hashlib
import json
import os
import sys

KEEP = set("abcdefghijklmnopqrstuvwxyz0123456789-")

# portable-roots-20260808: 配布物のルートディレクトリからの相対を表す前置き。
PORTABLE_PREFIX = "@app/"

# 読んだときに "@app/…" だった項目 (解いたあとの絶対パス) を覚えておき、_save で畳み直す。
# 同じプロセスの中で _load → 書き換え → _save と続く使い方だけを支えればよい。
_PORTABLE_SEEN: set = set()


def default_repo() -> str:
    """配布物のルートディレクトリ。この助っ人は必ず <ルート>/scripts/ingest_roots.py に置かれている。"""
    return _norm_repo(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _norm_repo(repo: str) -> str:
    """ルートの書き方を、足す側 (cmd_add の realpath) と同じ形に揃える。

    揃えないと、途中に近道 (symlink) が在るときに「配布物の中なのに外だ」と判定する。
    実測 2026-08-08: macOS の一時保存先 /var/folders/... は /private/var/folders/... の
    近道で、パッケージングの場がここに立つため --portable が必ず落ちた。
    """
    return os.path.realpath(os.path.expanduser(repo))


def resolve_path(host_path: str, repo: str) -> str:
    """バックアップに書かれた値を、この機材での絶対パスへ解く。"""
    if isinstance(host_path, str) and host_path.startswith(PORTABLE_PREFIX):
        return os.path.normpath(os.path.join(repo, host_path[len(PORTABLE_PREFIX):]))
    return host_path


def portable_form(abs_path: str, repo: str) -> str | None:
    """絶対パスが配布物の中なら "@app/…" を返す。外なら None (畳まない)。"""
    if not isinstance(abs_path, str) or not abs_path.startswith("/"):
        return None
    rel = os.path.relpath(abs_path, repo)
    if rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(rel):
        return None
    return PORTABLE_PREFIX + rel


def _sanitize(component: str) -> str:
    return "".join(c for c in component.lower() if c in KEEP)


def name_for(host_path: str, taken) -> str:
    parts = [p for p in host_path.rstrip("/").split("/") if p]
    toks = [t for t in (_sanitize(p) for p in parts[-2:]) if t]
    base = "-".join(toks)
    # 従来は「符号(8桁)を足してから base[:32] で切り詰め」ていたため、
    # 道筋の末尾が長いと避けるための符号ごと切り落とされ、再び衝突→SystemExit→サーバ全停止
    # になっていた。順序を改め「先に枠へ収めてから符号/連番を足す」ことで、避ける印が必ず
    # 32文字の枠に残るようにする。SystemExit もやめ、探し尽くしたときだけ通常の例外を投げて
    # 呼び出し側 (API) が読める文言で断れるようにする（サーバは落とさない）。
    # まず 32 文字の枠へ収めた形で衝突を判定する（従来は切り詰め前の base で判定し、
    # 切り詰め後に衝突する取りこぼしがあった）。
    base32 = base[:32]
    if base32 and base32 not in taken:
        return base32
    # 衝突する / 空 のときは、まず 8 桁の符号を「先に詰めた base」の後ろに足す。
    code = hashlib.sha256(host_path.encode("utf-8")).hexdigest()[:8]
    stem = base[: 32 - 1 - len(code)] if base else "src"
    candidate = f"{stem}-{code}"
    if candidate not in taken:
        return candidate
    # なお衝突するなら、末尾を連番で置き換えて空きを探す（枠内に必ず番号が残る）。
    for _i in range(1, 10000):
        suffix = f"-{_i}"
        head = candidate[: 32 - len(suffix)]
        alt = f"{head}{suffix}"
        if alt not in taken:
            return alt
    # ここまで空きが無いのは異常。SystemExit ではなく通常の例外にし、API に断らせる。
    raise ValueError(f"取り込み元の名前を割り当てられませんでした: {host_path}")


def used_map(data: dict) -> dict:
    """used_names を {中の名前: 割り当てた host_path} の対応に正規化して返す。

    root-name-reuse-20260729: 旧形式 (名前だけの文字列配列) も受ける。旧形式の項目は
    対応先不明 ("") として名前の予約だけを引き継ぎ、現に登録されているルートから対応を補う。
    data["used_names"] はこの呼び出しで対応表に置き換わる (以後の保存もこの形になる)。
    """
    raw = data.get("used_names") or []
    out = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            out[str(k)] = str(v or "")
    else:
        for n in raw:
            out[str(n)] = ""
    # 登録済みのルートは対応が自明なので補う (旧形式からの引き上げ経路でもある)
    for r in data.get("roots") or []:
        if r.get("name"):
            out[r["name"]] = r.get("host_path") or out.get(r["name"], "")
    data["used_names"] = out
    return out


def assign_name(data: dict, host_path: str) -> str:
    """host_path に付ける中の名前を決め、used_names へ記録して返す。

    1. 既に登録済みのルートなら、その名前をそのまま返す (名前は決して付け替えない)。
    2. 一度外した同じ host_path なら、used_names のバックアップから前と同じ名前を返す。
    3. どちらでもなければ name_for() で新しい名前を作る。既存の名前 (roots + used_names)
       は taken として避けるため、別のフォルダへ同じ名前が割り当たることはない。
    """
    for r in data.get("roots") or []:
        if r.get("host_path") == host_path:
            return r["name"]
    used = used_map(data)
    for _name, _hp in used.items():
        if _hp and _hp == host_path:
            return _name
    taken = set(used) | {r["name"] for r in (data.get("roots") or []) if r.get("name")}
    name = name_for(host_path, taken)
    used[name] = host_path
    return name


def _load(path: str, repo: str | None = None) -> dict:  # noqa: C901
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except ValueError:
            # _save の書き戻し (os.replace が使えない形態) の途中で落ちた
            # バックアップは本体が欠けるが、全文は .tmp 側に書き終わっている。そちらを読む。
            with open(path + ".tmp", "r", encoding="utf-8") as f:
                data = json.load(f)
    else:
        data = {"version": 1, "roots": []}
    data.setdefault("roots", [])
    data.setdefault("used_names", {})
    used_map(data)  # 旧形式 (文字列配列) をここで対応表へ正規化する
    # portable-roots-20260808: "@app/…" をこの機材の絶対パスへ解く。
    #   読む側 (server.py / routers/ / run-container.sh) には絶対パスだけを渡す。
    _repo = _norm_repo(repo) if repo else default_repo()
    for r in data["roots"]:
        _hp = r.get("host_path")
        if isinstance(_hp, str) and _hp.startswith(PORTABLE_PREFIX):
            r["host_path"] = resolve_path(_hp, _repo)
            _PORTABLE_SEEN.add(r["host_path"])
    for _n, _hp in list(data["used_names"].items()):
        if isinstance(_hp, str) and _hp.startswith(PORTABLE_PREFIX):
            _abs = resolve_path(_hp, _repo)
            data["used_names"][_n] = _abs
            _PORTABLE_SEEN.add(_abs)
    return data


def _save(path: str, data: dict, repo: str | None = None) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    # portable-roots-20260808: 読んだときに "@app/…" だった項目だけを畳み直す。
    #   受け取り手が自分で足したもの (絶対パスで入ってきたもの) はそのまま絶対で書く。
    _repo = _norm_repo(repo) if repo else default_repo()
    _out = json.loads(json.dumps(data, ensure_ascii=False))
    for r in _out.get("roots") or []:
        _hp = r.get("host_path")
        if _hp in _PORTABLE_SEEN:
            _p = portable_form(_hp, _repo)
            if _p:
                r["host_path"] = _p
    for _n, _hp in list((_out.get("used_names") or {}).items()):
        if _hp in _PORTABLE_SEEN:
            _p = portable_form(_hp, _repo)
            if _p:
                _out["used_names"][_n] = _p
    data = _out
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp, path)
    except OSError:
        # バックアップを1本の bind でコンテナへ渡す形態では、マウント点への
        # os.replace が EBUSY で失敗する (項9)。tmp に全文が書き
        # 終わっているので同じファイルへ書き戻す。途中で落ちても tmp が完全な
        # バックアップとして残り、_load が拾う。
        with open(path, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.unlink(tmp)


def cmd_add(args) -> int:
    repo = _repo_of(args)
    data = _load(args.file, repo)
    real = os.path.realpath(os.path.expanduser(args.path))
    if not os.path.isdir(real):
        print(f"error: not a directory: {real}", file=sys.stderr)
        return 2
    # portable-roots-20260808: --portable はパッケージングの場だけが使う。配布物の中を指す既定の
    #   取り込み元を、配布物のルートディレクトリからの相対でバックアップへ書き込むための指定である。
    #   配布物の外を指していたら畳めないので、黙って絶対で書かずに止める
    #   (パッケージングの場で気づかせる。受け取り手の機材で行き止まりになるより先に落とす)。
    if getattr(args, "portable", False):
        if portable_form(real, repo) is None:
            print(f"error: --portable but path is outside the app root: {real}", file=sys.stderr)
            return 2
        _PORTABLE_SEEN.add(real)
    for r in data["roots"]:
        if r["host_path"] == real:
            print(r["name"])
            return 0
    # root-name-reuse-20260729: 外したあとの再追加は前と同じ名前に戻す (assign_name がバックアップを引く)
    name = assign_name(data, real)
    label = args.label or os.path.basename(real.rstrip("/")) or real
    data["roots"].append({"name": name, "host_path": real, "label": label})
    _save(args.file, data, repo)
    print(name)
    return 0


def cmd_list(args) -> int:
    data = _load(args.file, _repo_of(args))
    print(json.dumps(data["roots"], ensure_ascii=False, indent=2))
    return 0


def cmd_remove(args) -> int:
    repo = _repo_of(args)
    data = _load(args.file, repo)
    before = len(data["roots"])
    data["roots"] = [r for r in data["roots"] if r["name"] != args.name]
    if len(data["roots"]) == before:
        print(f"error: no such name: {args.name}", file=sys.stderr)
        return 2
    # used_names には残す (別のフォルダへの名前の使い回しは禁止のまま)。
    # root-name-reuse-20260729: 対応先 host_path も残るので、同じフォルダを再び追加すると同じ名前に戻る。
    _save(args.file, data, repo)
    print(f"removed: {args.name}")
    return 0


def cmd_mount_args(args) -> int:
    data = _load(args.file, _repo_of(args))
    for r in data["roots"]:
        print(f"{r['name']}\t{r['host_path']}")
    return 0


def _repo_of(args) -> str:
    _r = getattr(args, "repo", None)
    return _norm_repo(_r) if _r else default_repo()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", required=True, help="バックアップファイル (store/ingest-roots.json) のパス")
    ap.add_argument("--repo", default=None,
                    help="配布物のルートディレクトリ (省略時はこの助っ人の保存先から解く)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add", help="ルートを1件追加し中の名前を出力")
    p.add_argument("path")
    p.add_argument("--label", default=None)
    p.add_argument("--portable", action="store_true",
                   help="配布物のルートディレクトリからの相対でバックアップへ書く (パッケージングの場だけが使う)")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("list", help="ルートの一覧を JSON で出力")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("remove", help="中の名前を指定して1件削除")
    p.add_argument("name")
    p.set_defaults(fn=cmd_remove)
    p = sub.add_parser("mount-args", help="name<TAB>host_path を1行ずつ出力")
    p.set_defaults(fn=cmd_mount_args)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
