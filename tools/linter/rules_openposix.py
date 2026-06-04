"""
.. module:: rules_openposix
    :platform: Linux
    :synopsis: Open POSIX test linter rules
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import re

from core import rule


@rule("Missing GPL license header", scope="openposix")
def check_gpl_header(lines):
    """
    Check that the GPL license header is present in the file.
    """
    for line in lines:
        if "licensed under the GPL license" in line:
            return
        if "GNU General Public License" in line:
            return
        if "SPDX-License-Identifier" in line and "GPL" in line:
            return

    yield 1, "GPL license header is missing"


@rule("Missing copyright", scope="openposix")
def check_copyright(lines):
    """
    Check that a copyright line with year is present.
    """
    for line in lines:
        if re.search(r"Copyright\s.*\d{4}", line, re.IGNORECASE):
            return

    yield 1, "no Copyright line with year found"


def _has_entry_point(lines):
    """
    Check whether the file defines test_main() or main().
    Build-only definition tests and helper files have neither.
    """
    for line in lines:
        if re.match(r"^int\s+(test_main|main)\s*\(", line):
            return True
    return False


@rule("Missing posixtest.h include", scope="openposix_only")
def check_posixtest_header(lines):
    """
    Check that posixtest.h is included. Also accepts testfrmw.h which
    includes posixtest.h transitively.
    """
    if not _has_entry_point(lines):
        return

    for line in lines:
        if re.match(r'^\s*#\s*include\s*[<"]posixtest\.h[>"]', line):
            return
        if re.search(r'#\s*include\s*[<"].*testfrmw\.h[>"]', line):
            return

    yield 1, 'must include "posixtest.h"'


@rule("Must use test_main(), not main()", scope="openposix_only")
def check_test_main(lines):
    """
    Check that test_main() is defined as the entry point instead of
    main(). The real main() is provided by lib/common.c.
    """
    has_test_main = False
    has_main = False
    main_line = 0

    for line_num, line in enumerate(lines, 1):
        if re.match(r"^int\s+test_main\s*\(", line):
            has_test_main = True

        if re.match(r"^int\s+main\s*\(", line):
            has_main = True
            main_line = line_num

    if has_main:
        yield (
            main_line,
            "define test_main() instead of main() — main() is provided by lib/common.c",
        )

    if not has_test_main and not has_main and _has_entry_point(lines):
        yield 1, "no test_main() entry point found"


@rule("Missing PTS return codes", scope="openposix_only")
def check_pts_return_codes(lines):
    """
    Check that at least one PTS return code is used (PTS_PASS,
    PTS_FAIL, PTS_UNRESOLVED, PTS_UNSUPPORTED, PTS_UNTESTED).
    """
    if not _has_entry_point(lines):
        return

    pts_codes = (
        "PTS_PASS",
        "PTS_FAIL",
        "PTS_UNRESOLVED",
        "PTS_UNSUPPORTED",
        "PTS_UNTESTED",
    )

    for line in lines:
        for code in pts_codes:
            if code in line:
                return

    yield 1, "no PTS return codes found (PTS_PASS, PTS_FAIL, etc.)"
