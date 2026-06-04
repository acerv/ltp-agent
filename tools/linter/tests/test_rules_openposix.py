"""
Tests for rules_openposix module: Open POSIX test linter rules.
"""

from rules_openposix import (
    check_copyright,
    check_gpl_header,
    check_posixtest_header,
    check_pts_return_codes,
    check_test_main,
)


class TestCheckGplHeader:
    """
    Tests for the GPL license header rule.
    """

    def test_present(self):
        """
        Verify no finding when GPL header is present.
        """
        lines = [
            " * This file is licensed under the GPL license.\n",
        ]
        assert list(check_gpl_header(lines)) == []

    def test_gnu_general_public(self):
        """
        Verify no finding when GNU General Public License is used.
        """
        lines = [
            " * under the terms of version 2 of the GNU General Public License as\n",
        ]
        assert list(check_gpl_header(lines)) == []

    def test_spdx_gpl(self):
        """
        Verify no finding when SPDX GPL identifier is present.
        """
        lines = [
            "// SPDX-License-Identifier: GPL-2.0-or-later\n",
        ]
        assert list(check_gpl_header(lines)) == []

    def test_missing(self):
        """
        Verify finding when GPL header is absent.
        """
        lines = ["#include <stdio.h>\n"]
        results = list(check_gpl_header(lines))
        assert len(results) == 1
        assert "GPL" in results[0][1]


class TestCheckCopyright:
    """
    Tests for the copyright rule.
    """

    def test_present(self):
        """
        Verify no finding when copyright with year is present.
        """
        lines = [
            " * Copyright (c) 2002, Intel Corporation. All rights reserved.\n",
        ]
        assert list(check_copyright(lines)) == []

    def test_without_paren_c(self):
        """
        Verify no finding when copyright has year but no (c).
        """
        lines = [" * Copyright 2024 SUSE LLC\n"]
        assert list(check_copyright(lines)) == []

    def test_missing(self):
        """
        Verify finding when copyright is absent.
        """
        lines = [" * Some comment\n"]
        results = list(check_copyright(lines))
        assert len(results) == 1

    def test_lowercase(self):
        """
        Verify case-insensitive match.
        """
        lines = [" * copyright (C) 2024, SUSE LLC\n"]
        assert list(check_copyright(lines)) == []


class TestCheckPosixtestHeader:
    """
    Tests for the posixtest.h include rule.
    """

    def test_present(self):
        """
        Verify no finding when posixtest.h is included.
        """
        lines = ['#include "posixtest.h"\n', "int test_main() {\n"]
        assert list(check_posixtest_header(lines)) == []

    def test_testfrmw_accepted(self):
        """
        Verify no finding when testfrmw.h is included (transitive).
        """
        lines = ['#include "testfrmw.h"\n', "int test_main() {\n"]
        assert list(check_posixtest_header(lines)) == []

    def test_testfrmw_relative_path(self):
        """
        Verify no finding when testfrmw.h is included via relative
        path.
        """
        lines = [
            '#include "../testfrmw/testfrmw.h"\n',
            "int test_main() {\n",
        ]
        assert list(check_posixtest_header(lines)) == []

    def test_missing(self):
        """
        Verify finding when posixtest.h is not included.
        """
        lines = ["#include <stdio.h>\n", "int test_main() {\n"]
        results = list(check_posixtest_header(lines))
        assert len(results) == 1
        assert "posixtest.h" in results[0][1]

    def test_no_entry_point_skipped(self):
        """
        Verify no finding for files without test_main() or main()
        (build-only definition tests, helper files).
        """
        lines = [
            "#include <aio.h>\n",
            "static void dummy() {\n",
            "}\n",
        ]
        assert list(check_posixtest_header(lines)) == []


class TestCheckTestMain:
    """
    Tests for the test_main() vs main() rule.
    """

    def test_correct_test_main(self):
        """
        Verify no finding when test_main() is defined.
        """
        lines = [
            "int test_main(int argc PTS_ATTRIBUTE_UNUSED,"
            " char **argv PTS_ATTRIBUTE_UNUSED)\n",
            "{\n",
        ]
        assert list(check_test_main(lines)) == []

    def test_main_instead(self):
        """
        Verify finding when main() is defined instead of test_main().
        """
        lines = ["int main(void)\n", "{\n"]
        results = list(check_test_main(lines))
        assert len(results) == 1
        assert "test_main()" in results[0][1]

    def test_no_entry_point_skipped(self):
        """
        Verify no finding for files without test_main() or main()
        (build-only definition tests, helper files).
        """
        lines = [
            "#include <signal.h>\n",
            "static void dummy() {\n",
            "}\n",
        ]
        assert list(check_test_main(lines)) == []


class TestCheckPtsReturnCodes:
    """
    Tests for the PTS return codes rule.
    """

    def test_pts_pass_present(self):
        """
        Verify no finding when PTS_PASS is used.
        """
        lines = ["\treturn PTS_PASS;\n"]
        assert list(check_pts_return_codes(lines)) == []

    def test_pts_fail_present(self):
        """
        Verify no finding when PTS_FAIL is used.
        """
        lines = ["\treturn PTS_FAIL;\n"]
        assert list(check_pts_return_codes(lines)) == []

    def test_pts_unresolved_present(self):
        """
        Verify no finding when PTS_UNRESOLVED is used.
        """
        lines = ["\treturn PTS_UNRESOLVED;\n"]
        assert list(check_pts_return_codes(lines)) == []

    def test_missing(self):
        """
        Verify finding when no PTS codes are used in a file with
        function bodies.
        """
        lines = ["int test_main() {\n", "\treturn 0;\n", "}\n"]
        results = list(check_pts_return_codes(lines))
        assert len(results) == 1
        assert "PTS_PASS" in results[0][1]

    def test_no_entry_point_skipped(self):
        """
        Verify no finding for files without test_main() or main()
        (build-only definition tests, helper files).
        """
        lines = [
            "#include <aio.h>\n",
            "static void dummy() {\n",
            "}\n",
        ]
        assert list(check_pts_return_codes(lines)) == []
