#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
#
# Deterministic build helper for the LTP conversion pipeline.
#
# Compiles a converted test with the LTP build system and prints a small,
# bounded summary (exit code plus capped error/warning lines) to stdout. The
# full compiler output is written to a private temporary log that is removed on
# exit, so verbose build output never reaches the caller's context.
#
# Both the 32-bit target and, when the test directory defines a "%_64" rule,
# the 64-bit large-file variant are built in a single invocation so that the
# shared "make clean" runs only once and both binaries remain on disk.
#
# Usage: ltp-build.sh <binary-path>
#
# <binary-path> is the path to the target binary (which may not exist yet);
# the test directory and target name are derived from it. A trailing "_64" is
# stripped so either width variant may be passed.
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

# Normalize to the base target so callers can pass either "fcntl18" or
# "fcntl18_64" and get identical behavior. Both width variants are built from
# the same source (the LTP "%_64" rule adds -D_FILE_OFFSET_BITS=64), and a
# single "make clean" wipes every binary in the leaf directory, so the two
# variants must be built together in one invocation.
case "$BINARY" in
*_64) BASE="${BINARY%_64}" ;;
*)    BASE="$BINARY" ;;
esac

[ -d "$TEST_DIR" ] || fail "test directory not found: $TEST_DIR"
[ -f "$TEST_DIR/Makefile" ] || fail "Makefile not found in: $TEST_DIR"

RUNDIR="$(mktemp -d "${TMPDIR:-/tmp}/opencode-ltp.XXXXXX")" ||
	fail "could not create temporary directory"
trap 'rm -rf "$RUNDIR"' EXIT INT TERM

LOG="$RUNDIR/${BASE}_build.log"

# make clean first to rule out stale objects, then build the 32-bit target and,
# when the directory defines it, the 64-bit variant. The "make -n" probe skips
# directories without a "%_64" rule so this stays generic across leaf dirs.
rc64=""
(
	cd "$TEST_DIR" || exit 2
	make clean
	make "$BASE"
	rc=$?
	if make -n "${BASE}_64" >/dev/null 2>&1; then
		make "${BASE}_64"
		echo "__RC64__=$?"
	fi
	exit "$rc"
) >"$LOG" 2>&1
rc=$?

rc64="$(sed -n 's/^__RC64__=//p' "$LOG")"

echo "=== build ($BASE) ==="
if [ -n "$rc64" ]; then
	echo "commands: make clean; make $BASE; make ${BASE}_64"
else
	echo "commands: make clean; make $BASE"
fi
echo "build_exit=$rc"
[ -n "$rc64" ] && echo "build_exit_64=$rc64"
echo "-- errors (capped at $CAP) --"
grep -nE 'error:|undefined reference|cannot find' "$LOG" | head -n "$CAP" || true
echo "-- warnings (capped at $CAP) --"
grep -nE 'warning:' "$LOG" | head -n "$CAP" || true

# Fail if either width variant failed to build.
if [ "$rc" -eq 0 ] && [ -n "$rc64" ] && [ "$rc64" -ne 0 ]; then
	rc="$rc64"
fi

exit "$rc"
