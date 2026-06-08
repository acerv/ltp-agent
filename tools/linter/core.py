"""
.. module:: core
    :platform: Linux
    :synopsis: Core linter implementation
.. moduleauthor:: Andrea Cervesato <andrea.cervesato@suse.com>
"""

import hashlib
from dataclasses import asdict, dataclass
from typing import Optional

_rules = []

CONFIDENCE_LEVELS = {"mechanical", "semantic", "experimental"}

SCOPE_MATCH = {
    "c": (".c", ".h"),
    "c_only": (".c",),
    "sh": (".sh",),
    "openposix": (".c", ".h"),
    "openposix_only": (".c",),
}


@dataclass(frozen=True)
class Finding:
    """
    A single linter finding.
    """

    file: str
    line: int
    rule_id: str
    confidence: str
    source: str
    message: str
    detail: str
    commit: str

    def __iter__(self):
        """
        Keep backwards-compatible tuple unpacking.
        """
        yield self.message
        yield self.line
        yield self.detail

    def __getitem__(self, index):
        """
        Keep backwards-compatible tuple indexing.
        """
        return tuple(self)[index]

    def to_dict(self):
        """
        Return a JSON-serializable representation.
        """
        return asdict(self)


class Rule:
    """
    A linter rule backed by a check function.
    """

    def __init__(
        self,
        message: str,
        check_fn,
        scope: str = "c",
        rule_id: Optional[str] = None,
        confidence: str = "mechanical",
    ):
        """
        :param message: Short description of what the rule checks.
        :param check_fn: Function that receives lines and yields
            (line_number, detail) tuples.
        :param scope: File scope - "c", "c_only", "sh",
            "openposix", or "openposix_only".
        :param rule_id: Stable rule identifier used in machine output.
        :param confidence: Finding confidence class.
        """
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                f"invalid confidence {confidence!r}, "
                f"must be one of {list(CONFIDENCE_LEVELS)}"
            )

        self._message = message
        self._check_fn = check_fn
        self._scope = scope
        self._rule_id = rule_id or _default_rule_id(scope, message)
        self._confidence = confidence

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

    @property
    def rule_id(self) -> str:
        """
        :returns: Stable rule identifier.
        """
        return self._rule_id

    @property
    def confidence(self) -> str:
        """
        :returns: Finding confidence class.
        """
        return self._confidence

    def check(self, lines: list[str]):
        """
        Run the check function against file lines.

        :param lines: List of file lines.
        :returns: Generator of (line_number, detail) tuples.
        """
        return self._check_fn(lines)


def _default_rule_id(scope: str, message: str) -> str:
    """
    Generate a deterministic rule ID when a rule does not provide one.
    """
    prefixes = {
        "c": "LTP-C",
        "c_only": "LTP-C",
        "sh": "LTP-S",
        "openposix": "LTP-O",
        "openposix_only": "LTP-O",
    }
    digest = hashlib.sha1(f"{scope}:{message}".encode()).hexdigest()[:8]

    return f"{prefixes[scope]}-{digest}"


def rule(
    message: str,
    scope: str = "c",
    rule_id: Optional[str] = None,
    confidence: str = "mechanical",
):
    """
    Decorator that registers a rule check function.

    The decorated function receives a list of file lines and yields
    (line_number, detail) tuples for each violation found.

    :param message: Short description of the rule.
    :param scope: File scope - "c", "c_only", "sh",
        "openposix", or "openposix_only".
    :param rule_id: Stable rule identifier used in machine output.
    :param confidence: Finding confidence class.
    """
    if scope not in SCOPE_MATCH:
        raise ValueError(f"invalid scope {scope!r}, must be one of {list(SCOPE_MATCH)}")

    def decorator(func):
        _rules.append(
            Rule(
                message,
                func,
                scope=scope,
                rule_id=rule_id,
                confidence=confidence,
            )
        )
        return func

    return decorator


def run_rules(
    lines: list[str],
    filepath: str = "",
    patch_lines: Optional[set[int]] = None,
    blame_map: Optional[dict[int, str]] = None,
) -> list[Finding]:
    """
    Run all registered rules against lines.

    :param lines: List of file lines.
    :param filepath: Path to the file being linted, used to
        determine which rules apply.
    :param patch_lines: Optional set of changed destination line numbers.
        When set, findings outside these lines are dropped.
    :param blame_map: Optional mapping of line number to commit hash.
    :returns: list of Finding objects.
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
            if patch_lines is not None and lineno not in patch_lines:
                continue

            commit = ""
            if blame_map is not None:
                commit = blame_map.get(lineno, "")

            findings.append(
                Finding(
                    file=filepath,
                    line=lineno,
                    rule_id=r.rule_id,
                    confidence=r.confidence,
                    source="linter",
                    message=r.message,
                    detail=detail,
                    commit=commit,
                )
            )

    return findings
