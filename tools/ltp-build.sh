#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
#
# Deterministic build helper for the LTP conversion pipeline.
#
# Compiles a single converted test with the LTP build system and prints a
# small, bounded summary (exit code plus capped error/warning lines) to
# stdout. The full compiler output is written to a private temporary log that
# is removed on exit, so verbose build output never reaches the caller's
# context.
#
# Usage: ltp-build.sh <binary-path>
#
# <binary-path> is the path to the target binary (which may not exist yet);
# the test directory and target name are derived from it.
#
# Environment:
#   LTP_GREP_CAP   Max error/warning lines to print (default 20).

set -u

CAP="${LTP_GREP_CAP:-20}"

fail() {
	echo "ltp-build: $1" >&2
	exit 2
}

[ "$#" -eq 1 ] || fail "usage: ltp-build.sh <binary-path>"

TEST_DIR="$(dirname -- "$1")"
BINARY="$(basename -- "$1")"

[ -d "$TEST_DIR" ] || fail "test directory not found: $TEST_DIR"
[ -f "$TEST_DIR/Makefile" ] || fail "Makefile not found in: $TEST_DIR"

RUNDIR="$(mktemp -d "${TMPDIR:-/tmp}/opencode-ltp.XXXXXX")" ||
	fail "could not create temporary directory"
trap 'rm -rf "$RUNDIR"' EXIT INT TERM

LOG="$RUNDIR/${BINARY}_build.log"

# make clean first to rule out stale objects, then build the target.
(
	cd "$TEST_DIR" || exit 2
	make clean
	make "$BINARY"
) >"$LOG" 2>&1
rc=$?

echo "=== build ($BINARY) ==="
echo "commands: make clean; make $BINARY"
echo "build_exit=$rc"
echo "-- errors (capped at $CAP) --"
grep -nE 'error:|undefined reference|cannot find' "$LOG" | head -n "$CAP" || true
echo "-- warnings (capped at $CAP) --"
grep -nE 'warning:' "$LOG" | head -n "$CAP" || true

exit "$rc"
