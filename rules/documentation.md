<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Documentation Rules

This file contains MANDATORY rules for LTP documentation.

## 1. Documentation system

- LTP documentation is built with Sphinx from reStructuredText sources
  rooted at `doc/` and the entry point is `doc/index.rst`.
- C API reference is generated from kernel-doc comments via the `linuxdoc`
  Sphinx extension.

## 2. File-level requirements

- All documentation files MUST be ASCII-only.
- Lines MUST stay under 100 characters. Wrap long sentences and URLs.
- Use spaces (not tabs) for indentation in `.rst` sources. Indent
  continuation lines of bullets to align with the text after the marker.
- `.rst` files under `doc/` must start with
  `.. SPDX-License-Identifier: GPL-2.0-or-later`.
- `.py` files under `doc/` must start with
  `# SPDX-License-Identifier: GPL-2.0-or-later`.

## 3. reStructuredText style

- Use the heading underline order already established in `doc/` (do NOT
  introduce a new style):
  - `=` for page title.
  - `-` for sections.
  - `~` for subsections.
  - `^` for sub-subsections.
- Separate every block-level construct (heading, list, code-block,
  directive, table) from surrounding paragraphs with a blank line.
- Ordered and bulleted lists MUST be preceded by a blank line.
- Inline literals use double backticks (` ``foo`` `), not single
  backticks. Single backticks invoke the default role (rendered as a
  `title-reference`), not inline literal text.
- Use `.. code-block:: <lang>` (with an explicit language) for code
  samples. Do NOT use bare `::` literal blocks in new prose.
- Cross-reference the LTP tree using the project's `extlinks` roles, not
  raw URLs:
  - `:master:` for files in `master` (e.g. ``:master:`include/tst_test.h` ``).
  - `:repo:` for non-blob repo paths.
  - `:shell_lib:` for shell library files.
  - `:kernel_tree:` for files in the upstream Linux tree.
  - `:kernel_doc:` for `docs.kernel.org` pages.
  - `:kselftest:` for selftest paths.
- Reference manpages with the `:manpage:` role and an explicit section,
  e.g. ``:manpage:`execve(2)` ``. The `manpages_url` config maps these
  to `man7.org`. Do NOT hand-write `https://man7.org/...` links.
- Reference C API symbols with the C domain roles:
  - `:c:func:` for functions.
  - `:c:struct:` for structs.
  - `:c:macro:` for macros.
  - `:c:type:` for typedefs.

## 4. RST inside C test doc-comments

- The high-level description block uses `/*\` on its own line to open
  and ` */` to close. Each interior line begins with `*`. The block
  MUST be valid reStructuredText; it is rendered as-is in the test
  catalog.
- Inside the block, follow the reST rules above:
  - blank line before lists, code-blocks, and section markers;
  - inline literals with double backticks;
  - manpage and `:master:` roles for syscall and file references.
- The optional `[Algorithm]` section MUST be a literal `[Algorithm]`
  header followed by a blank line and a bulleted list using `-`. Do NOT
  use the deprecated `[Description]` header.
- Keep the description focused on _what_ is tested and _why_ it matters.
  Do NOT restate the algorithm in prose when an `[Algorithm]` block
  already lists the steps.

## 5. kernel-doc API comments

- New or modified public functions, structs, and macros in `include/`,
  `include/lapi/`, and `lib/` MUST be documented with kernel-doc syntax
  recognized by `linuxdoc`. Existing undocumented symbols SHOULD gain
  kernel-doc when touched:

  ```c
  /**
   * tst_foo() - one-line summary ending with a period.
   * @arg1: meaning of arg1
   * @arg2: meaning of arg2
   *
   * Longer description in reST. May reference :c:func:`tst_bar` and
   * :manpage:`open(2)`.
   *
   * Return: description of the return value.
   */
  ```

- The summary line MUST match the symbol name exactly, with the
  kernel-doc type prefix required by `linuxdoc`:
  - `name()` for functions.
  - `struct name` for structs.
  - `union name` for unions.
  - `enum name` for enums.
  - `typedef name` for typedefs.
  - `name` (no prefix) for macros and constants.
- Every parameter MUST have an `@name:` entry, in declaration order.
- Use `Return:`, `Context:`, and `Note:` section labels as defined by
  kernel-doc; do NOT invent new ones.
- Private (`static`) symbols MUST NOT use `/** ... */`. Use a plain
  `/* ... */` comment if any explanation is needed.

## 6. Comments vs. documentation

- Comments inside test bodies MUST follow the rule from
  `doc/developers/writing_tests.rst`: explain _why_, not _how_, and
  never comment the obvious.
- Do NOT leave TODO/FIXME notes in the high-level description block or
  in kernel-doc summaries. Put them in regular `/* TODO: ... */`
  comments inside the implementation.

## 7. Spelling and language

- New or modified `.rst` content MUST pass `make spelling` (run from
  `doc/` after activating the Sphinx virtualenv).
- When a legitimate technical term is flagged, add it (one word per
  line, sorted) to `doc/spelling_wordlist`. Do NOT silence the warning
  by rewording correct technical names.
- Use US English spelling consistently.

## 8. Building locally

- Documentation builds depend on `make autotools && ./configure` at the
  tree root before `cd doc && make` so that metadata generators can run.
- Python 3.8+ is required; the upstream CI uses Python 3.12 via
  `.readthedocs.yml` and `.github/workflows/ci-sphinx-doc.yml`. Do NOT
  introduce syntax that breaks on 3.8.
- Do NOT commit generated artifacts under `doc/html/`, `doc/build/`, or
  `doc/.venv/`. They are produced by `make` and excluded by
  `.gitignore`.

## What NOT to do

- Do NOT use Doxygen tags (`\param`, `\return`, `@brief`, etc.) in kernel-doc
  comments.
- Do NOT use Markdown syntax in `.rst` sources: no `#`/`##` headings,
  no `_italic_` (reST uses `*italic*`), and no fenced ` ``` ` code blocks.
- Do NOT embed raw HTML (`<br>`, `<a href>`, `<pre>`, etc.) in `.rst`
  sources or in kernel-doc comments.
- Do NOT hand-write anchor labels (`.. _foo:`) that duplicate the
  auto-generated section or symbol anchors Sphinx already produces.
- Do NOT add new top-level pages without linking them from
  `doc/index.rst` or an existing toctree.
