---
name: ltp-import
description: LTP External Test Importer — turn any external test into a native LTP test
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Test Import Protocol

You are an agent that imports an **external** test into LTP as a native test
using the new API (`tst_test.h`) or the LTP shell API.

"External" means the source did NOT originate in the LTP tree: a kselftest, a
glibc/musl testcase, a bare C reproducer from a bug report or mailing list, a
syzkaller/syzbot reproducer, a CVE proof-of-concept, an strace-derived
sequence, or a standalone shell reproducer.

This is NOT a token translation. It is a **semantic re-authoring**: you extract
_what the source asserts about the kernel_, discard the source's framework and
control flow, and write a clean LTP test from scratch using LTP idioms.

## Invocation

`/ltp-import <file path | URL | pasted source | description>` — import one test.

---

## Step 0: Scope Gate

This skill targets, in priority order:

1. **In scope (v1):** a C reproducer or kselftest-style C source that
   exercises a syscall or kernel feature → import as an LTP **C test**.
2. **In scope:** a portable shell reproducer → import as an LTP **shell test**.

**Flag and STOP** (do not produce a test) when:

- The source's intent cannot be determined (no clear assertion about kernel
  behavior — e.g. a pure userspace/libc-logic test, a benchmark, or a fuzzing
  harness with no oracle).
- The source only "passes" by not actually exercising the kernel path, and you
  cannot reconstruct a real pass/fail oracle.

When stopping, tell the user exactly why and what would be needed to proceed.

## Step 1: Load Rules

Read `agents/ground-rules.md` first. Then read the rules for the **target**
test type (decided in Step 3); if the target is not yet obvious, read the rule
file matching the source language:

- C target → `agents/c-tests.md`
- Shell target → `agents/shell-tests.md`

Use `agents/classify.md` when deciding the target test type and whether the
produced binary is a test or a helper. The selected rules file is the
authoritative reference for what the imported code MUST look like.

## Step 2: Acquire and Classify the Source

Obtain the full source:

- File path → read it.
- URL → fetch it (raw source, not a rendered HTML page where avoidable).
- Pasted source or description → use as-is.

Then classify and report:

1. **Language / framework**: C + kselftest harness, C + glibc test driver,
   bare C `main()`, syzkaller C reproducer, shell, etc.
2. **Origin**: kselftest, glibc, syzbot/CVE, mailing-list repro, unknown.
3. **License**: identify the source license and SPDX tag. LTP is
   `GPL-2.0-or-later`. Flag any license incompatibility to the user before
   proceeding — do NOT copy code under an incompatible or unclear license;
   re-author from intent instead.
4. **Is it really external?** If it includes `test.h`/`tst_test.h` or lives in
   the LTP tree, redirect to `/ltp-convert` or `/ltp-analyze` and stop.

## Step 3: Extract Intent and Choose the Target

### 3a. Extract intent

Reconstruct the intent by answering the questionnaire in
`agents/test-intent.md`.

If the source is itself a runnable test, you MAY run its Steps 2–6 through the
`/ltp-analyze` skill (`.agents/skills/ltp-analyze/SKILL.md`) to harvest the
intent, scenarios, and coverage gaps.

### 3b. Choose target type

- Syscall / kernel feature in C → **C test** under
  `testcases/kernel/syscalls/<name>/` (or the appropriate subsystem dir).
- Behavior best expressed with shell utilities → **shell test**.

### 3c. Choose placement

Decide and report, before writing code:

- **Directory**: the correct subsystem directory (syscalls, mm, cve, ipc,
  net, …). A security reproducer usually belongs in `testcases/cve/`.
- **Test name**: follow the family naming convention of sibling tests in that
  directory (e.g. `foo01`, `foo02`). List siblings to confirm.
- **Runtest file**: which `runtest/` file the entry goes in.

## Step 4: Present the Import Plan

Present to the user and **wait for confirmation** before writing code:

1. **Source summary** — language, origin, license/SPDX status.
2. **Intent** — syscall/feature, scenarios, algorithm, pass/fail oracle.
3. **Target** — test type, directory, test name, runtest file, staging or not.
4. **Reproducer fidelity note** — for a security/regression import, state
   exactly what condition signals the bug, and confirm the LTP test will
   detect it (not merely run to completion).
5. **Risks / reservations** — anything uncertain (oracle, root requirement,
   portability, kernel-version gating).

If the user asks to skip or the source fails the Step 0 gate, stop here.

## Step 5: Design the LTP Test

Starting ONLY from the intent (Step 3a), design from scratch. Do NOT mirror
the source's control flow. Decide:

1. **Structure**: `.test` + `.tcnt` (multiple cases) vs `.test_all` (single).
2. **Assertion macros**: the `TST_EXP_*` macro that fits each scenario.
3. **Framework features**: `.needs_tmpdir`, `.forks_child`, `.needs_root`,
   `.needs_device`, `.needs_kconfigs`, `.save_restore`, `.bufs`, `.min_kver`,
   `.supported_archs`, `.tags` (for a regression/CVE import).
4. **Parametrization**: can scenarios collapse into a `struct tcase` array?
5. **Resource lifecycle**: static state, what `.setup` allocates, what
   `.cleanup` releases on every exit path.
6. **Synchronization**: if it forks, use checkpoints / `SAFE_WAITPID` /
   process-state wait — NEVER sleep-based timing (Ground Rule 2).

Produce a brief design summary before implementing.

## Step 6: Implement

Write the new test from the Step 5 design, following ALL rules in the selected
rules file and `ground-rules.md`.

**Critical rules:**

- Re-author from intent — NEVER copy the source's structure, helper
  decomposition, or error-accumulation patterns.
- Replace ad-hoc reporting (`printf`, `perror`, exit codes, `assert`) with
  `tst_res()` / `tst_brk()` / `TST_EXP_*` reported at the point of decision.
- Replace raw syscalls with the matching `SAFE_*` macro, EXCEPT the syscall
  that is the **subject** of the test (wrap that in `TEST()` / `TST_EXP_*`).
- Replace any `sleep()`-based synchronization with checkpoints or
  process-state polling (Ground Rule 2).
- Use runtime feature detection, not compile-time assumptions (Ground Rule 3).
  Return `TCONF` when the feature/syscall is unavailable.
- Clean up on ALL exit paths, including `tst_brk()`/`SAFE_*` aborts
  (Ground Rule 5).
- Add the SPDX header `// SPDX-License-Identifier: GPL-2.0-or-later`, a
  copyright line, and an RST `/*\ ... */` doc comment describing _what_ is
  tested. For a regression/CVE import, record the commit/CVE in `.tags`
  (never as GitHub PR/issue URLs).

### Plumbing

Create the supporting files so the test builds and runs:

- Add the test binary to the directory `.gitignore`.
- Ensure the directory `Makefile` picks it up (wildcard Makefiles need no
  change; explicit lists must include the new binary).
- Add the `runtest/` entry (or `runtest/staging`).
- For a new syscall, update `include/lapi/syscalls/*.in` and regenerate
  `lapi/syscalls.h` per the "New Syscalls Testing" section of `c-tests.md`.

## Step 7: Verify the Oracle

Before finalizing, confirm the test actually exercises the target path and
would FAIL if the kernel behavior were wrong. A test that only ever returns
`TPASS`/`TCONF` regardless of kernel state is not a faithful import — verify
the assertion is real (e.g. on a known-buggy or feature-missing kernel it
reports `TFAIL`/`TCONF`, not `TPASS`).

## Step 8: Finalize

Run the shared finalize pipeline in `agents/finalize.md` on `<test name>`.
