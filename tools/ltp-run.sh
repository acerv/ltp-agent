#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
#
# Deterministic run helper for the LTP conversion pipeline.
#
# Runs a converted new-API test three times (setup/cleanup only, one default
# run, and ten iterations) and prints a small, bounded summary per pass to
# stdout: the exit code, the LTP "Summary:" block, result-tag counts, and a
# capped list of failing lines. The full output of every pass is written to a
# private temporary log that is removed on exit, so verbose test output never
# reaches the caller's context.
#
# This helper only runs the test; it makes no pass/fail judgement. The caller
# classifies the run from the printed summary.
#
# Usage: ltp-run.sh <binary-path>
#
# <binary-path> is the path to the built test binary; the test directory and
# binary name are derived from it.
#
# Environment:
#   LTP_RUN_TIMEOUT   Per-pass timeout in seconds (default 600).
#   LTP_GREP_CAP      Max failing lines to print per pass (default 20).

set -u

TIMEOUT="${LTP_RUN_TIMEOUT:-600}"
CAP="${LTP_GREP_CAP:-20}"

fail() {
	echo "ltp-run: $1" >&2
	exit 2
}

[ "$#" -eq 1 ] || fail "usage: ltp-run.sh <binary-path>"

TEST_DIR="$(dirname -- "$1")"
BINARY="$(basename -- "$1")"

[ -d "$TEST_DIR" ] || fail "test directory not found: $TEST_DIR"
[ -x "$TEST_DIR/$BINARY" ] || fail "test binary not found or not executable: $TEST_DIR/$BINARY"

RUNDIR="$(mktemp -d "${TMPDIR:-/tmp}/opencode-ltp.XXXXXX")" ||
	fail "could not create temporary directory"
trap 'rm -rf "$RUNDIR"' EXIT INT TERM

# Reduce one pass log to a bounded summary on stdout.
summarize() {
	name="$1"
	args="$2"
	rc="$3"
	log="$4"

	echo "=== $name (args: ${args:-none}) ==="
	echo "command: timeout $TIMEOUT ./$BINARY $args"
	echo "${name}_exit=$rc"
	[ "$rc" -eq 124 ] && echo "note: killed by timeout after ${TIMEOUT}s (possible hang)"
	echo "-- summary --"
	grep -E '^Summary:' -A6 "$log" || true
	echo "-- tag counts --"
	grep -oE 'T(PASS|FAIL|BROK|CONF|WARN)' "$log" | sort | uniq -c || true
	echo "-- distinct failures (capped at $CAP) --"
	grep -E 'T(FAIL|BROK|WARN)' "$log" | sort | uniq -c | sort -rn | head -n "$CAP" || true
	echo
}

run_pass() {
	name="$1"
	args="$2"
	log="$RUNDIR/${BINARY}_${name}.log"

	# shellcheck disable=SC2086
	(cd "$TEST_DIR" && timeout "$TIMEOUT" ./"$BINARY" $args) >"$log" 2>&1
	rc=$?

	summarize "$name" "$args" "$rc" "$log"
}

run_pass "run0" "-i 0"
run_pass "run" ""
run_pass "run10" "-i 10"

exit 0
