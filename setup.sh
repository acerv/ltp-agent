#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
#
# Symlink ltp-agent config files into an LTP repo.
#
# Usage:
#   setup.sh [<ltp-dir>]
#
# If <ltp-dir> is omitted, the current directory is used.
#
# Examples:
#   cd /path/to/ltp && setup.sh
#   setup.sh /path/to/ltp

set -e

AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"

die() {
	echo "ERROR: $1" >&2
	exit 1
}

LTP_DIR="${1:-.}"
LTP_DIR="$(cd "$LTP_DIR" && pwd)"

# Verify we are inside an LTP repo
[ -d "$LTP_DIR/.git" ] ||
	die "$LTP_DIR is not a git repository"
[ -d "$LTP_DIR/testcases" ] ||
	die "$LTP_DIR does not look like an LTP repo"
[ -f "$LTP_DIR/include/tst_test.h" ] ||
	die "$LTP_DIR does not look like an LTP repo"

# Helper: create $link -> $target, replacing any existing symlink.
# Errors out if a non-symlink already exists at $link.
link_into_ltp() {
	link="$1"
	target="$2"

	if [ -L "$link" ]; then
		rm "$link"
	elif [ -e "$link" ]; then
		die "$link already exists and is not a symlink"
	fi

	ln -s "$target" "$link"
}

# Top-level rule/skill directories plus AGENTS.md.
for name in AGENTS.md agents skills linter; do
	link_into_ltp "$LTP_DIR/$name" "$AGENT_DIR/$name"
done

# Gemini CLI reads GEMINI.md instead of AGENTS.md.
link_into_ltp "$LTP_DIR/GEMINI.md" "$AGENT_DIR/AGENTS.md"

# Agent-specific skill directory layout.
# Claude Code expects skills under .claude/skills/
# Other agents (e.g. pi) expect skills under .agents/skills/
mkdir -p "$LTP_DIR/.claude" "$LTP_DIR/.agents"
link_into_ltp "$LTP_DIR/.claude/skills" "$AGENT_DIR/skills"
link_into_ltp "$LTP_DIR/.agents/skills" "$AGENT_DIR/skills"

echo "ltp-agent linked into $LTP_DIR"
