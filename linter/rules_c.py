"""
.. module:: rules_c
    :platform: Linux
    :synopsis: C test linter rules
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import re

from core import rule


@rule("Missing SPDX header")
def check_spdx(lines):
    """
    Check that the first line contains an SPDX license identifier.
    """
    if not lines or "SPDX-License-Identifier" not in lines[0]:
        yield 1, "first line must contain SPDX-License-Identifier"


@rule("Missing copyright")
def check_copyright(lines):
    """
    Check that a Copyright line with a year is present.
    """
    for line in lines:
        if re.search(r"Copyright\s.*\d{4}", line, re.IGNORECASE):
            return

    yield 1, "no Copyright line with year found"


@rule("Missing doc comment block", scope="c_only")
def check_doc_comment(lines):
    """
    Check that a doc comment block (/*\\) is present.
    """
    for line in lines:
        if line.rstrip() == "/*\\n" or line.rstrip() == "/*\\":
            return
        if re.match(r"\s*/\*\\", line):
            return

    yield 1, "no doc comment block (/*\\) found"


@rule("Deprecated [Description] tag")
def check_description_tag(lines):
    """
    Flag any use of the deprecated [Description] tag in doc comments.
    """
    for line_num, line in enumerate(lines, 1):
        if "[Description]" in line:
            yield line_num, "[Description] is deprecated, use a plain comment"


@rule("Wrong test header")
def check_tst_test_header(lines):
    """
    Check that tst_test.h is used instead of the legacy test.h.
    """
    has_old = False
    has_new = False

    for line_num, line in enumerate(lines, 1):
        if re.match(r'^\s*#\s*include\s*[<"]test\.h[>"]', line):
            has_old = True
        if re.match(r'^\s*#\s*include\s*[<"]tst_test\.h[>"]', line):
            has_new = True

    if has_old and not has_new:
        yield 1, 'use #include "tst_test.h" instead of #include "test.h"'


@rule("Unexpected main() definition", scope="c_only")
def check_no_main(lines):
    """
    Flag main() definitions when TST_NO_DEFAULT_MAIN is not set.
    """
    has_no_default = any("TST_NO_DEFAULT_MAIN" in line for line in lines)
    if has_no_default:
        return

    for line_num, line in enumerate(lines, 1):
        if re.match(r"^(int|void)\s+main\s*\(", line):
            yield line_num, "define struct tst_test instead of main()"


@rule("Missing struct tst_test", scope="c_only")
def check_struct_tst_test(lines):
    """
    Check that struct tst_test is defined, unless TST_NO_DEFAULT_MAIN is set.
    """
    for line in lines:
        if "struct tst_test" in line:
            return

    has_no_default = any("TST_NO_DEFAULT_MAIN" in line for line in lines)
    if has_no_default:
        return

    yield 1, "no struct tst_test found"


@rule("FD not initialized to -1")
def check_fd_init(lines):
    """
    Flag static file descriptor declarations that are not initialized to -1.
    Uninitialized static ints default to 0, which is a valid fd (stdin).
    """
    pattern = re.compile(r"^static\s+int\s+(\w*fd\w*)\s*;")

    for line_num, line in enumerate(lines, 1):
        match = pattern.search(line)
        if not match:
            continue

        yield (
            line_num,
            (f"initialize {match.group(1)} to -1, not 0 (0 is a valid fd — stdin)"),
        )


@rule("Wrong FD validity check")
def check_fd_validity(lines):
    """
    Flag fd >= 0 or fd > 0 checks. LTP convention is fd != -1 to match
    the -1 initialization.
    """
    pattern = re.compile(r"\b(\w*fd\w*)\s*(>=\s*0|>\s*0)\b")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        match = pattern.search(line)
        if not match:
            continue

        yield (
            line_num,
            (
                f"use {match.group(1)} != -1 instead of"
                f" {match.group(1)} {match.group(2).strip()}"
                " (matches the -1 initialization convention)"
            ),
        )


@rule("Redundant fd reset after SAFE_CLOSE")
def check_fd_reset_after_safe_close(lines):
    """
    Flag manual fd = -1 after SAFE_CLOSE(). SAFE_CLOSE() already sets
    the fd to -1 internally.
    """
    safe_close_re = re.compile(r"SAFE_CLOSE\(\s*(\w+)\s*\)")

    for line_num, line in enumerate(lines, 1):
        match = safe_close_re.search(line)
        if not match:
            continue

        if line_num >= len(lines):
            continue

        fd_name = match.group(1)
        if re.match(rf"^{re.escape(fd_name)}\s*=\s*-1\s*;$", lines[line_num].strip()):
            yield (
                line_num + 1,
                (f"{fd_name} = -1 is redundant — SAFE_CLOSE() already resets it to -1"),
            )


@rule("HAVE_* guard inside function")
def check_have_guard_placement(lines):
    """
    Flag #ifdef HAVE_* guards inside functions. They must wrap all test
    code at file level, with TST_TEST_TCONF() in the #else branch.
    """
    brace_depth = 0

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        brace_depth += stripped.count("{") - stripped.count("}")
        if brace_depth > 0 and re.match(r"#\s*if(?:def)?\s+.*HAVE_", stripped):
            yield (
                line_num,
                (
                    "move #ifdef HAVE_* to file level wrapping all test code"
                    " and use TST_TEST_TCONF() in the #else branch"
                ),
            )


@rule("Missing .needs_tmpdir", scope="c_only")
def check_needs_tmpdir(lines):
    """
    Flag tests that create files (SAFE_OPEN, SAFE_CREAT, SAFE_FILE_PRINTF,
    etc. with create-like arguments) without setting .needs_tmpdir = 1 in
    struct tst_test.
    """
    create_re = re.compile(r"\b(SAFE_CREAT|SAFE_TOUCH)\s*\(")
    open_create_re = re.compile(r"\bSAFE_OPEN\s*\(.*O_CREAT")

    has_tmpdir = any(".needs_tmpdir" in line for line in lines)
    has_mntpoint = any(".mntpoint" in line for line in lines)
    has_device = any(".needs_device" in line for line in lines)

    if has_tmpdir or has_mntpoint or has_device:
        return

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        if create_re.search(line) or open_create_re.search(line):
            yield (
                line_num,
                "test creates files — set .needs_tmpdir = 1 in struct tst_test",
            )
            return


@rule("Legacy cleanup_fn parameter")
def check_cleanup_fn_param(lines):
    """
    Flag safe_* function definitions that include a cleanup_fn parameter.
    The new LTP API does not use cleanup function pointers; use tst_brk_()
    instead of tst_brkm_().
    """
    pattern = re.compile(r"\bsafe_\w+\s*\(.*cleanup_fn")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        if pattern.search(line):
            yield (
                line_num,
                (
                    "cleanup_fn parameter is legacy API — use tst_brk_()"
                    " instead of tst_brkm_() and remove cleanup_fn"
                ),
            )


@rule("Raw syscall() instead of tst_syscall()")
def check_tst_syscall(lines):
    """
    Flag plain syscall() calls. Use tst_syscall() which automatically
    checks for ENOSYS.
    """
    pattern = re.compile(r"(?<!\w)syscall\s*\(")
    exempt_re = re.compile(r"\b(TEST|TST_EXP_\w+)\s*\(")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        if exempt_re.search(line):
            continue

        if "tst_syscall" in line:
            continue

        if pattern.search(line):
            yield (
                line_num,
                (
                    "use tst_syscall() instead of raw syscall() —"
                    " tst_syscall() automatically handles ENOSYS"
                ),
            )


@rule("Missing .supported_archs", scope="c_only")
def check_supported_archs(lines):
    """
    Flag #if defined(__arch__) guards when .supported_archs should be
    used in struct tst_test instead (for architectures supported by
    the framework).
    """
    arch_re = re.compile(
        r"#\s*if.*defined\s*\(\s*__("
        r"x86_64|i386|aarch64|arm|ppc64|ppc|s390x|s390"
        r")__\s*\)"
    )
    has_supported_archs = any(".supported_archs" in line for line in lines)
    if has_supported_archs:
        return

    for line_num, line in enumerate(lines, 1):
        if arch_re.search(line):
            yield (
                line_num,
                (
                    "use .supported_archs in struct tst_test instead of"
                    " #if defined(__arch__) preprocessor guards"
                ),
            )
            return


@rule("Use exit() instead of _exit() in child blocks")
def check_exit_in_child(lines):
    """
    Flag _exit() in forked child blocks. LTP requires exit() so the
    framework can propagate tst_res() results from child to parent.
    """
    pattern = re.compile(r"\b_exit\s*\(")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        if pattern.search(line):
            yield (
                line_num,
                "use exit() instead of _exit() — _exit() bypasses "
                "LTP result propagation from child to parent",
            )


_TYPE_TOKEN_RE = (
    r"(?:static|inline|extern|const|unsigned|signed|volatile|register|"
    r"struct|union|enum|void|int|char|short|long|float|double|bool|"
    r"FILE|DIR|\w+_t)"
)


@rule("Identifier starts with underscore")
def check_underscore_identifier(lines):
    """
    Flag function definitions and prototypes whose name starts with an
    underscore. Per the C standard, leading-underscore identifiers are
    reserved for the implementation (compiler, libc, kernel headers), so
    user code MUST NOT define them.

    Scope is intentionally narrow:

      - Only function definitions/prototypes at column 0, e.g.
            static void _helper(void)
            int _foo(int);
            static char *_buf(void)

      - ``extern`` declarations are skipped: they declare a symbol
        provided by libc/the kernel, not a user definition.

      - ``#define`` and variable declarations are not checked. Macro
        usage is dominated by legitimate cases (feature test macros
        like ``_GNU_SOURCE``, include guards, and ``__NR_*`` syscall
        fallbacks per the ``include/lapi/`` pattern) that cannot be
        distinguished from real violations without semantic analysis.
        The reviewer agent handles those by reading c-tests.md.
    """
    func_re = re.compile(
        rf"^(?:{_TYPE_TOKEN_RE}\s+)+\*?\s*(_\w+)\s*\("
    )

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith(("//", "*", "/*", "#")):
            continue

        # extern declarations expose libc/kernel-provided symbols.
        if re.match(r"^extern\b", line):
            continue

        # __attribute__((...)) is a gcc extension being *used*, not defined.
        if "__attribute__" in line:
            continue

        match = func_re.match(line)
        if match:
            yield (
                line_num,
                (
                    f"{match.group(1)} starts with underscore — "
                    "reserved for compiler/libc/kernel"
                ),
            )


@rule("Missing .needs_kconfigs", scope="c_only")
def check_needs_kconfigs(lines):
    """
    Flag manual kernel config checks at runtime (TCONF with CONFIG_ in
    the message) when .needs_kconfigs should be used instead.
    """
    has_needs_kconfigs = any(".needs_kconfigs" in line for line in lines)
    if has_needs_kconfigs:
        return

    pattern = re.compile(r"\b(tst_brk|tst_res)\s*\(\s*TCONF\b.*CONFIG_")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        if pattern.search(line):
            yield (
                line_num,
                (
                    "use .needs_kconfigs in struct tst_test instead of"
                    " manual runtime kernel config checks"
                ),
            )
            return
