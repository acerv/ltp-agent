<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Inline Review Template

This file defines how to write the body of the review email — phrasing,
quoting, and formatting. It applies to every review reply. The outer
shell (the `Hi <name>` greeting, the verdict, and the postamble) is
defined in `.agents/skills/ltp-review/SKILL.md` Phase 4 and Phase 5; this
file governs everything in between.

## Format

- Plain text only. No markdown, no HTML, no special characters.
- Wrap your own text at 78 characters. Long lines in the quoted patch may
  exceed this — preserve them as-is.
- Quote patch content with `> ` prefix, standard mailing list style.
- Insert your comments directly below the relevant quoted line(s),
  separated by a blank line before and after.
- End every review with a blank line.

## Tone

- Factual. Technical observations, not accusations.
- Frame issues as **questions about the code**, not statements about the
  author. Avoid "you" / "did you" — ask about the code.
- Don't add filler or praise. If something is correct, say nothing.
- Don't summarize what passed.
- Use the word "regression" sparingly. Never use "critical".
- Never use ALL CAPS, except when quoting code that uses it.

## Phrase issues as questions

Ask about the code or the resource, not about the author.

Avoid:

    Did you corrupt memory here?
    You forgot to close the fd.
    This leaks memory.

Prefer:

    Can this corrupt memory?
    Does this path leave the fd open?
    Does this code leak the allocation from setup()?

Name the specific resource or variable. Don't say "resource leak" — say
"does this leak the loop device?". Don't say "bounds issue" — say "does
this overflow `buf[]`?".

Vary your phrasing. Don't open every comment with "Does this code…".
Alternatives: "Can this …?", "Is this `…` reachable?", "Should this
also free `…`?", "What happens when `…`?".

## NEVER quote line numbers

Line numbers in your local working copy mean nothing to the maintainer
reading the reply. They do not match the patch context, the maintainer's
checkout, or the final merged commit.

- Reference code by **function name** and, when needed, by **call chain**
  (`funcA() → funcB()`).
- When you would otherwise say a line number, quote a short code snippet
  instead.

Avoid:

    Looking at line 142 of safe_macros.c, the SAFE_CLOSE() call is missing
    the matching cleanup at line 217.

Prefer:

    In `do_test()`, the `SAFE_OPEN()` in the setup path has no matching
    close in the failure return:

        fd = SAFE_OPEN(path, O_RDONLY);
        if (some_check())
            return;     /* fd leaked here */

This applies to the body of the review AND to the "Pre-existing issues"
section. Use `<file> in <function>()` rather than `<file>:<line>`.

## Snip aggressively

Quote only what is needed to explain each comment. The reader has the
full patch in their mail client — they don't need it repeated.

For each comment:

- Keep the diff hunk header(s) for files you reference.
- Drop entirely unrelated files from the quoted diff.
- Drop entirely unrelated hunks from quoted files.
- Drop unrelated functions/blocks from large hunks.
- Mark every place you snip with `[...]` on its own line.
- Keep enough context that the comment makes sense without the full
  patch.

Drop trailing files and hunks after your last comment unless they are
needed for context.

## Don't over-explain

Some issues need detail (subtle races, unclear ownership). Most don't.

- Obvious typos, duplicated lines, cut-and-paste errors: point them out
  in one short sentence. Don't explain why typos are bad.
- Simple omissions ("missing close on this path"): one sentence is
  enough. Don't elaborate on resource leak theory.
- Use detailed explanations only when the issue is genuinely subtle.

## Break up dense paragraphs

Avoid one long paragraph mixing observation and question. Split into
groups separated by blank lines, with the question at the end.

Avoid:

    The commit message claims this fixes a leak in setup() but looking at
    cleanup() the matching SAFE_CLOSE() is already there from commit
    abc123 so this hunk is redundant and may double-close the fd if
    cleanup() runs twice.

Prefer:

    The commit message says this fixes a leak in `setup()`.

    `cleanup()` already calls `SAFE_CLOSE(fd)` (added in commit abc123),
    so the new close in `setup()` is redundant.

    Could this double-close the fd if `cleanup()` runs after a failed
    `setup()`?

## Commit-message issues

When the issue is in the commit message itself (not the diff), quote the
relevant lines of the commit message as the first quoted block, then ask
the question after.

If the issue is a missing `Fixes:` tag, quote the full commit message
header (subject + body) so the reader sees the context.

If the issue is a typo in the subject:

    > shmctl01: convert to new API
    
    There's a typo (`shmctl01` → `shmctl1`?) in the subject line.

Quote the diff only if the commit-message issue depends on it.

## Pre-existing issues

When you noticed pre-existing issues in surrounding code not introduced
by the patch, list them after the review and before the postamble, under:

    Pre-existing issues noticed in the surrounding code (not introduced
    by this patch):

    - <file> in <function>() — <one-line description>
    - <file> in <function>() — <one-line description>

Use function names, never line numbers. Keep each item to one line. If
you have nothing to list, omit the block entirely.

## Examples

### Good: short, specific, question form

    > +	fd = SAFE_OPEN(path, O_RDONLY);
    > +	if (verify_data(buf) < 0)
    > +		return;
    
    Does this path leak `fd`? `cleanup()` doesn't close it because the
    test exits via `return` before `tst_test` records the fd.

### Good: commit-message issue

    > syscalls/openat02: add test for O_TMPFILE
    >
    > This adds coverage for O_TMPFILE.
    
    The body only restates the subject. Could it say why the coverage was
    missing (e.g. a recent kernel change, an uncovered branch in
    `do_tmpfile()`)?

### Good: pre-existing block

    Pre-existing issues noticed in the surrounding code (not introduced
    by this patch):
    
    - testcases/kernel/syscalls/foo01.c in setup() — `SAFE_MALLOC()` has
      no matching free in `cleanup()`.

### Avoid: line numbers and dense prose

    On line 87 of foo01.c the buffer is allocated with malloc but on
    lines 102-105 the cleanup function does not free it and on line 134
    the test exits via tst_brk which means the framework does not free
    it either so this is a leak that has been present since the test was
    added in 2019.

### Avoid: defensive-programming suggestion without proof

    You should add a NULL check on the result of `SAFE_MALLOC()` just to
    be safe.

`SAFE_MALLOC()` calls `tst_brk(TBROK, ...)` on failure and never returns
NULL. Don't suggest defensive checks where the framework already handles
the failure.
