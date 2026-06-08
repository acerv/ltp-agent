# LTP Linter

A Python linter for LTP (Linux Test Project) test files. It checks mechanical rules
before the LLM review, so the LLM can focus on semantic analysis.

## Usage

```bash
# Lint a single file
./ltp-linter -f testcases/kernel/syscalls/foo/foo01.c

# Lint all C files changed on current branch vs master
./ltp-linter -b

# Lint only findings on changed patch lines and emit JSON
./ltp-linter -b --scope patch --format json
```

## Output formats

The default text output is intended for humans:

```text
[abc123def012] file.c:42: LTP-C009: Wrong FD validity check: use fd != -1 instead of fd >= 0
```

When linting a single file (`-f`), the commit prefix is omitted:

```text
file.c:42: LTP-C009: Wrong FD validity check: use fd != -1 instead of fd >= 0
```

Use `--format json` when another tool or an LLM consumes the output:

```json
{
  "version": 1,
  "scope": "patch",
  "findings": [
    {
      "file": "file.c",
      "line": 42,
      "rule_id": "LTP-C-...",
      "confidence": "mechanical",
      "source": "linter",
      "message": "Wrong FD validity check",
      "detail": "use fd != -1 instead of fd >= 0",
      "commit": "abc123def012"
    }
  ]
}
```

The `commit` field contains the short (12-char) hash of the commit that
introduced the flagged line. It is populated only in branch mode (`-b`);
when linting a single file with `-f`, it is `null`.

`--scope file` lints whole files. `--scope patch` is available with `-b`
and reports only findings whose line is changed by the current branch diff.
This avoids reporting pre-existing failures during patch review.

## Confidence classes

Each finding has a `confidence` field:

- `mechanical`: exact syntax or presence check. Review agents should trust it.
- `semantic`: context-sensitive rule. Review agents should verify it before reporting.
- `experimental`: unstable rule. Review agents should never report it directly.

Most rules are mechanical. The current semantic rules are:

- `LTP-C011`: `HAVE_*` guard inside function.
- `LTP-C012`: missing `.needs_tmpdir`.
- `LTP-C015`: missing `.supported_archs`.
- `LTP-C018`: missing `.needs_kconfigs`.

## Rules

### C tests (.c and .h)

Rules with scope `c` apply to both `.c` and `.h` files. Rules with
scope `c_only` apply to `.c` files only.

| ID       | Conf.      | Scope  | Rule                           |
| -------- | ---------- | ------ | ------------------------------ |
| LTP-C001 | mechanical | c      | Missing SPDX header            |
| LTP-C002 | mechanical | c      | Missing copyright              |
| LTP-C003 | mechanical | c_only | Missing doc comment block      |
| LTP-C004 | mechanical | c      | Deprecated [Description] tag   |
| LTP-C005 | mechanical | c      | Wrong test header              |
| LTP-C006 | mechanical | c_only | Unexpected main()              |
| LTP-C007 | mechanical | c_only | Missing struct tst_test        |
| LTP-C008 | mechanical | c      | FD not initialized to -1       |
| LTP-C009 | mechanical | c      | Wrong FD validity check        |
| LTP-C010 | mechanical | c      | Redundant fd reset             |
| LTP-C011 | semantic   | c      | HAVE\_\* inside function       |
| LTP-C012 | semantic   | c_only | Missing .needs_tmpdir          |
| LTP-C013 | mechanical | c      | Legacy cleanup_fn              |
| LTP-C014 | mechanical | c      | Raw syscall()                  |
| LTP-C015 | semantic   | c_only | Missing .supported_archs       |
| LTP-C016 | mechanical | c      | Use exit() instead of \_exit() |
| LTP-C017 | mechanical | c      | Leading-underscore identifier  |
| LTP-C018 | semantic   | c_only | Missing .needs_kconfigs        |

### Shell tests (.sh)

All shell rules only apply to LTP test scripts that source the
framework (`. tst_run.sh` or `. tst_test.sh`). Standalone scripts
are skipped.

| ID       | Conf.      | Rule                       |
| -------- | ---------- | -------------------------- |
| LTP-S001 | mechanical | Wrong shebang              |
| LTP-S002 | mechanical | Missing SPDX header        |
| LTP-S003 | mechanical | Missing copyright          |
| LTP-S004 | mechanical | Missing doc block          |
| LTP-S005 | mechanical | Missing env block          |
| LTP-S006 | mechanical | Missing tst_run last       |
| LTP-S007 | mechanical | Bash-ism: [[]]             |
| LTP-S008 | mechanical | Bash-ism: function keyword |
| LTP-S009 | mechanical | Bash-ism: process subst    |
| LTP-S010 | mechanical | Bash-ism: array            |

### Open POSIX tests (.c and .h under open_posix_testsuite/)

Rules with scope `openposix` apply to both `.c` and `.h` files.
Rules with scope `openposix_only` apply to `.c` files only and
skip build-only definition tests (files without `test_main()` or
`main()`).

| ID       | Conf.      | Scope          | Rule                       |
| -------- | ---------- | -------------- | -------------------------- |
| LTP-O001 | mechanical | openposix      | Missing GPL license header |
| LTP-O002 | mechanical | openposix      | Missing copyright          |
| LTP-O003 | mechanical | openposix_only | Missing posixtest.h        |
| LTP-O004 | mechanical | openposix_only | Must use test_main()       |
| LTP-O005 | mechanical | openposix_only | Missing PTS return codes   |

## Running tests

```bash
cd tools/linter
python3 -m pytest tests/ -v
```
