<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Agent

AI agent configuration for reviewing, converting, and testing
[Linux Test Project](https://github.com/linux-test-project/ltp) patches.

This repository provides rule files and skills that teach AI coding agents how
to work with the LTP codebase. It is designed to be placed alongside an LTP git
checkout so that the agent can read source files, apply patches, build tests,
and run them.

## Prerequisites

- An AI coding agent that supports `AGENTS.md` and skill files (e.g.
  [Claude Code](https://claude.com/claude-code),
  [Gemini CLI](https://github.com/google-gemini/gemini-cli),
  [OpenCode](https://opencode.ai))
- An LTP git checkout
- Build dependencies for LTP: `git`, `gcc`, `make`, `autoconf`, `automake`,
  `m4`, `pkgconf`, Linux/libc headers
- Optional: `b4` (for fetching patches from lore/patchwork), `gh` (for GitHub
  PRs)

## Setup

1. Clone the LTP source tree:

   ```sh
   git clone --recurse-submodules https://github.com/linux-test-project/ltp.git
   cd ltp
   ```

2. Clone this repository and run the setup script:

   ```sh
   git clone <this-repo-url> ltp-agent
   ./ltp-agent/setup.sh
   ```

   This symlinks the agent configuration (`AGENTS.md`, `GEMINI.md`,
   `agents/`, `skills/`, `.claude/skills/`, `.agents/skills/`, `linter/`)
   into the LTP tree.

3. Build LTP once so that tests can be compiled:

   ```sh
   make autotools
   ./configure
   make
   ```

4. Start your AI coding agent from the LTP directory.

## Usage

### Applying a Patch

Before running any review or smoke test, apply the patch onto a review branch.
The helper script `ltp-agent/scripts/apply-patch.sh` supports multiple
sources:

```sh
# Patchwork URL
./ltp-agent/scripts/apply-patch.sh https://patchwork.ozlabs.org/project/ltp/patch/<id>/

# Lore URL
./ltp-agent/scripts/apply-patch.sh https://lore.kernel.org/ltp/<message-id>/

# GitHub PR
./ltp-agent/scripts/apply-patch.sh https://github.com/linux-test-project/ltp/pull/42

# Local .patch or .mbox file
./ltp-agent/scripts/apply-patch.sh /tmp/my-patch.mbox

# Existing branch
./ltp-agent/scripts/apply-patch.sh branch:feature-xyz

# Specific commit
./ltp-agent/scripts/apply-patch.sh commit:abc1234
```

### Cleaning Up Review Branches

To delete all `review/*` branches created by `apply-patch.sh`:

```sh
# Interactive — lists branches and asks for confirmation
./ltp-agent/scripts/review-cleanup.sh

# Force — no confirmation prompt
./ltp-agent/scripts/review-cleanup.sh -f
```

### Reviewing a Patch

With the patch applied, invoke the review skill inside your agent:

```
/ltp-review
```

This performs a deep code review against all LTP rules (ground rules, C test
rules, shell test rules, or Open POSIX rules depending on the files changed),
runs the mechanical linter (see [Linter](#linter)) to catch low-level
violations, and writes the resulting inline email reply to `review-inline.txt`
at the LTP tree root.

### Running a Review End-to-End

For a one-shot review without manually cloning, applying, and invoking the
agent, use `scripts/start-review.sh`. It clones LTP into a temporary
directory, links the agent config, applies a patch from any source supported
by `apply-patch.sh`, runs `/ltp-review`, and prints the email reply on
stdout.

```sh
# Auto-detect the agent (gemini, claude, or opencode)
./ltp-agent/scripts/start-review.sh https://patchwork.ozlabs.org/project/ltp/patch/<id>/

# Pick the agent explicitly and clean up afterwards
./ltp-agent/scripts/start-review.sh -a claude -c https://lore.kernel.org/r/<msgid>/

# Verbose, keep the clone in a known path
./ltp-agent/scripts/start-review.sh -v -d ~/reviews/my-patch /tmp/my-patch.mbox
```

See `start-review.sh -h` for the full option list.

### Converting Old Tests to New API

To convert a test from the legacy `test.h` API to the modern `tst_test.h` API:

```
/ltp-convert
```

The agent will analyze the old test, show a conversion plan, rewrite it using
the new API, build and run the converted test, then self-review the result.

To find candidates for conversion, scan the tree with:

```sh
# From the LTP tree root; prints JSON with old-API files grouped by directory
python3 ltp-agent/scripts/scan-old-api.py

# Limit to a subtree and write to a file
python3 ltp-agent/scripts/scan-old-api.py \
    --root-dir testcases/kernel/syscalls -o old-api.json
```

### Asking General Questions

You can ask the agent about LTP architecture, APIs, or conventions directly.
The instructions in `AGENTS.md` guide it to load the appropriate rule files and
use project documentation to answer.

## Rule Files

The `agents/` directory contains rule files that the agent loads on demand
based on the task:

- **ground-rules.md** — Mandatory rules for all LTP code: no kernel bug
  workarounds, no sleep-based synchronization, runtime feature detection,
  minimal root usage, cleanup on all paths, portable code, one change per
  patch, staging prefix for unreleased features.

- **c-tests.md** — Rules for LTP C tests: required structure, API usage
  (`SAFE_*` macros, `TST_EXP_*` result macros), file organization, resource
  management, test parametrization, architecture guards, compile-time feature
  guards, child process handling.

- **shell-tests.md** — Rules for LTP shell tests: required block order,
  POSIX shell portability, env block JSON format.

- **openposix.md** — Rules for the Open POSIX Test Suite: different structure
  from LTP tests (`main()`, `posixtest.h`, `PTS_*` return codes), separate
  build system.

- **commit-message.md** — Rules for LTP commit messages: required subject
  prefix, wording, trailers, and patch-description style. Loaded by the
  review skill during Phase 2.

- **false-positive.md** — Verification checklist run on every flagged issue
  before it is reported, to weed out spurious findings.

- **email-template.md** — Complete format of a review reply email: greeting,
  quoting style, per-issue layout, verdict wording, postamble, and the
  pre-existing-issues block. Loaded by the review skill during Phase 4.

## Linter

The `linter/` directory contains a Python-based mechanical rule checker
(`ltp-linter`) that the `/ltp-review` skill invokes before doing semantic
analysis. It catches low-level violations (missing SPDX headers, legacy APIs,
shell bash-isms, etc.) so the LLM can focus on logic and correctness.

It can also be used standalone from the LTP tree:

```sh
# Lint a single file
./linter/ltp-linter -f testcases/kernel/syscalls/foo/foo01.c

# Lint all files changed on the current branch vs master
./linter/ltp-linter -b
```

See `linter/README.md` for the full rule list.

## Continuous Integration

The `.github/workflows/ci-copilot-review.yml` workflow runs `/ltp-review`
automatically against LTP Patchwork series using GitHub Copilot CLI, posts
the verdict back to Patchwork as a check, and (if SMTP credentials are
configured) sends the inline review to the mailing list as a reply to the
original submission. It is triggered manually by series ID via
`workflow_dispatch`.

## Additional Resources

- LTP documentation: https://linux-test-project.readthedocs.io/
- LTP source code: https://github.com/linux-test-project/ltp
- LTP mailing list: https://lore.kernel.org/ltp/
- Patchwork: https://patchwork.ozlabs.org/project/ltp/list/
- Kirk test runner: https://github.com/linux-test-project/kirk

## License

This project is licensed under the GNU General Public License v2.0 or later.
See [COPYING](COPYING) for the full license text.
