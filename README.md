# Cynovela
A small-scale model of an enterprise AI data pipeline: ingest documents, mask
personal information, publish them, and get answers with citations, with what
each role can see kept separate.
Cynovela is a tool for personal use, small internal demos, and learning.
It is not a commercial offering and is not intended for production use.
The name is a coined word, from *cynosure* (a guiding star) and *Vela* (the
constellation of the Sail).
## Requirements
- macOS on Apple silicon.
- **falcon** (runs in a container): Podman is the supported path.
- **chewie** (runs directly on macOS): conda is the supported path; if conda is
  not present, venv can be used instead.
- Docker and other environments can be selected, but we have not verified them.
  You will need to adjust the setup yourself.
- An internet connection is needed the first time if you use a package that does
  not bundle the models.
## Distributions
Four forms are built. They are distributed as release assets:
| Form | Runs as | Models bundled |
|---|---|---|
| falcon, all-in-one | container | yes |
| falcon, lightweight | container | no |
| chewie, all-in-one | directly on macOS | yes |
| chewie, lightweight | directly on macOS | no |
The all-in-one packages are large and are split into parts. Each release ships a
`HOW-TO-ASSEMBLE.md` and a `SHA256SUMS` next to the parts; follow those to put a
package back together and verify it. If no release is listed yet, the packages
are not published at this point.
Pick lightweight if you already have the embedding model locally or are happy to
fetch it on first start. Pick all-in-one if you want a single self-contained
download.
## Running it
1. Download and assemble the package you picked.
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
  material through it and treat its output as authoritative.
- Behaviour with Docker or with container engines other than Podman has not been
  verified here.
## License
MIT. See `LICENSE`.
---
Japanese version: [README.ja.md](README.ja.md)
- https://note.com/tocchidegozaru
- https://huggingface.co/tocchitocchi
