<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Commit Message Rules

This file contains MANDATORY rules for commit messages. Load this file when
reviewing any patch.

For EACH commit, judge whether the message is **clear and informative**:

## 1. Subject is clear

Describes WHAT changed concisely. Flag if the subject is generic (e.g.
"fix test", "update code") without naming the affected component or behavior.
A good subject lets a reader predict the diff scope without opening it.

## 2. Body explains WHY

The body must contain at least one sentence beyond restating the subject line.
It must state the motivation (why the change is needed) or the problem being
solved. Flag if the body only describes what changed (e.g. "changed X to Y")
without explaining why, or if the body is empty.

Exception: do NOT flag an empty or minimal commit body when the patch is
trivially self-explanatory from the subject line alone. Examples include, but
are not limited to:

- Fixing a typo
- Whitespace or formatting fixes
- Adding a fallback `#ifndef` / `#define` in `include/lapi/` headers
- Updating a `.gitignore` entry
- Adding a missing `#include`

Only flag an empty commit body when understanding **why** the change was made
requires explanation beyond what the subject line conveys.

## 3. One logical change

Each commit is a single, self-contained change. Each patch MUST compile on its
own and MUST NOT introduce intermediate breakage. Flag patches that mix
unrelated changes (e.g. a bugfix bundled with a rename, or a new test bundled
with cleanup of an old one). A patch that adds a new test case MUST NOT add
more than one new test case — split them into separate commits.

## 4. Fixes tag

If `Fixes:` tag is present, it MUST refer to a valid commit in the git history.

## 5. Tags at the end

All tags (e.g. `Signed-off-by:`, `Fixes:`, `Suggested-by:`, `Reviewed-by:`,
`Acked-by:`, `Reported-by:`, `Link:`, `Closes:`, `Cc:`) MUST appear at the
end of the commit message body, after the explanatory text — not at the
beginning or interleaved within it. The `Signed-off-by:` tag MUST be present.

## 6. Series ordering (multi-commit only)

Commits are in logical order (e.g. helper/library changes before the test that
uses them, cleanup before new code that depends on it). Each intermediate
commit must be self-contained — no commit should reference code added by a
later commit. For each commit N, verify it does not call functions or use
variables introduced by commit N+1 or later.
