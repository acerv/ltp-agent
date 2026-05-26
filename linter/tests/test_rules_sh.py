"""
Tests for rules_sh module: shell test linter rules.
"""

from rules_sh import (
    check_copyright,
    check_doc_block,
    check_env_block,
    check_no_arrays,
    check_no_double_bracket,
    check_no_function_keyword,
    check_no_process_substitution,
    check_shebang,
    check_spdx,
    check_tst_run_last,
)

LTP_FRAMEWORK = ". tst_test.sh\n"


class TestCheckShebang:
    """
    Tests for the shebang rule.
    """

    def test_correct_shebang(self):
        """
        Verify no finding for correct #!/bin/sh.
        """
        lines = ["#!/bin/sh\n", LTP_FRAMEWORK]
        assert list(check_shebang(lines)) == []

    def test_wrong_shebang(self):
        """
        Verify finding for #!/bin/bash in LTP test.
        """
        lines = ["#!/bin/bash\n", LTP_FRAMEWORK]
        results = list(check_shebang(lines))
        assert len(results) == 1
        assert "#!/bin/sh" in results[0][1]

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts without LTP
        framework.
        """
        lines = ["#!/bin/bash\n", "echo hello\n"]
        assert list(check_shebang(lines)) == []


class TestCheckSpdx:
    """
    Tests for the shell SPDX header rule.
    """

    def test_spdx_on_second_line(self):
        """
        Verify no finding when SPDX is on the second line.
        """
        lines = [
            "#!/bin/sh\n",
            "# SPDX-License-Identifier: GPL-2.0-or-later\n",
            LTP_FRAMEWORK,
        ]
        assert list(check_spdx(lines)) == []

    def test_missing_spdx(self):
        """
        Verify finding when SPDX is missing in LTP test.
        """
        lines = ["#!/bin/sh\n", "# some comment\n", LTP_FRAMEWORK]
        results = list(check_spdx(lines))
        assert len(results) == 1

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts.
        """
        lines = ["#!/bin/sh\n", "# no spdx\n"]
        assert list(check_spdx(lines)) == []


class TestCheckCopyright:
    """
    Tests for the shell copyright rule.
    """

    def test_present(self):
        """
        Verify no finding when copyright is present.
        """
        lines = [
            "#!/bin/sh\n",
            "# Copyright (c) 2024 SUSE LLC\n",
            LTP_FRAMEWORK,
        ]
        assert list(check_copyright(lines)) == []

    def test_missing(self):
        """
        Verify finding when copyright is absent in LTP test.
        """
        lines = ["#!/bin/sh\n", "# no copyright\n", LTP_FRAMEWORK]
        results = list(check_copyright(lines))
        assert len(results) == 1

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts.
        """
        lines = ["#!/bin/sh\n", "# no copyright\n"]
        assert list(check_copyright(lines)) == []


class TestCheckDocBlock:
    """
    Tests for the doc block rule.
    """

    def test_present(self):
        """
        Verify no finding when doc block exists.
        """
        lines = [
            "# ---\n",
            "# doc\n",
            "# Some description.\n",
            "# ---\n",
            ". tst_run.sh\n",
        ]
        assert list(check_doc_block(lines)) == []

    def test_missing(self):
        """
        Verify finding when doc block is absent in new API test.
        """
        lines = ["#!/bin/sh\n", "# just a comment\n", ". tst_run.sh\n"]
        results = list(check_doc_block(lines))
        assert len(results) == 1
        assert "doc" in results[0][1]

    def test_skipped_for_old_api(self):
        """
        Verify no finding for old API tests (tst_run without dot).
        """
        lines = ["#!/bin/sh\n", ". tst_test.sh\n", "tst_run\n"]
        assert list(check_doc_block(lines)) == []


class TestCheckEnvBlock:
    """
    Tests for the env block rule.
    """

    def test_present(self):
        """
        Verify no finding when env block exists.
        """
        lines = [
            "# ---\n",
            "# env\n",
            "# {}\n",
            "# ---\n",
            ". tst_run.sh\n",
        ]
        assert list(check_env_block(lines)) == []

    def test_missing(self):
        """
        Verify finding when env block is absent in new API test.
        """
        lines = ["#!/bin/sh\n", "# no env\n", ". tst_run.sh\n"]
        results = list(check_env_block(lines))
        assert len(results) == 1
        assert "env" in results[0][1]

    def test_skipped_for_old_api(self):
        """
        Verify no finding for old API tests (tst_run without dot).
        """
        lines = ["#!/bin/sh\n", ". tst_test.sh\n", "tst_run\n"]
        assert list(check_env_block(lines)) == []


class TestCheckTstRunLast:
    """
    Tests for the tst_run last line rule.
    """

    def test_new_api(self):
        """
        Verify no finding when last line is . tst_run.sh (new API).
        """
        lines = ["#!/bin/sh\n", ". tst_run.sh\n"]
        assert list(check_tst_run_last(lines)) == []

    def test_old_api(self):
        """
        Verify no finding when last line is tst_run (old API).
        """
        lines = ["#!/bin/sh\n", ". tst_test.sh\n", "tst_run\n"]
        assert list(check_tst_run_last(lines)) == []

    def test_wrong_last_line(self):
        """
        Verify finding when last line is not tst_run in LTP test.
        """
        lines = [
            "#!/bin/sh\n",
            ". tst_test.sh\n",
            "echo done\n",
        ]
        results = list(check_tst_run_last(lines))
        assert len(results) == 1
        assert "tst_run" in results[0][1]

    def test_trailing_empty_lines(self):
        """
        Verify correct check when trailing empty lines exist.
        """
        lines = ["#!/bin/sh\n", ". tst_run.sh\n", "\n", "\n"]
        assert list(check_tst_run_last(lines)) == []

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts.
        """
        lines = ["#!/bin/sh\n", "echo done\n"]
        assert list(check_tst_run_last(lines)) == []


