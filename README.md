**日本語版はこちら → [README.ja.md](README.ja.md)**
> Cynovela（シノヴェラ）は、資料を取り込み、個人情報を伏せてから答えを返す仕組みを、
> 手元の Mac だけで動かしてみるための道具です。日本語の文書を想定して作っています。
> 売り物ではなく、学びと試しのためのものです。

本命は Podman で動くコンテナ版（falcon）です。`falcon-docker-beta` は Docker 対応の開発中のベータです（`falcon` とはファイルを共有しない、独立したフォルダです）。 / The Podman-based falcon is the primary form; `falcon-docker-beta` is a separate, in-development beta for Docker that shares no files with `falcon`.
---
# Cynovela
A small-scale model of an enterprise AI data pipeline: ingest documents, mask
personal information, publish them, and get answers with citations, with what
each role can see kept separate.
Cynovela is a tool for personal use, small internal demos, and learning.
It is not a commercial offering and is not intended for production use.
It is built with Japanese documents in mind, and its masking rules are written
for Japanese text.
The name is a coined word, from *cynosure* (a guiding star) and *Vela* (the
constellation of the Sail).
<!-- screenshot: place one image here once it has been captured and checked -->
## The three forms in this repository
| Directory | What it is |
|---|---|
| `falcon` | Runs inside a container (Podman). |
| `chewie` | Runs directly on macOS. |
| `falcon-docker-beta` | Runs inside a container (Docker; in-development beta, no bundled models). |
You only need one of them. They are three ways of running the same thing.
## Requirements
- macOS on Apple silicon.
- `falcon`: Podman is the supported path.
- `chewie`: conda is the supported path; if conda is not present, venv can be
  used instead. Python 3.10 or newer is required.
- Docker and other container engines can be selected, but we have not verified
  them here. You will need to adjust the setup yourself.
- An internet connection is needed on first start if you pick a package that
  does not bundle the models.
## Downloads
| Package | Runs as | Models bundled | Download shape |
|---|---|---|---|
| falcon, all-in-one | container | yes | **split into parts — needs assembling** |
| falcon, lightweight | container | no | single file |
| chewie, all-in-one | directly on macOS | yes | **split into parts — needs assembling** |
| chewie, lightweight | directly on macOS | no | single file |
| falcon, docker-beta | container (Docker, in development) | no | single file |
Pick **lightweight** if you already have the embedding model locally, or if you
are happy to fetch it on first start.
Pick **all-in-one** if you want everything in the download and no fetching.
The all-in-one packages are too large for a single file, so they are split.
Each release ships a `HOW-TO-ASSEMBLE.md` and a `SHA256SUMS` next to the parts.
Download every part, follow that file to join them, and check the result against
`SHA256SUMS` before starting. If no release is listed yet, the packages are not
published at this point.
The docker-beta package is a single file named
`cynovela-falcon-docker-beta-1.0.0-docker-beta.tar.gz`.
## Running it
1. Download and, for an all-in-one package, assemble it.
2. Start it with the launcher included in the package.
3. Open the address the launcher prints, and sign in with the account described
   in `STARTUP.md`. The administrator account is asked to change its password on
   first sign-in.
Detailed guides inside the packages are written in Japanese.
## What it does not do
- **Masking is not complete.** It applies pattern-based replacement before text
  leaves the machine, but it does not catch everything. Known gaps include names
  written in kana readings, the block-and-number part of addresses, and some
  landline area codes.
- It is a tool for learning and experimentation. Do not put real confidential
  material through it, and do not treat its output as authoritative.
- Behaviour with Docker, or with container engines other than Podman, has not
  been verified here.
## License
MIT. See `LICENSE`.
---
- https://note.com/tocchidegozaru
- https://huggingface.co/tocchitocchi
