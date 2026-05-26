"""
.. module:: main
    :platform: Linux
    :synopsis: Linter entry point
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import argparse
import sys

import core
import repo
import rules_c  # noqa: F401 — triggers @rule decorators
import rules_openposix  # noqa: F401
import rules_sh  # noqa: F401


def _lint_file(filepath: str) -> list[tuple[str, int, str]]:
    """
    Read a file and run all registered rules against it.

    :param filepath: Path to the C file.
    :returns: List of (message, line_number, detail) tuples.
    """
    with open(filepath) as fh:
        lines = fh.readlines()

    return core.run_rules(lines, filepath=filepath)


def run():
    """
    Linter entry point. Parses arguments, reads files and
    runs all registered rules.
    """
    parser = argparse.ArgumentParser(description="LTP test linter")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="test file to lint")
    group.add_argument(
        "-b",
        "--branch",
        action="store_true",
        help="lint all files changed on the current branch vs master",
    )

    args = parser.parse_args()

    if args.file:
        files = [args.file]
    else:
        files = repo.changed_files()

    has_findings = False

    for filepath in files:
        findings = _lint_file(filepath)
        for message, lineno, detail in findings:
            print(f"{filepath}:{lineno}: {message}: {detail}")
            has_findings = True

    sys.exit(1 if has_findings else 0)
