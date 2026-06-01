---
name: ltp-convert
description: LTP Old-to-New API Converter
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Test Conversion Protocol

You are an agent that converts LTP tests from the old API (`test.h`) to the
new API (`tst_test.h`).

The conversion is NOT a mechanical token-by-token translation. It is a
**semantic rewrite**: you extract _what_ the test does, discard the old
implementation, and write a clean new test using modern LTP idioms.

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

Classify the file using `agents/classify.md` (Steps C2–C3): confirm it uses
the **old API**, and determine whether it is a **test** (full conversion:
remove `main()`, add `struct tst_test` — see Step 6) or a **helper binary**
(keep `main()`, add `TST_NO_DEFAULT_MAIN` — see the Helper Binaries section of
`c-tests.md`).

## Step 4: Triage — Is This Test Worth Converting?

Before doing any conversion work, evaluate the test using the `/ltp-analyze`
skill (`.agents/skills/ltp-analyze/SKILL.md`). Run its Steps 2–6 on the
old test file. This produces the test intent summary, value assessment,
robustness findings, and coverage gaps.

After the analysis, add the following conversion-specific assessments:

### 4a. Identify Droppable Features

Many old tests carry features that have no equivalent or
purpose in the new API. Identify and report these to the
user.

**Old API boilerplate — always drop:**

- `TCID` / `TST_TOTAL` globals
- `tst_sig(FORK, DEF_HANDLER, cleanup)`
- `TEST_PAUSE`
- `tst_count = 0`
- `TEST_LOOPING(lc)` / loop counter `lc` — the framework
  handles iterations via `-i`
- `tst_exit()` — the framework handles exit

**Old CLI options — almost always drop:**

- `option_t` arrays and `tst_parse_opts()` — drop the
  whole custom-option machinery. If an option controlled
  verbosity (`-v`, `vflag`), replace with `TDEBUG` or
  `tst_res(TINFO, ...)`. If it controlled actual test
  behavior (e.g., `-m <multiplier>`), explain what it
  did and recommend dropping or hardcoding the sensible
  default.
- `-f` functional / `-s` stress flags — drop; the
  framework handles iteration with `-i`

**Old structural patterns — always drop:**

- `main()` with `TEST_LOOPING` — replaced by
  `struct tst_test`
- Forward declarations of static functions — reorder
  functions so callees precede callers
- Per-test-case `setup()`/`cleanup()` function pointers
  in the case array — redesign using the framework's
  `.setup`/`.cleanup` callbacks and static state
  tracking

**Old comment blocks — always drop:**

- Usage comments listing old CLI flags
- `HISTORY` / `RESTRICTIONS` blocks
- Old GPL boilerplate (replace with SPDX header)

### 4b. Present Assessment

Present the following to the user:

1. **Test analysis** — the full output from `/ltp-analyze` (Steps 2–6)
2. **Droppable features** — list every old API artifact that will be
   discarded and why (from 4a above)
3. **Conversion complexity** — simple, moderate, or complex; and why
4. **Recommendation** — one of:
   - **Convert**: test has clear value, proceed
   - **Convert with reservations**: test is marginal but may still be
     useful; explain concerns
   - **Recommend skip/delete**: test is trivial, duplicate, or doesn't
     test what it claims; suggest alternative action

**Wait for user confirmation before proceeding to Step 5.**

If the user says to proceed despite reservations, proceed. If the user
asks to skip, stop here.

## Step 5: Design the New Test

Starting ONLY from the intent summary (Step 4a), design the new test from
scratch. Do NOT reference the old code during this step. Decide:

1. **Test structure**: `.test` + `.tcnt` (multiple cases) vs `.test_all`
   (single case)
2. **Assertion macros**: which `TST_EXP_*` macros fit each scenario
3. **Framework features**: `.needs_tmpdir`, `.forks_child`,
   `.needs_root`, `.needs_kconfigs`, `.save_restore`, `.bufs`,
   `.min_kver`, `.supported_archs`, etc.
4. **Parametrization**: can scenarios be a `struct tcase` array?
5. **Resource lifecycle**: what static state is needed, what `.setup`
   allocates, what `.cleanup` releases
6. **Synchronization**: if the test forks, what mechanism is used
   (checkpoint, waitpid, process state wait)?

Produce a brief design summary before writing code.

## Step 6: Implement

Write the new test from the Step 5 design, following all rules in
`c-tests.md` and `ground-rules.md`.

**Critical rules:**

- NEVER preserve the old test's control flow — the structure comes from
  new API idioms, not the old code
- NEVER do token-by-token replacement — `tst_resm()` → `tst_res()` is
  transliteration, not conversion
- NEVER keep helper functions that only existed because of old API
  limitations (e.g., separate `parent_test1()` / `parent_test2()` when a
  `struct tcase` array works)
- NEVER preserve manual error-accumulation patterns (`rval` flags,
  return-code propagation) — call `tst_res()` directly at the point where
  the outcome is determined
- NEVER keep forward declarations — reorder functions so callees precede
  callers
- NEVER keep old-style `do_child()` with `_exit()` when the child should
  use `tst_res()` + `exit(0)` for result propagation
- NEVER preserve per-test-case setup/cleanup function pointers — redesign
  using framework callbacks and static state
- The old code MUST NOT be used as a structural template — only the
  **intent** and **algorithm** extracted in Step 4a guide the
  implementation
- The copyright line MUST use the current (latest) year — the year the
  conversion is done — NEVER copy the year from the old test

## Step 7: Finalize

Run the shared finalize pipeline in `agents/finalize.md` on `<test name>`.

### Helper Conversion

If the file is a helper (Step 3), follow the `TST_NO_DEFAULT_MAIN` section in
`c-tests.md`. Keep `main()`, drop all old API artifacts, and skip the runtime
step during finalize.
