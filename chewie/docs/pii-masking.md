> **このドキュメントについて**
> Cynovelaは、AI基盤ツールのコンセプトを個人が手を動かして理解するために作った
> 完全非公式の学習ツールです。商用製品・公式実装ではありません。
> 実装はすべてオリジナルで、FastAPI / SQLite / ChromaDB / BGE-M3 / ローカルLLM
> という OSS スタックで構成されています。
> 会社・製品の公式見解を一切代表しません。

# Cynovela PII マスキング

## 1. 設計思想：ベクター DB にはマスク済みのみ入れる

PII（Personally Identifiable Information：個人情報・社外秘情報）対策の基本方針は、「検索対象として広く露出するベクター DB（ChromaDB）には、原則としてマスク済みの本文だけを入れる」というものです。生本文（raw）は別系統で暗号化保管し、管理者ロールに限って引き出せるようにします。

この設計により、次のような状況でも漏えい経路を絞れます。

- 検索ヒットして LLM プロンプトに混入する経路 → マスク済み本文のみが渡る
- ChromaDB のデータをそのままダンプ・コピーされる経路 → マスク済みのみ
- DB ファイルを物理的に持ち去られる経路 → raw 側は Fernet で暗号化済み

これを実現するため、Cynovela は取込時マスキング（Tier1）と回答時マスキング（Tier2）の二重防御を採用しています。

> **廃止済み: マスキングなし取り込み（`collections.raw_only = 1`）** — マスキングを迂回する取り込み（Raw モード）は 2026-07-24 に廃止しました。いま指定すると HTTP 400 で拒否されます（2026-08-02 実測）。過去に作られた `raw_only = 1` のコレクションだけが masked 層を持たない状態で残り得ます（詳細は metadata-engine.md §6）。

---

## 2. Tier1：取込時マスキング

### 2.1 役割

Publish（コレクションを ChromaDB に流し込む処理）の途中で、各 chunk について「生本文（raw）」と「マスク済み本文（masked）」の dual-row を生成します。両方が SQLite の `chunks` テーブルと ChromaDB の両 collection に保存されます。

### 2.2 実装箇所

`rag.py:984-1075`（抜粋）：

```python
pii_flag = 1 if pii_pat.search(chunk or "") else 0
# §段1b: マスク済本文を生成 (context prefix 付き全文を対象)
try:
    _masked_chunk, _mask_spans = _mtws_publish(chunk or "")
except Exception as _me:
    _log.warning(f"§段1b mask 失敗 doc_id={doc_id}: {_me}")
    _masked_chunk, _mask_spans = (chunk or ""), []
# 項目④: 検出種別 × 件数のみを集計（値は捨てる）
...
_masked_doc_id = f"{doc_id}__masked"
# §段1b: masked 本文に対する PII 再評価 (マスクが十分なら 0)
_masked_pii_flag = 1 if pii_pat.search(_masked_chunk or "") else 0
...
_meta_raw["tier"] = "raw"
...
_meta_masked["tier"] = "masked"
all_docs_masked.append(_masked_chunk or "")
```

`_mtws_publish` は `guardrail.mask_text_with_spans` のエイリアスで、正規表現ベースのマスクを各 chunk に適用します。

### 2.3 保管先

| 保管先 | raw tier | masked tier |
|--------|----------|-------------|
| SQLite `chunks` テーブル | `doc_id` 行（`tier='raw'`） | `doc_id + '__masked'` 行（`tier='masked'`） |
| ChromaDB | `{collection_id}__raw` コレクション | `{collection_id}__masked` コレクション |
| 暗号化 | Fernet で暗号化（`enc:` プレフィックス） | 暗号化なし（検索性能確保） |

### 2.4 失敗時の挙動

マスク処理に例外が出ても Publish は止めず、`_log.warning` でログに出してから raw 本文のまま masked 側にも保存します。これは「取込が止まると業務が止まる」リスクを避けるための設計です。

---

## 3. Tier2：回答時マスキング

### 3.1 役割

LLM が生成した回答テキストに対して、利用者のロールに応じてさらに出口マスクを適用します。これにより、何らかの理由で raw 本文が context に混入してしまっても、admin 以外の利用者には届かないようにします。

### 3.2 実装箇所

`routers/chat.py:128-162`：

