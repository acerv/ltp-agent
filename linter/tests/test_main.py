"""
Tests for main module: run() entry point.
"""

import os
import tempfile
from unittest.mock import patch

import main
import pytest

GOOD_FILE = """\
// SPDX-License-Identifier: GPL-2.0-or-later
/*\\
 * Copyright (c) 2024 SUSE LLC
 * Author: Test User
 */
#include "tst_test.h"

static void run(void) {}

static struct tst_test test = {
    .test = run,
};
"""

BAD_FILE = """\
// no spdx
#include "test.h"
int main(void) {
    sleep(1);
}
"""


class TestRunFileMode:
    """
    Tests for the -f/--file mode.
    """

    def test_clean_file_exits_zero(self, monkeypatch, capsys):
        """
        Verify exit code 0 when no findings are produced.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as fh:
            fh.write(GOOD_FILE)
            path = fh.name

        try:
            monkeypatch.setattr("sys.argv", ["ltp-linter", "-f", path])
            with pytest.raises(SystemExit) as exc:
                main.run()
            assert exc.value.code == 0
            assert capsys.readouterr().out == ""
        finally:
            os.unlink(path)

    def test_bad_file_exits_one(self, monkeypatch, capsys):
        """
        Verify exit code 1 and printed findings for a bad file.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as fh:
            fh.write(BAD_FILE)
            path = fh.name

        try:
            monkeypatch.setattr("sys.argv", ["ltp-linter", "-f", path])
            with pytest.raises(SystemExit) as exc:
                main.run()
            assert exc.value.code == 1

            output = capsys.readouterr().out
            assert path in output
            assert "Missing SPDX header" in output
        finally:
            os.unlink(path)


class TestRunBranchMode:
    """
    Tests for the -b/--branch mode.
    """

    def test_branch_lints_changed_files(self, monkeypatch, capsys):
        """
        Verify that -b lints files returned by repo.changed_files().
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as fh:
            fh.write(BAD_FILE)
            path = fh.name

        try:
            monkeypatch.setattr("sys.argv", ["ltp-linter", "-b"])
            with patch("main.repo.changed_files", return_value=[path]):
                with pytest.raises(SystemExit) as exc:
                    main.run()

            assert exc.value.code == 1
            output = capsys.readouterr().out
            assert path in output
        finally:
            os.unlink(path)

    def test_branch_no_changed_files(self, monkeypatch, capsys):
        """
        Verify exit code 0 when no C files changed on the branch.
        """
        monkeypatch.setattr("sys.argv", ["ltp-linter", "-b"])
        with patch("main.repo.changed_files", return_value=[]):
            with pytest.raises(SystemExit) as exc:
                main.run()

        assert exc.value.code == 0
        assert capsys.readouterr().out == ""

    def test_branch_clean_files(self, monkeypatch, capsys):
        """
        Verify exit code 0 when all changed files are clean.
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as fh:
            fh.write(GOOD_FILE)
            path = fh.name

        try:
            monkeypatch.setattr("sys.argv", ["ltp-linter", "-b"])
            with patch("main.repo.changed_files", return_value=[path]):
                with pytest.raises(SystemExit) as exc:
                    main.run()

            assert exc.value.code == 0
        finally:
            os.unlink(path)


class TestArgParsing:
    """
    Tests for argument parsing and mutual exclusivity.
    """

    def test_no_arguments_exits_error(self, monkeypatch):
        """
        Verify that omitting both -f and -b causes an error.
        """
        monkeypatch.setattr("sys.argv", ["ltp-linter"])
        with pytest.raises(SystemExit) as exc:
            main.run()
        assert exc.value.code != 0

    def test_both_file_and_branch_exits_error(self, monkeypatch):
        """
        Verify that passing both -f and -b causes an error.
        """
        monkeypatch.setattr("sys.argv", ["ltp-linter", "-f", "foo.c", "-b"])
        with pytest.raises(SystemExit) as exc:
            main.run()
        assert exc.value.code != 0
