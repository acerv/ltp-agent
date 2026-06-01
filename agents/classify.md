<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Test Classification

This file defines how to classify an LTP test target. Load it whenever a skill
needs to decide what kind of test it is looking at. It is the single source of
truth for classification — skills MUST reference it instead of restating these
rules.

## Step C1: Determine the test type

Inspect the file path, extension, and contents:

- Path under `testcases/open_posix_testsuite/` → **Open POSIX test**.
  These use different APIs and conventions (see `agents/openposix.md`).
  Do NOT apply `agents/c-tests.md` rules to them.
- `*.sh` → **shell test** (see `agents/shell-tests.md`).
- `*.c` / `*.h` elsewhere → **C test or helper** (see `agents/c-tests.md`);
  continue to Step C2 to split test vs helper.
- `*.c` / `*.h` under `lib/newlib_tests/` → **C test** (LTP library
  self-test). Apply the full `agents/c-tests.md` rules.
- `*.c` / `*.h` under `lib/` or `include/` (excluding `lib/newlib_tests/`)
  → **library/header file**, NOT a test. Skip the test-structure rules.
- No file yet (a written description) → **design-only**. Apply
  `agents/ground-rules.md` plus whichever language rules will apply.

## Step C2: Determine the API (C tests)

- Includes `#include "tst_test.h"` → **new API**.
- Includes `#include "test.h"`, or defines `TCID` / `TST_TOTAL` /
  `tst_resm` → **old API**.

## Step C3: Determine test vs helper (C files)

Check whether the file's basename (without `.c`) appears in any `runtest/`
file:

    grep -RFw <basename> runtest/

- **Found** → **test**. It has a `struct tst_test` (new API) or a `main()`
  with `TEST_LOOPING` (old API).
- **Not found** → inspect path and contents before deciding:
  - If the file is under a test directory (e.g.
    `testcases/kernel/syscalls/`) or otherwise looks like a standalone test
    (uses `struct tst_test`), treat it as a **test** and flag the missing
    `runtest/` entry as a bug — do NOT treat the missing entry as proof that
    the file is a helper.
  - If the file is a spawned support binary (its own `main()`, not listed in
    `runtest/`), it is a **helper binary**. Helpers keep `main()` under
    `TST_NO_DEFAULT_MAIN` (see the "Helper Binaries" section of
    `agents/c-tests.md`).

## Step C4: Locate the runtest entry

Record which `runtest/` file the test belongs to (or note MISSING). Tests for
unreleased kernel features go in `runtest/staging` (see `ground-rules.md`
Rule 8).