```python
def _mask_for_viewer(text: str, user: dict | None) -> str:
    """M1 (設計正本準拠): 利用者の保管庫 tier (raw/masked) に応じて
    LLM 生成出力に出口マスクを適用する。

    判定は rag.tier_for_role() に一元化:
      - tier_for_role(role) == "raw"    → 素通し (= admin・素側保管庫の利用者)
      - tier_for_role(role) == "masked" → マスク (= curator/viewer/legacy/未設定・伏せ側保管庫)
    """
    if not text or not user:
        return text
    try:
        from rag import tier_for_role
        if tier_for_role(user.get("role") or "") == "raw":
            return text
    except Exception:
        pass
    try:
        from guardrail import mask_text_with_spans
        masked, _spans = mask_text_with_spans(text)
        return masked
    except Exception:
        return text
```

`_mask_for_viewer` は chat 経路 4 箇所（通常応答 / Compare A / Compare B / SSE 経路）で呼ばれます（`routers/chat.py:653 / 655 / 681 / 1814`）。

### 3.3 ロール別の振り分け

`rag.py:1726-1737`：

```python
def tier_for_role(role: str) -> str:
    """§段2: ロールに応じて保管庫の tier を決める。
    admin → 'raw'   (生本文を保管する管理者保管庫を引く)
    その他 → 'masked' (マスク済本文の一般保管庫を引く)
    """
    return "raw" if (role or "").strip() == "admin" else "masked"
```

`tier_for_role` は、ChromaDB の引き先（`{cid}__raw` か `{cid}__masked` か）と、出口マスクを通すか素通しするか、の両方を決めるため、二重防御として機能します。

---

## 4. Fernet 暗号化

### 4.1 役割

raw tier の本文を SQLite と ChromaDB に保存する直前に Fernet（対称鍵暗号方式の一つで、認証付きの AES-128-CBC + HMAC）で暗号化し、`enc:` というプレフィックス付きで保存します。冪等な実装（既に `enc:` で始まる文字列は再暗号化しない）になっており、二重暗号化を避けます。

### 4.2 実装

- **鍵管理**: `config.py:62` で `Fernet(_KEY)` を初期化。`CYNOVELA_SECRET_KEY` 環境変数で鍵を渡します。本番運用では明示的にこの環境変数を設定することが推奨されています。
- **インターフェース**: `vault_enc.py` の `enc_raw(text)` / `dec_raw(text)` が薄いラッパーを提供します。

```python
ENC_PREFIX = "enc:"

def enc_raw(text: str | None) -> str:
    """raw 本文を暗号化形式に揃える (冪等)。
    - 既に "enc:" 始まり: 二重暗号化しない
    - それ以外: "enc:" + config.encrypt(text) を返す """

def dec_raw(text: str | None) -> str:
    """暗号化形式なら復号、それ以外 (masked / 旧平文) はそのまま素通し (冪等)。"""
```

### 4.3 適用箇所

| 経路 | 適用箇所 | 対象 |
|------|----------|------|
| Chroma 投入時 | `rag.py:1285` | raw tier の `documents` 配列に `enc_raw` を一括適用 |
| SQLite chunks 保存時 | `rag.py:1393` | raw tier 行の `content` を `enc_raw` |
| SQLite parent_chunks 保存時 | `rag.py:1131` | parent の raw tier に `enc_raw` |

masked tier は暗号化しません。検索パフォーマンス（埋め込み計算や全文検索）を確保するためです。raw tier は ChromaDB の `documents` に暗号化済みのバイト列として入るため、引き出し時に `dec_raw` で復号する必要があります。

### 4.4 既存データの移行

`tools/vault_enc_migrate.py` が既存の SQLite / ChromaDB データを一括で `enc:` 形式に揃えるツールとして用意されています。

---

## 5. ロール別の見え方

| ロール | 引き先保管庫 | 出口マスク | 結果として見えるもの |
|--------|--------------|------------|----------------------|
| `admin` | raw tier（暗号化を復号した生本文） | 素通し | 生本文 |
| `curator` | masked tier | 通す | マスク済み本文 |
| `viewer` | masked tier | 通す | マスク済み本文 |
| 未認証・未設定 | masked tier | 通す | マスク済み本文 |

これにより、設定ミスでロールが空になっていても、構造的に raw 本文には届きません。

---

## 6. PII カテゴリ全件

PII 検出には 2 系統があります。

### 6.1 一次系：`guardrail.py`（正規表現ベース）

`guardrail.py:137-153` で 8 種類を定義しています。

