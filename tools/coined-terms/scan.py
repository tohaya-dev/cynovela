#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""造語(当機の造語)の検出器 — DD-CYN-0123 J-8 / J-9

禁則#61 の造語を一般的な技術用語へ置き換える作業のために、
「どのファイルの何行目に、どの造語が残っているか」を数え上げる道具である。

--------------------------------------------------------------------------
使い方
--------------------------------------------------------------------------
  python3 tools/coined-terms/scan.py              # 走査して一覧を出す
  python3 tools/coined-terms/scan.py --json       # 機械可読(JSON)で出す
  python3 tools/coined-terms/scan.py --self-test  # 陽性対照(J-9)を回す
  python3 tools/coined-terms/scan.py --list-files # 走査対象のファイル一覧だけ出す

  終了コード: 0 = 検出0件(または自己診断合格) / 1 = 検出1件以上(または自己診断不合格)
              2 = 設定ファイルが読めない等の実行時エラー

  設定の差し替え(試験用):
    --root DIR      リポジトリルート(既定: このスクリプトの2つ上)
    --scope FILE    scan-scope.txt の代わり
    --terms FILE    terms.tsv の代わり
    --allowed FILE  allowed-words.tsv の代わり

--------------------------------------------------------------------------
入力(いずれもタブ区切り・`#` 始まりはコメント・空行は無視)
--------------------------------------------------------------------------
  tools/coined-terms/scan-scope.txt
      include      <glob>
      skip-file    <glob>  <理由>
      skip-region  <path>  <開始行の正規表現>  <終了行の正規表現>  <理由>
    include に挙がった glob に当たるファイル「だけ」を走査する(allowlist)。
    skip-region は開始行から終了行まで「両端を含めて」走査対象から外す。
    同一ファイルに複数回現れてよい。glob はリポジトリルートからの相対で、
    `**` の再帰マッチに対応する。

  tools/coined-terms/terms.tsv        <造語>  <置き換え先>  <備考(任意)>
  tools/coined-terms/allowed-words.tsv <語>   <理由>        <主な出現箇所>

--------------------------------------------------------------------------
J-8 で決めたこと: 語境界(\\b)は使わない。allowed-words による除外で塞ぐ。
--------------------------------------------------------------------------
誤検出(「六本木」が造語「木」で当たる)を語の切れ目で塞げるかを実測した。
結論は「塞げない」。Python の `re` の `\\b` は日本語に対して使えない。

実測した事実(2026-08-17 / Python 3.13.12):
  1. 漢字・ひらがな・カタカナはすべて Unicode カテゴリ Lo であり、
     `re` は これらを `\\w`(単語構成文字)と判定する。
       '木' \\w=True category=Lo   'を' \\w=True category=Lo
  2. `\\b` は `\\w` と `\\W` の間にしか立たない。日本語の文中は `\\w` が
     連続するため、`\\b` は文字列の端と ASCII 記号の隣にしか現れない。
       '木を数える' -> \\b の位置 [0, 5]      (文中に境界が無い)
       '六本木'     -> \\b の位置 [0, 3]
  3. その結果 `\\b木\\b` は、消したい誤検出だけでなく、
     残したい真の用例まで丸ごと落とす。
       '六本木ヒルズに行く' -> MISS  (消したい     … 消えるが)
       '木を数える'         -> MISS  (残したい真 … これも消える)
       'この木は大きい'     -> MISS  (残したい真 … これも消える)
    つまり `\\b` は「切れ目を見る」働きをせず、単に見落とし(偽陰性)を作る。
    見落としは、この作業では取りこぼしたまま公開する事故に直結するので採れない。

よって本器は「素の部分一致で全部拾い、allowed-words に載った語の一部として
現れている1件だけを落とす」方式を採る。落とす判定は出現位置で行う。
すなわち、造語の当たった区間 [s, e) を丸ごと含む allowed-word の出現区間
[as, ae) が同じ行にあるとき(as <= s かつ e <= ae)、その1件だけを検出しない。
同じ行に別の当たりがあれば、そちらは検出する。
この方式なら、除外は allowed-words.tsv に語を足すという形で目に見えて残り、
なぜ落としたのかを後から追える(`--json` の suppressed に理由が出る)。

