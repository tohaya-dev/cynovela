# 同梱データの内訳

**日本語版はこちら → [日本語](#日本語)**

## English

What sample material ships in this package, and what is created on your machine.

The only data bundled in this package is **`dummy-corpus/`**: 21 explanatory sample
documents about a fictional organization, "アオゾラ商事" (Aozora Shoji). None of the
people, organisations, addresses, phone numbers, e-mail addresses or numbers in
them are real, and each file states so in its first line.

The sample material is split into three workspaces, so the demo can show that
different accounts see different material:

| Workspace | Folder | Files | Who belongs to it |
|---|---|---|---|
| 全社 (`ws-general`) | `dummy-corpus/general/` | 7 | The administrator and the viewer |
| 営業 (`ws-sales`) | `dummy-corpus/sales/` | 7 | The administrator only |
| 人事 (`ws-hr`) | `dummy-corpus/hr/` | 7 | The administrator only |

Signed in as the viewer, only 全社 is visible and searchable; the sales and HR
material does not appear. Signed in as the administrator, all three are visible.
Personal information in the material (names, phone numbers, e-mail addresses,
dates of birth, ID-style numbers) is detected at ingest and masked for the
viewer, so the demo shows both access separation and masking.

The following are **not** included in the package. They are created on your machine:

| Item | When it is created |
|---|---|
| Encryption key file (`store/secret.key`) | At the first startup |
| Token-signing key (`store/db/jwt/secret.key`) | At the first startup |
| Demo database (`store/db/demo.db`) | At the first `--demo` startup |
| Search index (`store/vector/demo/`) | At the first `--demo` startup |

At the first `--demo` startup, the server ingests `dummy-corpus/` on the spot:
it reads the 21 files, detects and masks personal information, encrypts the
chunks with the key generated on this machine, and builds the search index.
Progress is printed to the startup log. On later startups, nothing is
re-ingested; material you add yourself is kept.

Because the keys are generated per machine, no two installations share a key.

Chunks are stored in two layers, before masking and after masking, and both are
encrypted with the key generated on this machine. The index used for search
(the vectors) is built from **the masked layer only**.

---

# 日本語

この配布物に同梱されているサンプルと、受け取った機材の上で作られるものの内訳です。

配布物に同梱されているデータは **`dummy-corpus/`** だけです。架空の企業
「アオゾラ商事」を題材にした説明用のサンプル資料 21 ファイルで、登場する
人物・組織・住所・電話番号・メールアドレス・番号はすべて実在しません。
各ファイルの冒頭にもその旨を明記しています。

サンプルは3つの作業場所（ワークスペース）に分かれており、アカウントによって
見える範囲が違うことをデモで見せられます。

| 作業場所 | フォルダ | 資料 | 所属 |
|---|---|---|---|
| 全社（`ws-general`） | `dummy-corpus/general/` | 7 件 | 管理者と閲覧者 |
| 営業（`ws-sales`） | `dummy-corpus/sales/` | 7 件 | 管理者のみ |
| 人事（`ws-hr`） | `dummy-corpus/hr/` | 7 件 | 管理者のみ |

閲覧者でログインすると見える・検索できるのは「全社」だけで、営業と人事の資料は
出てきません。管理者は3つとも見えます。資料に含まれる個人情報（氏名・電話番号・
メールアドレス・生年月日・番号類）は取り込み時に検出され、閲覧者には伏せて
表示されます。アクセス権の分離と伏字の両方を、この構成で見せられます。

次のものは配布物に**入っていません**。受け取った機材の上で作られます。

| 項目 | 作られるとき |
|---|---|
| 暗号化用の鍵ファイル（`store/secret.key`） | 初回起動時 |
| トークン署名用の鍵（`store/db/jwt/secret.key`） | 初回起動時 |
| デモのデータベース（`store/db/demo.db`） | `--demo` の初回起動時 |
| 検索用のインデックス（`store/vector/demo/`） | `--demo` の初回起動時 |

`--demo` の初回起動時に、サーバが `dummy-corpus/` をその場で取り込みます。
21 ファイルを読み取り、個人情報を検出して伏せ、この機材で生成された鍵で
チャンクを暗号化し、検索用のインデックスを作ります。進捗は起動ログに出ます。
2 回目以降の起動では取り込み直しません。自分で足した資料も消えません。

鍵は機材ごとに生成されるため、別々のインストールが同じ鍵を持つことはありません。

チャンクはマスキング前とマスキング済みの二層で保管し、どちらもこの機材で生成された
鍵で暗号化されます。検索に使うインデックス（ベクター）は**マスキング済みの層だけ**から
作られます。
