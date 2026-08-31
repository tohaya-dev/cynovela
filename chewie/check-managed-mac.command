#!/bin/bash
# ============================================================
#  Cynovela — 入れる前の下調べ (macos-app-20260830)
#
#  管理された Mac (MDM 配下) は、管理の仕組みによって出来ることが
#  絞られていることがあります。このファイルは「いま何が出来て、何が
#  出来ないか」を測って並べるだけのものです。
#
#  🔴 このファイルは測るだけです。設定を変えません。管理の仕組みを
#     迂回しません。書き込みも、入れる操作も、一切行いません。
#     測った結果は画面に出るだけで、どこにも送りません。
#
#  使い方: ダブルクリックしてください。ターミナルが開いて結果が出ます。
# ============================================================
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
PASS=0; WARN=0; FAIL=0
# .pkg の道だけが塞がっているのか、この Mac では何も動かないのかを分けて数える。
# 前者なら Portable 版へ倒せる。後者は倒しても同じである。
PKG_RISK=0      # .pkg の道に障りが在る数
ANY_BLOCK=0     # どちらの道でも動かない数

line()  { printf '%s\n' "──────────────────────────────────────────────"; }
head2() { printf '\n== %s ==\n' "$1"; }
ok()    { printf '  [ OK ] %s\n' "$1"; PASS=$((PASS+1)); }
warn()  { printf '  [ 注意 ] %s\n' "$1"; WARN=$((WARN+1)); }
ng()    { printf '  [ 不可 ] %s\n' "$1"; FAIL=$((FAIL+1)); }
info()  { printf '         %s\n' "$1"; }

line
echo " Cynovela — 入れる前の下調べ"
echo " 測るだけです。設定は何も変えません。"
echo " 実行: $(date '+%Y-%m-%d %H:%M:%S')"
line

# ── 1. この Mac ────────────────────────────────────────────
head2 "1. この Mac"
_prod="$(sw_vers -productVersion 2>/dev/null || echo '不明')"
_build="$(sw_vers -buildVersion 2>/dev/null || echo '不明')"
_arch="$(uname -m 2>/dev/null || echo '不明')"
info "macOS $_prod ($_build)"
info "利用者: $(whoami)"
case "$_arch" in
  arm64) ok "Apple シリコン ($_arch)" ;;
  *)     ng "Apple シリコンではありません ($_arch)。Cynovela は Apple シリコン専用です"
         ANY_BLOCK=$((ANY_BLOCK+1)) ;;
esac
# 版の下限は 12 とする (配布物の Distribution が要求する版に合わせている)
_major="${_prod%%.*}"
if [ -n "$_major" ] && [ "$_major" -ge 12 ] 2>/dev/null; then
  ok "macOS の版は足りています (12 以上)"
else
  ng "macOS の版が足りません (12 以上が要ります)"
  ANY_BLOCK=$((ANY_BLOCK+1))
fi

# ── 2. 権限 ────────────────────────────────────────────────
head2 "2. 権限"
if id -Gn 2>/dev/null | tr ' ' '\n' | grep -qx admin; then
  ok "この利用者は管理者 (admin) です"
else
  warn "この利用者は管理者ではありません"
  info "→ .pkg は入れるときに管理者の名前とパスワードを聞きます。"
  info "  分からない場合は情報システム部門へ問い合わせるか、Portable 版を使ってください。"
  PKG_RISK=$((PKG_RISK+1))
fi

# ── 3. 入れ先へ書けるか ────────────────────────────────────
head2 "3. 入れ先へ書けるか"
_probe="cynovela-write-probe-$$"
if ( : > "/Applications/$_probe" ) 2>/dev/null; then
  rm -f "/Applications/$_probe" 2>/dev/null
  ok "/Applications へ書けます"
else
  warn "/Applications へ直接は書けません"
  info "→ .pkg は installer が root として書くため、これだけでは判断できません。"
  info "  管理者のパスワードを聞かれたら入力してください。"
  PKG_RISK=$((PKG_RISK+1))
fi
if [ -d "$HOME/Applications" ]; then
  if ( : > "$HOME/Applications/$_probe" ) 2>/dev/null; then
    rm -f "$HOME/Applications/$_probe" 2>/dev/null
    ok "~/Applications へ書けます"
  else
    warn "~/Applications へ書けません"
  fi
else
  info "~/Applications は在りません (無くて構いません)"
fi
# 🔴 資料・索引・鍵ファイルが実際に書かれるのはここである。どちらの形態でも要る。
#    ここが書けないと、入れられても最初の起動で止まる。
_sup="$HOME/Library/Application Support"
if [ -d "$_sup" ] && ( : > "$_sup/$_probe" ) 2>/dev/null; then
  rm -f "$_sup/$_probe" 2>/dev/null
  ok "~/Library/Application Support へ書けます (資料と索引の置き場)"
