---
name: ltp-convert
description: LTP Old-to-New API Converter
---

<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# LTP Test Conversion Protocol

You are an agent that converts LTP tests from the old API (`test.h`) to the
new API (`tst_test.h`).

There are two valid conversion strategies, and you MUST choose the best one
for each test:

- **Semantic rewrite**: extract _what_ the test does, discard the old
  implementation, and write a clean new test using modern LTP idioms.
- **Faithful port**: preserve the original structure, control flow, and
  ordering, swapping old-API calls for new-API equivalents with minimal
  restructuring.

Neither strategy is a mechanical token-by-token translation, and neither may
lose the original test intent.

The single invariant of this protocol: the original test intent MUST NEVER be
lost. Every scenario and every pass/fail oracle of the old test must survive
into the converted test, unless the user explicitly approves dropping it.

## Invocation

`/ltp-convert <file path or test name>` - convert one file.

---

## 1. Load Rules

- Read `{{LTP_AGENT_DIR}}/rules/ground-rules.md`.
- Read `{{LTP_AGENT_DIR}}/rules/c-tests.md`. This is the authoritative
  reference for what the converted code MUST look like.
- Read `{{LTP_AGENT_DIR}}/rules/documentation.md`. Section 4 is the
  authoritative reference for the high-level description block of the
  new test.
- Read `{{LTP_AGENT_DIR}}/rules/conversion-strategy.md`. This defines the two
  conversion strategies and how to choose between them.

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

## 3. Build the Intent Contract

Before doing any conversion work, evaluate the test using the `/ltp-analyze`
skill. From that analysis, build the **Intent Contract** using the structure
defined in `{{LTP_AGENT_DIR}}/rules/conversion-strategy.md`. Capture every
scenario and its exact oracle with zero loss; it is the single source of truth
for the rest of the conversion.

## 4. Decide the conversion strategy

Evaluate BOTH strategies against ALL criteria in
`{{LTP_AGENT_DIR}}/rules/conversion-strategy.md` for this test, and produce the
strategy decision output that file requires. This decision is mandatory for
every test; intent fidelity overrides all other criteria.

## 5. Present the Conversion Plan and STOP for confirmation

Present a written Conversion Plan to the user, following the Conversion Plan
contents defined in `{{LTP_AGENT_DIR}}/rules/conversion-strategy.md`. Do NOT
modify any file before the user approves it.

ALWAYS wait for user confirmation before proceeding. Accept: proceed / adjust
/ skip. On "adjust", revise the plan and present it again. On "skip", stop
here. Only on "proceed" continue to the next step.

## 6. Design the New Test

Design the new test to satisfy every item of the approved Intent Contract,
applying the chosen strategy. For a semantic rewrite, start ONLY from the
Intent Contract and do NOT reference the old code's structure. For a faithful
port, keep the original structure and ordering. Decide:

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

## 7. Implement

Write the new test from the design above, following all rules in
`{{LTP_AGENT_DIR}}/rules/c-tests.md`,
`{{LTP_AGENT_DIR}}/rules/ground-rules.md`, and the high-level
description block rules in `{{LTP_AGENT_DIR}}/rules/documentation.md`
(section 4).

Implement every scenario and every pass/fail oracle in the Intent Contract.
You MAY drop only the features on the approved droppable list, nothing else.

Apply the chosen strategy following its implementation rules (and the rules
for both strategies) in `{{LTP_AGENT_DIR}}/rules/conversion-strategy.md`.

### Helper Conversion

If the file is a helper, follow the `TST_NO_DEFAULT_MAIN` section in
`{{LTP_AGENT_DIR}}/rules/c-tests.md`. Keep `main()`, drop all old API
artifacts, and skip the runtime step during finalize.

### Makefile updates

If the conversion adds, removes, or renames test binaries, or changes
linked libraries, update `<dir>/Makefile` accordingly and verify it
against `{{LTP_AGENT_DIR}}/rules/build-system.md`. Drop manual `-lltp`,
prefer per-target `LDLIBS +=`, and keep the standard template intact.
