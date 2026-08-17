#!/usr/bin/env python3
"""DD-CYN-0117 R-3: 2つのマニフェスト (environment.yml / requirements.txt) を突き合わせる。

なぜ要るか:
    公式の作り方は2段である。
      (1) conda env create -f environment.yml   ← conda 層 + pip 層の凍結スナップショット
      (2) pip install -r requirements.txt        ← pip 層の正本マニフェスト
    両方に載っている部品の版が食い違うと、(1) だけで環境を作った受け取り手は
    ./launch.sh --check のたびに「版が違う部品」を並べて見ることになる。
    M5 実測ではこれが 19 件出ていた。requirements.txt が正である。

使い方:
    python3 tools/check-manifests.py                     (この配布物を見る)
    python3 tools/check-manifests.py <配布物のルートディレクトリ> ...     (複数まとめて見る)

終了の値:
    0 = 食い違い 0 件
    1 = 食い違いあり (全数を並べて出す)

標準ライブラリだけで動く。部品が1つも入っていない python でも走る。
falcon / chewie で同一ファイルを保つこと。
"""
import os
import re
import sys

_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def _norm(name):
    """PEP 503 の正規化。python-multipart と python_multipart を同じものとして扱う。"""
    return re.sub(r"[-_.]+", "-", name).lower()


def _strip_comment(raw):
    return re.split(r"\s+#", raw)[0].strip()


def read_requirements(path):
    """requirements.txt を読む → {正規化した名前: (版, 元の行)}。版が固定でないものは None。"""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh.read().splitlines():
            line = _strip_comment(raw)
            if not line or line.startswith("#"):
                continue
            # 直接 URL の書き方 (spacy のモデル) は版の比較の対象にしない
            if "@" in line and "==" not in line.split("@")[0]:
                continue
            m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*([^\s;]+)", line)
            if m:
                out[_norm(m.group(1))] = (m.group(2), line)
                continue
            m = _NAME.match(line)
            if m:
                out[_norm(m.group(1))] = (None, line)
    return out


def read_environment(path):
    """environment.yml の pip: の下だけを読む → {正規化した名前: (版, 元の行)}。"""
    out = {}
    in_pip = False
    with open(path, encoding="utf-8") as fh:
        for raw in fh.read().splitlines():
            if re.match(r"^\s*-\s*pip:\s*$", raw):
                in_pip = True
                continue
            if not in_pip:
                continue
            # 字下げの無い行まで来たら pip: の節は終わり
            if raw.strip() and not raw.startswith(" "):
                break
            line = _strip_comment(raw)
            if not line.startswith("- "):
                continue
            line = line[2:].strip()
            m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*([^\s;]+)", line)
            if m:
                out[_norm(m.group(1))] = (m.group(2), line)
                continue
            m = _NAME.match(line)
            if m:
                out[_norm(m.group(1))] = (None, line)
    return out


def check_tree(root):
    """1つの配布物を見る → (食い違いの件数, 一致の件数)。"""
    req_path = os.path.join(root, "requirements.txt")
    env_path = os.path.join(root, "environment.yml")
    print(f"== {root} ==")
    for p in (req_path, env_path):
        if not os.path.isfile(p):
            print(f"  ❌ 見つかりません: {p}")
            return 1, 0

    req = read_requirements(req_path)
    env = read_environment(env_path)

    both = sorted(set(req) & set(env))
    same, diff, unpinned = [], [], []
    for name in both:
        rv, rline = req[name]
        ev, eline = env[name]
        if rv is None or ev is None:
            # 片方でも版が固定されていなければ、固定されていない側を直す対象にする
            unpinned.append((name, rv, ev))
        elif rv == ev:
            same.append(name)
        else:
            diff.append((name, rv, ev))

    print(f"  requirements.txt の宣言   : {len(req)} 件")
    print(f"  environment.yml (pip) の宣言: {len(env)} 件")
    print(f"  両方に載っている部品       : {len(both)} 件")
    print(f"  版が一致                  : {len(same)} 件")
    print(f"  版が違う                  : {len(diff)} 件")
    print(f"  片方が版を固定していない    : {len(unpinned)} 件")

    if diff:
        print("  -- 版が違う (名前 / requirements.txt / environment.yml) --")
        for name, rv, ev in diff:
            print(f"     {name:40s} 正本={rv:14s} env={ev}")
    if unpinned:
        print("  -- 片方が版を固定していない --")
        for name, rv, ev in unpinned:
            print(f"     {name:40s} 正本={rv} env={ev}")

    bad = len(diff) + len(unpinned)
    print("  → 食い違い 0 件" if bad == 0 else f"  → 食い違い {bad} 件")
    print()
    return bad, len(same)


def main(argv):
    roots = argv[1:]
    if not roots:
        # 既定はこのファイルの1つ上 (= 配布物のルートディレクトリ)
        roots = [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    total_bad = 0
    for root in roots:
        bad, _ = check_tree(root)
        total_bad += bad
    if total_bad:
        print(f"食い違いが {total_bad} 件あります。requirements.txt (正本) に合わせてください。")
        return 1
    print("すべての部品で版が一致しています。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
