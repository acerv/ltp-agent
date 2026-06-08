"""
Tests for repo module: git helpers.
"""

from unittest.mock import MagicMock, call, patch

import repo


class TestMergeBase:
    """
    Tests for the _merge_base() helper.
    """

    @patch("repo.subprocess.run")
    def test_returns_merge_base_commit(self, mock_run):
        """
        Verify that _merge_base returns the trimmed merge-base SHA.
        """
        mock_run.return_value = MagicMock(stdout="abc123\n")

        result = repo._merge_base("master")

        assert result == "abc123"
        mock_run.assert_called_once_with(
            ["git", "merge-base", "master", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )


class TestChangedFiles:
    """
    Tests for the changed_files() function.
    """

    @patch("repo.subprocess.run")
    def test_returns_changed_c_files(self, mock_run):
        """
        Verify that changed C file paths are returned.
        """
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),
            MagicMock(stdout="testcases/kernel/foo.c\ntestcases/kernel/bar.c\n"),
        ]

        result = repo.changed_files()

        assert result == [
            "testcases/kernel/foo.c",
            "testcases/kernel/bar.c",
        ]
        assert mock_run.call_args_list == [
            call(
                ["git", "merge-base", "master", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ),
            call(
                [
                    "git",
                    "diff",
                    "--diff-filter=ACMR",
                    "--name-only",
                    "abc123..HEAD",
                    "--",
                    "*.c",
                    "*.h",
                    "*.sh",
                ],
                capture_output=True,
                text=True,
                check=True,
            ),
        ]

    @patch("repo.subprocess.run")
    def test_returns_empty_when_no_changes(self, mock_run):
        """
        Verify that an empty list is returned when no C files changed.
        """
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),
            MagicMock(stdout=""),
        ]

        result = repo.changed_files()

        assert result == []

    @patch("repo.subprocess.run")
    def test_custom_base_branch(self, mock_run):
        """
        Verify that a custom base branch is passed to git merge-base.
        """
        mock_run.side_effect = [
            MagicMock(stdout="def456\n"),
            MagicMock(stdout="foo.c\n"),
        ]

        repo.changed_files(base="develop")

        assert mock_run.call_args_list == [
            call(
                ["git", "merge-base", "develop", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ),
            call(
                [
                    "git",
                    "diff",
                    "--diff-filter=ACMR",
                    "--name-only",
                    "def456..HEAD",
                    "--",
                    "*.c",
                    "*.h",
                    "*.sh",
                ],
                capture_output=True,
                text=True,
                check=True,
            ),
        ]

    @patch("repo.subprocess.run")
    def test_whitespace_only_output(self, mock_run):
        """
        Verify that whitespace-only output returns an empty list.
        """
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),
            MagicMock(stdout="  \n"),
        ]

        result = repo.changed_files()

        assert result == []


class TestChangedLines:
    """
    Tests for the changed_lines() function.
    """

    @patch("repo.subprocess.run")
    def test_returns_changed_line_numbers(self, mock_run):
        """
        Verify that changed destination line numbers are parsed.
        """
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),
            MagicMock(
                stdout=(
                    "diff --git a/foo.c b/foo.c\n"
                    "--- a/foo.c\n"
                    "+++ b/foo.c\n"
                    "@@ -1 +1,2 @@\n"
                    "+line1\n"
                    "+line2\n"
                    "diff --git a/bar.sh b/bar.sh\n"
                    "--- a/bar.sh\n"
                    "+++ b/bar.sh\n"
                    "@@ -10,0 +11 @@\n"
                    "+line11\n"
                )
            ),
        ]

        result = repo.changed_lines()

        assert result == {
            "foo.c": {1, 2},
            "bar.sh": {11},
        }
        assert mock_run.call_args_list == [
            call(
                ["git", "merge-base", "master", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ),
            call(
                [
                    "git",
                    "diff",
                    "--diff-filter=ACMR",
                    "--unified=0",
                    "abc123..HEAD",
                    "--",
                    "*.c",
                    "*.h",
                    "*.sh",
                ],
                capture_output=True,
                text=True,
                check=True,
            ),
        ]

    @patch("repo.subprocess.run")
    def test_ignores_deleted_hunks(self, mock_run):
        """
        Verify that hunks with no destination lines are ignored.
        """
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),
            MagicMock(
                stdout=(
                    "diff --git a/foo.c b/foo.c\n"
                    "--- a/foo.c\n"
                    "+++ b/foo.c\n"
                    "@@ -5 +5,0 @@\n"
                    "-old\n"
                )
            ),
        ]

        result = repo.changed_lines()

        assert result == {"foo.c": set()}


class TestBlameLines:
    """
    Tests for the blame_lines() function.
    """

    @patch("repo.subprocess.run")
    def test_returns_commit_for_lines(self, mock_run):
        """
        Verify that blame maps line numbers to commit hashes.
        """
        sha = "a" * 40
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # merge-base
            MagicMock(
                returncode=0,
                stdout=(
                    f"{sha} 5 5 1\n"
                    "author Test\n"
                    f"\t code line\n"
                    f"{sha} 10 10 1\n"
                    "author Test\n"
                    f"\t another line\n"
                ),
            ),
        ]

        result = repo.blame_lines("foo.c", {5, 10})

        assert result == {5: sha[:12], 10: sha[:12]}

    @patch("repo.subprocess.run")
    def test_returns_empty_on_failure(self, mock_run):
        """
        Verify that blame returns empty dict on git failure.
        """
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # merge-base
            MagicMock(returncode=128, stdout=""),
        ]

        result = repo.blame_lines("foo.c", {5})

        assert result == {}

    @patch("repo.subprocess.run")
    def test_empty_lines_returns_empty(self, mock_run):
        """
        Verify that empty line set skips blame entirely.
        """
        result = repo.blame_lines("foo.c", set())

        assert result == {}
        mock_run.assert_not_called()
