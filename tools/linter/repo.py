"""
.. module:: repo
    :platform: Linux
    :synopsis: Git repository helpers
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import subprocess


def changed_files(base: str = "master") -> list[str]:
    """
    Return the list of test files changed on the current branch compared
    to the given base branch.

    :param base: Base branch to diff against.
    :returns: List of changed .c/.h/.sh file paths relative to the repo root.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..HEAD", "--", "*.c", "*.h", "*.sh"],
        capture_output=True,
        text=True,
        check=True,
    )

    if not result.stdout.strip():
        return []

    return result.stdout.strip().split("\n")
