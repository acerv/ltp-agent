---
name: ltp-convert
description: LTP Old-to-New API Converter
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Test Conversion Protocol

You are an agent that converts LTP tests from the old API (`test.h`) to the
new API (`tst_test.h`).

The conversion is NOT a mechanical token-by-token translation. It is a
**semantic rewrite**: you extract _what_ the test does, discard the old
implementation, and write a clean new test using modern LTP idioms.

## Invocation

`/ltp-convert <file path or test name>` - convert one file.

---

## 1. Load Rules

- Read `{{LTP_AGENT_DIR}}/rules/ground-rules.md`.
- Read `{{LTP_AGENT_DIR}}/rules/c-tests.md`. This is the authoritative
  reference for what the converted code MUST look like.

## 2. Resolve and classify the file

The argument may be a file path or a test name. Resolve it first:

- File path: use it directly.
- Test name (e.g. `getpid01`): locate the source under `testcases/`
  (search by basename). If multiple or no matches are found, ask the user
  to disambiguate or provide a path, then stop.

Read `{{LTP_AGENT_DIR}}/rules/classify.md` and classify the file.

Only **LTP test (old API)** can be converted. Continue to the next step.

For any other classification, stop and tell the user `/ltp-convert` only
converts old-API LTP tests.

## 3. Intent summary

Before doing any conversion work, evaluate the test using the `/ltp-analyze`
skill.

Present the following to the user:

1. Test analysis: the full output from `/ltp-analyze`.
2. Conversion complexity: simple, moderate, or complex; and why.
3. Droppable features: the list of features that can be dropped.
4. Recommendation one of:
   - Convert: test has clear value, proceed
   - Convert with reservations: test is marginal but may still be useful;
     explain concerns
   - Recommend skip/delete: test is trivial, duplicate, or doesn't test what
     it claims; suggest alternative action.

ALWAYS wait for user confirmation before proceeding to the next step.

If the user says to proceed despite reservations, proceed. If the user
asks to skip, stop here.

## 4. Design the New Test

Starting ONLY from the Intent summary, design the new test from
scratch. Do NOT reference the old code during this step. Decide:

1. Test structure: `.test` + `.tcnt` (multiple cases) vs `.test_all`
   (single case) with `struct tcase` array.
2. Assertion macros: which `TST_EXP_*` macros fit each scenario.
3. Framework features: `.needs_tmpdir`, `.forks_child`, `.needs_root`,
   `.needs_kconfigs`, `.save_restore`, `.bufs`, `.min_kver`,
   `.supported_archs`, etc.
4. Resource lifecycle: what static state is needed, what `.setup` allocates,
   what `.cleanup` releases.
5. Synchronization: if the test forks, what mechanism is used (checkpoint,
   waitpid, process state wait).

Produce a brief design summary before writing code.

## 5. Implement

Write the new test from the design above, following all rules in
`{{LTP_AGENT_DIR}}/rules/c-tests.md` and
`{{LTP_AGENT_DIR}}/rules/ground-rules.md`.

Critical rules:

- The old code MUST NOT be used as a structural template - only the
  intent and algorithm extracted in the Intent summary guide the
  implementation.
- NEVER preserve the old test's control flow - the structure comes from
  new API idioms, not the old code.
- NEVER do token-by-token replacement - from `tst_resm()` to `tst_res()` is
  transliteration, not conversion.
- NEVER keep helper functions that only existed because of old API
  limitations (e.g., separate `parent_test1()` / `parent_test2()` when a
  `struct tcase` array works).
- NEVER preserve manual error-accumulation patterns (`rval` flags,
  return-code propagation) - call `tst_res()` directly at the point where
  the outcome is determined.
- NEVER keep forward declarations - reorder functions so callees precede
  callers.
- NEVER preserve per-test-case setup/cleanup function pointers - redesign
  using framework callbacks and static state.
- ALWAYS handle iterations with `-i` option.
- ALWAYS handle verbosity with `TDEBUG` messages and `-v` option.
- ALWAYS keep the original copyright if it's not `GPL-2` compatible.

### Helper Conversion

If the file is a helper, follow the `TST_NO_DEFAULT_MAIN` section in
`{{LTP_AGENT_DIR}}/rules/c-tests.md`. Keep `main()`, drop all old API
artifacts, and skip the runtime step during finalize.