else
  ng "~/Library/Application Support へ書けません"
  info "→ Cynovela は資料・索引・鍵ファイルをここに置きます。書けないと起動できません。"
  info "  .pkg でも Portable でも同じ場所を使うため、形態を変えても直りません。"
  info "  情報システム部門へ、この行をそのまま見せてください。"
  ANY_BLOCK=$((ANY_BLOCK+1))
fi

# ── 4. 入れる操作の可否 (Gatekeeper) ───────────────────────
head2 "4. 入れる操作の可否 (Gatekeeper)"
_spctl="$(spctl --status 2>&1 || true)"
info "spctl --status: ${_spctl:-取得できませんでした}"
case "$_spctl" in
  *"assessments enabled"*)
    warn "Gatekeeper は有効です"
    info "→ 配る .pkg は署名していません (Apple の Developer Program の証明書を持たないため)。"
    info "  そのままダブルクリックすると「開けません」と言われます。"
    info "  Finder で .pkg を右クリック →「開く」→ もう一度「開く」で入れられます。"
    info "  この操作そのものを管理の仕組みが止めている場合は、Portable 版を使ってください。"
    PKG_RISK=$((PKG_RISK+1))
    ;;
  *"assessments disabled"*) ok "Gatekeeper は無効です (そのまま開けます)" ;;
  *) info "判定できませんでした (管理の仕組みが応答を絞っていることがあります)" ;;
esac
if [ -d /Library/Apple/System/Library/CoreServices/MRT.app ] || [ -d /System/Library/CoreServices/XProtect.bundle ]; then
  info "XProtect / MRT は在ります (通常の状態です)"
fi

# ── 5. 待ち受けの番号 ──────────────────────────────────────
head2 "5. 待ち受けの番号 (8765)"
if command -v lsof >/dev/null 2>&1; then
  _busy="$(lsof -nP -iTCP:8765 -sTCP:LISTEN 2>/dev/null | awk 'NR>1{print $1" (PID "$2")"}' | sort -u)"
  if [ -z "$_busy" ]; then
    ok "127.0.0.1:8765 は空いています"
  else
    warn "127.0.0.1:8765 は使われています:"
    printf '%s\n' "$_busy" | sed 's/^/         /'
    info "→ Cynovela を既に動かしている場合は、先に止めてください。"
  fi
else
  info "lsof が無いため測れませんでした"
fi

# ── 6. 答えを作るモデルの置き場 ────────────────────────────
head2 "6. 答えを作るモデル (LM Studio / Ollama)"
_found=0
for _u in "http://localhost:1234" "http://127.0.0.1:1234"; do
  _code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$_u/v1/models" 2>/dev/null || true)"
  if [ "${_code:-000}" = "200" ]; then ok "LM Studio が応答しました ($_u)"; _found=1; break; fi
done
[ "$_found" = "0" ] && info "LM Studio は応答しませんでした (localhost:1234)"
_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://localhost:11434/api/tags" 2>/dev/null || true)"
if [ "${_code:-000}" = "200" ]; then ok "Ollama が応答しました (localhost:11434)"; else info "Ollama は応答しませんでした (localhost:11434)"; fi
[ -d "/Applications/LM Studio.app" ] && info "/Applications/LM Studio.app は在ります"
command -v ollama >/dev/null 2>&1 && info "ollama コマンドは在ります: $(command -v ollama)"
if [ "$_found" = "0" ] && [ "${_code:-000}" != "200" ]; then
  warn "答えを作るモデルの置き場が見つかりません"
  info "→ 取り込みと検索は動きますが、質問への回答は出ません。"
  info "  LM Studio か Ollama を先に起動してください。"
fi

# ── 7. 既に入っている Cynovela ─────────────────────────────
head2 "7. 既に入っている Cynovela"
if [ -d /Applications/Cynovela.app ]; then
  _v="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' /Applications/Cynovela.app/Contents/Info.plist 2>/dev/null || echo '不明')"
  info "/Applications/Cynovela.app が在ります (版 $_v)"
else
  info "/Applications/Cynovela.app は在りません"
fi
_data="$HOME/Library/Application Support/Cynovela"
if [ -d "$_data" ]; then
  info "$_data が在ります ($(du -sh "$_data" 2>/dev/null | cut -f1))"
  info "→ .app を捨てても、この中の資料と設定は残ります。"
else
  info "$HOME/Library/Application Support/Cynovela は在りません (初めての導入です)"
fi

