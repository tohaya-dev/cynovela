# 同梱データの内訳（コンテナ版 / all-in-one）

**日本語版はこちら → [日本語](#日本語)**

## English

Breakdown of the bundled data (container edition / all-in-one).

This document is written out automatically when the package is built. The numbers are the values counted
when the package was built, for the things that are actually in this package. They are not values written by hand.

The only source of the bundled data is **`dummy-corpus/` inside this package**. No working documents or
indexes of the side that builds it are included at all.

| Item | Count |
|---|---|
| Documents (files) | 7 |
| Chunks | 128 |
| Parent chunks | 48 |
| Workspaces | 1 |
| Ingest sources | 1 |
| Collections | 1 |
| Places masked at ingest time | 16 |

Chunks are stored in two layers, before masking and after masking, and both are encrypted with the key of the safe.
The index used for search (the vector) is built **only from the masked layer**.

All the bundled documents are explanatory samples on the theme of a fictitious company "アオゾラ商事". The people,
organizations, addresses, phone numbers, email addresses and so on that appear in them do not exist in reality.

---

# 日本語

この文書は配布物を作るときに自動で書き出しています。数字は、この配布物に実際に入っている
ものを配布物を作るときに数えた値です。手で書いた値ではありません。

同梱データの入手元は、**この配布物の中の `dummy-corpus/` だけ**です。作る側の作業用の
資料やインデックスは一切入っていません。

| 項目 | 件数 |
|---|---|
| 資料（ファイル） | 7 |
| 塊（チャンク） | 128 |
| 親の塊 | 48 |
| 作業場所（ワークスペース） | 1 |
| 取り込み元 | 1 |
| コレクション | 1 |
| 取り込み時に伏せた箇所 | 16 |

塊はマスキング前とマスキング済みの二層で保管し、どちらも金庫の鍵で暗号化しています。検索に使うインデックス
（ベクター）は**マスキング済みの層だけ**から作っています。

同梱の資料はすべて架空の企業「アオゾラ商事」を題材にした説明用のサンプルです。登場する
人物・組織・住所・電話番号・メールアドレスなどはすべて実在しません。
