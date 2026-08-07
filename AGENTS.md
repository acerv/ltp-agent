<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# AGENTS.md

Guidance for AI coding agents working on this repository (`ltp-agent`).
This project hosts skills, rules, and tooling used by AI agents to review,
analyze, and convert [Linux Test Project](https://github.com/linux-test-project/ltp)
tests. It does NOT contain LTP tests itself.

## Repository Layout

- `agents/` — per-agent installer scripts (`claude.sh`, `pi.sh`,
  `opencode.sh`, `gemini.sh`, `copilot.sh`), invoked by `setup.sh`. Agent-
  specific assets live in subdirectories, e.g. `agents/opencode/agent/*.md`
  holds the opencode multi-agent conversion pipeline definitions.
- `skills/` — skill bundles (`ltp-review`, `ltp-analyze`, `ltp-convert`).
  Each skill has a `SKILL.md` and supporting prompt or template files.
- `rules/` — rule files loaded on demand by skills. One topic per file.
- `tools/` — helper scripts (`scan-old-api.py`, `ltp-build.sh`,
  `ltp-run.sh`).
- `setup.sh` — entry point that dispatches to `agents/<agent>.sh`.
- `.github/workflows/` — CI that runs `/ltp-review` against Patchwork series.

## Scope Rules

- This repo configures agents; it does NOT modify the LTP source tree.
- When a task says "review/analyze/convert a test", the target file lives
  in a separate LTP checkout, not in this repo.
- Skills MUST stay agent-agnostic. Do NOT hardcode paths or behaviors that
  only work for one agent (Claude, pi, opencode, gemini, copilot).

## Editing Rules

- Every new file MUST start with an `SPDX-License-Identifier: GPL-2.0-or-later`
  comment in the syntax appropriate for the file type.
- Markdown lines MUST stay under 100 characters. Wrap longer lines.
- Shell scripts MUST start with `#!/bin/sh` or `#!/bin/bash` and the SPDX tag
  on the second line.
- Use tabs for indentation in Makefiles, two spaces in YAML, four spaces in
  Python.
- Keep rule files factual and concise. Use MUST / SHOULD / MAY / MUST NOT
  for normative statements so an LLM can match them deterministically.
- All files MUST use ASCII-only characters.

## Rule File Conventions

Files under `rules/` are read by skills as authoritative input:

- One topic per file; do NOT duplicate rules across files.
- Prefer short bullets over prose. Group related rules under a heading.
- Show a minimal correct example before listing rules about it.
- Put prohibitions in a dedicated "What NOT to do" subsection when useful.
- Cross-reference other rule files by relative path, not by URL.

## Skill Conventions

Each skill under `skills/<name>/` MUST contain:

- `SKILL.md` describing when the skill applies and what it produces.
- Any prompt fragments, templates, or checklists it depends on.

Skills MUST:

- Declare the rule files they load.
- Be read-only unless their purpose is to modify files (e.g. `ltp-convert`).
- Write outputs to predictable paths at the LTP tree root (e.g.
  `review-inline.txt`).

## Tooling

- Python scripts MUST run on Python 3.8+ without third-party dependencies
  unless the dependency is documented in the script header.
- Shell scripts MUST be POSIX-compatible unless they explicitly require
  bash; in that case use `#!/bin/bash`.
- Do NOT add build artifacts, caches, or virtualenvs to the repo. Update
  `.gitignore` if a new tool produces them.

## README Maintenance

`README.md` is the user-facing index of this repo and MUST stay in sync
with the tree. Update it in the SAME commit whenever you:

- Add, rename, or remove a file under `rules/` (update the Rule Files
  table).
- Add, rename, or remove a skill under `skills/` (update the Usage
  section with the new slash command and a short description).
- Add, rename, or remove a helper under `tools/` that users invoke
  directly (update the relevant Usage subsection).
- Add or remove a supported agent under `agents/` (update the Supported
  AI coding agents list and the `<agent>` enumeration in Setup).
- Add a new top-level directory (also update this file, see
  "What NOT to Do").
- Change a CI workflow under `.github/workflows/` in a way that affects
  user-visible behavior (update the Continuous Integration section).

Documentation-only changes to existing files (typo fixes, clarifications)
do NOT require a README update.

## Commit and PR Rules

- Commit messages follow the LTP convention documented in
  `rules/commit-message.md`.
- One logical change per commit. Skill, rule, and tooling changes SHOULD
  be split into separate commits.
- Every commit MUST include a `Signed-off-by:` trailer.

## What NOT to Do

- Do NOT add agent-specific logic to `rules/` or `skills/`; it belongs in
  `agents/<agent>.sh`.
- Do NOT modify files under a user's LTP checkout from this repo's tooling
  except through an explicit conversion skill.
- Do NOT introduce new top-level directories without updating this file
  and `README.md`.
- Do NOT vendor LTP source, kernel headers, or test fixtures.