# ── 8. Portable 版がこの Mac で動くか ──────────────────────
head2 "8. Portable 版がこの Mac で動くか"
_py="$HERE/.condapack-cynovela/bin/python"
[ -x "$_py" ] || _py="$HERE/.condapack-cynovela/bin/python3"
if [ -x "$_py" ]; then
  _ver="$("$_py" -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])' 2>&1 || true)"
  if printf '%s' "$_ver" | grep -qE '^3\.(1[2-9]|[2-9][0-9])'; then
    ok "同梱の python が動きます ($_ver)"
  else
    ng "同梱の python が動きません: $_ver"
    info "→ 拡張属性 (quarantine) か、署名の壊れが疑われます。"
  fi
  if "$_py" -c 'import fastapi, uvicorn, chromadb, torch' >/dev/null 2>&1; then
    ok "主要な部品が読み込めます (fastapi / uvicorn / chromadb / torch)"
  else
    ng "主要な部品が読み込めません"
    info "  $("$_py" -c 'import fastapi, uvicorn, chromadb, torch' 2>&1 | tail -1)"
  fi
else
  info "このフォルダに Portable 版の同梱環境 (.condapack-cynovela) は在りません"
  info "→ この下調べだけを取り出して実行した場合は、これで正常です。"
fi

# ── 9. 空き容量 ────────────────────────────────────────────
head2 "9. 空き容量"
_avail_k="$(df -k / | awk 'NR==2{print $4}')"
_avail_g=$(( _avail_k / 1024 / 1024 ))
info "起動ディスクの空き: ${_avail_g} GiB"
# 形態ごとに要る量が違う。まとめて 1 つの敷居で測ると、
# 「.pkg は無理だが Portable なら入る」を見落とす。
#   .pkg     … 配布物 3.7GiB + 入った後の .app 7.1GiB が同時に載る = 11GiB
#   Portable … 配布物 2.1GiB + 展開後 8GiB が同時に載る            =  8GiB
_need_pkg=11
_need_portable=8
if [ "$_avail_g" -ge "$_need_pkg" ]; then
  ok ".pkg の道に足ります (${_need_pkg} GiB 以上)"
else
  ng ".pkg の道には足りません (${_need_pkg} GiB 以上が要ります)"
  PKG_RISK=$((PKG_RISK+1))
fi
if [ "$_avail_g" -ge "$_need_portable" ]; then
  ok "Portable の道に足ります (${_need_portable} GiB 以上)"
else
  ng "Portable の道にも足りません (${_need_portable} GiB 以上が要ります)"
  info "→ 先に空きを作ってください。どちらの形態でも足りません。"
  ANY_BLOCK=$((ANY_BLOCK+1))
fi

# ── まとめ ─────────────────────────────────────────────────
line
printf ' まとめ: OK %d 件 / 注意 %d 件 / 不可 %d 件\n' "$PASS" "$WARN" "$FAIL"
echo ""
# 🔴 「入れてみて失敗した」ではなく「入れる前に、どちらの道を行けばよいか」を出す。
#    Cynovela には形態が 2 つ在り、片方が塞がっていても、もう片方が通ることが多い。
if [ "$ANY_BLOCK" -gt 0 ]; then
  echo " この Mac では、どちらの形態も動きません。"
  echo " 上の [ 不可 ] の行を、そのまま情報システム部門へ見せてください。"
  echo " 形態を変えても直りません (Apple シリコン・macOS の版・資料の置き場・空き容量)。"
elif [ "$PKG_RISK" -gt 0 ]; then
  echo " 🔴 .pkg (Cynovela.app) の道には、この Mac で障りが $PKG_RISK 件 在ります。"
  echo ""
  echo " → Portable 版を使ってください。こちらは管理者の権限を使いません。"
  echo "   ・/Applications へ書きません (置いた場所でそのまま動きます)"
  echo "   ・インストーラを走らせません (Gatekeeper の許可を求めません)"
  echo "   ・止めるのはフォルダを捨てるだけです"
  echo ""
  echo "   取り寄せ方と始め方は、配布ページの HOW-TO-ASSEMBLE.md に書いてあります。"
  echo "   ファイル名は cynovela-chewie-package-<版>.tar.gz です。"
  echo ""
  echo " (.pkg を使いたい場合は、上の [ 注意 ] の行を情報システム部門へ見せてください。)"
elif [ "$WARN" -gt 0 ]; then
  echo " 「注意」の項目に目を通してから進めてください。どちらの形態も使えます。"
else
  echo " この Mac では、.pkg と Portable のどちらも使えます。"
  echo " 迷う場合は .pkg (Cynovela.app) をお勧めします。"
fi
line
echo ""
echo "この画面は閉じて構いません。"
