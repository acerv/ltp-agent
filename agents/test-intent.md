<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Test Intent Extraction

This file defines the shared questionnaire for extracting a test's **intent**,
independent of API or framework details. Load it whenever a skill needs to
understand _what a test asserts about the kernel_ — for analysis, import, or
conversion. It is the single source of truth for these questions; skills MUST
reference it instead of restating them.

Answer each question, ignoring the source's API-level and framework details:

1. **What syscall / feature / behavior is being exercised?**
2. **What are the distinct scenarios?** Each assertion or test case.
3. **What is the algorithm?** Step-by-step what the test does (e.g. "fork a
   child, child calls `exit(1)`, parent waits, checks `WEXITSTATUS == 1`").
4. **What resources does it need?** tmpdir, root, fork, device, kconfigs,
   min_kver, network, IPC, etc.
5. **What setup/teardown is needed?** Files, signals, mounts, IPC, etc.
6. **What is the pass/fail oracle?** Expected return value, expected errno,
   expected side-effect. For a security/regression reproducer, the
   crash/corruption/leak the source demonstrates — not merely running to
   completion.
