"""
.. module:: main
    :platform: Linux
    :synopsis: Linter entry point
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import argparse
import json
import sys
from typing import Optional

import core
import repo
import rules_c  # noqa: F401 - triggers @rule decorators
import rules_openposix  # noqa: F401
import rules_sh  # noqa: F401


def _lint_file(
    filepath: str,
    patch_lines: Optional[set[int]] = None,
    blame_map: Optional[dict[int, str]] = None,
) -> list[core.Finding]:
    """
    Read a file and run all registered rules against it.

    :param filepath: Path to the C file.
    :param patch_lines: Optional set of changed destination line numbers.
    :param blame_map: Optional mapping of line number to commit hash.
    :returns: List of findings.
    """
    with open(filepath) as fh:
        lines = fh.readlines()

    return core.run_rules(
        lines,
        filepath=filepath,
        patch_lines=patch_lines,
        blame_map=blame_map,
    )


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
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--scope",
        choices=("file", "patch"),
        default="file",
        help="lint full files or only changed patch lines (default: file)",
    )

    args = parser.parse_args()

    if args.scope == "patch" and not args.branch:
        parser.error("--scope patch requires -b/--branch")

    patch_line_map = None
    if args.file:
        files = [args.file]
    else:
        files = repo.changed_files()
        if args.scope == "patch":
            patch_line_map = repo.changed_lines()

    findings = []

    for filepath in files:
        patch_lines = None
        if patch_line_map is not None:
            patch_lines = patch_line_map.get(filepath, set())

        blame_map = None
        if args.branch:
            # Read all lines in the file to get full blame coverage
            with open(filepath) as fh:
                all_lines = set(range(1, len(fh.readlines()) + 1))
            blame_map = repo.blame_lines(filepath, all_lines)

        findings.extend(
            _lint_file(filepath, patch_lines=patch_lines, blame_map=blame_map)
        )

    if args.format == "json":
        print(
            json.dumps(
                {
                    "version": 1,
                    "scope": args.scope,
                    "findings": [finding.to_dict() for finding in findings],
                },
                indent=2,
            )
        )
    else:
        for finding in findings:
            commit_prefix = f"[{finding.commit}] " if finding.commit else ""
            print(
                f"{commit_prefix}{finding.file}:{finding.line}: "
                f"{finding.rule_id}: {finding.message}: {finding.detail}"
            )

    sys.exit(1 if findings else 0)
