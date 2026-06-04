<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Ground Rules

These rules are **MANDATORY** and must **NEVER** be violated when writing or
reviewing LTP code. Violations MUST be flagged in reviews.

## Rule 1: No Kernel Bug Workarounds

Code MUST NOT work around known kernel bugs.

NEVER work around a kernel bug in LTP test code. Workarounds mask failures for
everyone else. If a test fails because a fix was not backported, that is the
expected (correct) result.

## Rule 2: No Sleep-Based Synchronization

Code MUST NOT use timed waits for synchronization.

NEVER use sleep or delay calls to synchronize between processes. It causes
rare flaky failures, wastes CI time, and breaks under load. Tests that use
timed waits as part of testing timer APIs are exempt.

**Use instead:**

- Parent waits for child to finish -> blocking wait
- Child must reach a code point before parent continues -> checkpoint synchronization
- Child must be sleeping in a syscall -> process state polling
- Async or deferred kernel actions -> exponential-backoff polling loop

## Rule 3: Runtime Feature Detection Only

Code MUST use runtime checks, NOT compile-time assumptions.

Compile-time checks may ONLY enable fallback API definitions. NEVER assume
compile-time results reflect the running kernel.

**Runtime detection methods:**

- Error code checks at call site
- Minimum kernel version gating
- Kernel configuration requirements
- Kernel config file parsing

## Rule 4: Minimize Root Usage

Tests MUST NOT require root unless absolutely necessary.

If root is required, the reason MUST be documented in the test's doc comment.
Drop privileges for sections that do not need them.

## Rule 5: Always Clean Up

Tests MUST clean up on ALL exit paths (success, failure, early exit).

Every test MUST leave the system exactly as it found it:

- Filesystems -> Unmount
- Sysctls, `/proc`/`/sys` values -> Restore
- Temp files/dirs -> Delete
- Spawned processes -> Kill
- Cgroups/namespaces -> Remove
- Loop devices -> Detach
- Ulimits -> Restore

Prefer framework helpers over manual setup/teardown when available.

## Rule 6: Write Portable Code

- MUST NOT use nonstandard libc APIs when portable equivalent exists
- MUST NOT assume 64-bit, page size, endianness, or tool versions
- Architecture-specific tests MUST still compile everywhere
- Shell tests MUST be portable POSIX shell (no bash-isms)

Verify with `make check`.

## Rule 7: One Logical Change Per Patch

- Each patch MUST contain exactly ONE logical change
- Each patch MUST compile successfully on its own
- Each patch MUST keep all tests and tooling functional
- Each patch MUST NOT introduce intermediate breakage
- Commit message MUST clearly explain the change

Patches mixing unrelated changes will be delayed or ignored.

## Rule 8: Unreleased Kernel Features

- Tests for unreleased kernel features MUST use `[STAGING]` subject prefix
- Staging tests MUST go into `runtest/staging` only

Tests for features not yet in a mainline kernel release will NOT be merged into
default test suites until the kernel code is finalized and released.

**Before flagging a test as staging**, verify whether the kernel version has
actually been released. Do NOT assume a version is unreleased based on the
number alone. Check `https://kernel.org` to confirm the latest stable release.
Conversely, if the feature IS in a released kernel, flag any `[STAGING]`
prefix or `runtest/staging` entry as incorrect.
