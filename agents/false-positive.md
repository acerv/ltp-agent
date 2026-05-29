<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# False Positive Prevention

Process every flagged issue through this guide before including it in the
review. Avoiding false positives is more important than processing speed —
shift bias toward following these instructions carefully.

## Core Principle

**If you cannot prove an issue exists with concrete evidence in at least one
execution path, do not report it.**

This applies even when a rule from `c-tests.md`, `shell-tests.md`,
`openposix.md`, `ground-rules.md`, or `commit-message.md` appears violated:
you must still verify the violation is real in this specific patch, not a
pattern-match that looks similar.

## Common false-positive patterns

### 0. Context preservation

- Make sure the full commit message is still in context. If not, reread it
  (`git log -1 --format=fuller <sha>`).
- Make sure the full patch hunk under review is still in context. If not,
  reread it (`git show <sha>`).
- Do not proceed with false-positive verification without this context.

### 1. Defensive programming requests

**Never suggest** defensive checks unless you can prove:

- The input comes from an untrusted source (user input, command-line args,
  parsed file contents, network data).
- An actual path exists where invalid data reaches the code.
- The current code can demonstrably fail.

LTP is a test framework — internal helper functions called from `setup()`
or `run()` with framework-provided arguments are NOT untrusted input.

**Examples:**

- Avoid: "Add a bounds check on `i` here for safety."
- Avoid: "This should validate the fd before using it."
- Prefer: "User input from `tst_parse_int()` at `parse_args()` reaches this
  without validation; can this overflow `buf[]`?"

### 1.1 Failure to handle errors

Never report failure to handle an error unless:

- You can prove the error is possible (e.g. read the man page or LTP API
  doc for the function being called).
- You confirmed the function arguments used don't prevent the error.
- The framework isn't already handling it: `SAFE_*` macros call
  `tst_brk(TBROK, ...)` on failure, so a missing return-value check after
  `SAFE_OPEN()` is by design — not a bug.

### 3. Unverifiable assumptions

**Assume the author is wrong** and require proof they are correct.

- Untrusted sources (user/network/parsed input) always need concrete proof
  of correctness.
- Research assumptions and claims in commit messages, comments, and code —
  prove whether they are correct.
- If the author makes a claim without code evidence, treat it as
  unverified.
- Design decisions must be justified by code or documentation.
- Read the entire commit message. If it explains a behavior, verify the
  explanation against the code.
- Read surrounding code comments. Verify they accurately describe the code.

**Report unless:**

- You found specific code that proves the author correct.
- You can verify all assumptions with concrete code paths.
- The behavior is proven correct, not just claimed.

### 3.1 Comment-based dismissals

When dismissing an issue because a comment or documentation says the code
behaves a certain way, you MUST verify against the actual implementation:

1. **Read the function body, not just the comment.** Comments can be
   copy-pasted between implementations with different semantics. The same
   comment may appear on both sides of an `#ifdef/#else` block.
2. **Check for conditional compilation.** If code has
   `#ifdef CONFIG_FOO`/`#else` branches, determine which applies on the
   target platform.
3. **Verify helper-function behavior.** If dismissing because "function X
   returns Y", read function X's implementation. Check if X has
   config-dependent behavior.
4. **When in doubt, report the issue.** A bug dismissed based on
   incorrect documentation is worse than a false positive.

### 5. Use-after-free confusion

Distinguish between:

- Use-after-free (accessing freed memory) → Report
- Use-before-free (using then freeing) → Don't report
- Free-after-use (normal cleanup) → Don't report

Trace the exact sequence: `alloc@loc → use@loc → free@loc → use@loc`.
Check if object ownership was transferred (e.g. to a `struct tst_test`
hook, to a child process, to a cleanup callback).

### 6. Resource-leak misconceptions

**Not a leak if:**

- Ownership was transferred to the framework (`.cleanup` hook,
  `tst_res()`/`tst_brk()` exit paths).
- The resource is bound to the test's tmpdir, which the framework removes
  on exit.
- It's intentional one-shot test code that calls `tst_brk(TCONF, ...)` or
  `tst_brk(TBROK, ...)` and exits the process.
- Cleanup happens in a callback or deferred work.

LTP test code runs as a short-lived process per test; process-scoped
resources (memory, fds without external visibility) are reclaimed on exit.
**Do NOT flag** missing `free()`/`close()`/`munmap()` in `cleanup()` when
the test process exits immediately after — but DO flag them if the
resource has external scope (loop devices, mounts, sysctls, files in
`/tmp` not under tmpdir, spawned processes still running).

Also: `setup()` and `cleanup()` in `struct tst_test` run once per test
process. Do NOT flag missing pointer resets in `cleanup()` (e.g.
`p = NULL` after `SAFE_FREE(p)`) — the process exits next.

### 7. Order changes

Don't report order changes unless you can prove:

- A new race condition is introduced.
- A dependency is violated (e.g. `cleanup()` now runs before the resource
  is created).
- State becomes invalid.

### 12. Uninitialized variables

- Assigning to a variable is the same as initializing it.
- Passing an uninitialized variable to a function is fine if that function
  writes to it before reading it (e.g. `read()` into a buffer).
- Only report **reading** from an uninitialized variable, not writing to
  it.
- LTP's `SAFE_MALLOC()` does NOT zero memory; treat output as
  uninitialized. By contrast, `SAFE_CALLOC()` zeros the allocation — do
  not flag missing explicit initialization for fields whose zero value is
  correct.

