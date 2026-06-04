<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# False Positive Prevention

Process every flagged issue through this guide before including it in the
review. Avoiding false positives is more important than processing speed.

## Core Principle

**If you cannot prove an issue exists with concrete evidence in at least one
execution path, do not report it.**

This applies even when another rule appears violated: you must still verify
the violation is real in this specific patch, not a pattern-match that looks
similar.

## Common false-positive patterns

### 0. Context preservation

- Make sure the full commit message is still in context. If not, reread it
  (`git log -1 --format=fuller <sha>`).
- Make sure the full patch hunk under review is still in context. If not,
  reread it (`git show <sha>`).
- Do not proceed with verification without this context.

### 1. Defensive programming requests

Never suggest defensive checks unless you can prove:

- The input comes from an untrusted source (user input, CLI args, parsed
  files, network data).
- An actual path exists where invalid data reaches the code.
- The current code can demonstrably fail.

Internal helpers called with values produced by the surrounding code or
framework are not untrusted input.

Avoid framing like "Add a bounds check here for safety." Prefer concrete
framing like "Untrusted value from X reaches Y without validation; can it
overflow Z?"

### 2. Failure to handle errors

Never report a missing error check unless:

- You can prove the error is possible (consult the API doc / man page).
- The arguments used don't already preclude the error.
- The framework or wrapper isn't already handling it (e.g. macros that
  abort on failure).

### 3. Unverifiable assumptions

**Don't accept author claims as proof.** Verify them against code. The
burden of proof for a _report_ still falls on the reviewer: an unverified
claim is not by itself a bug.

- Treat commit-message and comment claims as unverified until matched to
  code.
- Do not report an issue solely because the author failed to prove safety
  — you must still demonstrate a concrete failure path.
- Do not dismiss an issue solely because the author asserts it is safe.

**Outcomes:**

- Claim verified against code → no report.
- Claim contradicted by code with a concrete failure path → report.
- Claim unverifiable and no concrete failure path found → no report.

### 4. Comment-based dismissals

When dismissing an issue because a comment or doc says the code behaves a
certain way, verify against the actual implementation:

1. Read the function body, not just the comment. Comments get copy-pasted
   between implementations with different semantics.
2. Check for conditional compilation / feature flags. Determine which
   branch applies on the target platform.
3. Verify helper-function behavior. Read the helper's implementation, not
   its docstring.
4. When in doubt, report. A bug dismissed on incorrect documentation is
   worse than a false positive.

### 5. Use-after-free confusion

Distinguish:

- Use-after-free -> report.
- Use-then-free -> don't report.
- Free-after-use -> don't report.

Trace the exact sequence: `alloc -> use -> free -> use`. Check whether
ownership was transferred (to a cleanup hook, a child process, a
callback).

### 6. Resource-leak misconceptions

**Not a leak if:**

- Ownership was transferred to a cleanup hook, framework, or caller.
- The resource is bound to a scope the runtime tears down (process exit,
  request scope, transaction).
- The process exits immediately after, and the resource is process-scoped
  (memory, anonymous fds).

**Do flag** when the resource has external scope that outlives the
process or scope: files outside a managed tmpdir, system-wide state
(devices, mounts, sysctls), spawned processes, kernel objects, remote
state.

### 7. Order changes

Don't report reordering unless you can prove:

- A new race condition is introduced.
- A dependency is violated (e.g. cleanup runs before creation).
- State becomes invalid.

### 8. Uninitialized variables

- An assignment on every path before the read counts as initialization.
  Only flag a read that has at least one path with no prior write.
- Passing an uninitialized variable to a function is fine if that function
  writes before reading.
- Only report **reading** uninitialized data, not writing to it.
- Know which allocators zero memory and which don't.

### 9. Implicit guard conditions

Before reporting a NULL/invalid dereference:

- Check whether an earlier guard, assertion, or aborting macro already
  ensures the value is valid at the dereference site.
- Check whether the framework guarantees it (lifecycle ordering: init
  before use).
- Check whether the path that would make it invalid is unreachable.

### 10. Patch series

Each patch must compile and not introduce new bugs, but intermediate
patches may legitimately:

- Add a helper before its caller.
- Add an API before the consumer.
- Remove the consumer before deleting the API.

If a flagged issue is "completed later in the series", it is a false
positive. Check `git log master..HEAD` for fixes/uses in later commits
before flagging.

## Verification Checklist

Complete each step. Do not skip.

1. **Can I prove this path executes?**
   - Quote the call chain to the issue site.
   - Verify the code is not behind a disabled feature gate for this build.
   - Output: call chain + gate (or "always compiled").

2. **Is the bad behavior structurally possible?**
   - Show the step-by-step path that produces the failure.
   - State the concrete failure mode (crash, hang, wrong result, leak with
     external scope, corruption) — not "increases risk".
   - Output: failure mode + triggering condition.

3. **Did I check the full context?**
   - Examine callers, lifecycle hooks, sibling helpers.
   - Verify framework conventions actually apply here.
   - Output: callers examined + conventions found.

4. **Is this actually wrong?**
   - Is it an intentional design choice documented in the commit message
     or a comment?
   - Is it a documented limitation?
   - Confirm the bug exists today, not only if code changes later.
   - Output: quote any explanation, or "no explanation found".

5. **Did I check the commit message and surrounding comments?**
   - Quote any commit-message text explaining this behavior.
   - Quote relevant comments near the issue site.
   - Output: quoted text, or "no relevant context".

6. **Did I hallucinate?**
   - Quote the exact code from the file. Reread to confirm.
   - Check arithmetic (off-by-one, division by zero requires a zero
     denominator, etc.).
   - Output: verbatim code + arithmetic verification (or "no arithmetic").

7. **Did I check for fixes in later commits?**
   - Search forward in `git log master..HEAD`.
   - Output: "found fix in <sha>" or "no fix found".

8. **If dismissing based on a comment or doc, did I verify the
   implementation?**
   - Quote the implementation that proves the comment accurate.
   - List conditional branches that affect behavior.
   - If you cannot verify, do NOT dismiss — report.

9. **Debate yourself.**
   - As the author, generate the strongest counterargument: existing
     guards, ownership transfer, intentional design, defensive vs
     concrete.
   - As the reviewer, address each counterargument with code evidence.
   - Output: strongest counterargument + refutation (or "cannot refute —
     likely false positive").

## Final Filter

Before adding to the review, answer all four:

1. **Do I have proof, not just suspicion?** [yes / no]
2. **Would an experienced maintainer see this as a real issue?** [yes / no]
3. **Is this worth the maintainer's time?** [yes / no]
4. **Am I suggesting defensive programming, or reporting a concrete
   issue?** [defensive / concrete]

If you didn't answer yes to 1–3 and "concrete" to 4, investigate further or
discard.

## Remember

- Reports without clear proof waste maintainer time.
- Missed bugs also waste maintainer time — a real bug shipped is worse than
  a false positive caught in review.
- Real bugs have real proof: an execution path that exists and a failure
  mode that follows from it.
