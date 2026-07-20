<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Conversion Strategy Selection

When converting an LTP test from the old API (`test.h`) to the new API
(`tst_test.h`), there is no single correct shape. Two conversion strategies
are possible. This file defines both strategies and how to choose between
them.

The strategy decision MUST be made for EVERY old-API test being converted.
It is NOT reserved for special cases such as reproducers or CVE tests. Both
strategies MUST be evaluated for every test, and the winner MUST be chosen
with an explicit written justification.

This file is the single source of truth for the conversion contract: the
Intent Contract, the strategy decision, and the Conversion Plan presented to
the user.

## The Intent Contract

The Intent Contract is a punctual, enumerated checklist (NOT a prose summary)
that captures the original test's intent with zero loss. It is the single
source of truth carried through analysis, implementation, and review. Missing
an item here means the converted test can silently lose intent, which is
forbidden. It MUST record:

1. Target: the syscall / feature / behavior under test.
2. Scenarios: EVERY distinct scenario (each assertion or test case),
   enumerated and numbered. Omit none.
3. Algorithm: per scenario, the step-by-step actions the test performs.
4. Oracle: per scenario, the exact pass/fail condition (expected return
   value, expected errno, expected side effect, or, for a reproducer, the
   crash / corruption / leak the source demonstrates). "Runs to completion"
   is NOT an oracle; find the real one.
5. Resources: tmpdir, root, fork, device, kconfigs, min_kver, network, IPC,
   arch constraints, etc.
6. Setup/teardown: files, signals, mounts, IPC, sysctl, loop devices, etc.
7. Subtle behavior a rewrite could silently drop: exact ordering, timing/race
   windows, a signal delivered mid-syscall, an ordering-dependent side effect.

   The `-i` (iteration), `-v` (verbose), `--variant`, `-h`/`--help`, and `-I`
   (loop-output) options are NOT subtle behavior to capture here. They are
   provided natively by the new API through `struct tst_test` fields and the
   framework-driven `.setup` / `.test` / `.cleanup` lifecycle (see
   `c-tests.md` section 3). The Intent Contract MUST NOT list them as
   scenarios, oracles, or items to preserve; they are wiring, not intent.

## Framework-provided behavior (do NOT reimplement)

The old API required the test to hand-roll machinery the new API supplies
natively. Both the analyzer and the creator MUST treat that machinery as
scaffolding to drop, never as behavior to port or preserve.

The following are provided by the new API and MUST NOT be reimplemented, no
matter which strategy is chosen (the analyzer MUST NOT enumerate them in the
Intent Contract; the creator MUST wire them to framework fields and trust the
framework; the reviewer MUST flag any hand-rolled survival):

- Iteration count: old API ran the test body in a manual `for` loop, often
  driven by `tst_parse_opts()`/`getopt` for `-i`. New API: the framework
  calls `.test` / `.test_all` for each iteration automatically; the `-i`
  option is parsed and applied by the library. The test only has to keep
  per-iteration state re-entrant (see `ground-rules.md` and `c-tests.md`
  section 12).
- Verbosity: old API tests printed their own debug lines or wrapped
  `tst_resm()`. New API: `TDEBUG` messages and the `-v` flag are handled by
  the library; the test emits `tst_res(TPASS/TFAIL/TINFO, ...)` and
  `tst_brk(...)` and the framework controls verbosity.
- Multiple test cases: old API used a manual dispatcher table or a `for`
  loop over a `TCID * TST_TOTAL` matrix. New API: declare a `struct tcase`
  array and set `.test` + `.tcnt` (or let `.test_all` iterate inline). The
  framework advances the case counter and reports case names.
- Help / usage: old API tests implemented `usage()` and parsed `-h`. New API:
  the library prints usage from `struct tst_test` automatically.
- Test identity / totals: old API required `TCID` and `TST_TOTAL` globals and
  `tst_init()`. New API: identity and totals are derived from
  `struct tst_test` and the registered cases.
- Option parsing boilerplate: old API tests called `tst_parse_opts()` and
  walked `optarg`. New API: `struct tst_test` fields (`.needs_root`,
  `.needs_tmpdir`, `.needs_kconfigs`, `.min_kver`, `.supported_archs`,
  `.save_restore`, `.tags`, etc.) and any custom options are declared, not
  parsed by hand.

In a faithful port, the test logic, control flow, and ordering are preserved;
the option-parsing, loop-driving, and verbose-printing scaffolding above are
still dropped and replaced by the framework-supplied equivalents. Keeping
that scaffolding is NOT a faithful port, it is an unmaintained hybrid.

## The two strategies

### Strategy A: Semantic rewrite

Extract WHAT the test does, discard the old implementation, and write a clean
new test using modern new-API idioms.

