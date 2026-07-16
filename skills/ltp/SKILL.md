---
name: ltp
description: Load anytime the working directory is a Linux Test Project (LTP)
  tree, and always load it when you answer questions or edit code inside an
  LTP tree. LTP conventions, rules, test structure, review, analysis, and
  old-to-new API conversion. Read this anytime you operate on LTP code.
invocation_policy: automatic
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Entry Point

This skill is the framework that makes you aware of the LTP - Linux Test
Project conventions and rules. When you work inside an LTP tree, LTP-specific
rules apply and MUST be satisfied. This skill exists to route you to those
rules and to the specialized LTP skills.

## Are you in an LTP tree?

You are in an LTP tree when the working directory contains typical LTP
markers, such as:

- a `testcases/` directory with subtrees like `kernel/syscalls/`, `cve/`,
  `open_posix_testsuite/`.
- a `runtest/` directory.
- a `metadata/` directory.
- a `VERSION` file.
- a `configure.ac` file.

If these markers are present, treat every code change, review, analysis, and
commit message as subject to the LTP rules below.

## Configuration

The ltp-agent directory is configured during installation:

- **LTP_AGENT_DIR**: {{LTP_AGENT_DIR}}

The rule files referenced below live under `{{LTP_AGENT_DIR}}/rules/`.

## Rules that always apply

When you actively edit or write LTP code, these are MANDATORY:

1. Read `{{LTP_AGENT_DIR}}/rules/ground-rules.md`. These are the
   non-negotiable rules for all LTP code.
2. Read `{{LTP_AGENT_DIR}}/rules/classify.md` to determine what kind of file
   you are touching (C test, shell test, Open POSIX, build file, doc, etc.).
3. Read `{{LTP_AGENT_DIR}}/rules/dispatch.md` and load ONLY the rule files
   matching each file's classification.

Do NOT diverge from any rule loaded through this dispatch.

## Rule files

Load these on demand, according to the task and the file classification:

| File                      | When to load                                |
| ------------------------- | ------------------------------------------- |
| `ground-rules.md`         | Always, for any LTP code change.            |
| `classify.md`             | To classify a file before applying rules.   |
| `dispatch.md`             | To map a classification to its rule files.  |
| `c-tests.md`              | Editing or reviewing an LTP C test.         |
| `shell-tests.md`          | Editing or reviewing an LTP shell test.     |
| `openposix.md`            | Editing or reviewing an Open POSIX test.    |
| `build-system.md`         | Touching Makefiles or the build system.     |
| `git.md`                  | Touching git config files.                  |
| `documentation.md`        | Writing docs or kernel-doc test comments.   |
| `commit-message.md`       | Writing or reviewing an LTP commit message. |
| `false-positive-guide.md` | Verifying findings before reporting them.   |
| `email-template.md`       | Composing a review reply email.             |

## Capabilities

### Patch Review

When asked to review an LTP patch, commit, or series, use the `ltp-review`
skill and follow its protocol. It loads the rule files above and writes the
inline email reply to `review-inline.txt` at the LTP tree root.

Invoke with `/ltp-review`.

### Test Analysis

When asked to evaluate the quality, robustness, or coverage of an LTP test,
use the `ltp-analyze` skill. It is read-only: it reports findings and
recommendations without modifying files.

Invoke with `/ltp-analyze <file path or test name>`.

### Old-to-New API Conversion

When asked to convert an LTP test from the old API (`test.h`) to the new API
(`tst_test.h`), use the `ltp-convert` skill. This is a semantic rewrite, not a
token-by-token translation, and the result is a draft to be refined by hand.

Invoke with `/ltp-convert <file path or test name>`.

## Output conventions

- Patch reviews produce `review-inline.txt` at the LTP tree root.
- Analysis and conversion follow the output rules of their respective skills.
- Never write ltp-agent outputs into unrelated parts of the LTP source tree.
