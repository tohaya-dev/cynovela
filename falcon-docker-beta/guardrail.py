import json
import re


# ============================================================
# settlement-part3 L1: 出力トラップトークン遮断 (両経路・全 tier 共通)
# 間接プロンプトインジェクションが成功した痕跡 (HACKED / PWNED / 秘密トークン /
# [SYSTEM OVERRIDE]) を LLM 応答から検知する決定論ブロッカ。
# chat.py の EXFILTRATION_PATTERNS をここへ集約し二重管理を解消する。
# ============================================================
TRAP_TOKEN_PATTERNS = [
    re.compile(r"\bHACKED\b"),
    re.compile(r"\bPWNED\b"),
    re.compile(r"SECRET-ALPHA-TOKEN"),
    re.compile(r"\[\s*SYSTEM\s+OVERRIDE\s*\]"),
]


def scan_output_for_trap_tokens(text: str) -> dict:
    """LLM 応答にトラップトークン (間接 PI 成功痕跡) が含まれるか検査する。

    全 tier (admin / raw 含む) で呼ぶこと。出口の最終決定論ブロッカであり、
    回答モデルの強弱に依存せず「毒に従った痕跡」を遮断する。
    Returns: {'detected': bool, 'pattern': str}
    """
    if not text:
        return {"detected": False}
    for rx in TRAP_TOKEN_PATTERNS:
        if rx.search(text):
            return {"detected": True, "pattern": rx.pattern}
    return {"detected": False}


def apply_guardrail(
    policy_rules: list[dict],
    chunks: list[dict],
    file_categories: dict,
) -> tuple[list[dict], list[dict]]:
    """
    Apply Guardrail Policy to search results.

    Args:
        policy_rules: [{"classifier": "PII", "action": "mask"}, ...]
        chunks: [{"chunk_text": "...", "file_name": "...", "score": 0.1}, ...]
        file_categories: {"file_name": ["PII", "HR"], ...}

    Returns:
        (filtered_chunks, applied_actions)
    """
    if not policy_rules:
        return chunks, []

    exclude_classifiers = set()
    mask_classifiers = set()
    log_classifiers = set()

    for rule in policy_rules:
        action = rule.get("action", "")
        classifier = rule.get("classifier", "")
        if action == "exclude_from_rag":
            exclude_classifiers.add(classifier)
        elif action == "mask":
            mask_classifiers.add(classifier)
        elif action == "log_only":
            log_classifiers.add(classifier)

    filtered = []
    applied = []
    exclude_count = 0
    mask_count = 0
    log_count = 0

    for chunk in chunks:
        fname = chunk.get("file_name", "")
        cats = set(file_categories.get(fname, []))

        # Exclude check
        if cats & exclude_classifiers:
            exclude_count += 1
            continue

        # Mask check
        if cats & mask_classifiers:
            chunk = dict(chunk)
            # §段4: mask_pii (DEPRECATED 3-type) を撤去し mask_text_with_spans
            # (7-type + span tracking) に一本化。policy 経由のマスクも本実装で統一。
            try:
                _masked_text, _ = mask_text_with_spans(chunk.get("chunk_text") or "")
                chunk["chunk_text"] = _masked_text
            except Exception:
                pass  # マスク失敗時は元 chunk を維持
            mask_count += 1

        # Log check
        if cats & log_classifiers:
            log_count += 1

        filtered.append(chunk)

    if exclude_count > 0:
        applied.append(
            {
                "action": "exclude_from_rag",
                "classifier": ",".join(exclude_classifiers),
                "count": exclude_count,
            }
        )
    if mask_count > 0:
        applied.append(
            {
                "action": "mask",
                "classifier": ",".join(mask_classifiers),
                "count": mask_count,
            }
        )
    if log_count > 0:
        applied.append(
            {
                "action": "log_only",
                "classifier": ",".join(log_classifiers),
                "count": log_count,
            }
        )

    return filtered, applied