- Uses `struct tcase` arrays, `.test` + `.tcnt` or `.test_all`.
- Uses `TST_EXP_*` assertion macros.
- Uses framework features (`.needs_root`, `.needs_tmpdir`, `.save_restore`,
  `.forks_child`, checkpoints) instead of hand-rolled equivalents.
- Drops old-API artifacts: error-accumulation flags, forward declarations,
  per-test-case function pointers, helper functions that only existed to work
  around old-API limits.
- MUST NOT use the old code as a structural template, transliterate it
  token-by-token, or keep its control flow; reorder functions so callees
  precede callers.

Best when the test maps cleanly onto new-API idioms and a rewrite makes the
intent clearer without risking any behavior.

### Strategy B: Faithful port

Preserve the original test's structure, control flow, and ordering, swapping
old-API calls for their new-API equivalents with minimal restructuring.

- Keeps the original sequence of operations and function layout where possible.
- Still MUST use `SAFE_*` macros, `tst_res()` / `tst_brk()`, and a valid
  `struct tst_test`; a faithful port is NOT a license to keep broken patterns.
- Keeps the result easy to diff and verify against the original source.

Best when exact sequencing, timing, or ordering carries test meaning that a
rewrite could silently lose.

### Rules for both strategies

Regardless of the chosen strategy, the converted test MUST:

- Let the framework handle iterations: the `-i` option is parsed and applied
  by the library; `.test` / `.test_all` is re-entered per iteration. The test
  body only has to keep per-iteration state re-entrant.
- Let the framework handle verbosity: `TDEBUG` messages and the `-v` flag
  are provided by the library; the test emits `tst_res()` / `tst_brk()` and
  does not print its own debug plumbing.
- Drop old-API scaffolding for option parsing, loop driving, usage printing,
  `TCID` / `TST_TOTAL` bookkeeping, and hand-rolled multi-case dispatch
  (see "Framework-provided behavior" above). These are NOT preserved, they
  are replaced by `struct tst_test` fields.
- Keep the original copyright if it is not GPL-2 compatible.
- Release resources on all exit paths using framework callbacks and static
  state.

## Selection criteria

Evaluate BOTH strategies for the test against ALL of the following, then pick
the winner. These criteria are neutral and apply to every test:

1. Intent fidelity risk: does either strategy risk dropping or weakening any
   scenario, pass/fail oracle, side-effect check, or exact errno check?
2. Coverage preservation: can every original scenario be represented in the
   target structure without loss?
3. Sequencing and timing sensitivity: does the test depend on the exact order
   or timing of operations (e.g. a race window, a signal delivered mid-call,
   an ordering-dependent side effect)?
4. Clarity and idiomatic fit: which result is clearer and more idiomatic in
   the new API?
5. Maintainability vs diffability: a semantic rewrite is cleaner long-term; a
   faithful port is easier to verify against the original.
6. Size and artifact cruft: how much old-API-only scaffolding exists, and how
   much does each strategy remove or retain?

Reproducers and CVE tests are only one example of tests where sequencing and
timing sensitivity (criterion 3) may dominate. They do NOT automatically force
strategy B; run the full evaluation like any other test.

## The overriding rule

Intent fidelity overrides every other criterion. Neither strategy may drop or
weaken any scenario or pass/fail oracle recorded in the Intent Contract. If a
strategy cannot preserve the full Intent Contract, it MUST NOT be chosen,
regardless of how it scores on clarity, idiom, or diffability.

## Tie-breaker

When both strategies preserve the full Intent Contract and score equally on
the remaining criteria, prefer Strategy A (semantic rewrite), because it
matches LTP's long-term direction. The justification MUST state that the
choice was made on the tie-breaker.

## Required output of the decision

The strategy decision MUST record, in writing:

- The chosen strategy (A or B).
- A justification referencing the criteria above.
- What the rejected strategy would have cost (what would be lost, harder, or
  riskier).
- Confirmation that the chosen strategy preserves the full Intent Contract.

## The Conversion Plan

Before any file is modified, the conversion MUST present a written Conversion
Plan and stop for the user to confirm it. The plan MUST contain:

1. Intent Contract: the full enumerated scenarios and pass/fail oracles.
2. Chosen strategy: with justification and the cost of the rejected strategy
   (the strategy decision output above).
3. Droppable features: everything proposed to be dropped, each with a reason,
   called out explicitly for sign-off. Never place a real scenario or oracle
   here.
4. Target test structure: `.test` + `.tcnt` vs `.test_all`, `struct tcase`
   layout, chosen `TST_EXP_*` macros.
5. Framework features: `.needs_root`, `.needs_tmpdir`, `.forks_child`,
   `.save_restore`, `.min_kver`, `.supported_archs`, etc.
6. Resource lifecycle: setup/cleanup responsibilities, static state,
   synchronization mechanism.
7. Makefile / runtest impact: any build or runtest entry changes.
8. Recommendation: Convert / Convert with reservations (explain) / Recommend
   skip (explain and suggest an alternative).
