#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
#
# Install ltp-agent skills into the chosen agent's skill directory.
#
# Usage: ./setup.sh <agent>
#
# <agent> must match one of agents/<agent>.sh.
#
# Each skill at skills/<name>/SKILL.md is copied to
# $SKILL_BASE_DIR/<name>/$SKILL_FILE_NAME with the placeholder
# {{LTP_AGENT_DIR}} expanded to the absolute path of this checkout.
#
# No symlinks are created; nothing is written into any LTP source tree.

set -e

AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
	cat <<-EOF
	Usage: $0 <agent>

	Install ltp-agent skills for the chosen agent.

	Available agents:
	EOF
	for f in "$AGENT_DIR"/agents/*.sh; do
		[ -f "$f" ] || continue
		printf '  - %s\n' "$(basename "$f" .sh)"
	done
}

die() {
	echo "ERROR: $1" >&2
	exit 1
}

case "${1:-}" in
	-h|--help)
		usage
		exit 0
		;;
	"")
		usage >&2
		exit 1
		;;
esac

AGENT="$1"
AGENT_SCRIPT="$AGENT_DIR/agents/$AGENT.sh"

[ -f "$AGENT_SCRIPT" ] ||
	die "unknown agent '$AGENT' (no $AGENT_SCRIPT)"

# Source the per-agent script. It must export SKILL_BASE_DIR,
# COMMANDS_DIR and SKILL_FILE_NAME. It may also override install_skills().
# shellcheck disable=SC1090
. "$AGENT_SCRIPT"

[ -n "${SKILL_BASE_DIR:-}" ]  || die "$AGENT_SCRIPT did not export SKILL_BASE_DIR"
[ -n "${SKILL_FILE_NAME:-}" ] || die "$AGENT_SCRIPT did not export SKILL_FILE_NAME"
: "${COMMANDS_DIR:=$SKILL_BASE_DIR}"

# Default skill installer. Per-agent scripts may override by redefining
# this function before setup.sh reaches its install loop.
install_skills() {
	src_dir="$AGENT_DIR/skills"

	[ -d "$src_dir" ] ||
		die "no skills directory at $src_dir"

	mkdir -p "$SKILL_BASE_DIR"

	for skill_dir in "$src_dir"/*/; do
		[ -d "$skill_dir" ] || continue
		skill_name="$(basename "$skill_dir")"
		src_skill="$skill_dir/SKILL.md"

		[ -f "$src_skill" ] ||
			die "missing $src_skill"

		dest_dir="$SKILL_BASE_DIR/$skill_name"
		dest="$dest_dir/$SKILL_FILE_NAME"

		mkdir -p "$dest_dir"
		sed "s|{{LTP_AGENT_DIR}}|$AGENT_DIR|g" "$src_skill" > "$dest"

		echo "  $dest"
	done
}

echo "ltp-agent: $AGENT_DIR"
echo "Installing skills for: $AGENT"
echo ""
echo "Installed skills:"
install_skills
echo ""
echo "Done."
