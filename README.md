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
| `chewie` | Runs directly on macOS. | Published on GitHub Releases (v1.2.0). |
| `falcon` | Runs inside a container (Podman). | Built from the source in this repository. No distribution package is provided. |
| `falcon-docker-beta` | Runs inside a container (Docker; in-development beta, no bundled models). | Built from the source in this repository. No distribution package is provided. |

You only need one of them. They are three ways of running the same thing.

## Requirements

- macOS on Apple silicon.
- `chewie`, App edition (`.pkg`): **in preparation.** It is not part of this
  release.
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

Everything is on GitHub Releases (v1.2.0):
https://github.com/tohaya-dev/cynovela/releases

The one-page answer to "which of these do I take" is in
[chewie/docs/editions.md](chewie/docs/editions.md).

| Edition | Runs as | Models bundled | Download shape | What it needs |
|---|---|---|---|---|
| **App edition** (`.pkg`) | — | — | **In preparation.** Not part of this release | — |
| **Package edition** `cynovela-chewie-package-1.2.0.tar.gz` | a folder you run in place | no — take the AI models as well | single file | **Neither Python nor conda.** Nothing is installed on this Mac |
| **Source edition** | a folder you run in place | no — take the AI models as well | not a download — the source is this repository (clone it, or use GitHub's "Download ZIP") | Python 3.12 or later, or conda |
| **AI models** `cynovela-chewie-models-1.2.0.tar.gz.part00`–`part02` | — | — | split into parts — needs assembling | Despite the name, these are the AI models themselves, not conda packages |

The **App edition** (`.pkg`) is **in preparation** and is not part of this
release.

Take the **Package edition** if you would rather not install anything: extract it,
add the AI models, and run `./launch.sh`. It writes inside its own folder, and the
extracted folder can be moved to another location later — start it again from the
new place with the same `./launch.sh`.

Take the **source edition** if you want to see and control what is installed:
the source is this repository — take the `chewie/` tree, add the AI models, and
run `./launch.sh`; on the first start it builds the environment for you. No
source archive is distributed on the releases page.

The release also carries `HOW-TO-ASSEMBLE.md`, the checksum list `SHA256SUMS`
for the package edition and the AI models, and `check-managed-mac.command`, a
diagnostic that tells you — without changing any setting — whether a
managed Mac (under MDM) will let you run this. A single release file cannot exceed
2 GiB, so the AI models are split into parts; join them as
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
| [chewie/docs/editions.md](chewie/docs/editions.md) | Which edition to take, on one page |
| [chewie/docs/getting-started.md](chewie/docs/getting-started.md) | Never opened a terminal? From the downloaded file to the first answer, nothing skipped |
| [chewie/docs/operations.md](chewie/docs/operations.md) | Keeping it running: stopping and starting, connecting an LLM, backup and restore, users, logs |
| [chewie/docs/reference/cli.md](chewie/docs/reference/cli.md) | Every terminal command and every argument |
| [chewie/docs/reference/mcp.md](chewie/docs/reference/mcp.md) | Every MCP tool: what you hand each one, what comes back |
| [chewie/docs/reference/api.md](chewie/docs/reference/api.md) | Every HTTP endpoint, read out of the code |
| [chewie/docs/handson.md](chewie/docs/handson.md) | Exercises against the bundled sample material, once it is running |

For `falcon`, start from [falcon/docs/HAJIMETE.md](falcon/docs/HAJIMETE.md),
then [falcon/docs/STARTUP.md](falcon/docs/STARTUP.md). For
`falcon-docker-beta`, start from
[falcon-docker-beta/docs/HAJIMETE.md](falcon-docker-beta/docs/HAJIMETE.md),
then [falcon-docker-beta/docs/STARTUP.md](falcon-docker-beta/docs/STARTUP.md).

Every guide is bilingual: English first, Japanese after.

**The first password.** The administrator user name is `cynovela` and the viewer
account is `demo`. Their first passwords are **written inside the download
itself, in `cynovela.yaml`** — read the value of `auth.admin_initial_password`
(and `auth.viewer_initial_password` for the viewer). Nothing is sent to you
separately, and no password is written in any of these documents.

- **Package edition and source editions:** `cynovela.yaml` is in the folder you
  unpacked, next to `launch.sh`.

The start-up screen also prints it once, at the first start. Neither database
ships inside the package, so both routes — the demo start (`./launch.sh --demo`)
and the ordinary start — count as a first start. Whichever
form you pick, the administrator account is asked to change its password on
first sign-in.

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
