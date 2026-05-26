# LTP Linter

A Python linter for LTP (Linux Test Project) test files. It checks mechanical rules
before the LLM review, so the LLM can focus on semantic analysis.

## Usage

```bash
# Lint a single file
./ltp-linter -f testcases/kernel/syscalls/foo/foo01.c

# Lint all C files changed on current branch vs master
./ltp-linter -b
```

## Rules

### C tests (.c and .h)

Rules with scope `c` apply to both `.c` and `.h` files. Rules with
scope `c_only` apply to `.c` files only.

| Rule                         | Scope  | Description                                                  |
| ---------------------------- | ------ | ------------------------------------------------------------ |
| Missing SPDX header          | c      | First line must contain `SPDX-License-Identifier`            |
| Missing copyright            | c      | A `Copyright` line with year must be present                 |
| Missing doc comment block    | c_only | A `/*\` doc comment block must be present                    |
| Deprecated [Description] tag | c      | `[Description]` in doc comments is deprecated                |
| Wrong test header            | c      | Use `tst_test.h` instead of legacy `test.h`                  |
| Unexpected main()            | c_only | Use `struct tst_test` instead of `main()`                    |
| Missing struct tst_test      | c_only | `struct tst_test` must be defined                            |
| FD not initialized to -1     | c      | Static fd vars must be initialized to `-1`                   |
| Wrong FD validity check      | c      | Use `fd != -1` instead of `fd >= 0` or `fd > 0`              |
| Redundant fd reset           | c      | `SAFE_CLOSE()` already resets the fd to `-1`                 |
| HAVE\_\* inside function     | c      | `#ifdef HAVE_*` must wrap code at file level                 |
| Missing .needs_tmpdir        | c_only | Tests creating files with `O_CREAT` need `.needs_tmpdir = 1` |
| Legacy cleanup_fn            | c      | `safe_*` must not use `cleanup_fn` (legacy API)              |
| Raw syscall()                | c      | Use `tst_syscall()` which handles `ENOSYS`                   |
| Missing .supported_archs     | c_only | Use `.supported_archs` instead of `#if defined()`            |
| Missing .needs_kconfigs      | c_only | Use `.needs_kconfigs` instead of manual config checks        |

### Shell tests (.sh)

All shell rules only apply to LTP test scripts that source the
framework (`. tst_run.sh` or `. tst_test.sh`). Standalone scripts
are skipped.

| Rule                    | Description                                                   |
| ----------------------- | ------------------------------------------------------------- |
| Wrong shebang           | Shebang must be exactly `#!/bin/sh`                           |
| Missing SPDX header     | Second line must contain `SPDX-License-Identifier`            |
| Missing copyright       | A `Copyright` line with year must be present                  |
| Missing doc block       | New API tests must have a `# --- doc ... # ---` block         |
| Missing env block       | New API tests must have a `# --- env ... # ---` block         |
| Missing tst_run last    | Last line must be `. tst_run.sh` or `tst_run`                 |
| Bash-ism: [[]]          | Use `[ ]` instead of `[[ ]]` (POSIX portability)              |
| Bash-ism: function      | Use `name() {` instead of `function name` (POSIX portability) |
| Bash-ism: process subst | Do not use `<()` or `>()` (POSIX portability)                 |
| Bash-ism: array         | Do not use bash arrays (POSIX portability)                    |

### Open POSIX tests (.c and .h under open_posix_testsuite/)

Rules with scope `openposix` apply to both `.c` and `.h` files.
Rules with scope `openposix_only` apply to `.c` files only and
skip build-only definition tests (files without `test_main()` or
`main()`).

| Rule                       | Scope          | Description                                           |
| -------------------------- | -------------- | ----------------------------------------------------- |
| Missing GPL license header | openposix      | GPL header must be present (GPL license text or SPDX) |
| Missing copyright          | openposix      | A `Copyright` line with year must be present          |
| Missing posixtest.h        | openposix_only | Must include `posixtest.h` (or `testfrmw.h`)          |
| Must use test_main()       | openposix_only | Define `test_main()` instead of `main()`              |
| Missing PTS return codes   | openposix_only | Must use `PTS_PASS`, `PTS_FAIL`, etc.                 |

## Running tests

```bash
cd linter
python3 -m pytest tests/ -v
```