class TestCheckNoDoubleBracket:
    """
    Tests for the [[ ]] bash-ism rule.
    """

    def test_double_bracket(self):
        """
        Verify finding for [[ ]] usage in LTP test.
        """
        lines = [LTP_FRAMEWORK, '\tif [[ "$var" == "val" ]]; then\n']
        results = list(check_no_double_bracket(lines))
        assert len(results) == 1
        assert "[ ]" in results[0][1]

    def test_single_bracket(self):
        """
        Verify no finding for [ ] usage.
        """
        lines = [LTP_FRAMEWORK, '\tif [ "$var" = "val" ]; then\n']
        assert list(check_no_double_bracket(lines)) == []

    def test_comment_skipped(self):
        """
        Verify that [[ in comments is ignored.
        """
        lines = [LTP_FRAMEWORK, "# if [[ foo ]]; then\n"]
        assert list(check_no_double_bracket(lines)) == []

    def test_posix_char_class(self):
        """
        Verify that POSIX character classes [[:space:]] are not flagged.
        """
        lines = [LTP_FRAMEWORK, 'check="^10[0-9][[:space:]]"\n']
        assert list(check_no_double_bracket(lines)) == []

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts.
        """
        lines = ['if [[ "$var" == "val" ]]; then\n']
        assert list(check_no_double_bracket(lines)) == []


class TestCheckNoFunctionKeyword:
    """
    Tests for the function keyword bash-ism rule.
    """

    def test_function_keyword(self):
        """
        Verify finding for function keyword in LTP test.
        """
        lines = [LTP_FRAMEWORK, "function setup {\n"]
        results = list(check_no_function_keyword(lines))
        assert len(results) == 1
        assert "name() {" in results[0][1]

    def test_posix_function(self):
        """
        Verify no finding for POSIX function syntax.
        """
        lines = [LTP_FRAMEWORK, "setup()\n", "{\n"]
        assert list(check_no_function_keyword(lines)) == []

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts.
        """
        lines = ["function setup {\n"]
        assert list(check_no_function_keyword(lines)) == []


class TestCheckNoProcessSubstitution:
    """
    Tests for the process substitution bash-ism rule.
    """

    def test_process_substitution(self):
        """
        Verify finding for <() usage in LTP test.
        """
        lines = [LTP_FRAMEWORK, "\tdiff <(cmd1) <(cmd2)\n"]
        results = list(check_no_process_substitution(lines))
        assert len(results) == 1

    def test_normal_redirect(self):
        """
        Verify no finding for normal redirects.
        """
        lines = [LTP_FRAMEWORK, "\tcmd > file\n"]
        assert list(check_no_process_substitution(lines)) == []

    def test_comment_skipped(self):
        """
        Verify that process substitution in comments is ignored.
        """
        lines = [LTP_FRAMEWORK, "# diff <(cmd1) <(cmd2)\n"]
        assert list(check_no_process_substitution(lines)) == []

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts.
        """
        lines = ["\tdiff <(cmd1) <(cmd2)\n"]
        assert list(check_no_process_substitution(lines)) == []


class TestCheckNoArrays:
    """
    Tests for the array bash-ism rule.
    """

    def test_array_detected(self):
        """
        Verify finding for bash array syntax in LTP test.
        """
        lines = [LTP_FRAMEWORK, "arr=(one two three)\n"]
        results = list(check_no_arrays(lines))
        assert len(results) == 1

    def test_no_array(self):
        """
        Verify no finding for normal assignments.
        """
        lines = [LTP_FRAMEWORK, 'var="value"\n']
        assert list(check_no_arrays(lines)) == []

    def test_comment_skipped(self):
        """
        Verify that arrays in comments are ignored.
        """
        lines = [LTP_FRAMEWORK, "# arr=(one two)\n"]
        assert list(check_no_arrays(lines)) == []

    def test_standalone_skipped(self):
        """
        Verify no finding for standalone scripts.
        """
        lines = ["arr=(one two three)\n"]
        assert list(check_no_arrays(lines)) == []
