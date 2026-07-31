<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Git configuration

This file contains MANDATORY rules for git configuration files in LTP.

## .gitignore

LTP prefers many small per-directory `.gitignore` files over a single root
file. The root `.gitignore` only covers global build and tool artifacts
(object files, autotools output, editor/swap files, cscope/tags, patch
artifacts, `compile_commands.json`). Test binaries are ignored by the
`.gitignore` file in their own test directory.

Rationale: a `.gitignore` per test directory does not need updating when a
directory is moved, and is removed automatically when the directory is
removed.

Minimal correct example (leaf test directory `.gitignore`):

```.gitignore
/statx01
/statx02
```

Rules:

- New test binaries MUST be added to the `.gitignore` in their own
  directory, NOT to the root `.gitignore`.
- Only generated artifacts belong in `.gitignore`. Do NOT ignore source
  files (`*.c`, `*.h`, `*.sh`, `Makefile`, `*.mk`, `*.rst`).
- A binary's ignore entry MUST match the binary name produced by the
  Makefile (same name as the `.c` file, no extension).
- Leaf-directory entries SHOULD be anchored with a leading `/` so they only
  match in that directory.
- Keep entries sorted and free of duplicates.

### What NOT to do

- Do NOT add a new global pattern to the root `.gitignore` for a single
  test binary.
- Do NOT commit a test binary because its `.gitignore` entry is missing;
  flag the missing entry instead.
- Do NOT commit binary files.

## .gitmodules

LTP uses git submodules for external tools and third-party test suites.

Minimal correct example:

```.gitmodules
[submodule "tools/kirk/kirk-src"]
    path = tools/kirk/kirk-src
    url = https://github.com/linux-test-project/kirk.git
```

Rules:

- Each `[submodule "..."]` block MUST define both `path` and `url`.
- URLs MUST use `https://`. Do NOT use `git://` or `ssh://` / `git@github.com:`
  forms, which break anonymous clones.
- First-party LTP tools MUST live under `https://github.com/linux-test-project/`.
- Tool submodules SHOULD place the checkout in a `-src` subdirectory
  (e.g. `tools/ltx/ltx-src`), matching existing entries.
- The submodule name SHOULD equal its `path`.
- Adding or updating a submodule MUST keep the entry consistent with the
  actual committed gitlink; document the reason in the commit message.

## .gitattributes

LTP does NOT track a `.gitattributes` file; the name is listed in the root
`.gitignore` so local copies stay untracked.

Rules:

- Do NOT add a tracked `.gitattributes` file without an explicit, documented
  reason and maintainer agreement.

## .mailmap

`.mailmap` canonicalizes contributor names and email addresses.

Minimal correct example:

```.mailmap
Li Wang <li.wang@linux.dev> <liwang@redhat.com>
```

Rules:

- Each entry maps one or more old identities to a single canonical `Name <email>`.
- Use the format `Canonical Name <canonical@email> <old@email>`.
- Keep the canonical identity consistent across all of a contributor's entries.
- Do NOT alter another contributor's canonical identity without their agreement.
