"""
Tests for core module: Rule class, rule() decorator and run_rules().
"""

import pytest

import core


class TestRule:
    """
    Tests for the Rule class.
    """

    def test_message_property(self):
        """
        Verify that the message property returns the stored message.
        """
        r = core.Rule("test message", lambda lines: iter([]))
        assert r.message == "test message"

    def test_metadata_properties(self):
        """
        Verify that rule metadata properties are exposed.
        """
        r = core.Rule(
            "test message",
            lambda lines: iter([]),
            rule_id="LTP-T001",
            confidence="mechanical",
        )
        assert r.rule_id == "LTP-T001"
        assert r.confidence == "mechanical"

    def test_invalid_confidence_raises(self):
        """
        Verify that an invalid confidence raises ValueError.
        """
        with pytest.raises(ValueError, match="invalid confidence"):
            core.Rule("test message", lambda lines: iter([]), confidence="bad")

    def test_check_delegates_to_function(self):
        """
        Verify that check() calls the wrapped function with lines.
        """

        def fn(lines):
            yield 1, "found"

        r = core.Rule("msg", fn)
        results = list(r.check(["hello\n"]))
        assert results == [(1, "found")]

    def test_check_empty_when_no_match(self):
        """
        Verify that check() returns nothing when the function yields nothing.
        """
        r = core.Rule("msg", lambda lines: iter([]))
        assert list(r.check(["hello\n"])) == []


class TestRuleDecorator:
    """
    Tests for the rule() decorator.
    """

    def test_decorator_registers_rule(self):
        """
        Verify that applying @rule appends a Rule to _rules.
        """
        initial_count = len(core._rules)

        @core.rule("decorator test")
        def dummy_rule(lines):
            """
            Dummy rule for testing.
            """
            yield 1, "dummy"

        assert len(core._rules) == initial_count + 1
        assert core._rules[-1].message == "decorator test"

        core._rules.pop()

    def test_decorator_preserves_function(self):
        """
        Verify that the decorator returns the original function unchanged.
        """

        @core.rule("preserve test")
        def my_check(lines):
            """
            Rule that returns a constant.
            """
            return 42

        assert my_check(["x"]) == 42

        core._rules.pop()

    def test_invalid_scope_raises(self):
        """
        Verify that an invalid scope raises ValueError.
        """
        with pytest.raises(ValueError, match="invalid scope"):

            @core.rule("bad scope", scope="nope")
            def bad(lines):
                """
                Rule with invalid scope.
                """
                yield 1, "bad"

    def test_decorator_sets_rule_metadata(self):
        """
        Verify that the decorator passes rule metadata to Rule.
        """
        initial_count = len(core._rules)

        @core.rule("metadata test", rule_id="LTP-T002", confidence="semantic")
        def metadata_rule(lines):
            """
            Dummy rule for testing metadata.
            """
            yield 1, "dummy"

        assert len(core._rules) == initial_count + 1
        assert core._rules[-1].rule_id == "LTP-T002"
        assert core._rules[-1].confidence == "semantic"

        core._rules.pop()


