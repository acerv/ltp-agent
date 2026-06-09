<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Rule Dispatch Table

Load rule files based on the file classification produced during
review. Match the classification from the table below and load
ONLY the rule files listed for that classification. Do NOT
load rule files for other classifications.

A single changed file matches exactly one row. If a patch touches
multiple files with different classifications, load each matching
set of rule files once.

All rule file paths below are relative to this file's directory.

| Classification     | Rule files                       |
| ------------------ | -------------------------------- |
| Open POSIX test    | `openposix.md`                   |
| LTP self-test      | `c-tests.md`                     |
| LTP test helper    | `c-tests.md`                     |
| LTP test header    | `c-tests.md`                     |
| LTP test (old API) | `c-tests.md`                     |
| LTP test           | `c-tests.md`, `documentation.md` |
| LTP shell test     | `shell-tests.md`                 |
| LTP library        | `c-tests.md`, `documentation.md` |
| Build system       | `build-system.md`                |
| Documentation      | `documentation.md`               |
| Others             | _(none)_                         |

## Per-classification instructions

- Open POSIX test: Apply ALL rules.
- LTP self-test: Do NOT flag missing `struct tst_test`,
  missing doc block, or missing `main()`.
- LTP test helper: Apply ONLY the Helper Binaries rules.
- LTP test header: Do NOT flag missing `struct tst_test`,
  missing doc block, or missing `main()`.
- LTP test (old API): If the patch is NOT converting to the
  new API, skip coding style and API usage checks. Still apply
  file organization, result reporting, syscall correctness, and
  ground rules.
- LTP test: Apply ALL c-tests rules. From `documentation.md`
  apply ONLY the high-level description block rules (section 4)
  to the `/*\ ... */` block at the top of the test. Also:
  - If a new C test is added, read `<dir>/Makefile`. If it
    uses a wildcard, the new test is picked up automatically.
    If it lists targets explicitly, verify the new test binary
    name appears.
  - Verify the test's syscall usage matches documented kernel
    behavior. Cross-check with: man pages, local kernel source
    at `/usr/src/linux`, or online at
    `https://github.com/torvalds/linux`. If unverifiable, flag
    as Needs discussion.
- LTP shell test: Apply ALL rules. If old API (`. test.sh`,
  `tst_resm`, `TCID`, `TST_TOTAL`) and the patch is NOT
  converting, skip structural checks; still apply coding style,
  result reporting, and ground rules.
- LTP library: Do NOT flag missing `struct tst_test`, missing
  doc block, or missing `main()`. From `documentation.md` apply
  ONLY the kernel-doc rules (section 5) to any new or modified
  public function, struct, or macro.
- Build system: Apply ALL rules.
- Documentation: Apply ALL rules.
- Others: Review based on the file extension.
