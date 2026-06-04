---
name: ltp-analyze
description: LTP Test Analyzer - evaluate test quality, robustness, and coverage
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Test Analysis Protocol

You are an agent that performs a deep analysis of an LTP test to evaluate its
quality, robustness, and coverage. This skill works on any LTP test (old API,
new API or shell) and it's read-only: analyze and report only, do not modify
any files.

The goal is to answer: Is this test effective, and how can it be improved?

## Invocation

`/ltp-analyze <file path or test name>`

---

## Step 1: Resolve and classify the input

The argument may be a file path or a test name. Resolve it first:

- File path: use it directly.
- Test name (e.g. `getpid01`): locate the source under `testcases/`
  (search by basename). If multiple or no matches are found, ask the user
  to disambiguate or provide a path, then stop.

Read `{{LTP_AGENT_DIR}}/rules/classify.md` and classify the file. Then read
these files according to the file type:

- C tests: `{{LTP_AGENT_DIR}}/rules/c-tests.md` and
  `{{LTP_AGENT_DIR}}/rules/ground-rules.md`.
- Shell tests: `{{LTP_AGENT_DIR}}/rules/shell-tests.md` and
  `{{LTP_AGENT_DIR}}/rules/ground-rules.md`.
- Open POSIX tests: `{{LTP_AGENT_DIR}}/rules/openposix.md` and
  `{{LTP_AGENT_DIR}}/rules/ground-rules.md`.

If the file cannot be classified, stop and tell the user why.

## Step 2: Understand the Test

Answer each question, ignoring the source's API-level and framework details:

