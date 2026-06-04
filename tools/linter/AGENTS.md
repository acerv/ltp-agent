# Linter Project Patterns

## Architecture

- **Decorator-based rule registration**: rules are plain functions
  decorated with `@rule(message, scope=...)`. The decorator appends
  a `Rule` object to `core._rules` at import time.
- **Scope filtering**: each rule declares a scope string (`"c"`,
  `"c_only"`, `"sh"`). `SCOPE_MATCH` in `core.py` maps each scope
  to a tuple of file extensions. `run_rules()` skips rules whose
  scope doesn't match the file being linted.
- **Entry point**: `ltp-linter` script adds the linter dir to
  `sys.path` and calls `main.run()`. `main.py` imports all
  `rules_*.py` modules to trigger decorator registration.

## File layout

```
tools/linter/
  core.py          — Rule class, rule() decorator, run_rules(), SCOPE_MATCH
  main.py          — argparse entry point, _lint_file()
  repo.py          — git helpers (changed_files)
  rules_c.py       — C test rules (scope="c" or "c_only")
  rules_sh.py      — shell test rules (scope="sh")
  ltp-linter       — CLI entry script
  tests/
    conftest.py    — adds tools/linter/ to sys.path
    test_core.py   — tests for core module
    test_main.py   — tests for main module
    test_repo.py   — tests for repo module
    test_rules_c.py  — tests for C rules
    test_rules_sh.py — tests for shell rules
```

## Adding a new rule

1. Choose the right file: `rules_c.py` for C/H files,
   `rules_sh.py` for shell scripts. For a new file type,
   create `rules_<type>.py` and import it from `main.py`.
2. Write a function that takes `lines` (list of strings) and
   yields `(line_number, detail_message)` tuples.
3. Decorate it with `@rule("Short message", scope="<scope>")`.
4. Add a multi-line docstring explaining what the rule checks.
5. Add tests in the corresponding `tests/test_rules_<type>.py`.
6. Run `ruff format tools/linter/` and `ruff check tools/linter/` before
   committing.

## Adding a new scope

1. Add the scope string and its extensions to `SCOPE_MATCH`
   in `core.py`.
2. Create `rules_<type>.py` with rules using the new scope.
3. Import the new module from `main.py`.
4. Add `"*.<ext>"` to the git diff in `repo.py` for branch mode.
5. Add scope filtering tests to `test_core.py`.

## Conventions

- **Docstrings**: always multi-line, never one-line.
- **Loop variables**: use `line_num` for line numbers, `match`
  for regex matches, `stripped` for stripped lines.
- **Comment skipping**: strip once with `stripped = line.lstrip()`
  then check `stripped.startswith("//")` or
  `stripped.startswith("*")` for C, `stripped.startswith("#")`
  for shell.
- **Early continue**: use `if not match: continue` guard pattern
  instead of nesting logic inside `if match:`.
- **Blank lines**: add a blank line after each `if ... continue`
  guard and between separate logical blocks inside functions.
  Each guard-continue pair is its own block.
- **Rule messages**: cross-check against `rules/c-tests.md` or
  `rules/shell-tests.md` to ensure accuracy. The linter message
  should match the project guideline, not invent its own.

## Testing patterns

- Each rule function is imported directly and tested by passing
  lines and asserting on the yielded `(line_num, detail)` tuples.
- Test classes are named `TestCheck<RuleName>`.
- Each test class has positive tests (finding expected) and
  negative tests (no finding expected).
- Comment-skipping tests verify that rules ignore commented code.
- `test_core.py` tests scope filtering with temporary rules
  that are cleaned up via `saved = core._rules[:]` /
  `core._rules.clear()` / `core._rules.extend(saved)`.
- `test_main.py` uses `tempfile.NamedTemporaryFile` for file
  mode tests and mocks `repo.changed_files` for branch mode.
- `test_repo.py` mocks `subprocess.run` to avoid git calls.

## Formatting and linting with ruff

All Python code must be formatted with `ruff` before committing.

```bash
# Format all files
ruff format tools/linter/

# Check for lint issues
ruff check tools/linter/

# Fix auto-fixable lint issues
ruff check --fix tools/linter/
```

Run `ruff format` after every change.

## Running tests

```bash
cd tools/linter
python3 -m pytest tests/ -v
```
