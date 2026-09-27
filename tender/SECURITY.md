# Security Policy / セキュリティについて

**This file is bilingual: each point is given in English first, then in Japanese.**
**この文書は日英併記です。各項目を英語・日本語の順で書いています。**

Please do not open a public issue for security problems.
Use GitHub's private vulnerability reporting (Security > Report a vulnerability)
on this repository, with steps to reproduce and the version you used.

セキュリティに関わる問題は、公開の Issue に書かず、このリポジトリの
非公開の報告窓口（Security > Report a vulnerability）からお知らせください。
再現の手順と、お使いの版を添えてください。

Notes / 前提:

- This software is designed to run locally. Exposing it to a network is the
  operator's decision. / 手元の機械で動かす前提です。外へ開くかどうかは運用の判断です。
- The first passwords of the two initial users (administrator `cynovela`,
  viewer `demo`) are published in `README.md` / `README.ja.md`, section 4. The
  package's `cynovela.yaml` holds only their hashes. Both users must change the
  password on first sign-in; other operations are refused until then.
  / 最初の2人（管理者 `cynovela`・閲覧者 `demo`）の最初のパスワードは
  `README.md` / `README.ja.md` の 4 節に載せています。配布物の `cynovela.yaml` には
  ハッシュだけが入っています。どちらも最初のログインで必ず変更し、変えるまでほかの操作はできません。
- When an external endpoint is configured, redaction is applied before sending,
  but choosing a trustworthy endpoint is the operator's responsibility.
  / 外部の宛先を設定した場合、送る前にマスキングを掛けますが、宛先を選ぶ責任は運用の側にあります。