### 13. Implicit guard conditions

Before reporting a NULL dereference:

- Check whether an earlier `if (p)` / `if (!p) return` / `SAFE_*` macro
  guarantees `p != NULL` by the time of the dereference.
- Check whether the framework already ensures it (e.g. `tst_test.test_all`
  always receives a valid `struct tst_test *`; `setup()` runs before
  `run()`, so anything `setup()` allocates is non-NULL in `run()` unless
  `SAFE_*` was bypassed).
- Check whether the variable is on a path that cannot be reached when it
  would be NULL (e.g. `if (fd != -1) close(fd)`).

### 14. Patch series

Large changes are broken into small logical units. Each patch must compile
and not introduce new bugs, but intermediate patches may legitimately:

- Add a helper used by a later patch (so the helper has no caller yet).
- Add an API before the consumer.
- Remove the consumer before deleting the API.

If a flagged issue is "work in progress completed later in the series",
it is a false positive. Check `git log master..HEAD` for fixes/uses in
later commits before flagging.

## TASK POSITIVE.1 Verification Checklist

Complete each step and produce the required output. Do not skip steps.

Before reporting any issue, verify:

1. **Can I prove this path executes?**
   - Quote the call chain reaching the issue site (e.g.
     `run() → do_test() → check_value()`).
   - Verify the code is not behind a disabled `#ifdef` for this build.
   - Output: call chain + config gate (or "always compiled").

2. **Is the bad behavior structurally possible?**
   - Show the step-by-step execution path with function names that
     produces the failure.
   - State the concrete failure mode (crash, hang, wrong test verdict,
     resource leak with external scope, memory corruption) — not
     "increases risk".
   - Output: failure mode + triggering condition.

3. **Did I check the full context?**
   - Examine calling functions (`setup()`, `cleanup()`, `run()`,
     `test_all`, sibling helpers).
   - Verify framework conventions (does the rule from `c-tests.md` truly
     apply here?).
   - Output: callers examined + conventions found.

4. **Is this actually wrong?**
   - Is it an intentional design choice documented in the commit message
     or a comment?
   - Is it a documented limitation (e.g. `[STAGING]` test, unreleased
     kernel feature)?
   - Confirm the bug exists today, not only if code changes later.
   - Output: quote any explanation, or "no explanation found".

5. **Did I check the commit message and surrounding comments?**
   - Quote any commit-message text explaining this behavior.
   - Quote relevant comments near the issue site.
   - Output: quoted text, or "no relevant context".

6. **Did I hallucinate?**
   - Quote the exact code snippet from the file. Reread to confirm.
   - Check your arithmetic (off-by-one, division by zero requires a zero
     denominator, etc.).
   - Output: verbatim code + arithmetic verification (or "no arithmetic").

7. **Did I check for fixes in later commits?**
   - Search forward in `git log master..HEAD` for a commit that
     resolves this.
   - Output: "found fix in <sha> — reporting as real bug with later fix"
     or "no fix found".

8. **If dismissing based on a comment or doc, did I verify the
   implementation?**
   - Quote the implementation that proves the comment accurate.
   - List `#ifdef`/`#else` branches that affect behavior.
   - If you cannot verify, do NOT dismiss — report.

9. **Debate yourself.**
   - 9.1 As the author, generate the strongest counterargument:
     - Did the reviewer check existing NULL guards or invariants?
     - Did the reviewer trace resource ownership and cleanup hooks?
     - Is this intentional based on the commit message?
     - Are they confusing structural possibility with defensive
       programming?
   - 9.2 As the reviewer, address each counterargument with code
     evidence.
   - Output: strongest counterargument + code refutation (or "cannot
     refute — likely false positive").

## Final Filter

Before adding to the review, answer all four:

1. **Do I have proof, not just suspicion?** [yes / no]
2. **Would an experienced LTP maintainer see this as a real issue?**
   [yes / no]
3. **Is this worth the maintainer's time?** [yes / no]
4. **Am I suggesting defensive programming, or reporting a concrete
   issue?** Defensive ("add a NULL check for safety") → discard.
   Concrete ("this leaks the loop device on the error path") → report.
   [defensive / concrete]

If you didn't answer yes to questions 1-3 and "concrete" to 4,
investigate further or discard.

## Special cases for LTP

- **Test-code resource scoping**: memory and fd leaks contained within a
  test process that exits immediately are not bugs. Only flag if the
  resource outlives the process (loop devices, mounts, sysctls, files
  outside tmpdir, kernel objects, spawned processes).
- **Trivial commits**: small mechanical changes (typo fixes, gitignore
  updates, lapi fallback definitions) may have minimal commit-message
  bodies. Do not flag empty bodies on self-explanatory patches.
- **Old API tests**: when a patch touches an existing old-API test
  without converting it, do not flag the pre-existing old-API usage as
  a regression introduced by this patch.
- **`#ifdef HAVE_*` with `TST_TEST_TCONF` in `#else`**: this is the
  documented LTP pattern for compile-time feature gating with runtime
  reporting. Not a violation of the runtime-detection ground rule.

## Remember

- Reports without clear proof waste maintainer time.
- Missed bugs also waste maintainer time — a real leak shipped is worse
  than a false positive caught in review.
- Real bugs have real proof: an execution path that exists and a failure
  mode that follows from it.
