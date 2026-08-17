# Cynovela スライドHTML 変換ルール

**日本語版はこちら → [日本語](#日本語)**

## English

# Every subagent must cat this file before starting work

## Preconditions
- Input: `docs/[name].md`
- Output: `docs/html/[name].html`
- CSS: embed the full contents of `docs/html/_slide-base.css` inline in `<style>`
- Light mode fixed. Dark mode prohibited. Do not write `@media prefers-color-scheme`
- Company names and specific product names prohibited. Refer to the reference AI tool as 「参照元のAIツール」
- Fully standalone (no external URL / CDN / font references)

## HTML skeleton (must follow this structure)
```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[ドキュメント名] — Cynovela</title>
<style>
    /* _slide-base.css の内容を全文ここに貼る */
</style>
</head>
<body>
<div class="slide-deck" id="deck">
<!-- スライドをここに並べる -->
</div>
<nav class="nav-bar">
<button id="btn-prev" onclick="navigate(-1)">← 前へ</button>
<span id="slide-counter">1 / N</span>
<button id="btn-next" onclick="navigate(1)">次へ →</button>
</nav>
<script>
let current = 0;
const slides = document.querySelectorAll('.slide');
function show(n) {
  slides.forEach((s,i) => s.classList.toggle('active', i===n));
  document.getElementById('slide-counter').textContent = (n+1)+' / '+slides.length;
  document.getElementById('btn-prev').disabled = n===0;
  document.getElementById('btn-next').disabled = n===slides.length-1;
  current = n;
  location.hash = 'slide-'+(n+1);
}
function navigate(dir) { show(Math.max(0,Math.min(slides.length-1,current+dir))); }
document.addEventListener('keydown', e => {
  if(e.key==='ArrowRight'||e.key==='ArrowDown'||e.key===' ') { navigate(1); e.preventDefault(); }
  if(e.key==='ArrowLeft'||e.key==='ArrowUp') { navigate(-1); e.preventDefault(); }
});
const hash = location.hash.match(/slide-(\d+)/);
show(hash ? Math.min(parseInt(hash[1])-1, slides.length-1) : 0);
</script>
</body>
</html>
```

## Markdown → slide conversion rules

### Rule 1: cover slide (always one at the top)
```html
<div class="slide cover active" id="slide-1">
<div class="cover-brand">📊 Cynovela</div>
<div class="cover-title">[# の見出しテキスト、なければファイル名]</div>
<div class="cover-sub">Cynovela — 非公式・個人学習目的</div>
</div>
```

### Rule 2: `##` heading → start a new slide
Each `## テキスト` becomes one slide.
```html
<div class="slide" id="slide-N">
<div class="slide-header">
<span class="doc-name">[ドキュメント名]</span>
<span class="slide-title">[## のテキスト]</span>
</div>
<div class="slide-body">
<!-- ## 以降 次の ## までの内容 -->
</div>
<div class="slide-footer">
<span class="brand">Cyno<span class="accent">vela</span></span>
<span>非公式・個人学習目的</span>
</div>
</div>
```

### Rule 3: content splitting (required)
If any of the following applies, split the slide automatically.

- More than 7 bullet items → split into 2 slides, first half / second half
- A code block over 20 lines → make a separate slide for the code block alone
- A table over 8 rows → make a separate slide for the table alone
- Total text in the slide body over 900 characters → split as appropriate

Add `<span class="continued">(2/2)</span>` to the header of split slides.
You may append "(続き)" to the slide title from the second slide onward.

### Rule 4: element conversion
| Markdown | HTML |
|----------|------|
| `### テキスト` | `<h3>テキスト</h3>` |
| `#### テキスト` | `<h4>テキスト</h4>` |
| `- 項目` / `* 項目` | `<ul><li>項目</li></ul>` |
| `1. 項目` | `<ol><li>項目</li></ol>` |
| ` ```lang ... ``` ` | `<pre><code>...</code></pre>` (HTML escaping required) |
| `\| テーブル \|` | `<table><thead><tr><th>...</thead><tbody><tr><td>...</tbody></table>` |
| `**太字**` | `<strong>太字</strong>` |
| `*斜体*` | `<em>斜体</em>` |
| `> 引用` | `<blockquote>引用</blockquote>` |
| `[text](url)` | `<a href="url" target="_blank" rel="noopener">text</a>` |
| `` `code` `` | `<code>code</code>` |
| `<!-- BACKLOG: ... -->` | Keep as an HTML comment (not displayed) |

Note: `<`, `>` and `&` must be HTML escaped (including characters inside code and tables).

### Rule 5: disclaimer block
A notice block at the top of the Markdown, such as `> **このドキュメントについて**`,
becomes its own slide as a single `<blockquote>` right after the cover slide.

```html
<div class="slide" id="slide-2">
<div class="slide-header">
<span class="doc-name">[ドキュメント名]</span>
<span class="slide-title">このドキュメントについて</span>
</div>
<div class="slide-body">
<blockquote>[免責テキスト全文]</blockquote>
</div>
<div class="slide-footer">
<span class="brand">Cyno<span class="accent">vela</span></span>
<span>非公式・個人学習目的</span>
</div>
</div>
```

### Rule 6: for manual-complete.md only
Add one chapter title slide before each `## 見出し`.
Chapter detection uses the heading text (prefixes such as "S-1", "G-1", "D-1", or "Stage" / "Guide" / "Deep").

```html
<div class="slide chapter-slide" id="slide-N">
<div class="chapter-title">[章名（S-1 セットアップ など）]</div>
</div>
```

### Rule 7: footer
Put a `slide-footer` at the end of every non-cover slide:
```html
<div class="slide-footer">
<span class="brand">Cyno<span class="accent">vela</span></span>
<span>非公式・個人学習目的</span>
</div>
```

## Counter initialisation
After generating all slides, write the actual number of slides into the N of
`<span id="slide-counter">1 / N</span>`.

## Prohibitions
- Do not write dark mode CSS (`prefers-color-scheme` prohibited)
- Do not write company names or specific product names (write the name of the reference AI tool as 「参照元のAIツール」 too)
- Do not reference external CDNs / URLs (including fonts, JS and CSS)
- Do not rewrite existing `docs/*.md` or `docs/*.html` (write only into `docs/html/`)
- `BACKLOG.md` is out of scope for conversion
- Do not put `active` on any `class="slide"` other than `slide-1` (JS adds it)

## Operation check (after generating each file)
- `wc -l docs/html/[name].html` → must not be 0 lines
- Must start with `<!DOCTYPE html>`
- Must have `</script></body></html>` near the end
- Must have exactly one `class="slide cover active"`
- The N in `<span id="slide-counter">` must match the actual number of slides

---

# 日本語

# 全サブエージェントはこのファイルを cat してから作業すること

## 前提
- 入力: `docs/[name].md`
- 出力: `docs/html/[name].html`
- CSS: `docs/html/_slide-base.css` の内容を全文インラインで `<style>` に埋め込む
- ライトモード固定。ダークモード禁止。`@media prefers-color-scheme` は書かない
- 会社名・固有製品名禁止。参照元AIツールは「参照元のAIツール」と表記
- 完全スタンドアロン（外部URL/CDN/フォント参照なし）

## HTMLの骨格（必ずこの構造にする）
```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[ドキュメント名] — Cynovela</title>
<style>
    /* _slide-base.css の内容を全文ここに貼る */
</style>
</head>
<body>
<div class="slide-deck" id="deck">
<!-- スライドをここに並べる -->
</div>
<nav class="nav-bar">
<button id="btn-prev" onclick="navigate(-1)">← 前へ</button>
<span id="slide-counter">1 / N</span>
<button id="btn-next" onclick="navigate(1)">次へ →</button>
</nav>
<script>
let current = 0;
const slides = document.querySelectorAll('.slide');
function show(n) {
  slides.forEach((s,i) => s.classList.toggle('active', i===n));
  document.getElementById('slide-counter').textContent = (n+1)+' / '+slides.length;
  document.getElementById('btn-prev').disabled = n===0;
  document.getElementById('btn-next').disabled = n===slides.length-1;
  current = n;
  location.hash = 'slide-'+(n+1);
}
function navigate(dir) { show(Math.max(0,Math.min(slides.length-1,current+dir))); }
document.addEventListener('keydown', e => {
  if(e.key==='ArrowRight'||e.key==='ArrowDown'||e.key===' ') { navigate(1); e.preventDefault(); }
  if(e.key==='ArrowLeft'||e.key==='ArrowUp') { navigate(-1); e.preventDefault(); }
});
const hash = location.hash.match(/slide-(\d+)/);
show(hash ? Math.min(parseInt(hash[1])-1, slides.length-1) : 0);
</script>
</body>
</html>
```

## Markdown → スライド変換ルール

### ルール1: カバースライド（先頭に必ず1枚）
```html
<div class="slide cover active" id="slide-1">
<div class="cover-brand">📊 Cynovela</div>
<div class="cover-title">[# の見出しテキスト、なければファイル名]</div>
<div class="cover-sub">Cynovela — 非公式・個人学習目的</div>
</div>
```

### ルール2: `##` 見出し → 新スライド開始
各 `## テキスト` が1枚のスライドになる。
```html
<div class="slide" id="slide-N">
<div class="slide-header">
<span class="doc-name">[ドキュメント名]</span>
<span class="slide-title">[## のテキスト]</span>
</div>
<div class="slide-body">
<!-- ## 以降 次の ## までの内容 -->
</div>
<div class="slide-footer">
<span class="brand">Cyno<span class="accent">vela</span></span>
<span>非公式・個人学習目的</span>
</div>
</div>
```

### ルール3: コンテンツ分割（必須）
以下のいずれかに該当する場合、スライドを自動分割する。

- 箇条書きアイテムが 7件を超える → 前半/後半で2枚に分割
- コードブロックが 20行を超える → コードブロックだけで別スライドを作る
- テーブルが 8行を超える → テーブルだけで別スライドを作る
- スライド本文の合計テキスト量が 900文字を超える → 適宜分割

分割したスライドにはヘッダーに `<span class="continued">(2/2)</span>` を追加する。
2枚目以降はスライドタイトルに「(続き)」を付けても良い。

### ルール4: 要素の変換
| Markdown | HTML |
|----------|------|
| `### テキスト` | `<h3>テキスト</h3>` |
| `#### テキスト` | `<h4>テキスト</h4>` |
| `- 項目` / `* 項目` | `<ul><li>項目</li></ul>` |
| `1. 項目` | `<ol><li>項目</li></ol>` |
| ` ```lang ... ``` ` | `<pre><code>...</code></pre>` （HTMLエスケープ必須） |
| `\| テーブル \|` | `<table><thead><tr><th>...</thead><tbody><tr><td>...</tbody></table>` |
| `**太字**` | `<strong>太字</strong>` |
| `*斜体*` | `<em>斜体</em>` |
| `> 引用` | `<blockquote>引用</blockquote>` |
| `[text](url)` | `<a href="url" target="_blank" rel="noopener">text</a>` |
| `` `code` `` | `<code>code</code>` |
| `<!-- BACKLOG: ... -->` | HTMLコメントとして残す（表示しない） |

注意: `<`, `>`, `&` は HTML エスケープすること（コード/テーブル内の文字も含む）。

### ルール5: 免責ブロック
Markdownの先頭にある `> **このドキュメントについて**` などの注意書きブロックは
カバースライドの後ろに `<blockquote>` 1枚として独立スライドにする。

```html
<div class="slide" id="slide-2">
<div class="slide-header">
<span class="doc-name">[ドキュメント名]</span>
<span class="slide-title">このドキュメントについて</span>
</div>
<div class="slide-body">
<blockquote>[免責テキスト全文]</blockquote>
</div>
<div class="slide-footer">
<span class="brand">Cyno<span class="accent">vela</span></span>
<span>非公式・個人学習目的</span>
</div>
</div>
```

### ルール6: manual-complete.md 専用
`## 見出し` の前に章タイトルスライドを1枚追加する。
章の判定は見出しテキスト（"S-1", "G-1", "D-1" 等のプレフィックス、または "Stage" / "Guide" / "Deep" 等）で行う。

```html
<div class="slide chapter-slide" id="slide-N">
<div class="chapter-title">[章名（S-1 セットアップ など）]</div>
</div>
```

### ルール7: フッター
すべての非カバースライドの末尾に `slide-footer` を入れる:
```html
<div class="slide-footer">
<span class="brand">Cyno<span class="accent">vela</span></span>
<span>非公式・個人学習目的</span>
</div>
```

## カウンタ初期化
全スライド生成後、`<span id="slide-counter">1 / N</span>` の N に実際のスライド枚数を書く。

## 禁止事項
- ダークモード CSS を書くな（`prefers-color-scheme` 禁止）
- 会社名・固有製品名を書くな（参照元AIツール名も「参照元のAIツール」と表記）
- 外部CDN/URLを参照するな（フォント・JS・CSS含む）
- 既存の `docs/*.md` や `docs/*.html` を書き換えるな（`docs/html/` への書き込みのみ）
- `BACKLOG.md` は変換対象外
- `slide-1` 以外の `class="slide"` には `active` を付けるな（JSが付与する）

## 動作確認（各ファイル生成後）
- `wc -l docs/html/[name].html` → 0行ではないこと
- 先頭が `<!DOCTYPE html>` で始まること
- 末尾近くに `</script></body></html>` があること
- `class="slide cover active"` が1つだけあること
- `<span id="slide-counter">` の N が実際のスライド数と一致していること