1. What syscall / feature / behavior is being exercised?
2. What are the distinct scenarios? Each assertion or test case.
3. What is the algorithm? Step-by-step what the test does (e.g. "fork a child,
   child calls `exit(1)`, parent waits, checks `WEXITSTATUS == 1`").
4. What resources does it need? tmpdir, root, fork, device, kconfigs, min_kver,
   network, IPC, etc.
5. What setup/teardown is needed? Files, signals, mounts, IPC, etc.
6. What is the pass/fail oracle? Expected return value, expected errno,
   expected side-effect. For a security/regression reproducer, the
   crash/corruption/leak the source demonstrates - not merely running to
   completion.

## Step 3: Assess Test Value

Evaluate the test on these dimensions and flag any concerns:

### 3a. Trivial or vacuous tests

Flag tests that do not meaningfully exercise the target feature:

- The test calls the syscall but only checks that it returns without
  crashing (no return-value or side-effect verification).
- The test is almost entirely scaffolding with a trivial check at the end.
- The test claims to test syscall X but the actual verification is on
  something unrelated (e.g., it mostly tests `fork()`/`wait()` rather
  than the nominal target).

### 3b. Duplicate coverage

Check whether other tests in the same directory or `runtest/` file already
cover the same behavior with better rigor:

- List existing tests for the same syscall/feature that test the same
  scenarios.
- Note which scenarios overlap and which are unique to this test.

### 3c. Tests that don't belong

Flag tests that exercise libc string functions, userspace-only logic, or
other things that are not kernel functionality when placed under kernel
test directories (e.g., `string01.c` tests `strchr`, `strcmp`, etc. under
`testcases/kernel/`).

### 3d. Complexity vs value ratio

Flag tests where the code is hundreds of lines but the actual kernel
feature coverage is minimal. These may benefit from being rewritten with a
simpler, more focused approach.

## Step 4: Robustness Analysis

Evaluate the test's resilience to real-world conditions:

### 4a. Error path coverage

- Does the test verify failure cases (wrong arguments, missing
  permissions, resource exhaustion)?
- Are expected errno values checked, not just return codes?
- Does the test distinguish between "syscall failed correctly" (TPASS) and
  "syscall failed unexpectedly" (TFAIL)?

### 4b. Race conditions and timing

- Are there sleep-based synchronization patterns?
- If the test forks, is the parent-child ordering guaranteed?
- Could the test flake under heavy system load?
- Are there TOCTOU (time-of-check-time-of-use) windows?

### 4c. Resource cleanup

- Does the test clean up on ALL exit paths?
- Are there resources that survive process exit (mounts, SysV IPC, sysctl
  changes, loop devices, cgroups) that are not handled in cleanup?
- If `tst_brk()` or a `SAFE_*` macro aborts mid-test, will cleanup still
  release everything?

### 4d. Portability

- Does the test assume 64-bit, specific page size, endianness, or tool
  versions?
- Are there hardcoded constants that should be runtime-detected?
- Does the test use `#ifdef` for feature detection where runtime detection
  should be used?

### 4e. Iteration safety

- If run with `-i N` (multiple iterations), does the test re-initialize
  all state correctly?
- Are static variables reset between iterations?
- Could repeated runs accumulate side-effects?

## Step 5: Coverage Gap Analysis

Identify what the test does NOT cover that it probably should:

### 5a. Missing scenarios

Based on the syscall's man page and kernel implementation, list scenarios
that are not tested but should be:

- Boundary values (0, -1, MAX, off-by-one)
- Permission checks (different uids, capabilities)
- Error conditions documented in the man page but not tested
- Interaction with other syscalls or features

### 5b. Missing side-effect verification

Flag cases where the test only checks the return value but not the
side-effects:

- File was supposed to be created/modified - is it checked?
- Memory mapping was supposed to change - is the content verified?
- Signal was supposed to be delivered - is it caught and verified?
- Process state was supposed to change - is it observed?

### 5c. Edge cases

Identify edge cases that could reveal kernel bugs:

- Empty inputs, NULL pointers, zero-length buffers
- Maximum-length paths, filenames at NAME_MAX
- Operations on special filesystems (proc, sys, tmpfs)
- Operations across namespace boundaries
- Concurrent access patterns

## Step 6: API and Style Compliance (LTP C test only)

Check compliance with the loaded rules (`{{LTP_AGENT_DIR}}/rules/c-tests.md`).
This is NOT a full patch review - it is a health check:

- Framework features: Are there manual patterns that the framework
  handles automatically? (e.g., manual save/restore vs `.save_restore`,
  manual option parsing vs framework options, manual tmpdir vs
  `.needs_tmpdir`)
- Safe macros: Are there bare syscalls that should use `SAFE_*`?
- Result reporting: Are results reported directly or propagated through
  return values/exit codes?
- Test structure: If there are multiple test cases, are they using
  `struct tcase` + `.test` + `.tcnt`, or separate functions?

## Step 7: Present Analysis

Present the complete analysis to the user in this format:

### Test Identity

- **File**: path
- **Type**: C test / shell test / Open POSIX / helper
- **API**: new (`tst_test.h`) / old (`test.h`) / shell / N/A
- **Runtest**: entry found in `runtest/<file>` or MISSING

### Test Intent

Summary from Step 2 - what the test does and how.

### Value Assessment

One of:

- **High value** - test provides meaningful, non-duplicated coverage
- **Moderate value** - test has coverage but with concerns (explain)
- **Low value** - test is trivial, duplicate, or misplaced (explain)

### Robustness Assessment

One of:

- **Robust** - test handles error paths, cleanup, portability well
- **Needs hardening** - specific issues identified (list them)
- **Fragile** - significant robustness problems (list them)

### Coverage Gaps

Numbered list of missing scenarios, side-effect checks, and edge cases
from Step 5. For each gap, briefly explain what it would catch.

### API/Style Issues

List of compliance findings from Step 6, if any. Mark each as:

- **Must fix** - Ground Rule violation or broken test logic
- **Should fix** - Non-idiomatic but functional
- **Nice to have** - Minor style improvement

### Recommendations

Prioritized list of concrete actions to improve the test, from most
impactful to least. Each recommendation should be actionable (not
"improve coverage" but "add a test case for EINVAL when fd is negative").
