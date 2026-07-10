<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Agent

AI agent configuration for reviewing, converting, and testing
[Linux Test Project](https://github.com/linux-test-project/ltp) patches.

Supported AI coding agents:

- [Claude Code](https://github.com/anthropics/claude-code)
- [pi](https://github.com/earendil-works/pi)
- [OpenCode](https://github.com/sst/opencode)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [GitHub Copilot CLI](https://github.com/github/copilot-cli)

## Setup

1. Clone this repository and install the skills for your agent:

   ```sh
   git clone <this-repo-url> ltp-agent
   ./ltp-agent/setup.sh <agent>
   ```

   `<agent>` is one of: `claude`, `pi`, `opencode`, `gemini`, `copilot`.
   The skills are copied into the agent's native skill directory.
   The LTP source tree is not touched.

2. Clone the LTP source tree:

   ```sh
   git clone --recurse-submodules https://github.com/linux-test-project/ltp.git
   ```

3. Start your AI coding agent from the LTP directory. The skills are
   discovered automatically from their installed location.

## Entry Point

The `ltp` skill is an automatic entry point. When you work inside an LTP
tree, it loads on its own and makes the agent aware that LTP-specific rules
apply to every code change, review, analysis, and commit message. It routes
the agent to the relevant rule files under `rules/` and to the specialized
skills (`ltp-review`, `ltp-analyze`, `ltp-convert`). You do not invoke it
directly; it activates whenever the working directory looks like an LTP tree.

## Usage

### Reviewing a Patch

With the patches applied into your development branch, invoke the review skill
inside your agent:

```
/ltp-review
```

This performs a deep code review against all LTP rules and writes the resulting
inline email reply to `review-inline.txt` at the LTP tree root.

### Analyzing a Test

To perform a deep, read-only analysis of an LTP test (quality, robustness,
and coverage):

```
/ltp-analyze <file path or test name>
```

The skill works on any LTP test (old API, new API, or shell). It produces a
report covering test intent, value, robustness, coverage gaps, API/style
compliance, and prioritized recommendations. No files are modified.

### Converting Old Tests to New API

To convert a test from the legacy `test.h` API to the modern `tst_test.h` API:

```
/ltp-convert
```

The agent will analyze the old test, show a conversion plan, rewrite it using
the new API.

> [!NOTE]
> Converted test is just a draft, most of the times the developer will need to
> update the test by hand.

To find candidates for conversion, scan the tree with:

```sh
python3 ltp-agent/tools/scan-old-api.py --root-dir <ltp directory>
```

## Rule Files

The `rules/` directory contains rule files that the agent loads on demand
based on the task:

| File                      | Description                                  |
| ------------------------- | -------------------------------------------- |
| `ground-rules.md`         | Mandatory rules for all LTP code.            |
| `c-tests.md`              | Rules for LTP C tests.                       |
| `shell-tests.md`          | Rules for LTP shell tests.                   |
| `openposix.md`            | Rules for Open POSIX Test Suite.             |
| `classify.md`             | Classify rules for LTP files.                |
| `dispatch.md`             | Maps classifications to rule files.          |
| `commit-message.md`       | Rules for LTP commit messages.               |
| `build-system.md`         | Rules for LTP Makefiles and build system.    |
| `documentation.md`        | Rules for LTP Sphinx docs and doc-comments.  |
| `false-positive-guide.md` | Verification checklist applied after review. |
| `email-template.md`       | Complete format of a review reply email.     |

## Continuous Integration

The `.github/workflows/ci-copilot-review.yml` workflow runs `/ltp-review`
automatically against LTP Patchwork series using GitHub Copilot CLI, posts
the verdict back to Patchwork as a check, and (if SMTP credentials are
configured) sends the inline review to the mailing list as a reply to the
original submission. It is triggered manually by series ID via
`workflow_dispatch`.

## Additional Resources

- [LTP documentation](https://linux-test-project.readthedocs.io/)
- [LTP source code](https://github.com/linux-test-project/ltp)
- [LTP mailing list](https://lore.kernel.org/ltp/)
- [Patchwork](https://patchwork.ozlabs.org/project/ltp/list/)
- [Kirk test runner](https://github.com/linux-test-project/kirk)

## License

This project is licensed under the GNU General Public License v2.0 or later.
See [COPYING](COPYING) for the full license text.
