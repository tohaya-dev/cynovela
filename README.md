**日本語版はこちら → [README.ja.md](README.ja.md)**

# Cynovela

A small-scale model of an enterprise AI data pipeline: ingest files, mask
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

| Directory | What it is | Distribution package |
|---|---|---|
| `chewie` | Runs directly on macOS. | Published on GitHub Releases (v1.1.0). |
| `falcon` | Runs inside a container (Podman). | Built from the source in this repository. No distribution package is provided. |
| `falcon-docker-beta` | Runs inside a container (Docker; in-development beta, no bundled models). | Built from the source in this repository. No distribution package is provided. |

You only need one of them. They are three ways of running the same thing.

## Requirements

- macOS on Apple silicon.
- `chewie`, Package edition: **neither Python nor conda is needed.** The folder
  carries its own Python inside it, and nothing is installed on this Mac.
- `chewie`, Source editions: Python 3.12 or later. `launch.sh` builds the
  environment for you — it offers a dedicated `conda` environment, and where
  `conda` is not present it builds the environment inside the distribution
  folder instead.
- `falcon`: Podman.
- Docker and other container engines can be selected, but we have not verified
  them here. You will need to adjust the setup yourself.
- An internet connection is needed on first start for the source editions,
  because they build their environment at that point.
- 8 GB of RAM or more, and an LM Studio or OpenAI-compatible API for the
  answering model.

## Downloads

Everything is on GitHub Releases (v1.1.0):
https://github.com/tohaya-dev/cynovela/releases

The one-page answer to "which of these do I take" is in
[chewie/docs/editions.md](chewie/docs/editions.md).

| Edition | Runs as | Models bundled | Download shape | What it needs |
|---|---|---|---|---|
| **Package edition** `cynovela-chewie-package-1.1.0.tar.gz` | directly on macOS | no — take the AI models as well | single file | **Neither Python nor conda.** Nothing is installed on this Mac |
| **Source edition, all-in-one** `cynovela-chewie-all-in-one-1.1.0.tar.gz.part00`–`part02` | directly on macOS | yes | split into parts — needs assembling | Python 3.12 or later |
| **Source edition, lightweight** `cynovela-chewie-lightweight-1.1.0.tar.gz` | directly on macOS | no — take the AI models as well | single file | Python 3.12 or later |
| **AI models** `cynovela-chewie-models-1.1.0.tar.gz.part00`–`part02` | — | — | split into parts — needs assembling | Despite the name, these are the AI models themselves, not conda packages |

Take the **Package edition** if you want the fewest requirements: extract it,
add the AI models, and run `./launch.sh`.

Take **all-in-one** if you want the models in the same download and nothing
fetched afterwards. Take **lightweight** if you want a small download and are
happy to build the environment on first start.

The release also carries `SHA256SUMS` and `HOW-TO-ASSEMBLE.md`. Download
`SHA256SUMS` whichever edition you pick. The all-in-one and the AI models are
too large for a single file, so they are split; join the parts as
[HOW-TO-ASSEMBLE.md](HOW-TO-ASSEMBLE.md) describes and check the result against
`SHA256SUMS` before starting.

`falcon` and `falcon-docker-beta` are built from the source in this repository.
Distribution packages for them are not provided.

## First time here

For `chewie` there is one entrance:
**[chewie/START-HERE.md](chewie/START-HERE.md)**. Open that first; it carries
the map of every other document.

| Document | What it covers |
|---|---|
| [chewie/START-HERE.md](chewie/START-HERE.md) | The entrance. First start, restart, reinstall, uninstall, and where everything else is |
| [chewie/docs/editions.md](chewie/docs/editions.md) | Which of the four downloads to take, on one page |
| [chewie/docs/first-run.md](chewie/docs/first-run.md) | Never opened a terminal? From the downloaded file to the first answer, nothing skipped |
| [chewie/docs/restart.md](chewie/docs/restart.md) | Stopping it, and starting it again |
| [chewie/docs/cli-reference.md](chewie/docs/cli-reference.md) | Every terminal command and every argument |
| [chewie/docs/mcp-reference.md](chewie/docs/mcp-reference.md) | Every MCP tool: what you hand each one, what comes back |
| [chewie/docs/api-reference.md](chewie/docs/api-reference.md) | Every HTTP endpoint, read out of the code |
| [chewie/docs/quickstart.md](chewie/docs/quickstart.md) | The short version for people in a hurry |

For `falcon`, start from [falcon/docs/HAJIMETE.md](falcon/docs/HAJIMETE.md),
then [falcon/docs/STARTUP.md](falcon/docs/STARTUP.md). For
`falcon-docker-beta`, start from
[falcon-docker-beta/docs/HAJIMETE.md](falcon-docker-beta/docs/HAJIMETE.md),
then [falcon-docker-beta/docs/STARTUP.md](falcon-docker-beta/docs/STARTUP.md).

Every guide is bilingual: English first, Japanese after. Whichever form you
pick, the administrator account is asked to change its password on first
sign-in.

## What it does not do

- **Masking has limits.** It applies pattern-based replacement before text
  leaves the machine, and it does not catch everything. Known gaps include names
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