# §段4: mask_pii (DEPRECATED 3-type) は撤去済。masking-rework-overnight-v5 では
# mask_text_with_spans (7-type + span tracking) に一本化。policy 経路の apply_guardrail
# もこちらを使う。新コードは mask_text_with_spans / utils.metadata.pii.mask_pii を使う。


# ============================================================
# P5 BLOCK-C: 入力/出力 Guardrail（PII detect & mask with span tracking）
# ============================================================

# 項目② 全角の電話・メール正規化（item2-fullwidth-research.md 確定方針）
# - 長さ保存 1→1 の str.translate マップで検出用コピーのみ作る
# - 検出 start/end は元テキストに 1:1 で適用できる（NFKC 全文変換は禁止）
# - ー (U+30FC 長音) は意味変化リスクあり → 既定で対象外
NORMALIZE_FULLWIDTH_MAP = str.maketrans({
    "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
    "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
    "Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D", "Ｅ": "E", "Ｆ": "F", "Ｇ": "G",
    "Ｈ": "H", "Ｉ": "I", "Ｊ": "J", "Ｋ": "K", "Ｌ": "L", "Ｍ": "M", "Ｎ": "N",
    "Ｏ": "O", "Ｐ": "P", "Ｑ": "Q", "Ｒ": "R", "Ｓ": "S", "Ｔ": "T", "Ｕ": "U",
    "Ｖ": "V", "Ｗ": "W", "Ｘ": "X", "Ｙ": "Y", "Ｚ": "Z",
    "ａ": "a", "ｂ": "b", "ｃ": "c", "ｄ": "d", "ｅ": "e", "ｆ": "f", "ｇ": "g",
    "ｈ": "h", "ｉ": "i", "ｊ": "j", "ｋ": "k", "ｌ": "l", "ｍ": "m", "ｎ": "n",
    "ｏ": "o", "ｐ": "p", "ｑ": "q", "ｒ": "r", "ｓ": "s", "ｔ": "t", "ｕ": "u",
    "ｖ": "v", "ｗ": "w", "ｘ": "x", "ｙ": "y", "ｚ": "z",
    "＠": "@", "．": ".", "－": "-", "＋": "+", "　": " ",
})


def _normalize_fullwidth(text: str) -> str:
    if not text:
        return text
    return text.translate(NORMALIZE_FULLWIDTH_MAP)


