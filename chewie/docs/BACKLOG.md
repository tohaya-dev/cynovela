# ドキュメント整備 バックログ一覧

**日本語版はこちら → [日本語](#日本語)**

## English

Created: 2026-05-26

This file is a list of undecided items that were recorded as HTML comments (BACKLOG tags)
while each Phase B document was being generated.
Because no basis was found in spec-raw, a definitive statement was deferred; these are
candidates to be added later after checking the code / design.

Total: 25 items

## List of BACKLOG items by document

- **answer-modes.md** (line 103): The specification for structured answer templates (fixed JSON output, forced tags, etc.) is undecided
- **answer-modes.md** (line 132): Full integration of the Abstention fallback based on confidence_threshold is unimplemented
- **architecture.md** (line 186): A physical workspace boundary at the ChromaDB level is listed in A-6 as a HIGH priority bug handed over to Phase 3; currently separation is per collection_id
- **api-reference.md** (line 22): The token format after moving to JWT is undecided
- **api-reference.md** (line 194): Full coverage of the individual specification of each endpoint (path, method, input/output schema) is still being organised
- **guardrails.md** (line 55): The 5 categories Legal / Healthcare / Sales / Technical / Marketing are defined in the old classifier.py but are not used by the current guardrail seed. Whether to enable them at GA, and how to connect them to the classification engine, has no confirming information in spec-raw
- **faq.md** (line 14): A comparison table against the specific features of the reference tool has no basis in spec-raw. Do not write it.
- **faq.md** (line 37): The list of extensions supported by extract_text is not enumerated in spec-raw. Add after confirming.
- **faq.md** (line 97): The rest of the roadmap detail (RAG quality / JWT authentication / MCP publication, etc.) is in CLAUDE.md, but there are places that cannot be confirmed in spec-raw. In the FAQ, keep it to one line only.
- **handson-advanced.md** (line 46): The A-6 specification explicitly states "WS separation: no ChromaDB physical boundary" as a HIGH bug handed over to Phase 3
- **handson-advanced.md** (line 186): The A-5 specification raises "MCP limited to conda" as a known-limitations candidate, but gives no explicit cause
- **deployment.md** (line 25): The status of operation checks on Windows / Linux / Docker environments is unconfirmed, as spec-raw does not describe it
- **deployment.md** (line 26): Details for GPU use (CUDA version, memory guidance) are unconfirmed, as spec-raw does not describe them
- **known-limitations.md** (line 81): The technical reason why MCP is limited to conda is unconfirmed, as spec-raw does not state it explicitly
- **known-limitations.md** (line 121): spec-raw has no explicit description of the relationship between IP masking behaviour and the admin tier, and the cause is under investigation. Detailed conditions and workarounds are unconfirmed
- **known-limitations.md** (line 129): Whether a cross-collection search UI / API exists in the GUI is unconfirmed, as spec-raw does not describe it
- **metadata-engine.md** (line 208): Differential synchronisation based on content_hash comparison is specification-undecided
- **rag-pipeline.md** (line 129): An independent prompt switch equivalent to a "STRICT mode", and a strictness dial that changes guardrail strength in stages, could not be confirmed in spec-raw, so here the two-way switch of the system prompt is treated as the "strictness mode"
- **rag-pipeline.md** (line 158): confidence_threshold is already defined in config, but the actual Abstention exclusion logic is only partially integrated into the search pipeline. On the state of integration across all stages, spec-raw only says "partially integrated into the pipeline", and which branch actually rejects could not be confirmed
- **security-design.md** (line 62): Making WS separation a physical boundary, and strengthening cross-boundary checks, is Phase 3 work
- **security-design.md** (line 128): The existence of docs/guardrails.md is planned to be generated in the B-3 phase
- **security-design.md** (line 226): The design detail of dedicated detection for indirect prompt injection is fixed in Phase 3
- **rbac.md** (line 125): Changes to the role check helper when JWT is introduced are undefined
- **spec-overview.md** (line 118): Differential detection by content_hash comparison is specification-undecided
- **spec-overview.md** (line 124): Whether to introduce structured answer templates is undecided

## By category

### A. ChromaDB / WS physical boundary (handed over to Phase 3)
- docs/architecture.md:186:<!-- BACKLOG: ChromaDB レベルでの workspace 物理境界は Phase 3 引き継ぎの HIGH 優先度バグとして A-6 に挙がっており、現状は collection_id 単位での分離 -->
- docs/handson-advanced.md:46:> **補足**: ワークスペース分離のうち、ChromaDB レベルでの物理境界は強化が継続中です。`<!-- BACKLOG: A-6 仕様で「WS 分離: ChromaDB 物理境界なし」が Phase 3 引き継ぎ HIGH バグとして明示されています -->`
- docs/security-design.md:62:<!-- BACKLOG: WS 分離の物理境界化、越境チェックの強化は Phase 3 対応 -->

### B. JWT / authentication (planned for Beta GA)
- docs/api-reference.md:22:<!-- BACKLOG: JWT 化後のトークン形式は未定 -->
- docs/faq.md:97:<!-- BACKLOG: それ以外のロードマップ詳細（RAG 品質・JWT 認証・MCP 公開等）は CLAUDE.md にあるが、spec-raw では確認できない箇所がある。FAQ では一行のみとする。 -->
- docs/rbac.md:125:<!-- BACKLOG: JWT 導入時のロール検査ヘルパーの変更点は未定義 -->

### C. RAG / Abstention / structured answers
- docs/answer-modes.md:103:<!-- BACKLOG: 構造化回答テンプレート（JSON 出力固定、タグ強制など）の仕様は未定 -->
- docs/answer-modes.md:132:<!-- BACKLOG: confidence_threshold を踏まえた Abstention フォールバックの完全統合は未実装 -->
- docs/rag-pipeline.md:129:<!-- BACKLOG: 「STRICT モード」相当の独立したプロンプト切替や、ガードレール強度を段階的に変える厳格度ダイヤルは spec-raw で確認できなかったため、ここではシステムプロンプトの 2 種類切替を「厳格度モード」として扱う -->
- docs/rag-pipeline.md:158:<!-- BACKLOG: confidence_threshold は config に定義済みだが、実際の Abstention 除外ロジックは検索パイプラインに部分統合のみ。全段への統合状況は spec-raw に「パイプラインに部分統合」とだけあり、どの分岐で実際にハジくかまでは確認できなかった -->
- docs/spec-overview.md:124:<!-- BACKLOG: 構造化回答テンプレートの導入可否は未定 -->

### D. Environment / platform operation checks
- docs/handson-advanced.md:186:> **既知の制限**: MCP サーバーの実行は conda 環境前提です。<!-- BACKLOG: A-5 仕様に「MCP の conda 限定」の旨が known-limitations 候補として挙げられているが、原因の明示はなし -->
- docs/deployment.md:25:<!-- BACKLOG: Windows / Linux / Docker 環境での動作確認状況は spec-raw に記載がないため未確認 -->
- docs/deployment.md:26:<!-- BACKLOG: GPU 利用時の詳細（CUDA バージョン、メモリ目安）は spec-raw に記載がないため未確認 -->
- docs/known-limitations.md:81:<!-- BACKLOG: MCP が conda 限定である技術的な理由は spec-raw に明示されていないため未確認 -->

### E. Other (unclassified)
- docs/api-reference.md:194:<!-- BACKLOG: 各エンドポイントの個別仕様（パス、メソッド、入出力スキーマ）の網羅はまだ整理途中 -->
- docs/guardrails.md:55:<!-- BACKLOG: Legal / Healthcare / Sales / Technical / Marketing の 5 カテゴリは旧 classifier.py に定義はあるが、現行のガードレールシードでは使われていない。GA 時点でこれらを有効化するのか・分類エンジンとの接続をどうするかは spec-raw に確認情報なし -->
- docs/faq.md:14:<!-- BACKLOG: 参照元ツールの具体的機能との対照表は spec-raw に根拠なし。書かない。 -->
- docs/faq.md:37:<!-- BACKLOG: extract_text の対応拡張子一覧は spec-raw に列挙がない。確認後追記。 -->
- docs/known-limitations.md:121:<!-- BACKLOG: spec-raw には IP マスキングの挙動と admin tier の関係について明示的な記述がなく、原因は調査中。詳細条件・回避策は未確認 -->
- docs/known-limitations.md:129:<!-- BACKLOG: GUI 上での横断検索 UI / API の有無は spec-raw に記載がないため未確認 -->
- docs/metadata-engine.md:208:<!-- BACKLOG: content_hash 比較ベースの差分同期は仕様未確定 -->
- docs/security-design.md:128:<!-- BACKLOG: docs/guardrails.md の存在は B-3 フェーズで生成予定 -->
- docs/security-design.md:226:<!-- BACKLOG: 間接プロンプトインジェクション専用検出の設計詳細は Phase 3 で確定 -->
- docs/spec-overview.md:118:<!-- BACKLOG: content_hash 比較の差分検出は仕様未確定 -->

---
Last updated: 2026-05-26 / Alpha GA edition

---

# 日本語

作成日: 2026-05-26

本ファイルは Phase B の各ドキュメント生成中に HTML コメント（BACKLOG タグ）として記録された未確定事項の一覧です。
spec-raw に根拠が見つからないため断定を保留し、後日コード/設計確認のうえ追記する候補となります。

総件数: 25 件

## ドキュメント別 BACKLOG 一覧

- **answer-modes.md** (行103): 構造化回答テンプレート（JSON 出力固定、タグ強制など）の仕様は未定 
- **answer-modes.md** (行132): confidence_threshold を踏まえた Abstention フォールバックの完全統合は未実装 
- **architecture.md** (行186): ChromaDB レベルでの workspace 物理境界は Phase 3 引き継ぎの HIGH 優先度バグとして A-6 に挙がっており、現状は collection_id 単位での分離 
- **api-reference.md** (行22): JWT 化後のトークン形式は未定 
- **api-reference.md** (行194): 各エンドポイントの個別仕様（パス、メソッド、入出力スキーマ）の網羅はまだ整理途中 
- **guardrails.md** (行55): Legal / Healthcare / Sales / Technical / Marketing の 5 カテゴリは旧 classifier.py に定義はあるが、現行のガードレールシードでは使われていない。GA 時点でこれらを有効化するのか・分類エンジンとの接続をどうするかは spec-raw に確認情報なし 
- **faq.md** (行14): 参照元ツールの具体的機能との対照表は spec-raw に根拠なし。書かない。 
- **faq.md** (行37): extract_text の対応拡張子一覧は spec-raw に列挙がない。確認後追記。 
- **faq.md** (行97): それ以外のロードマップ詳細（RAG 品質・JWT 認証・MCP 公開等）は CLAUDE.md にあるが、spec-raw では確認できない箇所がある。FAQ では一行のみとする。 
- **handson-advanced.md** (行46): A-6 仕様で「WS 分離: ChromaDB 物理境界なし」が Phase 3 引き継ぎ HIGH バグとして明示されています 
- **handson-advanced.md** (行186): A-5 仕様に「MCP の conda 限定」の旨が known-limitations 候補として挙げられているが、原因の明示はなし 
- **deployment.md** (行25): Windows / Linux / Docker 環境での動作確認状況は spec-raw に記載がないため未確認 
- **deployment.md** (行26): GPU 利用時の詳細（CUDA バージョン、メモリ目安）は spec-raw に記載がないため未確認 
- **known-limitations.md** (行81): MCP が conda 限定である技術的な理由は spec-raw に明示されていないため未確認 
- **known-limitations.md** (行121): spec-raw には IP マスキングの挙動と admin tier の関係について明示的な記述がなく、原因は調査中。詳細条件・回避策は未確認 
- **known-limitations.md** (行129): GUI 上での横断検索 UI / API の有無は spec-raw に記載がないため未確認 
- **metadata-engine.md** (行208): content_hash 比較ベースの差分同期は仕様未確定 
- **rag-pipeline.md** (行129): 「STRICT モード」相当の独立したプロンプト切替や、ガードレール強度を段階的に変える厳格度ダイヤルは spec-raw で確認できなかったため、ここではシステムプロンプトの 2 種類切替を「厳格度モード」として扱う 
- **rag-pipeline.md** (行158): confidence_threshold は config に定義済みだが、実際の Abstention 除外ロジックは検索パイプラインに部分統合のみ。全段への統合状況は spec-raw に「パイプラインに部分統合」とだけあり、どの分岐で実際にハジくかまでは確認できなかった 
- **security-design.md** (行62): WS 分離の物理境界化、越境チェックの強化は Phase 3 対応 
- **security-design.md** (行128): docs/guardrails.md の存在は B-3 フェーズで生成予定 
- **security-design.md** (行226): 間接プロンプトインジェクション専用検出の設計詳細は Phase 3 で確定 
- **rbac.md** (行125): JWT 導入時のロール検査ヘルパーの変更点は未定義 
- **spec-overview.md** (行118): content_hash 比較の差分検出は仕様未確定 
- **spec-overview.md** (行124): 構造化回答テンプレートの導入可否は未定 

## カテゴリ別

### A. ChromaDB / WS 物理境界（Phase 3 引継ぎ）
- docs/architecture.md:186:<!-- BACKLOG: ChromaDB レベルでの workspace 物理境界は Phase 3 引き継ぎの HIGH 優先度バグとして A-6 に挙がっており、現状は collection_id 単位での分離 -->
- docs/handson-advanced.md:46:> **補足**: ワークスペース分離のうち、ChromaDB レベルでの物理境界は強化が継続中です。`<!-- BACKLOG: A-6 仕様で「WS 分離: ChromaDB 物理境界なし」が Phase 3 引き継ぎ HIGH バグとして明示されています -->`
- docs/security-design.md:62:<!-- BACKLOG: WS 分離の物理境界化、越境チェックの強化は Phase 3 対応 -->

### B. JWT / 認証関連（Beta GA 予定）
- docs/api-reference.md:22:<!-- BACKLOG: JWT 化後のトークン形式は未定 -->
- docs/faq.md:97:<!-- BACKLOG: それ以外のロードマップ詳細（RAG 品質・JWT 認証・MCP 公開等）は CLAUDE.md にあるが、spec-raw では確認できない箇所がある。FAQ では一行のみとする。 -->
- docs/rbac.md:125:<!-- BACKLOG: JWT 導入時のロール検査ヘルパーの変更点は未定義 -->

### C. RAG / Abstention / 構造化回答
- docs/answer-modes.md:103:<!-- BACKLOG: 構造化回答テンプレート（JSON 出力固定、タグ強制など）の仕様は未定 -->
- docs/answer-modes.md:132:<!-- BACKLOG: confidence_threshold を踏まえた Abstention フォールバックの完全統合は未実装 -->
- docs/rag-pipeline.md:129:<!-- BACKLOG: 「STRICT モード」相当の独立したプロンプト切替や、ガードレール強度を段階的に変える厳格度ダイヤルは spec-raw で確認できなかったため、ここではシステムプロンプトの 2 種類切替を「厳格度モード」として扱う -->
- docs/rag-pipeline.md:158:<!-- BACKLOG: confidence_threshold は config に定義済みだが、実際の Abstention 除外ロジックは検索パイプラインに部分統合のみ。全段への統合状況は spec-raw に「パイプラインに部分統合」とだけあり、どの分岐で実際にハジくかまでは確認できなかった -->
- docs/spec-overview.md:124:<!-- BACKLOG: 構造化回答テンプレートの導入可否は未定 -->

### D. 環境 / プラットフォーム動作確認
- docs/handson-advanced.md:186:> **既知の制限**: MCP サーバーの実行は conda 環境前提です。<!-- BACKLOG: A-5 仕様に「MCP の conda 限定」の旨が known-limitations 候補として挙げられているが、原因の明示はなし -->
- docs/deployment.md:25:<!-- BACKLOG: Windows / Linux / Docker 環境での動作確認状況は spec-raw に記載がないため未確認 -->
- docs/deployment.md:26:<!-- BACKLOG: GPU 利用時の詳細（CUDA バージョン、メモリ目安）は spec-raw に記載がないため未確認 -->
- docs/known-limitations.md:81:<!-- BACKLOG: MCP が conda 限定である技術的な理由は spec-raw に明示されていないため未確認 -->

### E. その他（未分類）
- docs/api-reference.md:194:<!-- BACKLOG: 各エンドポイントの個別仕様（パス、メソッド、入出力スキーマ）の網羅はまだ整理途中 -->
- docs/guardrails.md:55:<!-- BACKLOG: Legal / Healthcare / Sales / Technical / Marketing の 5 カテゴリは旧 classifier.py に定義はあるが、現行のガードレールシードでは使われていない。GA 時点でこれらを有効化するのか・分類エンジンとの接続をどうするかは spec-raw に確認情報なし -->
- docs/faq.md:14:<!-- BACKLOG: 参照元ツールの具体的機能との対照表は spec-raw に根拠なし。書かない。 -->
- docs/faq.md:37:<!-- BACKLOG: extract_text の対応拡張子一覧は spec-raw に列挙がない。確認後追記。 -->
- docs/known-limitations.md:121:<!-- BACKLOG: spec-raw には IP マスキングの挙動と admin tier の関係について明示的な記述がなく、原因は調査中。詳細条件・回避策は未確認 -->
- docs/known-limitations.md:129:<!-- BACKLOG: GUI 上での横断検索 UI / API の有無は spec-raw に記載がないため未確認 -->
- docs/metadata-engine.md:208:<!-- BACKLOG: content_hash 比較ベースの差分同期は仕様未確定 -->
- docs/security-design.md:128:<!-- BACKLOG: docs/guardrails.md の存在は B-3 フェーズで生成予定 -->
- docs/security-design.md:226:<!-- BACKLOG: 間接プロンプトインジェクション専用検出の設計詳細は Phase 3 で確定 -->
- docs/spec-overview.md:118:<!-- BACKLOG: content_hash 比較の差分検出は仕様未確定 -->

---
最終更新: 2026-05-26 / Alpha GA 対応版
