# ドキュメント整備 バックログ一覧

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
