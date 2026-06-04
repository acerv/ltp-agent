# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Andrea Cervesato <andrea.cervesato@suse.com>
#
# Per-agent install paths for GitHub Copilot CLI.
# Sourced by setup.sh.
#
# Copilot CLI personal skills live under ~/.copilot/skills/<name>/SKILL.md.
# There is no separate commands directory; Copilot uses skills as the
# discovery mechanism.

export SKILL_BASE_DIR="$HOME/.copilot/skills"
export COMMANDS_DIR="$SKILL_BASE_DIR"
export SKILL_FILE_NAME="SKILL.md"
