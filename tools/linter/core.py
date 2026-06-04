"""
.. module:: core
    :platform: Linux
    :synopsis: Core linter implementation
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

_rules = []

SCOPE_MATCH = {
    "c": (".c", ".h"),
    "c_only": (".c",),
    "sh": (".sh",),
    "openposix": (".c", ".h"),
    "openposix_only": (".c",),
}


class Rule:
    """
    A linter rule backed by a check function.
    """

    def __init__(self, message: str, check_fn, scope: str = "c"):
        """
        :param message: Short description of what the rule checks.
        :param check_fn: Function that receives lines and yields
            (line_number, detail) tuples.
        :param scope: File scope — "c", "c_only", "sh",
            "openposix", or "openposix_only".
        """
        self._message = message
        self._check_fn = check_fn
        self._scope = scope

    @property
    def message(self) -> str:
        """
        :returns: Rule linting message.
        """
        return self._message

    @property
    def scope(self) -> str:
        """
        :returns: The scope this rule applies to.
        """
        return self._scope

    def check(self, lines: list[str]):
        """
        Run the check function against file lines.

        :param lines: List of file lines.
        :returns: Generator of (line_number, detail) tuples.
        """
        return self._check_fn(lines)


def rule(message: str, scope: str = "c"):
    """
    Decorator that registers a rule check function.

    The decorated function receives a list of file lines and yields
    (line_number, detail) tuples for each violation found.

    :param message: Short description of the rule.
    :param scope: File scope — "c", "c_only", "sh",
        "openposix", or "openposix_only".
    """
    if scope not in SCOPE_MATCH:
        raise ValueError(f"invalid scope {scope!r}, must be one of {list(SCOPE_MATCH)}")

    def decorator(func):
        _rules.append(Rule(message, func, scope=scope))
        return func

    return decorator


def run_rules(lines: list[str], filepath: str = "") -> list[tuple[str, int, str]]:
    """
    Run all registered rules against lines.

    :param lines: List of file lines.
    :param filepath: Path to the file being linted, used to
        determine which rules apply.
    :returns: list of (message, line_number, detail) tuples.
    """
    is_openposix = "open_posix_testsuite" in filepath
    findings = []

    for r in _rules:
        if filepath and not filepath.endswith(SCOPE_MATCH[r.scope]):
            continue

        if r.scope in ("openposix", "openposix_only") and not is_openposix:
            continue

        if r.scope in ("c", "c_only") and is_openposix:
            continue

        for lineno, detail in r.check(lines):
            findings.append((r.message, lineno, detail))

    return findings
