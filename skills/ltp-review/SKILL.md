---
name: ltp-review
description: LTP Patch Reviewer - perform reviews on patches
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Patch Review Protocol

You are an agent that performs a deep code review on patches for the
LTP - Linux Test Project. Your job is the code review - understanding intent,
conventions and correctness.

## Analysis Philosophy

This review assumes the patch has bugs, including in its comments and commit
message. Every change, comment, and commit-message assertion must be proven
correct against the code, otherwise flag it. New APIs are checked for
consistency and ease of use; any deviation from LTP conventions is reported.

## Step 1: Verify patches are applied

Run `git rev-list --count master..HEAD`. If the count is 0 (no commits ahead
of master), or the current branch IS master, STOP immediately and tell the
user:

> No patches found. Please checkout a branch with patches applied on top of
> master before running this review.

Do NOT proceed with the review.

## Step 2: Classify changed files

Use `git diff --name-only master..HEAD` to list what files have been changed.
Read `{{LTP_AGENT_DIR}}/rules/classify.md` and classify each changed file.
Produce a mapping `{file -> category}` to be consumed by Step 5.4.

## Step 3: Verify patch type

Using the file list and classification from Step 2:

- If the patch only deletes files (no added or modified code), skip code
  review entirely. Only review commit messages and verify that related
  entries (runtest, .gitignore, Makefile) are also removed.
- If the patch only touches non-test files (runtest/\*, .gitignore,
  doc/, ci/, scripts/), skip the code review entirely. Only
  review commit messages and verify the changes are correct.

## Step 4: Commit message review

Read `{{LTP_AGENT_DIR}}/rules/commit-message.md` and apply ALL rules.

## Step 5: Code Review

### 5.1. Read the Diff

For each commit in the series, run `git show <hash>` to read the individual
diff. Then read the full content of each changed file for surrounding context.
Use `git diff master..HEAD` for the combined diff when checking cross-commit
consistency.

### 5.2. Scope

Read full changed files for context, but only flag issues that meet one of:

1. Code added or modified by the patch.
2. Pre-existing code that is now broken or incomplete because of the patch
   (e.g. patch adds an fd in setup() but existing cleanup() never closes it).
3. Pre-existing code on a path directly exercised by the patch's new logic.

Do NOT flag pre-existing style issues or old API usage as review failures.

When reading full files for context, specifically watch for pre-existing
memory issues such as:

- leaks (`malloc`/`mmap` without matching `free`/`munmap`).
- use-after-free.
- double-free.
- uninitialized reads.
- buffer overflows.

### 5.3. Ground Rules (MANDATORY)

Read `{{LTP_AGENT_DIR}}/rules/ground-rules.md` and apply ALL the rules in
there.
These rules are MANDATORY and any violation means reject.

### 5.4. Verify rules

For each changed file, use the classification produced in Step 2 to
determine which rule files to load. MUST NOT diverge from any of the
rules.

#### 5.4.1. Open POSIX test

Read `{{LTP_AGENT_DIR}}/rules/openposix.md` and apply ALL the rules inside it.

#### 5.4.2. LTP self-test

Read `{{LTP_AGENT_DIR}}/rules/c-tests.md` and apply ALL the rules inside it.

#### 5.4.3. LTP test helper

Read `{{LTP_AGENT_DIR}}/rules/c-tests.md` and apply ALL Helper Binaries rules.

#### 5.4.4. LTP test (old API)

Read `{{LTP_AGENT_DIR}}/rules/c-tests.md`.

If the patch is NOT converting the file to the new API, skip coding style
and API usage checks. Still apply file organization, result reporting,
syscall correctness, and ground rules.

#### 5.4.5. LTP test

Read `{{LTP_AGENT_DIR}}/rules/c-tests.md` and apply ALL the rules inside it.

Additional checks:

- If a new C test is added, read `<dir>/Makefile`. If it uses a wildcard
  (e.g. no explicit file list), the new test is picked up automatically. If
  it lists targets explicitly, verify the new test binary name appears.
- Verify the test's syscall usage matches documented kernel behavior.
  Cross-check with: man pages, local kernel source at `/usr/src/linux`,
  or online at `https://github.com/torvalds/linux`. If unverifiable, flag as
  **Needs discussion**.

#### 5.4.6. LTP shell test

Read `{{LTP_AGENT_DIR}}/rules/shell-tests.md` and apply ALL the rules inside
it.

If the shell file uses the old API (`. test.sh`, `tst_resm`, `TCID`,
`TST_TOTAL`) and the patch is NOT converting it to the new API, skip
structural checks. Still apply coding style, result reporting, and
ground rules.

#### 5.4.7. LTP library

Read `{{LTP_AGENT_DIR}}/rules/c-tests.md` and apply ALL the rules inside it.

#### 5.4.8. Build system

Read `{{LTP_AGENT_DIR}}/rules/build-system.md` and apply ALL the rules
inside it.

#### 5.4.9. Others

Skip code review.

### 5.5. False-positive verification

Read `{{LTP_AGENT_DIR}}/rules/false-positive-guide.md` and follow the entire file
for each candidate.

Drop any issue that fails. A rule violation surfaced by
`{{LTP_AGENT_DIR}}/rules/c-tests.md`,
`{{LTP_AGENT_DIR}}/rules/shell-tests.md`,
`{{LTP_AGENT_DIR}}/rules/openposix.md`,
`{{LTP_AGENT_DIR}}/rules/build-system.md`,
`{{LTP_AGENT_DIR}}/rules/ground-rules.md`, or
`{{LTP_AGENT_DIR}}/rules/commit-message.md`
is a candidate -- not a confirmed finding -- until it clears this step.

## Step 6: Writing Output

Read `{{LTP_AGENT_DIR}}/rules/email-template.md` and compose the review reply
following ALL rules in `{{LTP_AGENT_DIR}}/rules/email-template.md`.

Write the email to `./review-inline.txt`. Create, do not append.
