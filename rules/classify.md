<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Classify file

This file contains the rules to classify a file inside LTP. It's the single
source of truth for all files in the project.

## File type

Extract name, extension and path of the file, then classify it using the
first section below whose rules ALL match. Sections are ordered by priority
(most specific first), so always evaluate them in order and stop at the first
match.

### 1. Open POSIX test

If ALL of the following rules apply to the file, it's an Open POSIX test:

- MUST be a `*.c` file.
- MUST be inside `testcases/open_posix_testsuite/` folder.
- MUST define `test_main`.

### 2. LTP self-test

If ALL of the following rules apply to the file, it's an LTP self-test:

- MUST be a `*.c` file.
- MUST be inside `lib/newlib_tests/` folder.

### 3. LTP test helper

If ALL of the following rules apply to the file, it's an LTP test helper:

- MUST be a `*.c` file.
- MUST define `TST_NO_DEFAULT_MAIN`.

### 4. LTP test header

If ALL of the following rules apply to the file, it's an LTP test
header:

- MUST be a `*.h` file.
- MUST be inside `testcases/` folder.

### 5. LTP test (old API)

If ALL of the following rules apply to the file, it's an LTP test using the
old API:

- MUST be a `*.c` file.
- MUST be inside `testcases/` folder.
- MUST import `test.h`.
- MUST declare `TCID`.

### 6. LTP test

If ALL of the following rules apply to the file, it's an LTP test:

- MUST be a `*.c` file.
- MUST be inside `testcases/` folder.
- MUST define `struct tst_test` instance.

### 7. LTP shell test

If ALL of the following rules apply to the file, it's an LTP shell test:

- MUST be a `*.sh` script.
- MUST be inside `testcases/` folder.
- MUST import `tst_test.sh`.
- MUST run `tst_run`.

### 8. LTP library

If ALL of the following rules apply to the file, it's an LTP library:

- Can be a `*.c` or `*.h` file.
- MUST be inside `lib/` or `include/` folder.

### 9. Build system

If ALL of the following rules apply to the file, it's a Build system file:

- MUST be named `Makefile` or have extension `.mk`.

### 10. Documentation

If ANY of the following rules apply to the file, it's a Documentation
file:

- MUST have extension `.rst`.
- MUST be under `doc/` (any depth).

### 11. Others

Any other file will be classified as `Others`.
