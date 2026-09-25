#!/usr/bin/env python3
"""製品の呼び名を一括で置き換える (元に戻せる形で)。

overnight-20260923 (A-2): Chewie → Tender の改名に使った道具。

使い方:
  python3 tools/rename-product.py --from chewie --to tender            # 何が変わるかを見るだけ
  python3 tools/rename-product.py --from chewie --to tender --apply    # 置き換える (台帳を書く)
  python3 tools/rename-product.py --revert tools/rename-product.chewie-to-tender.json
                                                                     # 台帳どおりに元へ戻す

置き換える形は 3 つ: 小文字 (chewie→tender)・頭文字だけ大文字 (Chewie→Tender)・
全部大文字 (CHEWIE→TENDER)。

置き換えないもの (呼び名ではなく、実在する「もの」の名前だから):
  1. 公開済みの配布物のファイル名 (cynovela-chewie-package-1.2.0.tar.gz など)。
     名前を変えると、GitHub に置いてある実物と文書の記載が食い違う。
  2. 公開済みの配布物を展開してできるフォルダの名前 (展開してできる chewie フォルダ・
     ~/Downloads/chewie・cd chewie など)。実物の中身がその名前だから。
     ただし「リポジトリのディレクトリツリー」を指す `chewie/` と、これから作る配布物の名前のひな形
     (cynovela-chewie-package-<版>) は置き換える (prep-tender-20260925 A。
     TREE_LINE_MARKERS・FORCE_FILES を参照)。
  3. 「実測」を含む行 (その時点の記録。当時の名前のまま残す)。
  4. EXCLUDE_FILES に挙げたファイル (変更履歴・フォルダのツリーを指す組み立て道具のコメント・
     falcon のツリーと同一内容を保つファイル)。

台帳 (JSON) には、ファイルごとに「置き換え後の内容の sha256」と「置き換えた位置」を
残す。--revert は sha256 が一致するファイルだけを戻す (その後に手が入ったファイルは
戻さずに名前を出す)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

SKIP_DIRS = {
    ".git", ".condapack-cynovela", "node_modules", "__pycache__", "store",
    "models", ".pytest_cache", ".mypy_cache",
}
SELF = os.path.basename(__file__)
# 丸ごと触らないファイル: 過去の記録 (変更履歴) と、フォルダのツリーの名前として書いている
# 組み立て用の道具のコメント。どちらも「当時の/実在するフォルダの」名前である。
# もう1つ: 公開リポジトリで falcon のツリーと中身が完全に同じファイル。片方だけ書き換えると
# 「同一ファイルを保つこと」の約束が崩れるので、falcon 側と揃えて変えるときまで触らない。
EXCLUDE_FILES = {
    "docs/reference/changelog.md",
    "tools/build_clean_demo_db.py",
    "tools/check-manifests.py",
    "mas/mas_server.py",
}

# prep-tender-20260925 A: フォルダ名・配布物名まで広げた分。リポジトリのディレクトリツリーそのものを
# tender/ に改めるので、「リポジトリのディレクトリツリー」を指す書き方と、これから作る配布物の名前の
# ひな形は置き換える。公開済み 1.2.0 の配布物 (ファイル名と、展開してできる chewie
# フォルダの手順) は実物がそのままなので残す。
#   (a) `chewie/` を「リポジトリのディレクトリツリー」として書いた行 (tree / \u6728 / repository / リポジトリ /
#       "from `" / "から" を含む行)
#   (b) 版の代わりに <版> などと書いた、配布物の名前のひな形 (cynovela-chewie-package-<版>)
#   (c) FORCE_FILES のファイルは、履歴を書いた行 (印の語を含む行) 以外すべて
# 既存の文書は「ツリー」を漢字1字で書いているので、その字 (U+6728) を印に含める。
TREE_LINE_MARKERS = ("tree", "\u6728", "repository", "リポジトリ", "from `", "から")
FORCE_FILES = {
    # 組み立て道具のコメント。いまのツリーの形を書いた行は改め、過去の失敗の記録は残す。
    "tools/build-dist.sh": ("落ちていた", "混ざり"),
}


def _protect_patterns(old: str) -> list[re.Pattern]:
    o = re.escape(old)
    return [
        # 1. 版付きの配布物のファイル名
        #    (配布物の名前はフォルダ名から作られる。版の位置が <版> のような書き方でも同じ)
        re.compile(rf"cynovela-{o}-(?:package|models|all-in-one|lightweight)-", re.I),
        # 2. フォルダの実名
        re.compile(rf"(?:(?<=^)|(?<=[\s`'\"(>/*.]))(?:\.\./)?{o}/", re.I | re.M),
        re.compile(rf"Downloads/{o}\b", re.I),
        re.compile(rf"Cynovela/{o}\b", re.I),
        re.compile(rf"\bcd (?:\.\./)?(?:~/Downloads/)?{o}\b", re.I),
        re.compile(rf"`{o}`", re.I),
        re.compile(rf"<code>{o}</code>", re.I),
        re.compile(rf"\b{o}(?= ?(?:folder|フォルダ))", re.I),
        re.compile(rf"(?<=extracted ){o}\b|(?<=unpacked ){o}\b|(?<=展開済みの ){o}\b", re.I),
    ]


def _variants(old: str, new: str) -> list[tuple[str, str]]:
    return [(old.lower(), new.lower()), (old.capitalize(), new.capitalize()), (old.upper(), new.upper())]


def _iter_files(root: str):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f == SELF or (f.startswith("rename-product.") and f.endswith(".json")):
                continue
            p = os.path.join(d, f)
            if os.path.islink(p):
                continue
            yield p


def _read_text(p: str) -> str | None:
    try:
        with open(p, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\x00" in raw[:8192]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def plan_file(text: str, old: str, new: str, rel: str = "") -> list[tuple[int, str, str]]:
    """置き換える位置の一覧 [(元の内容での位置, 旧, 新)] を返す。"""
    o = re.escape(old)
    protected = [False] * len(text)
    for pat in _protect_patterns(old):
        for m in pat.finditer(text):
            for i in range(m.start(), m.end()):
                protected[i] = True
    # (a)(b)(c): 守りを外して置き換える側へ戻す
    force_markers = FORCE_FILES.get(rel)
    pos = 0
    for line in text.splitlines(keepends=True):
        if force_markers is not None:
            _hist = any(mk in line for mk in force_markers)
            for m in re.finditer(o, line, re.I):
                for i in range(pos + m.start(), pos + m.end()):
                    protected[i] = _hist  # 履歴の行は守り、それ以外は置き換える
        elif any(mk in line for mk in TREE_LINE_MARKERS):
            for m in re.finditer(rf"`{o}/`", line, re.I):
                for i in range(pos + m.start() + 1, pos + m.end() - 2):
                    protected[i] = False
        for m in re.finditer(rf"cynovela-({o})-(?:package|models|all-in-one|lightweight)-<", line, re.I):
            for i in range(pos + m.start(1), pos + m.end(1)):
                protected[i] = False
        pos += len(line)
    # 3. 「実測」を含む行は丸ごと残す
    pos = 0
    for line in text.splitlines(keepends=True):
        if "実測" in line:
            for i in range(pos, pos + len(line)):
                protected[i] = True
        pos += len(line)
    edits = []
    rx = re.compile(re.escape(old), re.I)
    vmap = dict(_variants(old, new))
    for m in rx.finditer(text):
        if any(protected[m.start():m.end()]):
            continue
        s = m.group(0)
        rep = vmap.get(s)
        if rep is None:  # 混在した大小 (cHeWie 等) は触らない
            continue
        edits.append((m.start(), s, rep))
    return edits


def cmd_rename(root: str, old: str, new: str, apply: bool, ledger_path: str, show: bool) -> int:
    # root は台帳の保存先からの相対で残す (機材ごとの絶対パスを台帳に書かない)
    ledger = {"from": old, "to": new,
              "root": os.path.relpath(os.path.abspath(root), os.path.dirname(os.path.abspath(ledger_path))),
              "files": {}}
    total = kept = 0
    for p in sorted(_iter_files(root)):
        text = _read_text(p)
        if text is None or not re.search(re.escape(old), text, re.I):
            continue
        rel = os.path.relpath(p, root)
        edits = plan_file(text, old, new, rel)
        n_all = len(re.findall(re.escape(old), text, re.I))
        kept += n_all - len(edits)
        if not edits:
            continue
        rel = os.path.relpath(p, root)
        if rel in EXCLUDE_FILES:
            kept += len(edits)
            continue
        total += len(edits)
        out, last, shift, recs = [], 0, 0, []
        for (i, s, r) in edits:
            out.append(text[last:i])
            out.append(r)
            recs.append([i + shift, s, r])  # 置き換え後の内容での位置
            shift += len(r) - len(s)
            last = i + len(s)
        out.append(text[last:])
        new_text = "".join(out)
        print(f"{len(edits):4d}  {rel}")
        if show:
            for (i, s, r) in edits:
                a = text.rfind("\n", 0, i) + 1
                b = text.find("\n", i)
                print("        | " + text[a:b if b >= 0 else None].strip()[:150])
        if apply:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
            ledger["files"][rel] = {
                "sha256_after": hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
                "edits": recs,
            }
    print(f"置き換え {total} 件 / 残した (配布物名・フォルダ名・実測の行) {kept} 件"
          + ("" if apply else "  ※ --apply を付けるまで書き換えない"))
    if apply:
        with open(ledger_path, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh, ensure_ascii=False, indent=1)
        print(f"台帳: {ledger_path}")
    return 0


def cmd_revert(ledger_path: str) -> int:
    with open(ledger_path, encoding="utf-8") as fh:
        ledger = json.load(fh)
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(ledger_path)), ledger["root"]))
    bad = 0
    for rel, info in ledger["files"].items():
        p = os.path.join(root, rel)
        text = _read_text(p)
        if text is None or hashlib.sha256(text.encode("utf-8")).hexdigest() != info["sha256_after"]:
            print(f"戻さない (置き換えの後に手が入っている): {rel}")
            bad += 1
            continue
        for pos, s, r in sorted(info["edits"], key=lambda e: e[0], reverse=True):
            assert text[pos:pos + len(r)] == r, (rel, pos)
            text = text[:pos] + s + text[pos + len(r):]
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print(f"戻した: {rel}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="old")
    ap.add_argument("--to", dest="new")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--show", action="store_true", help="置き換える行を表示する")
    ap.add_argument("--ledger")
    ap.add_argument("--revert", metavar="LEDGER")
    a = ap.parse_args()
    if a.revert:
        return cmd_revert(a.revert)
    if not a.old or not a.new:
        ap.error("--from と --to を指定してください (戻すときは --revert 台帳)")
    ledger = a.ledger or os.path.join(a.root, "tools", f"rename-product.{a.old.lower()}-to-{a.new.lower()}.json")
    return cmd_rename(a.root, a.old, a.new, a.apply, ledger, a.show)


if __name__ == "__main__":
    sys.exit(main())
