"""
.. module:: repo
    :platform: Linux
    :synopsis: Git repository helpers
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import re
import subprocess


def _merge_base(base: str) -> str:
    """
    Return the merge-base between base and HEAD.

    Using the merge-base ensures we only see changes introduced on the
    current branch, not unrelated commits that landed on base since the
    branch point.
    """
    result = subprocess.run(
        ["git", "merge-base", base, "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def changed_files(base: str = "master") -> list[str]:
    """
    Return the list of test files changed on the current branch compared
    to the given base branch.

    :param base: Base branch to diff against.
    :returns: List of changed .c/.h/.sh file paths relative to the repo root.
    """
    merge_base = _merge_base(base)
    result = subprocess.run(
        [
            "git",
            "diff",
            "--diff-filter=ACMR",
            "--name-only",
            f"{merge_base}..HEAD",
            "--",
            "*.c",
            "*.h",
            "*.sh",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    if not result.stdout.strip():
        return []

    return result.stdout.strip().split("\n")


def changed_lines(base: str = "master") -> dict[str, set[int]]:
    """
    Return changed destination line numbers for lintable files.

    :param base: Base branch to diff against.
    :returns: Mapping of file path to changed destination line numbers.
    """
    merge_base = _merge_base(base)
    result = subprocess.run(
        [
            "git",
            "diff",
            "--diff-filter=ACMR",
            "--unified=0",
            f"{merge_base}..HEAD",
            "--",
            "*.c",
            "*.h",
            "*.sh",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    files = {}
    current_file = None

    for line in result.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[len("+++ b/") :]
            files.setdefault(current_file, set())
            continue

        if not current_file or not line.startswith("@@"):
            continue

        match = re.search(r"\+(\d+)(?:,(\d+))?", line)
        if not match:
            continue

        start = int(match.group(1))
        count = int(match.group(2) or 1)
        if count == 0:
            continue

        files[current_file].update(range(start, start + count))

    return files


def blame_lines(filepath: str, lines: set[int], base: str = "master") -> dict[int, str]:
    """
    Return the commit hash that last touched each given line.

    :param filepath: Path to the file (relative to repo root).
    :param lines: Set of line numbers to blame.
    :param base: Base branch (used to compute the blame range).
    :returns: Mapping of line number to short commit hash.
    """
    if not lines:
        return {}

    merge_base = _merge_base(base)

    result = subprocess.run(
        [
            "git",
            "blame",
            "--porcelain",
            f"{merge_base}..HEAD",
            "--",
            filepath,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {}

    mapping = {}
    current_commit = None
    current_line = None

    for raw_line in result.stdout.splitlines():
        # Header lines: <sha> <orig-line> <final-line> [<num-lines>]
        parts = raw_line.split()
        if (
            len(parts) >= 3
            and len(parts[0]) == 40
            and parts[1].isdigit()
            and parts[2].isdigit()
        ):
            current_commit = parts[0]
            current_line = int(parts[2])
            if current_line in lines:
                mapping[current_line] = current_commit[:12]

    return mapping
