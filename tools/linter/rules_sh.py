"""
.. module:: rules_sh
    :platform: Linux
    :synopsis: Shell test linter rules
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import re

from core import rule


@rule("Wrong shebang", scope="sh", rule_id="LTP-S001")
def check_shebang(lines):
    """
    Check that the first line is exactly #!/bin/sh.
    """
    if not _is_ltp_test(lines):
        return

    if not lines or lines[0].rstrip() != "#!/bin/sh":
        yield 1, "shebang must be exactly #!/bin/sh"


@rule("Missing SPDX header", scope="sh", rule_id="LTP-S002")
def check_spdx(lines):
    """
    Check that the second line contains the SPDX license identifier.
    """
    if not _is_ltp_test(lines):
        return

    if len(lines) < 2 or "SPDX-License-Identifier" not in lines[1]:
        yield 2, "second line must contain SPDX-License-Identifier"


@rule("Missing copyright", scope="sh", rule_id="LTP-S003")
def check_copyright(lines):
    """
    Check that a copyright line with year is present.
    """
    if not _is_ltp_test(lines):
        return

    for line in lines:
        if re.search(r"Copyright\s.*\d{4}", line, re.IGNORECASE):
            return

    yield 1, "no Copyright line with year found"


def _is_ltp_test(lines):
    """
    Check whether the file sources the LTP shell test framework
    (. tst_run.sh or . tst_test.sh).
    """
    for line in lines:
        stripped = line.strip()
        if stripped == ". tst_run.sh" or stripped == ". tst_test.sh":
            return True
    return False


def _is_new_shell_api(lines):
    """
    Check whether the file uses the new shell API (. tst_run.sh)
    vs the old API (. tst_test.sh + tst_run).
    """
    for line in lines:
        if line.strip() == ". tst_run.sh":
            return True

    return False


@rule("Missing doc block", scope="sh", rule_id="LTP-S004")
def check_doc_block(lines):
    """
    Check that a # --- doc ... # --- block is present.
    Only applies to new shell API tests (. tst_run.sh).
    """
    if not _is_new_shell_api(lines):
        return

    in_doc = False

    for line in lines:
        stripped = line.strip()
        if stripped == "# ---" and not in_doc:
            in_doc = True
            continue

        if stripped == "# ---" and in_doc:
            return

        if in_doc and stripped.startswith("# doc"):
            return

    yield 1, "missing # --- doc ... # --- block"


@rule("Missing env block", scope="sh", rule_id="LTP-S005")
def check_env_block(lines):
    """
    Check that a # --- env ... # --- block is present.
    Only applies to new shell API tests (. tst_run.sh).
    """
    if not _is_new_shell_api(lines):
        return

    found_env = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# env"):
            found_env = True

        if stripped == "# ---" and found_env:
            return

    yield 1, "missing # --- env ... # --- block"


@rule("Missing tst_run as last line", scope="sh", rule_id="LTP-S006")
def check_tst_run_last(lines):
    """
    Check that the last non-empty line is . tst_run.sh (new API)
    or tst_run (old API).
    """
    if not _is_ltp_test(lines):
        return

    valid = (". tst_run.sh", "tst_run")

    for line in reversed(lines):
        stripped = line.strip()
        if stripped:
            if stripped not in valid:
                yield len(lines), "last line must be . tst_run.sh or tst_run"
            return

    yield 1, "empty file"


@rule("Bash-ism: [[ ]]", scope="sh", rule_id="LTP-S007")
def check_no_double_bracket(lines):
    """
    Flag [[ ]] usage. Shell tests must use [ ] for POSIX portability.
    """
    if not _is_ltp_test(lines):
        return

    pattern = re.compile(r"\[\[(?!:)")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue

        match = pattern.search(line)
        if not match:
            continue

        yield line_num, "use [ ] instead of [[ ]] (POSIX portability)"


@rule("Bash-ism: function keyword", scope="sh", rule_id="LTP-S008")
def check_no_function_keyword(lines):
    """
    Flag the function keyword. POSIX shell uses name() { syntax.
    """
    if not _is_ltp_test(lines):
        return

    pattern = re.compile(r"^\s*function\s+\w+")

    for line_num, line in enumerate(lines, 1):
        match = pattern.match(line)
        if not match:
            continue

        yield (
            line_num,
            "do not use function keyword, use name() { instead (POSIX portability)",
        )


@rule("Bash-ism: process substitution", scope="sh", rule_id="LTP-S009")
def check_no_process_substitution(lines):
    """
    Flag <() and >() process substitution which is not POSIX.
    """
    if not _is_ltp_test(lines):
        return

    pattern = re.compile(r"[<>]\(")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue

        match = pattern.search(line)
        if not match:
            continue

        yield (
            line_num,
            "do not use process substitution <() or >() (POSIX portability)",
        )


@rule("Bash-ism: array", scope="sh", rule_id="LTP-S010")
def check_no_arrays(lines):
    """
    Flag bash array syntax which is not POSIX.
    """
    if not _is_ltp_test(lines):
        return

    pattern = re.compile(r"\w+=\(")

    for line_num, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue

        match = pattern.search(line)
        if not match:
            continue

        yield line_num, "do not use arrays (POSIX portability)"
