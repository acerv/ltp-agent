"""
Tests for repo module: git helpers.
"""

from unittest.mock import MagicMock, patch

import repo


class TestChangedFiles:
    """
    Tests for the changed_files() function.
    """

    @patch("repo.subprocess.run")
    def test_returns_changed_c_files(self, mock_run):
        """
        Verify that changed C file paths are returned.
        """
        mock_run.return_value = MagicMock(
            stdout="testcases/kernel/foo.c\ntestcases/kernel/bar.c\n"
        )

        result = repo.changed_files()

        assert result == [
            "testcases/kernel/foo.c",
            "testcases/kernel/bar.c",
        ]
        mock_run.assert_called_once_with(
            ["git", "diff", "--name-only", "master..HEAD", "--", "*.c", "*.h", "*.sh"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("repo.subprocess.run")
    def test_returns_empty_when_no_changes(self, mock_run):
        """
        Verify that an empty list is returned when no C files changed.
        """
        mock_run.return_value = MagicMock(stdout="")

        result = repo.changed_files()

        assert result == []

    @patch("repo.subprocess.run")
    def test_custom_base_branch(self, mock_run):
        """
        Verify that a custom base branch is passed to git diff.
        """
        mock_run.return_value = MagicMock(stdout="foo.c\n")

        repo.changed_files(base="develop")

        mock_run.assert_called_once_with(
            ["git", "diff", "--name-only", "develop..HEAD", "--", "*.c", "*.h", "*.sh"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("repo.subprocess.run")
    def test_whitespace_only_output(self, mock_run):
        """
        Verify that whitespace-only output returns an empty list.
        """
        mock_run.return_value = MagicMock(stdout="  \n")

        result = repo.changed_files()

        assert result == []
