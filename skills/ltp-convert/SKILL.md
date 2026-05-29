---
name: ltp-convert
description: LTP Old-to-New API Converter
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Test Conversion Protocol

You are an agent that converts LTP tests from the old API (`test.h`) to the
new API (`tst_test.h`).

## Invocation

`/ltp-convert <file path or test name>` — convert one file.

---

## Step 1: Load Rules

Read `agents/ground-rules.md` and `agents/c-tests.md` before doing
anything else. `c-tests.md` is the authoritative reference for what the
converted code MUST look like.

## Step 2: Verify Old API

Verify the file includes `test.h` (old API). If it already includes
`tst_test.h`, stop and tell the user.

If the file is under `testcases/open_posix_testsuite/`, stop and tell the
user that `/ltp-convert` does not apply to Open POSIX tests. They use a
different API and must follow `agents/openposix.md` instead of `c-tests.md`.

## Step 3: Detect Test vs Helper

Check whether the file's basename (without `.c`) appears in any
`runtest/` file.

- Found → **test**. Full conversion: remove `main()`, add `struct tst_test`
  (see Test Conversion below).
- Not found → inspect the file path and contents before deciding:
  - If the file is under a test directory (for example
    `testcases/kernel/syscalls/`) or otherwise looks like a standalone test,
    treat the missing `runtest/` entry as a bug to flag, not as proof that the
    file is a helper.
  - If the file is a spawned support binary, it is a **helper**. Keep
    `main()`, add `TST_NO_DEFAULT_MAIN` (see Helper Conversion below).

## Step 4: Convert

Apply the relevant API mapping tables, the rules from `c-tests.md` and
`ground-rules.md`.

### Common Old → New API Mapping

| Old                                     | New                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------ |
| `#include "test.h"`                     | `#include "tst_test.h"` (helpers: prepend `#define TST_NO_DEFAULT_MAIN`) |
| `char *TCID = "...";`                   | Remove                                                                   |
| `int TST_TOTAL = ...;`                  | Remove                                                                   |
| `tst_parse_opts(...)`                   | Remove                                                                   |
| `tst_exit();`                           | Remove                                                                   |
| `tst_resm(TPASS/TFAIL/TINFO, ...)`      | `tst_res(TPASS/TFAIL/TINFO, ...)`                                        |
| `tst_brkm(TBROK\|TERRNO, cleanup, ...)` | `tst_brk(TBROK\|TERRNO, ...)`                                            |
| `tst_brkm(TCONF, cleanup, ...)`         | `tst_brk(TCONF, ...)`                                                    |
| `TEST_RETURN` / `TEST_ERRNO`            | `TST_RET` / `TST_ERR`                                                    |
| `SAFE_*(cleanup, ...)`                  | `SAFE_*(...)` (drop cleanup arg)                                         |
| `tst_sig(...)` / `TEST_PAUSE`           | Remove entirely                                                          |
| Old GPL boilerplate                     | `// SPDX-License-Identifier: GPL-2.0-or-later`                           |
| Old-style doc comment                   | `/*\` RST-formatted doc comment                                          |

### Test-only Old → New API Mapping

| Old                                    | New                                         |
| -------------------------------------- | ------------------------------------------- |
| `int main(int argc, char *argv[])`     | Remove; use `struct tst_test`               |
| `TEST_LOOPING(lc)`                     | Remove; framework handles iterations        |
| `tst_count = 0;`                       | Remove                                      |
| `tst_tmpdir()` / `tst_rmdir()`         | `.needs_tmpdir = 1` (remove calls)          |
| Explicit `waitpid()` for child reaping | Remove when it only reaps leftover children |

### Helper-only Old → New API Mapping

| Old                                | New                                                                    |
| ---------------------------------- | ---------------------------------------------------------------------- |
| `int main(int argc, char *argv[])` | Keep `main()`                                                          |
| default LTP-provided `main()`      | Define `TST_NO_DEFAULT_MAIN` before including `tst_test.h`             |
| `tst_tmpdir()` / `tst_rmdir()`     | Handle manually; helpers have no `struct tst_test` for `.needs_tmpdir` |

### Test Conversion

Remove `main()` and replace with `struct tst_test`. Follow the
structure and parametrization rules in `c-tests.md`.

### Helper Conversion

Follow the `TST_NO_DEFAULT_MAIN` section in `c-tests.md`.

## Step 5: Verify linting errors

MUST run `make check-<test name>` inside the test folder. The result MUST
produce zero checkpatch errors/warnings. Fix ALL issues, including
pre-existing ones.

## Step 6: Build

MUST run `make <test name>` inside the test folder. The result MUST produce
zero compiler warnings and zero errors/warnings. Fix ALL issues, including
pre-existing ones.

## Step 7: Runtime Test (Skip helpers)

MUST run the test with `-i 0`, `-i 1`, `-i 10`. TCONF is acceptable.
Any TFAIL or TBROK is a blocker and MUST be fixed before proceeding,
UNLESS it reproduces a known unfixed kernel bug on the host — per
`ground-rules.md` Rule 1, that is the expected (correct) outcome and
MUST NOT be worked around in the converted test.

## Step 8: Self-Review and Fix

MUST invoke the `/ltp-review` skill once. It writes the email reply to
`./review-inline.txt` at the LTP tree root. Read that file and fix
every issue it raises in the converted source.