| entity_type | 検出対象 | マスク後トークン |
|-------------|----------|------------------|
| `URL` | `https?://...` | `[MASKED:URL]` |
| `EMAIL` | メールアドレス | `[MASKED:EMAIL]` |
| `PHONE_JP` | 携帯番号（070/080/090） | `[MASKED:PHONE]` |
| `PHONE_LAND` | 固定電話番号 | `[MASKED:PHONE]` |
| `CREDIT` | クレジットカード番号（4-4-4-4 形式） | `[MASKED:CREDIT]` |
| `MYNUMBER` | マイナンバー（12 桁） | `[MASKED:MYNUM]` |
| `PASSPORT` | パスポート番号（英 2 + 数字 7） | `[MASKED:PASSPORT]` |
| `IPV4` | IPv4 アドレス | `[MASKED:IP]` |

### 6.2 二次系：`utils/metadata/pii.py`（presidio + GiNZA フォールバック）

presidio（Microsoft Presidio：PII 検出・匿名化ライブラリ）が利用可能なら presidio を使い、ダメなら正規表現フォールバックに切り替わります。日本語 NER は GiNZA（spaCy ベースの日本語 NLP ライブラリ）で固有表現抽出を行います。

検出される追加カテゴリ：

| entity_type | 説明 |
|-------------|------|
| `EMAIL` | メールアドレス（正規表現） |
| `PHONE_JP` | 日本の電話番号 |
| `PHONE_INTL` | 国際電話番号 |
| `IP_ADDRESS` | IP アドレス |
| `MY_NUMBER` | マイナンバー |
| `CREDIT_CARD` | クレジットカード番号 |
| `INTERNAL_URL` | 内部 URL |
| `EMAIL_ADDRESS` | presidio が検出するメール |
| `PHONE_NUMBER` | presidio が検出する電話番号 |
| `DATE_TIME` | presidio が検出する日時 |
| `PERSON_JP` | GiNZA が検出する人名（日本語） |
| `ORG_JP` | GiNZA が検出する組織名（日本語） |
| `LOC_JP` | GiNZA が検出する地名（日本語） |
| `ADDRESS_JP` | 日本語住所ルール |

`HIGH_RISK_TYPES` として `{CREDIT_CARD, MY_NUMBER, SSN, PASSPORT, IBAN_CODE}` が定義されており、感度スコア（0〜100）の計算で重く扱われます。

### 6.3 ポリシーマトリクス対象

`routers/policies.py:159` で、Workspace ポリシーから選択可能な PII タイプは次の 6 種に絞られています。

```python
pii_types = ["EMAIL", "PHONE_JP", "PHONE_LAND", "CREDIT", "MYNUMBER", "IPV4"]
```

URL と PASSPORT は検出はされますがポリシー UI からの選択肢には入っていません。

---

## 7. `pii_mode` の違い

### 7.1 設定方法

`cynovela.yaml` の `pii_mode` キーで設定します。CLI 引数（旧 `--pii-mode`）は廃止されました。実行時に変更したい場合は `/api/settings/pii-mode`（PUT）で切り替えられます（admin 限定）。

### 7.2 3 モードの動作

| 値 | 検出方式 | 速度 | 精度 | 主用途 |
|----|----------|------|------|--------|
| `lite` | 正規表現のみ | 高速 | 低〜中 | 大量取込・軽量環境 |
| `standard`（既定） | 正規表現 + GiNZA NER | 中庸 | 中〜高 | 既定値・推奨 |
| `quality` | 正規表現 + GiNZA NER + 詳細フィルタリング | 低速 | 高 | 研究開発・機微情報の精査 |

無効な値が与えられた場合は `standard` にリセットされます（`server.py:3135-3137`）。

起動時に次のようなログが出ます：

```
[Cynovela] PII detection mode: standard (from cynovela.yaml)
```

### 7.3 検出件数の集計

PII 検出は次の 2 系統で集計されます。

- **`/api/guardrails/pii-detections`（GET）**: `audit_logs` テーブルから集計（admin 限定）
- **`/api/pii-detections`（GET）**: `chunks` テーブルからドキュメント単位で集計（P4-14、admin 限定）

両方とも admin ロール必須で、`_require_admin(request)` がエンドポイント先頭で呼ばれます。

---

## 8. 旧実装からの移行

旧 `utils/pii_detector.py` は削除され、実装は `utils/metadata/pii.py` に集約されました（Stage R6-fix / Phase 3-fix 経由）。新実装の `llm_judge_pi(text)` は LLM judge ベースで追加判定を行う関数で、Stage R7 C-5 で導入されました。

---

最終更新: 2026-05-26 / Alpha GA 対応版