PII_PATTERNS = [
    # (label, regex, replacement_token)
    # #04: URL を先頭に置いて他パターンに先行マッチさせる
    #     (URL内のドメインがEMAIL等として誤検出されないように)
    ("URL", re.compile(r'https?://[^\s<>"　]+'), "[MASKED:URL]"),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b"), "[MASKED:EMAIL]"),
    # masking-mask-gap-fix-and-resume-v1 §F1: -? → [\s-]? (CREDIT に倣う対称化)
    # 取りこぼし fix: スペース区切り「080 4444 5555」等。網羅は保証しないが
    # ハイフン/スペース/連続の 3 書式を揃える最小修正。
    # ADDRESS_JP誤検出 fix (随伴): 先頭/末尾の \b は ASCII 単語境界のため、電話番号が
    # 日本語 (CJK は \w 扱い) に直接連接する「電話090-1234-5678です」を取りこぼす
    # (両端とも \b が成立せずマスク漏れ)。\b と等価な「数字/英字/_ に連接しない」境界を
    # 明示する lookaround に置換し、ASCII 連接の既存挙動 (数字途中・英字直後は非マッチ)
    # を完全保存したまま CJK/記号連接の電話番号のみマスク対象に加える。
    ("PHONE_JP", re.compile(r"(?<![0-9A-Za-z_])0[789]0[\s-]?\d{4}[\s-]?\d{4}(?![0-9A-Za-z_])"), "[MASKED:PHONE]"),
    # §F1: -? → [\s-]? (PHONE_JP と対称)
    ("PHONE_LAND", re.compile(r"(?<![0-9A-Za-z_])0(?!7\d|8\d|9\d)\d{1,4}[\s-]?\d{1,4}[\s-]?\d{4}(?![0-9A-Za-z_])"), "[MASKED:PHONE]"),
    # ga-close-v3 PartD D-2 (小数の除外 / 過剰遮断の低減): 既存 2 枝の本体は一字も変えず、
    # 「小数の一部である」ことを示す除外 lookaround だけを各枝の前後へ足す。
    #   (?<!\d\.) … 直前が「数字 + 小数点」= この数字列は小数部の先頭
    #   (?!\.\d)  … 直後が「小数点 + 数字」= この数字列は整数部の末尾
    # どちらも小数であることの決定論的な印であり、文脈語ゲートや確信度の足切りは使わない。
    # 文末の "…4111111111111111." (後ろに数字が来ないピリオド/句点) は従来どおり伏字される。
    ("CREDIT", re.compile(r"(?<!\d\.)\b(?:\d{4}[\s-]?){3}\d{4}\b(?!\.\d)|(?<!\d\.)(?<![0-9A-Za-z_])\d{4}[\s-]\d{4}[\s-]?\d{4}[\s-]?\d{4}(?![0-9A-Za-z_])(?!\.\d)"), "[MASKED:CREDIT]"),
    # §F1: -? → [\s-]? (CREDIT/PHONE と対称)
    # fix-security-batch-v2 (2026-05-28): 桁可変対応 (3-4 + 3-4 + 3-6) で
    # 「123-456-789012」「1234-5678-9012」「1234 5678 9012」「123456789012」を網羅。
    # mynumber-boundary-fix (2026-07-09 instr-…-mynumber-and-piicount-…-v1): 第3枝を追加。
    # 第1枝の \b は CJK が \w 扱いのため「在庫は123456789012個」等の日本語直連・区切り無し
    # 12桁を取りこぼし、文脈語ゲート(_MYNUM_CTX_RX)も近傍16文字に文脈語が無いとすり抜けて
    # 生マイナンバーが masked 層に残留していた (2026-07-09 MBP監査 Agent2 実測)。
    # 第3枝 (?<!\d)\d{12}(?!\d) は「数字の直前・直後に数字が来ない連続12桁」を文脈語なしで
    # 無条件検出する (マイナンバーは常に12桁ちょうど)。13桁以上の連続数字 (カード16桁等) の
    # 内部にはマッチせず、9-11/13-14桁の財務・技術数値 (売上1234567890円等) も対象外のため
    # 既存の過剰マスク防止 (test_t1_overmask) は不変。12桁ちょうどの一般数値が新たにマスク
    # される点は漏れ封鎖優先 (fail-safe) の意図的トレードオフ。第1・第2枝は一字も変えず温存。
    ("MYNUMBER", re.compile(r"\b\d{3,4}[\s-]?\d{3,4}[\s-]?\d{3,6}\b|(?<![0-9A-Za-z_])\d{3,4}[\s-]\d{3,4}[\s-]?\d{3,6}(?![0-9A-Za-z_])|(?<!\d)\d{12}(?!\d)"), "[MASKED:MYNUM]"),
    ("PASSPORT", re.compile(r"\b[A-Z]{2}\d{7}\b"), "[MASKED:PASSPORT]"),
    # uifix v1 H (2026-05-24): \b は - で word boundary を成立させるため
    # "MLNX_OFED_LINUX-1.2.3.0" の 1.2.3.0 を IP として誤検知していた。
    # 負の lookbehind (?<![-_\w.]) でハイフン/アンダーバー/英数字/ドット直後を除外し、
    # バージョン文字列を弾く。先頭・空白後・行頭の通常 IP はマスク継続。
    # §F2 (2026-06-21 境界修正): 旧 lookbehind の \w は CJK も語文字扱いするため
    # 「サーバ192.0.2.10」(日本語直連) を取りこぼした。lookbehind を ASCII 英数字/記号
    # (?<![-_0-9A-Za-z.]) に限定し、末尾 \b も ASCII 限定 lookahead (?![0-9A-Za-z_.]) に
    # 置換。これでバージョン文字列保護 (ASCII 文脈) と octet 検証(0-255)は不変のまま、
    # CJK 直連 IP のみマスク対象に加える。
    ("IPV4", re.compile(r"(?<![-_0-9A-Za-z.])(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)(?![0-9A-Za-z_.])"), "[MASKED:IP]"),
    # ------------------------------------------------------------------
    # credential-in-document (ga-finish-20260727 Part3): 資料本文に書かれた
    # 「資格情報」を伏字対象へ追加する。既存種別の正規表現・判定順序・トークンは
    # 一字も変更していない（本ブロックは末尾への追加のみ）。末尾追加のため、
    # 既存種別とスパンが完全一致した場合は detect_pii_spans の重複排除で
    # 「先に入った既存種別」が残り、既存の伏字結果は変わらない。
    #
    # 追加する 3 種:
    #   PASSWORD    … 「パスワード: X」「password=X」等のラベル+値の様式
    #   APIKEY      … sk- / sk-ant- / ghp_ / github_pat_ / AKIA / AIza / xox / glpat
    #                  / Bearer <token> / 「api_key: X」等のラベル+値の様式
    #   PRIVATEKEY  … -----BEGIN ... PRIVATE KEY----- ブロック
    #
    # 過剰伏字を避けるための共通設計:
    #   - 値は ASCII 図形文字 [!-~] のみ（空白・CJK で必ず切れる）。よって
    #     「パスワードは定期的に変更してください」「パスワードポリシーは9文字以上」
    #     のような日本語の一般記述はマッチしない。
    #   - ラベルと値の間の区切り [:：=＝] または「は」を必須とする（空白区切りは
    #     採らない。"password protection" 等を巻き込まないため）。
    #   - 区切り前後の空白は [ \t　] に限定し改行をまたがない。
    # ------------------------------------------------------------------
    # PASSWORD: ラベル + 区切り + 値。スパンはラベルを含む（値だけを指す可変長
    # lookbehind は re モジュールが許さないため）。
    # 「pass」「token」のような一語だけのラベルは採らない (ソース断片の
    # 「pass = ...」「token = ...」まで巻き込むため)。
    ("PASSWORD", re.compile(r"(?<![0-9A-Za-z])(?:pass(?:word|phrase)|passwd|pwd|パスワード|パスフレーズ|合言葉)[ \t　]*(?:[:：=＝]|は)[ \t　]*[!-~]{4,128}", re.IGNORECASE), "[MASKED:PASSWORD]"),
    # APIKEY: 発行元書式が自己識別する型（値そのものだけがスパン）。
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])sk-(?:ant-)?[A-Za-z0-9_\-]{16,}"), "[MASKED:APIKEY]"),
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,}"), "[MASKED:APIKEY]"),
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])github_pat_[A-Za-z0-9_]{20,}"), "[MASKED:APIKEY]"),
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])(?:AKIA|ASIA)[0-9A-Z]{16}(?![0-9A-Za-z])"), "[MASKED:APIKEY]"),
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])AIza[0-9A-Za-z_\-]{20,}"), "[MASKED:APIKEY]"),
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])xox[abprse]-[A-Za-z0-9\-]{10,}"), "[MASKED:APIKEY]"),
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])glpat-[A-Za-z0-9_\-]{16,}"), "[MASKED:APIKEY]"),
    # APIKEY: Authorization ヘッダの Bearer トークン。lookbehind は固定長 6 文字。
    ("APIKEY", re.compile(r"(?<=bearer)[ \t]+[A-Za-z0-9\-._~+/]{16,}={0,2}", re.IGNORECASE), "[MASKED:APIKEY]"),
    # APIKEY: ラベル + 区切り + 値（値 8 文字以上。PASSWORD より長めにして誤検出を抑える）。
    ("APIKEY", re.compile(r"(?<![0-9A-Za-z])(?:api[_\-. ]?keys?|api[_\-. ]?tokens?|access[_\-. ]?tokens?|refresh[_\-. ]?tokens?|auth[_\-. ]?tokens?|bearer[_\-. ]?tokens?|secret[_\-. ]?(?:access[_\-. ]?)?keys?|client[_\-. ]?secrets?|APIキー|シークレットキー|トークン)[ \t　]*(?:[:：=＝]|は)[ \t　]*[!-~]{8,256}", re.IGNORECASE), "[MASKED:APIKEY]"),
    # PRIVATEKEY: PEM ブロック。BEGIN..END の完全形を先に置き、END 欠落
    # (チャンク境界・切り詰め) 用の本体行のみの形を後に置く。start 同点なら
    # mask_text_with_spans が長い方 (=完全形) を採る。
    ("PRIVATEKEY", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----"), "[MASKED:PRIVATEKEY]"),
    ("PRIVATEKEY", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----(?:[ \t]*\r?\n[A-Za-z0-9+/=]{16,})*"), "[MASKED:PRIVATEKEY]"),
    # ------------------------------------------------------------------
    # ga-close-v3 PartD D-1 (海外3種): 社会保障番号(米SSN) / 旅券番号 / 国際銀行番号(IBAN)。
    # utils/metadata/pii.py の HIGH_RISK_TYPES には SSN / PASSPORT / IBAN_CODE が名前だけ
    # 載っていたが、SSN と IBAN は規則が 1 行も無く、旅券は日本語直連で不成立だった
    # (着手前実測: 「社会保障番号は123-45-6789です」「口座はGB82WEST12345698765432です」
    #  「旅券番号TK1234567を確認」いずれも検出 0 件)。
    #
    # 方針: 素直な正規表現を 1 本ずつ足すだけにする。文脈語ゲート・確信度の足切りは
    # 一切足さない (2026-07-09 に MYNUMBER の文脈語ゲートが別の穴と重なって逆に漏れを
    # 生んだ実例があるため、同じ作り込みを繰り返さない)。
    # 境界は新しく作り込まず、PHONE_JP / CREDIT / IPV4 が既に使っている
    # 「英数字/_ に連接しない」lookaround と同じ書き方をそのまま使う (\b は CJK が \w
    # 扱いのため日本語直連で成立せず、上記の実測どおり取りこぼす)。
    # 追加位置は末尾。detect_pii_spans の重複排除は先に入った span を残すため、
    # 既存種別とスパンが完全一致した場合 (例 "012-34-5678" は PHONE_LAND と SSN の
    # 両方の形) は従来どおり既存種別が残る。
    # ------------------------------------------------------------------
    # SSN: 米社会保障番号の表記形 3-2-4。区切り無しの 9 桁連続は一般数値と区別が付かず
    # 過剰遮断になるため採らない (追わないもの §1「区切りなし連続桁の直連接」)。
    ("SSN", re.compile(r"(?<![0-9A-Za-z_])\d{3}-\d{2}-\d{4}(?![0-9A-Za-z_])"), "[MASKED:SSN]"),
    # PASSPORT: 英 2 + 数字 7。上の既存 PASSPORT 行 (\b 版) は一字も変えず温存し、
    # 日本語直連のみを拾う同形を足す (\b 版が拾う範囲はこの行の真部分集合)。
    ("PASSPORT", re.compile(r"(?<![0-9A-Za-z_])[A-Z]{2}\d{7}(?![0-9A-Za-z_])"), "[MASKED:PASSPORT]"),
    # IBAN: 国コード 2 + 検査数字 2 + 基本口座番号 11-30 桁 (英数字)。4 桁ごとに空白を
    # 入れる印字形 ("DE89 3704 0044 0532 0130 00") も同じ 1 本で拾えるよう、残りの
    # 各文字の前に空白 1 個までを許す。
    # 国コードは IBAN 規格が定める採番国の一覧 (ISO 3166-1 alpha-2 のうち IBAN 登録済み)
    # そのものを書く。これは型の定義であって文脈語ゲートでも確信度の足切りでもない
    # (CREDIT の Luhn 検証・IPV4 の octet 0-255 と同じ位置づけ)。
    # D-5 実測の根拠: 国コードを [A-Z]{2} と広く取ると、ONTAP マニュアルの API 応答例
    # 'DX12U609DMRVD8U30Z1M' (S3 access_key) と 'DI89811J9JWMJCCO7IOH' (Cisco Duo
    # INTEGRATION-KEY) を IBAN として伏字してしまう。DX / DI は採番国に無いため、
    # 規格どおりの一覧にするだけでこの 2 件は当たらなくなる (増分 0)。
    ("IBAN", re.compile(r"(?<![0-9A-Za-z])(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE|GI|GL|GR|GT|HN|HR|HU|IE|IL|IQ|IS|IT|JO|KW|KZ|LB|LC|LI|LT|LU|LV|LY|MC|MD|ME|MK|MN|MR|MT|MU|NI|NL|NO|PK|PL|PS|PT|QA|RO|RS|RU|SA|SC|SD|SE|SI|SK|SM|SO|ST|SV|TL|TN|TR|UA|VA|VG|XK|YE)\d{2}(?:[ ]?[A-Z0-9]){11,30}(?![0-9A-Za-z])"), "[MASKED:IBAN]"),
]

# C (mynumber-context): 文脈語近傍の区切り無し連続12桁を MYNUMBER 補完検出するための語彙と正規表現。
# 既存 PII_PATTERNS の MYNUMBER は \b 境界で日本語直連を取りこぼすため、文脈語ゲート付きで補う。
_MYNUM_CTX_WORDS = ("マイナンバー", "個人番号", "マイナ番号", "個人番号カード", "通知カード")
_MYNUM_CTX_RX = re.compile(r"(?<!\d)\d{12}(?!\d)")

# §F1 (2026-06-21 カード境界修正): 区切り無し連続カード番号の CJK 直連取りこぼし補完。
# 既存 CREDIT 正規表現は (1)第1 alt が \b 依存で「カード4111111111111111で」の CJK 直連で
# 不成立、(2)第2 alt が先頭 [\s-] セパレータ必須のため区切り無し連続桁を取りこぼす。
# ここでは「英数字/_ に連接しない 13-19 桁の連続数字」かつ Luhn 検証通過のものだけを
# CREDIT として補完検出する。Luhn ゲートにより 100200300400 等の非カード連番は誤爆しない。
# 区切り入り (4111-1111-... / スペース) は既存 CREDIT 正規表現が従来どおり担当する。
# ga-close-v3 PartD D-2: 連続桁枝にも同じ小数除外 lookaround を足す (枝の本体は不変)。
# 実測 (着手前) では "3.1415926535897932" の小数部 16 桁が Luhn を通過して CREDIT と
# 判定され、円周率が伏字されていた。既存の境界 lookaround は '.' を除外していないため。
_CREDIT_RUN_RX = re.compile(r"(?<![0-9A-Za-z_])(?<!\d\.)\d{13,19}(?![0-9A-Za-z_])(?!\.\d)")


def _luhn_ok(num: str) -> bool:
    """Luhn (mod10) チェック。カード番号の妥当性で連番ID等の誤爆を抑える。"""
    if not num or not num.isdigit():
        return False
    total = 0
    for i, ch in enumerate(reversed(num)):
        d = ord(ch) - 48
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def detect_pii_spans(text: str) -> list[dict]:
    """テキストから PII を検出し、種別とスパン (start/end/value) のリストを返す。"""
    if not text:
        return []
    text_for_detect = _normalize_fullwidth(text)
    assert len(text_for_detect) == len(text), "fullwidth map must be 1:1"
    spans: list[dict] = []
    for label, rx, _tok in PII_PATTERNS:
        for m in rx.finditer(text_for_detect):
            spans.append(
                {
                    "type": label,
                    "start": m.start(),
                    "end": m.end(),
                    "value": text[m.start():m.end()],
                }
            )
    # C (mynumber-context): 文脈語(マイナンバー/個人番号/...)の近傍にある「区切り無し連続12桁」を
    #   MYNUMBER として検出する。既存 MYNUMBER 正規表現(PII_PATTERNS)は語境界 \b が日本語直連で
    #   立たず「マイナンバー123456789000」のような直連を取りこぼすため、文脈語ゲート付きで補完する。
    #   - 文脈語が直前(最大16文字以内)に在るときだけ発火 → 注文番号/連番ID 等(文脈語なし)は伏字しない。
    #   - span は 12桁の数字のみ(文脈語は残す)。ラベルは既存 MYNUMBER と同一([MASKED:MYNUM])。
    #   - (?<!\d)\d{12}(?!\d) で 13桁以上・16桁カードの一部にはマッチしない。重複範囲は下流の dedup が解消。
    for _cm in _MYNUM_CTX_RX.finditer(text_for_detect):
        _ws, _we = _cm.start(), _cm.end()
        _ctx_window = text_for_detect[max(0, _ws - 16):_ws]
        if any(_w in _ctx_window for _w in _MYNUM_CTX_WORDS):
            spans.append(
                {
                    "type": "MYNUMBER",
                    "start": _ws,
                    "end": _we,
                    "value": text[_ws:_we],
                }
            )
    # §F1 (card-boundary): 区切り無し連続 13-19 桁 + Luhn 通過を CREDIT として補完。
    #   既存 CREDIT が拾う区切り入り (4111-1111-…) はそのまま二重検出され下流 dedup で解消。
    #   Luhn ゲートで連番ID (100200300400 等) の誤爆を防ぐ。
    for _cc in _CREDIT_RUN_RX.finditer(text_for_detect):
        if _luhn_ok(text_for_detect[_cc.start():_cc.end()]):
            spans.append(
                {
                    "type": "CREDIT",
                    "start": _cc.start(),
                    "end": _cc.end(),
                    "value": text[_cc.start():_cc.end()],
                }
            )
    # スパンを start で安定化
    spans.sort(key=lambda s: (s["start"], s["end"]))
    # 重複スパン排除（同一範囲のPHONE_JP + PHONE_LAND二重検出対策）
    deduped: list[dict] = []
    for sp in spans:
        if not any(d["start"] == sp["start"] and d["end"] == sp["end"] for d in deduped):
            deduped.append(sp)
    return deduped


# ============================================================
# ga-close-v3 PartD D-3: 伏字件数の「数え方」を本ファイル 1 か所へ集約する
# ============================================================
# 着手前は数える場所ごとに定義が違い、同じ資料で違う数が出ていた (実測):
#   要約 (GET /api/collections/{id}/publish-summary) … masked 層 + 5 種の許可リスト
#       {PERSON_JP,PHONE_JP,EMAIL,MYNUMBER,CREDIT} だけを数える → 361
#   一覧 (GET /api/workspaces)                       … raw 層の pii_detected 列   → 2128
#   一覧 (GET /api/workspaces/{id}/chunks, viewer)   … masked 層の pii_detected 列 → 18
#       (伏字が効くほど masked 層の再判定は 0 になるので「伏字が効いているのに 0 件」)
#   公開履歴 (publish_history.pii_count)             … 層を絞らず raw+masked を合算 → 2146
# 以後はここが唯一の定義であり、表示側・SQL 側で数え直さないこと。
#
# 定義: 「1 論理チャンク = tier='raw' の 1 行」を単位とし、そのチャンクの pii_summary
#       (取り込み時に実際に当てた伏字の {種別: 件数}) に 1 件以上あれば伏字ありと数える。
#   - pii_summary は raw 行と masked 行に同じ値が入るため、どちらの層から数えても
#     同じ数になる (層で意味がずれない)。
#   - pii_detected 列は使わない。raw 側は簡易正規表現 (メール/電話/12桁) の当たりも
#     立てるため実際の伏字 0 件でも 1 になり、masked 側は伏字後の再判定なので普通 0 になる。
PII_COUNT_TIER = "raw"


def pii_counts_from_summaries(summaries) -> dict:
    """pii_summary の並びから伏字件数を集計する唯一の実装。

    Args:
        summaries: pii_summary の並び。各要素は JSON 文字列 / dict / None のいずれか。
    Returns:
        {"chunk_count": 走査した塊数,
         "pii_chunks":  伏字が 1 件以上当たった塊数,
         "pii_spans":   伏字の総件数 (種別ごとの合計),
         "labels":      {種別: 件数} (許可リストで絞らない)}
    """
    labels: dict[str, int] = {}
    chunk_count = 0
    pii_chunks = 0
    pii_spans = 0
    for s in summaries:
        chunk_count += 1
        d = s
        if isinstance(d, str):
            if not d:
                continue
            try:
                d = json.loads(d)
            except Exception:
                continue
        if not isinstance(d, dict):
            continue
        hit = False
        for k, v in d.items():
            try:
                iv = int(v)
            except Exception:
                continue
            if iv <= 0:
                continue
            labels[k] = labels.get(k, 0) + iv
            pii_spans += iv
            hit = True
        if hit:
            pii_chunks += 1
    return {
        "chunk_count": chunk_count,
        "pii_chunks": pii_chunks,
        "pii_spans": pii_spans,
        "labels": labels,
    }


def pii_counts_from_rows(rows, tier: str = PII_COUNT_TIER) -> dict:
    """取り込み結果の行 (dict に tier / pii_summary を持つ) から集計する。"""
    return pii_counts_from_summaries(
        r.get("pii_summary") for r in rows if (r.get("tier") or PII_COUNT_TIER) == tier
    )


def pii_counts_from_db(
    conn,
    workspace_id: str | None = None,
    collection_id: str | None = None,
    tier: str = PII_COUNT_TIER,
) -> dict:
    """chunks 表から集計する。conn は sqlite3 互換の接続。"""
    where = ["tier = ?"]
    params: list = [tier]
    if workspace_id:
        where.append("workspace_id = ?")
        params.append(workspace_id)
    if collection_id:
        where.append("collection_id = ?")
        params.append(collection_id)
    sql = "SELECT pii_summary FROM chunks WHERE " + " AND ".join(where)
    return pii_counts_from_summaries(r[0] for r in conn.execute(sql, params).fetchall())


def pii_count_sql(alias: str = "") -> str:
    """SQL 側で同じ数え方を書くための述語。pii_counts_from_summaries と同じ定義。

    集計を SQL の GROUP BY で行う口 (ドキュメント別一覧・CSV 等) 用。
    alias は chunks 表の別名 ("c" 等)。空なら別名なし。
    """
    p = f"{alias}." if alias else ""
    return (
        f"{p}tier = '{PII_COUNT_TIER}' AND {p}pii_summary IS NOT NULL "
        f"AND {p}pii_summary <> '' AND {p}pii_summary <> '{{}}'"
    )


def mask_text_with_spans(text: str) -> tuple[str, list[dict]]:
    """テキストに PII マスクを適用し、(masked_text, applied_spans) を返す。
    applied_spans は元テキスト基準の start/end を保持する。"""
    if not text:
        return text, []
    spans = detect_pii_spans(text)
    if not spans:
        return text, []
    # 重複/交差を解消。start 同点なら長い span (より具体的パターン) を優先する。
    # 例: '4111-1111-1111-1111' は CREDIT(4-23) を MYNUMBER(4-18) より優先する。
    spans_sorted = sorted(spans, key=lambda s: (s["start"], -s["end"]))
    deduped: list[dict] = []
    last_end = -1
    for s in spans_sorted:
        if s["start"] >= last_end:
            deduped.append(s)
            last_end = s["end"]
    out_parts: list[str] = []
    cursor = 0
    label_to_token = {label: tok for label, _rx, tok in PII_PATTERNS}
    for s in deduped:
        out_parts.append(text[cursor : s["start"]])
        out_parts.append(label_to_token.get(s["type"], "[MASKED]"))
        cursor = s["end"]
    out_parts.append(text[cursor:])
    return "".join(out_parts), deduped