あわせて「長い造語が先」を実装した。terms.tsv には「置き場所」と「置き場」、
「取り寄せる」と「取り寄せ」のように、短い造語が長い造語の一部になっている組があり、
素直に全部当てると同じ場所を二重に数えてしまう(実測で確認済み)。
そこで造語を長い順に当て、先に採った当たりの区間に丸ごと入る短い造語の当たりは
数えない。落とした分は `--json` の suppressed に suppressed_by="longer-term" で残る。
なお terms.tsv 自身も長い順に並んでいるが、本器は読み込み時に長さで並べ直すので、
表の並びが崩れても結果は変わらない(同じ長さのものは表の並びを保つ)。

--------------------------------------------------------------------------
J-9 で決めたこと: --self-test は陽性対照を置いて必ず片付ける
--------------------------------------------------------------------------
「検出0件」が「走査そのものが動いていないから0件」でないことを示すため、
--self-test は走査対象になる場所へ一時ファイルを作り、そこへ造語を1つ置いて、
それが検出されることを確かめる。作った一時ファイルは finally で必ず消し、
前後の `git status --porcelain` が一致することまで確かめる。
一時ファイル名には `dd-cyn-0123-selftest-<pid>` が入るので、
万一残っても取り違えない。

標準ライブラリのみ。外部依存を足さない。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

DDR = "DD-CYN-0123"

#: 決定 §61 により hansolo/ は GitHub 公開絶対禁止。置き換え作業の対象外なので、
#: scan-scope が何を言おうと走査しない。黙って落とすと欠陥になるため、
#: 落とした件数は必ず標準エラーへ知らせる。
HARD_EXCLUDE_PREFIXES = ("hansolo/",)

#: git が使えないときの歩き回りで降りない置き場
WALK_PRUNE_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules",
    ".venv", "venv", ".venv-cynovela", ".mas-env",
    ".hypothesis",
}

DEFAULT_CONTEXT_CHARS = 200


# ---------------------------------------------------------------------------
# glob
# ---------------------------------------------------------------------------