class TestRunRules:
    """
    Tests for run_rules().
    """

    def test_collects_findings(self):
        """
        Verify that run_rules collects findings from all registered rules.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("rule A")
        def rule_a(lines):
            """
            First test rule.
            """
            yield 1, "detail A"

        @core.rule("rule B")
        def rule_b(lines):
            """
            Second test rule.
            """
            yield 3, "detail B"

        findings = core.run_rules(["line1\n", "line2\n", "line3\n"])
        assert [tuple(finding) for finding in findings] == [
            ("rule A", 1, "detail A"),
            ("rule B", 3, "detail B"),
        ]
        assert findings[0].file == ""
        assert findings[0].confidence == "mechanical"

        core._rules.clear()
        core._rules.extend(saved)

    def test_patch_lines_filter_findings(self):
        """
        Verify that patch_lines keeps only findings on changed lines.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("rule A")
        def rule_a(lines):
            """
            First test rule.
            """
            yield 1, "detail A"
            yield 3, "detail B"

        findings = core.run_rules(
            ["line1\n", "line2\n", "line3\n"],
            filepath="foo.c",
            patch_lines={3},
        )
        assert len(findings) == 1
        assert findings[0].line == 3

        core._rules.clear()
        core._rules.extend(saved)

    def test_empty_when_no_findings(self):
        """
        Verify that run_rules returns an empty list when nothing matches.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("silent rule")
        def silent(lines):
            """
            Rule that never yields.
            """
            return
            yield  # makes this a generator (unreachable)

        assert core.run_rules(["line\n"]) == []

        core._rules.clear()
        core._rules.extend(saved)

    def test_c_only_skipped_for_header(self):
        """
        Verify that c_only rules are skipped for .h files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("c only", scope="c_only")
        def c_rule(lines):
            """
            Rule that only applies to .c files.
            """
            yield 1, "c finding"

        @core.rule("c and h")
        def ch_rule(lines):
            """
            Rule that applies to .c and .h files.
            """
            yield 1, "ch finding"

        findings = core.run_rules(["line\n"], filepath="foo.h")
        assert len(findings) == 1
        assert findings[0][0] == "c and h"

        core._rules.clear()
        core._rules.extend(saved)

    def test_c_only_runs_for_c_file(self):
        """
        Verify that c_only rules run for .c files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("c only", scope="c_only")
        def c_rule(lines):
            """
            Rule that only applies to .c files.
            """
            yield 1, "c finding"

        findings = core.run_rules(["line\n"], filepath="foo.c")
        assert len(findings) == 1
        assert findings[0][0] == "c only"

        core._rules.clear()
        core._rules.extend(saved)

    def test_sh_rules_skipped_for_c_file(self):
        """
        Verify that shell rules are skipped for .c files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("sh rule", scope="sh")
        def sh_rule(lines):
            """
            Rule that only applies to .sh files.
            """
            yield 1, "sh finding"

        findings = core.run_rules(["line\n"], filepath="foo.c")
        assert findings == []

        core._rules.clear()
        core._rules.extend(saved)

    def test_sh_rules_run_for_sh_file(self):
        """
        Verify that shell rules run for .sh files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("sh rule", scope="sh")
        def sh_rule(lines):
            """
            Rule that only applies to .sh files.
            """
            yield 1, "sh finding"

        findings = core.run_rules(["line\n"], filepath="foo.sh")
        assert len(findings) == 1
        assert findings[0][0] == "sh rule"

        core._rules.clear()
        core._rules.extend(saved)

    def test_c_rules_skipped_for_sh_file(self):
        """
        Verify that C rules are skipped for .sh files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("c rule")
        def c_rule(lines):
            """
            Rule that applies to C files.
            """
            yield 1, "c finding"

        findings = core.run_rules(["line\n"], filepath="foo.sh")
        assert findings == []

        core._rules.clear()
        core._rules.extend(saved)

    def test_openposix_rules_run_for_openposix_file(self):
        """
        Verify that openposix rules run for .c files under
        open_posix_testsuite/.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("openposix rule", scope="openposix")
        def op_rule(lines):
            """
            Rule that only applies to openposix tests.
            """
            yield 1, "op finding"

        filepath = "testcases/open_posix_testsuite/conformance/foo/1-1.c"
        findings = core.run_rules(["line\n"], filepath=filepath)
        assert len(findings) == 1
        assert findings[0][0] == "openposix rule"

        core._rules.clear()
        core._rules.extend(saved)

    def test_openposix_rules_skipped_for_regular_c(self):
        """
        Verify that openposix rules are skipped for regular .c files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("openposix rule", scope="openposix")
        def op_rule(lines):
            """
            Rule that only applies to openposix tests.
            """
            yield 1, "op finding"

        findings = core.run_rules(["line\n"], filepath="testcases/kernel/foo.c")
        assert findings == []

        core._rules.clear()
        core._rules.extend(saved)

    def test_c_rules_skipped_for_openposix_file(self):
        """
        Verify that C rules are skipped for openposix .c files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("c rule")
        def c_rule(lines):
            """
            Rule that applies to regular C files.
            """
            yield 1, "c finding"

        filepath = "testcases/open_posix_testsuite/conformance/foo/1-1.c"
        findings = core.run_rules(["line\n"], filepath=filepath)
        assert findings == []

        core._rules.clear()
        core._rules.extend(saved)

    def test_openposix_rules_run_for_openposix_header(self):
        """
        Verify that openposix rules run for .h files under
        open_posix_testsuite/.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("openposix rule", scope="openposix")
        def op_rule(lines):
            """
            Rule that applies to openposix .c and .h files.
            """
            yield 1, "op finding"

        filepath = "testcases/open_posix_testsuite/include/helpers.h"
        findings = core.run_rules(["line\n"], filepath=filepath)
        assert len(findings) == 1
        assert findings[0][0] == "openposix rule"

        core._rules.clear()
        core._rules.extend(saved)

    def test_openposix_only_skipped_for_header(self):
        """
        Verify that openposix_only rules are skipped for .h files
        under open_posix_testsuite/.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("openposix c-only rule", scope="openposix_only")
        def op_c_rule(lines):
            """
            Rule that only applies to openposix .c files.
            """
            yield 1, "c-only finding"

        filepath = "testcases/open_posix_testsuite/include/helpers.h"
        findings = core.run_rules(["line\n"], filepath=filepath)
        assert findings == []

        core._rules.clear()
        core._rules.extend(saved)

    def test_openposix_only_runs_for_openposix_c_file(self):
        """
        Verify that openposix_only rules run for .c files under
        open_posix_testsuite/.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("openposix c-only rule", scope="openposix_only")
        def op_c_rule(lines):
            """
            Rule that only applies to openposix .c files.
            """
            yield 1, "c-only finding"

        filepath = "testcases/open_posix_testsuite/conformance/foo/1-1.c"
        findings = core.run_rules(["line\n"], filepath=filepath)
        assert len(findings) == 1
        assert findings[0][0] == "openposix c-only rule"

        core._rules.clear()
        core._rules.extend(saved)

    def test_openposix_only_skipped_for_regular_c(self):
        """
        Verify that openposix_only rules are skipped for regular
        .c files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("openposix c-only rule", scope="openposix_only")
        def op_c_rule(lines):
            """
            Rule that only applies to openposix .c files.
            """
            yield 1, "c-only finding"

        findings = core.run_rules(["line\n"], filepath="testcases/kernel/foo.c")
        assert findings == []

        core._rules.clear()
        core._rules.extend(saved)

    def test_c_rules_skipped_for_openposix_header(self):
        """
        Verify that C rules are skipped for openposix .h files.
        """
        saved = core._rules[:]
        core._rules.clear()

        @core.rule("c rule")
        def c_rule(lines):
            """
            Rule that applies to regular C files.
            """
            yield 1, "c finding"

        filepath = "testcases/open_posix_testsuite/include/helpers.h"
        findings = core.run_rules(["line\n"], filepath=filepath)
        assert findings == []

        core._rules.clear()
        core._rules.extend(saved)
