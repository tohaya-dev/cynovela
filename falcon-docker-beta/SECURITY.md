# Security Policy / セキュリティについて

Please do not open a public issue for security problems.
Use GitHub's private vulnerability reporting (Security > Report a vulnerability)
on this repository, with steps to reproduce and the version you used.

セキュリティに関わる問題は、公開の Issue に書かず、このリポジトリの
非公開の報告窓口（Security > Report a vulnerability）からお知らせください。
再現の手順と、お使いの版を添えてください。

Notes / 前提:

- This software is designed to run locally. Exposing it to a network is the
  operator's decision. / 手元の機械で動かす前提です。外へ開くかどうかは運用の判断です。
- The bundled initial credentials are placeholders and must be changed on
  first login. / 同梱の初期の資格情報は仮のもので、初回に必ず変更します。
- When an external endpoint is configured, redaction is applied before sending,
  but choosing a trustworthy endpoint is the operator's responsibility.
  / 外部の宛先を設定した場合、送る前にマスキングを掛けますが、宛先を選ぶ責任は運用の側にあります。
