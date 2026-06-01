<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Finalize Pipeline

This file defines the shared finalization pipeline for skills that **produce or
modify** an LTP test (e.g. `/ltp-convert`, `/ltp-import`). It is the single
source of truth for lint → build → run → review → fix. Skills MUST reference it
instead of restating these steps.

This pipeline covers only the **logical** work of getting a test correct. It
does **not** create commits: whether and how to commit is an operational
decision left to the user. The work is finalized as changes in the working
tree; the user commits (or not) when they choose.

Throughout, `<test>` is the test binary/basename being finalized.

## Step F1: Lint

Run `make check-<test>` inside the test folder. The result MUST produce zero
checkpatch errors/warnings. Fix ALL issues, including pre-existing ones.

## Step F2: Build

Run `make <test>` inside the test folder. The result MUST produce zero
compiler errors and zero warnings. Fix ALL issues, including pre-existing ones.

## Step F3: Runtime (skip for helper binaries)

Run the test with `-i 0`, `-i 1`, and `-i 10`. `TCONF` is acceptable.

Any `TFAIL` or `TBROK` is a blocker and MUST be fixed before proceeding —
UNLESS it reproduces a known unfixed kernel bug on the host. Per
`ground-rules.md` Rule 1 that is the expected (correct) outcome and MUST NOT be
worked around in the test.

Helper binaries have no runtime test — skip this step for them.

## Step F4: Self-Review in a Fresh Context

The `/ltp-review` skill MUST run in a **fresh agent context**, not in the
current session — running it inline pollutes the review with the current
session's reasoning and previously discussed fixes, producing biased or stale
findings.

This step is agent-agnostic. Use whatever mechanism your host agent provides to
spawn an isolated session, for example a subagent/sub-task with a clean
context, or a new CLI invocation of the same agent in the same working
directory.

The fresh session MUST:

1. Start in the LTP tree root.
2. Run the `/ltp-review` skill, passing `<test>` as the review target so it
   reviews the test directly from the working tree (no commit required).
3. Produce `./review-inline.txt` at the LTP tree root, then exit.

Do NOT pass the diff, prior analysis, or any hints into the fresh session — it
must rediscover everything from the repository state.

## Step F5: Apply Review Fixes

Back in the working session, read `./review-inline.txt` and fix every issue it
raises in the source. After applying fixes, re-run Steps F1–F3 (lint, build,
runtime).

If the fixes are non-trivial, repeat Step F4 once more in another fresh context
to confirm the review is clean.
