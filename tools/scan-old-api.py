#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
"""Scan LTP testcases for files still using the old C test API."""

import argparse
import json
import os
import re
import sys

OLD_API_SIGNALS = [
    re.compile(r'#include\s+"test\.h"'),
    re.compile(r"\bchar\s+\*TCID\b"),
    re.compile(r"\bint\s+TST_TOTAL\b"),
    re.compile(r"\btst_resm\s*\("),
    re.compile(r"\btst_brkm\s*\("),
    re.compile(r"\btst_parse_opts\b"),
]

NEW_API_SIGNALS = [
    re.compile(r'#include\s+"tst_test\.h"'),
    re.compile(r"\bstruct\s+tst_test\b"),
]

HELPER_SUFFIXES = ("_common.c", "_support.c", "_helper.c")

EXCLUDED_DIRS = {
    "open_posix_testsuite",
    "datafiles",
}


def is_excluded(path):
    parts = path.split(os.sep)
    return any(p in EXCLUDED_DIRS for p in parts)


def parse_makefile_filters(makefile_path):
    """Extract unconditional FILTER_OUT_MAKE_TARGETS from a Makefile."""
    targets = set()
    if not os.path.isfile(makefile_path):
        return targets

    depth = 0
    with open(makefile_path, errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if re.match(r"^if(eq|def|ndef)\b", stripped):
                depth += 1
            elif stripped == "endif":
                depth = max(0, depth - 1)
            elif depth == 0:
                m = re.match(r"FILTER_OUT_MAKE_TARGETS\s*[:+]?=\s*(.*)", stripped)
                if m:
                    targets.update(m.group(1).split())
    return targets


def has_old_api(content):
    return any(sig.search(content) for sig in OLD_API_SIGNALS)


def has_new_api(content):
    return any(sig.search(content) for sig in NEW_API_SIGNALS)


def needs_root(content):
    return "tst_require_root" in content


def classify_type(filepath, basename_no_ext, filter_cache, root_dir):
    if "/lib/" in filepath:
        return "helper"
    if basename_no_ext.endswith(tuple(s.replace(".c", "") for s in HELPER_SUFFIXES)):
        return "helper"

    dirpath = os.path.dirname(os.path.join(root_dir, filepath))
    if dirpath not in filter_cache:
        filter_cache[dirpath] = parse_makefile_filters(
            os.path.join(dirpath, "Makefile")
        )
    if basename_no_ext in filter_cache[dirpath]:
        return "helper"

    return "test"


def scan(root_dir):
    testcases_dir = os.path.join(root_dir, "testcases")
    if not os.path.isdir(testcases_dir):
        print(f"Error: {testcases_dir} not found", file=sys.stderr)
        sys.exit(1)

    filter_cache = {}
    entries = []
    old_api_dirs = set()

    for dirpath, dirnames, filenames in os.walk(testcases_dir):
        rel_dir = os.path.relpath(dirpath, root_dir)
        if is_excluded(rel_dir):
            dirnames.clear()
            continue

        for fname in filenames:
            if not fname.endswith(".c"):
                continue

            fullpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fullpath, root_dir)

            try:
                with open(fullpath, errors="replace") as f:
                    content = f.read()
            except OSError:
                continue

            if not has_old_api(content) or has_new_api(content):
                continue

            line_count = content.count("\n")
            basename_no_ext = fname[:-2]

            entry = {
                "type": classify_type(
                    rel_path, basename_no_ext, filter_cache, root_dir
                ),
                "location": rel_path,
                "root": 1 if needs_root(content) else 0,
                "lines": line_count,
                "converted": 0,
            }
            entries.append(entry)
            old_api_dirs.add(dirpath)

    for dirpath in sorted(old_api_dirs):
        makefile = os.path.join(dirpath, "Makefile")
        if os.path.isfile(makefile):
            with open(makefile, errors="replace") as f:
                line_count = f.read().count("\n")
            entries.append(
                {
                    "type": "makefile",
                    "location": os.path.relpath(makefile, root_dir),
                    "root": 0,
                    "lines": line_count,
                    "converted": 0,
                }
            )

    entries.sort(key=lambda e: e["location"])
    return entries


def main():
    parser = argparse.ArgumentParser(description="Scan LTP testcases for old API files")
    parser.add_argument(
        "--root-dir",
        default=os.getcwd(),
        help="LTP root directory (default: cwd)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )
    args = parser.parse_args()

    entries = scan(args.root_dir)

    output = json.dumps(entries, indent=2) + "\n"
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