def glob_to_regex(pattern: str) -> re.Pattern:
    """リポジトリルート相対の glob を正規表現へ直す。`**` の再帰に対応する。

    `**/` は「0個以上の階層」、`**` は「/ を跨いでよい任意」、
    `*` と `?` は「/ を跨がない」。
    """
    i, n, out = 0, len(pattern), []
    while i < n:
        if pattern.startswith("**/", i):
            out.append(r"(?:[^/]+/)*")
            i += 3
        elif pattern.startswith("**", i):
            out.append(r".*")
            i += 2
        elif pattern[i] == "*":
            out.append(r"[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append(r"[^/]")
            i += 1
        elif pattern[i] == "[":
            j = i + 1
            if j < n and pattern[j] in "!^":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j >= n:                      # 閉じていない [ はただの文字
                out.append(re.escape("["))
                i += 1
            else:
                inner = pattern[i + 1:j]
                if inner.startswith("!"):
                    inner = "^" + inner[1:]
                out.append("[" + inner + "]")
                i = j + 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def concretize_glob(pattern: str, token: str) -> str:
    """glob から、それに当たる実在しうるパスを1つ作る(--self-test 用)。

    `**/` は0階層に、`*` は token に、`?` は 'x' に、`[abc]` は先頭の文字に潰す。
    """
    i, n, out = 0, len(pattern), []
    while i < n:
        if pattern.startswith("**/", i):
            i += 3
        elif pattern.startswith("**", i):
            out.append(token)
            i += 2
        elif pattern[i] == "*":
            out.append(token)
            i += 1
        elif pattern[i] == "?":
            out.append("x")
            i += 1
        elif pattern[i] == "[":
            j = i + 1
            if j < n and pattern[j] in "!^":
                j += 1
            start = j
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j >= n:
                out.append("[")
                i += 1
            else:
                out.append(pattern[start] if start < j else "x")
                i = j + 1
        else:
            out.append(pattern[i])
            i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# 設定の読み込み
# ---------------------------------------------------------------------------

class ConfigError(Exception):
    pass


def _read_tsv(path: Path) -> list[tuple[int, list[str]]]:
    """タブ区切りを読む。`#` 始まりと空行は捨てる。(行番号, 欄の一覧) を返す。"""
    if not path.exists():
        raise ConfigError(f"設定ファイルが無い: {path}")
    rows = []
    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            rows.append((lineno, line.split("\t")))
    return rows


class Scope:
    def __init__(self) -> None:
        self.includes: list[str] = []
        self.skip_files: list[tuple[str, str, re.Pattern]] = []       # glob, 理由, 正規表現
        self.skip_regions: list[dict] = []                            # path/開始/終了/理由
        self.warnings: list[str] = []

    @property
    def include_res(self) -> list[re.Pattern]:
        if not hasattr(self, "_inc_res"):
            self._inc_res = [glob_to_regex(g) for g in self.includes]
        return self._inc_res

    def is_included(self, relpath: str) -> bool:
        return any(r.match(relpath) for r in self.include_res)

    def skip_file_reason(self, relpath: str) -> str | None:
        for _glob, reason, rx in self.skip_files:
            if rx.match(relpath):
                return reason
        return None

    def regions_for(self, relpath: str) -> list[dict]:
        return [r for r in self.skip_regions if r["re_path"].match(relpath)]


def load_scope(path: Path) -> Scope:
    scope = Scope()
    for lineno, cols in _read_tsv(path):
        kind = cols[0].strip()
        if kind == "include":
            if len(cols) < 2 or not cols[1].strip():
                raise ConfigError(f"{path}:{lineno}: include に glob が無い")
            scope.includes.append(cols[1].strip())
        elif kind == "skip-file":
            if len(cols) < 2 or not cols[1].strip():
                raise ConfigError(f"{path}:{lineno}: skip-file に glob が無い")
            g = cols[1].strip()
            reason = cols[2].strip() if len(cols) > 2 else ""
            scope.skip_files.append((g, reason, glob_to_regex(g)))
        elif kind == "skip-region":
            if len(cols) < 4:
                raise ConfigError(
                    f"{path}:{lineno}: skip-region は "
                    "<path> <開始の正規表現> <終了の正規表現> <理由> が要る"
                )
            target = cols[1].strip()
            try:
                start_re = re.compile(cols[2])
                end_re = re.compile(cols[3])
            except re.error as exc:
                raise ConfigError(f"{path}:{lineno}: 正規表現が壊れている: {exc}") from exc
            scope.skip_regions.append({
                "path": target,
                "re_path": glob_to_regex(target),
                "start": cols[2],
                "end": cols[3],
                "re_start": start_re,
                "re_end": end_re,
                "reason": cols[4].strip() if len(cols) > 4 else "",
            })
        else:
            scope.warnings.append(f"{path}:{lineno}: 知らない指示 {kind!r} を読み飛ばした")
    if not scope.includes:
        raise ConfigError(f"{path}: include が1件も無い。走査対象が空になる")
    return scope


def load_terms(path: Path) -> list[dict]:
    terms = []
    seen = set()
    for lineno, cols in _read_tsv(path):
        term = cols[0].strip()
        if not term:
            continue
        if term in seen:
            continue
        seen.add(term)
        terms.append({
            "term": term,
            "replacement": cols[1].strip() if len(cols) > 1 else "",
            "note": cols[2].strip() if len(cols) > 2 else "",
            "source_line": lineno,
        })
    if not terms:
        raise ConfigError(f"{path}: 造語が1件も無い")
    # 長いものから当てる(短い造語が長い造語を食わないように)
    terms.sort(key=lambda t: len(t["term"]), reverse=True)
    return terms


def load_allowed(path: Path) -> list[dict]:
    """allowed-words.tsv を読む。無くても空で通す(除外0件の走査は成り立つ)。"""
    if not path.exists():
        return []
    allowed = []
    seen = set()
    for _lineno, cols in _read_tsv(path):
        word = cols[0].strip()
        if not word or word in seen:
            continue
        seen.add(word)
        allowed.append({
            "word": word,
            "reason": cols[1].strip() if len(cols) > 1 else "",
            "where": cols[2].strip() if len(cols) > 2 else "",
        })
    return allowed


# ---------------------------------------------------------------------------
# ファイルの数え上げ
# ---------------------------------------------------------------------------

def enumerate_repo_files(root: Path) -> tuple[list[str], str]:
    """走査候補のパス(ルート相対)を集める。git が使えればそれを使う。

    git ls-files -z を使う理由: 日本語のファイル名は -z を付けないと
    引用符付きのエスケープ表記で返り、実在しないパスになる。
    --cached --others --exclude-standard で「追跡中 + 追跡外だが無視されない」
    を採る。追跡外を含めるのは --self-test の一時ファイルを見えるようにするため。
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z",
             "--cached", "--others", "--exclude-standard"],
            capture_output=True, check=False,
        )
        if proc.returncode == 0:
            paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
            return sorted(set(paths)), "git"
    except (OSError, UnicodeDecodeError):
        pass
    return _walk_files(root), "walk"


def _walk_files(root: Path) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in WALK_PRUNE_DIRS]
        for name in filenames:
            full = Path(dirpath) / name
            try:
                out.append(full.relative_to(root).as_posix())
            except ValueError:
                continue
    return sorted(set(out))


def resolve_targets(root: Path, scope: Scope) -> dict:
    """走査対象と、外したもの(と理由)を決める。"""
    candidates, method = enumerate_repo_files(root)

    hard_excluded = [p for p in candidates
                     if any(p.startswith(pre) for pre in HARD_EXCLUDE_PREFIXES)]
    candidates = [p for p in candidates if p not in set(hard_excluded)]

    included = [p for p in candidates if scope.is_included(p)]

    targets, skipped = [], []
    for p in included:
        reason = scope.skip_file_reason(p)
        if reason is None:
            targets.append(p)
        else:
            skipped.append({"path": p, "reason": reason})

    return {
        "method": method,
        "candidates": len(candidates),
        "targets": targets,
        "skipped_files": skipped,
        "hard_excluded": hard_excluded,
    }


# ---------------------------------------------------------------------------
# skip-region
# ---------------------------------------------------------------------------

def compute_skipped_lines(lines: list[str], regions: list[dict]) -> tuple[set[int], list[str]]:
    """走査から外す行番号(1始まり)の集合を返す。開始行と終了行の両端を含む。"""
    skipped: set[int] = set()
    warnings: list[str] = []
    for region in regions:
        idx = 0
        while idx < len(lines):
            if not region["re_start"].search(lines[idx]):
                idx += 1
                continue
            start = idx
            end = None
            for j in range(start + 1, len(lines)):   # 終了は開始の次の行から探す
                if region["re_end"].search(lines[j]):
                    end = j
                    break
            if end is None:
                warnings.append(
                    f"skip-region {region['path']}: {start + 1} 行目で始まった区間の"
                    f"終わり(/{region['end']}/)が見つからず、ファイル末尾まで外した"
                )
                end = len(lines) - 1
            for k in range(start, end + 1):
                skipped.add(k + 1)
            idx = end + 1
    return skipped, warnings


# ---------------------------------------------------------------------------
# 本体の走査
# ---------------------------------------------------------------------------

def allowed_spans(line: str, allowed: list[dict]) -> list[tuple[int, int, str, str]]:
    """行中に現れる allowed-word の区間 (開始, 終了, 語, 理由) を全部返す。"""
    spans = []
    for entry in allowed:
        word = entry["word"]
        start = line.find(word)
        while start != -1:
            spans.append((start, start + len(word), word, entry["reason"]))
            start = line.find(word, start + 1)
    return spans


def make_context(line: str, start: int, end: int, width: int = DEFAULT_CONTEXT_CHARS) -> str:
    """文脈を文字単位で切り出す。バイト数では切らない(UTF-8 の日本語を割らないため)。"""
    line = line.rstrip("\n").rstrip("\r")
    if len(line) <= width:
        return line.strip()
    span = end - start
    half = max(0, (width - span) // 2)
    left = max(0, start - half)
    right = min(len(line), left + width)
    left = max(0, right - width)
    piece = line[left:right]
    return ("…" if left > 0 else "") + piece.strip() + ("…" if right < len(line) else "")


def scan_file(root: Path, relpath: str, terms: list[dict], allowed: list[dict],
              scope: Scope, context_chars: int) -> tuple[list[dict], list[dict], list[str]]:
    """1ファイルを走査して (検出, 除外した当たり, 注意) を返す。"""
    full = root / relpath
    notes: list[str] = []
    try:
        text = full.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [], [], [f"{relpath}: UTF-8 として読めないので飛ばした(バイナリか別の符号化)"]
    except (OSError, IsADirectoryError) as exc:
        return [], [], [f"{relpath}: 読めない ({exc})"]

    lines = text.split("\n")
    skip_lines, region_warns = compute_skipped_lines(lines, scope.regions_for(relpath))
    notes.extend(region_warns)

    findings: list[dict] = []
    suppressed: list[dict] = []

    for lineno, line in enumerate(lines, 1):
        if lineno in skip_lines:
            continue
        if not line:
            continue
        spans = allowed_spans(line, allowed) if allowed else []
        # 長い造語が先に押さえた区間。短い造語が同じところで二重に当たるのを防ぐ。
        claimed: list[tuple[int, int, str]] = []
        for entry in terms:                     # terms は長い順に並んでいる
            term = entry["term"]
            pos = line.find(term)
            while pos != -1:
                end = pos + len(term)
                record = {
                    "path": relpath,
                    "line": lineno,
                    "column": pos + 1,          # 文字単位・1始まり
                    "term": term,
                    "replacement": entry["replacement"],
                    "context": make_context(line, pos, end, context_chars),
                }
                longer = next((c for c in claimed if c[0] <= pos and end <= c[1]), None)
                cover = next((s for s in spans if s[0] <= pos and end <= s[1]), None)
                if longer is not None:
                    # 例: 「置き場所」を先に採ったので、その中の「置き場」は数えない
                    record["suppressed_by"] = "longer-term"
                    record["longer_term"] = longer[2]
                    suppressed.append(record)
                elif cover is not None:
                    # 例: 「六本木」の一部としての「木」は数えない
                    record["suppressed_by"] = "allowed-word"
                    record["allowed_word"] = cover[2]
                    record["allowed_reason"] = cover[3]
                    suppressed.append(record)
                else:
                    findings.append(record)
                    claimed.append((pos, end, term))
                pos = line.find(term, pos + 1)

    return findings, suppressed, notes


def run_scan(root: Path, scope: Scope, terms: list[dict], allowed: list[dict],
             context_chars: int = DEFAULT_CONTEXT_CHARS,
             only: list[str] | None = None) -> dict:
    resolved = resolve_targets(root, scope)
    targets = resolved["targets"]
    if only is not None:
        wanted = set(only)
        targets = [p for p in targets if p in wanted]

    findings: list[dict] = []
    suppressed: list[dict] = []
    notes: list[str] = list(scope.warnings)

    for relpath in targets:
        f, s, n = scan_file(root, relpath, terms, allowed, scope, context_chars)
        findings.extend(f)
        suppressed.extend(s)
        notes.extend(n)

    findings.sort(key=lambda r: (r["path"], r["line"], r["column"]))

    by_term: dict[str, int] = {}
    for r in findings:
        by_term[r["term"]] = by_term.get(r["term"], 0) + 1

    return {
        "ddr": DDR,
        "root": str(root),
        "enumeration": resolved["method"],
        "files_scanned": len(targets),
        "files_skipped": resolved["skipped_files"],
        "hard_excluded_count": len(resolved["hard_excluded"]),
        "terms_loaded": len(terms),
        "allowed_words_loaded": len(allowed),
        "findings": findings,
        "count": len(findings),
        "count_by_term": dict(sorted(by_term.items(), key=lambda kv: -kv[1])),
        "suppressed": suppressed,
        "suppressed_count": len(suppressed),
        "notes": notes,
        "targets": targets,
    }


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------

def print_text_report(result: dict, stream=sys.stdout) -> None:
    for note in result["notes"]:
        print(f"注意: {note}", file=sys.stderr)
    if result["hard_excluded_count"]:
        print(
            f"注意: 決定 §61 により hansolo/ 配下 {result['hard_excluded_count']} 件を"
            "走査対象から外した(公開対象外のため)",
            file=sys.stderr,
        )

    for r in result["findings"]:
        print(f"{r['path']}:{r['line']}:{r['term']}: {r['context']}", file=stream)

    print("", file=stream)
    print(f"走査したファイル: {result['files_scanned']} 件"
          f"(数え上げ={result['enumeration']}) / "
          f"造語 {result['terms_loaded']} 語 / "
          f"除外語 {result['allowed_words_loaded']} 語", file=stream)
    if result["files_skipped"]:
        print(f"skip-file で外したファイル: {len(result['files_skipped'])} 件", file=stream)
    if result["suppressed_count"]:
        by_allowed = sum(1 for r in result["suppressed"]
                         if r.get("suppressed_by") == "allowed-word")
        by_longer = sum(1 for r in result["suppressed"]
                        if r.get("suppressed_by") == "longer-term")
        print(f"落とした当たり: {result['suppressed_count']} 件"
              f"(除外語による {by_allowed} 件 / 長い造語が先に採った {by_longer} 件)",
              file=stream)
    if result["count_by_term"]:
        print("造語ごとの件数:", file=stream)
        for term, n in result["count_by_term"].items():
            print(f"  {term}: {n}", file=stream)
    print(f"合計: {result['count']} 件", file=stream)


# ---------------------------------------------------------------------------
# J-9 陽性対照
# ---------------------------------------------------------------------------

def _git_status(root: Path) -> str:
    proc = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                          capture_output=True, check=False)
    if proc.returncode != 0:
        return "<git status が取れない>"
    return proc.stdout.decode("utf-8", "replace")


def pick_selftest_path(root: Path, scope: Scope, token: str) -> str | None:
    """include の glob から、実際に走査対象になる一時ファイルのパスを1つ選ぶ。"""
    for pattern in scope.includes:
        candidate = concretize_glob(pattern, token)
        if not candidate or candidate.endswith("/"):
            continue
        if not scope.is_included(candidate):
            continue
        if scope.skip_file_reason(candidate) is not None:
            continue
        if any(candidate.startswith(pre) for pre in HARD_EXCLUDE_PREFIXES):
            continue
        parent = (root / candidate).parent
        if not parent.is_dir():
            continue                     # 置き場を新しく作らない(後片付けを単純に保つ)
        if (root / candidate).exists():
            continue                     # 既にある実物を絶対に踏まない
        return candidate
    return None


def self_test(root: Path, scope: Scope, terms: list[dict], allowed: list[dict]) -> int:
    """陽性対照: 走査対象の場所へ造語を1つ置き、検出されることを確かめて必ず消す。"""
    token = f"dd-cyn-0123-selftest-{os.getpid()}"
    print("[self-test] DD-CYN-0123 J-9 陽性対照")
    print(f"[self-test] ルート: {root}")

    before = _git_status(root)
    print(f"[self-test] 走行前の git status --porcelain: {len(before.splitlines())} 行")
    print("--- 走行前 git status --porcelain ここから ---")
    sys.stdout.write(before)
    print("--- 走行前 git status --porcelain ここまで ---")

    relpath = pick_selftest_path(root, scope, token)
    if relpath is None:
        print("[self-test] 不合格: include の glob から一時ファイルの置き場を決められなかった")
        return 1

    # allowed-words にそのまま食われない造語を選ぶ
    chosen = None
    for entry in terms:
        # その造語が除外語の一部として現れうるなら、陽性対照には使わない
        if not any(entry["term"] in a["word"] for a in allowed):
            chosen = entry
            break
    if chosen is None:
        chosen = terms[0]
        print("[self-test] 注意: すべての造語が allowed-words と重なる。先頭の造語で試す")

    target = root / relpath
    print(f"[self-test] 陽性対照ファイル: {relpath}")
    print(f"[self-test] 埋め込む造語: {chosen['term']}")

    exit_code = 1
    try:
        target.write_text(
            f"# {DDR} J-9 陽性対照 ({token})\n"
            f"これは走査が生きていることを示すためだけの一時ファイルである。{chosen['term']}\n",
            encoding="utf-8",
        )
        result = run_scan(root, scope, terms, allowed, only=[relpath])
        hits = [r for r in result["findings"]
                if r["path"] == relpath and r["term"] == chosen["term"]]
        print(f"[self-test] 走査対象に入ったか: files_scanned={result['files_scanned']}")
        print("--- 陽性対照の検出結果 ここから ---")
        for r in result["findings"]:
            print(f"{r['path']}:{r['line']}:{r['term']}: {r['context']}")
        print("--- 陽性対照の検出結果 ここまで ---")
        if hits:
            print(f"[self-test] 合格: 陽性対照が検出された({len(hits)} 件)")
            exit_code = 0
        else:
            print("[self-test] 不合格: 陽性対照が検出されなかった。走査が動いていない")
            exit_code = 1
    finally:
        try:
            if target.exists():
                target.unlink()
                print(f"[self-test] 後片付け: {relpath} を削除した")
        except OSError as exc:
            print(f"[self-test] 後片付けに失敗: {exc}")
            exit_code = 1

    after = _git_status(root)
    print(f"[self-test] 走行後の git status --porcelain: {len(after.splitlines())} 行")
    print("--- 走行後 git status --porcelain ここから ---")
    sys.stdout.write(after)
    print("--- 走行後 git status --porcelain ここまで ---")
    if after == before:
        print("[self-test] 後片付け確認: 走行前と一字一句一致した")
    else:
        print("[self-test] 不合格: 走行前後で git status が食い違う。作業木が汚れている")
        exit_code = 1

    return exit_code


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    default_root = here.parent.parent

    ap = argparse.ArgumentParser(
        description="造語(禁則#61)の検出器 — DD-CYN-0123 J-8/J-9",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--root", default=str(default_root), help="リポジトリルート")
    ap.add_argument("--scope", default=None, help="scan-scope.txt の代わり")
    ap.add_argument("--terms", default=None, help="terms.tsv の代わり")
    ap.add_argument("--allowed", default=None, help="allowed-words.tsv の代わり")
    ap.add_argument("--json", action="store_true", help="機械可読(JSON)で出す")
    ap.add_argument("--self-test", action="store_true", help="陽性対照(J-9)を回す")
    ap.add_argument("--list-files", action="store_true", help="走査対象の一覧だけ出す")
    ap.add_argument("--no-allowed", action="store_true",
                    help="allowed-words を使わずに走らせる(J-8 の対照用)")
    ap.add_argument("--context-chars", type=int, default=DEFAULT_CONTEXT_CHARS,
                    help=f"文脈の最大文字数(既定 {DEFAULT_CONTEXT_CHARS})")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    conf_dir = here
    scope_path = Path(args.scope) if args.scope else conf_dir / "scan-scope.txt"
    terms_path = Path(args.terms) if args.terms else conf_dir / "terms.tsv"
    allowed_path = Path(args.allowed) if args.allowed else conf_dir / "allowed-words.tsv"

    try:
        scope = load_scope(scope_path)
        terms = load_terms(terms_path)
        allowed = [] if args.no_allowed else load_allowed(allowed_path)
    except ConfigError as exc:
        print(f"設定の誤り: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        return self_test(root, scope, terms, allowed)

    if args.list_files:
        resolved = resolve_targets(root, scope)
        for p in resolved["targets"]:
            print(p)
        print(f"\n走査対象: {len(resolved['targets'])} 件 "
              f"(候補 {resolved['candidates']} 件 / "
              f"skip-file {len(resolved['skipped_files'])} 件)", file=sys.stderr)
        return 0

    result = run_scan(root, scope, terms, allowed, context_chars=args.context_chars)

    if args.json:
        payload = dict(result)
        payload.pop("targets", None)
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print_text_report(result)

    return 1 if result["count"] else 0


if __name__ == "__main__":
    sys.exit(main())
