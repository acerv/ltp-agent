# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
#
# Per-agent install paths for opencode.
# Sourced by setup.sh.

export SKILL_BASE_DIR="$HOME/.opencode/skills"
export COMMANDS_DIR="$HOME/.opencode/commands"
export SKILL_FILE_NAME="SKILL.md"
export AGENT_BASE_DIR="$HOME/.config/opencode/agent"

# Install opencode multi-agent conversion pipeline definitions.
# Each agent at agents/opencode/agent/<name>.md is copied to
# $AGENT_BASE_DIR/<name>.md with {{LTP_AGENT_DIR}} expanded.
install_agents() {
	src_dir="$AGENT_DIR/agents/opencode/agent"

	[ -d "$src_dir" ] || return 0

	mkdir -p "$AGENT_BASE_DIR"

	for agent_file in "$src_dir"/*.md; do
		[ -f "$agent_file" ] || continue
		agent_name="$(basename "$agent_file")"
		dest="$AGENT_BASE_DIR/$agent_name"

		sed "s|{{LTP_AGENT_DIR}}|$AGENT_DIR|g" "$agent_file" >"$dest"

		echo "  $dest"
	done
}
