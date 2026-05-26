"""
Tests for rules_c module: C test linter rules.
"""

from rules_c import (
    check_cleanup_fn_param,
    check_copyright,
    check_description_tag,
    check_doc_comment,
    check_exit_in_child,
    check_fd_init,
    check_fd_reset_after_safe_close,
    check_fd_validity,
    check_have_guard_placement,
    check_needs_kconfigs,
    check_needs_tmpdir,
    check_no_main,
    check_spdx,
    check_struct_tst_test,
    check_supported_archs,
    check_tst_syscall,
    check_tst_test_header,
)


class TestCheckSpdx:
    """
    Tests for the SPDX header rule.
    """

    def test_missing_spdx(self):
        """
        Verify finding when SPDX header is absent.
        """
        results = list(check_spdx(["// no spdx\n"]))
        assert len(results) == 1
        assert results[0][0] == 1

    def test_present_spdx(self):
        """
        Verify no finding when SPDX header is present.
        """
        results = list(check_spdx(["// SPDX-License-Identifier: GPL-2.0\n"]))
        assert results == []

    def test_empty_file(self):
        """
        Verify finding on empty input.
        """
        results = list(check_spdx([]))
        assert len(results) == 1


class TestCheckCopyright:
    """
    Tests for the copyright rule.
    """

    def test_missing_copyright(self):
        """
        Verify finding when no copyright line exists.
        """
        results = list(check_copyright(["// just a comment\n"]))
        assert len(results) == 1

    def test_present_copyright(self):
        """
        Verify no finding when copyright with year is present.
        """
        lines = [" * Copyright (c) 2024 SUSE LLC\n"]
        assert list(check_copyright(lines)) == []

    def test_copyright_case_insensitive(self):
        """
        Verify copyright detection is case-insensitive.
        """
        lines = [" * copyright (C) 2024 Author\n"]
        assert list(check_copyright(lines)) == []


class TestCheckDocComment:
    """
    Tests for the doc comment block rule.
    """

    def test_missing_doc_comment(self):
        """
        Verify finding when no doc comment block is present.
        """
        lines = ["// SPDX\n", "/* normal comment */\n"]
        results = list(check_doc_comment(lines))
        assert len(results) == 1

    def test_present_doc_comment(self):
        """
        Verify no finding when doc comment block exists.
        """
        lines = ["// SPDX\n", "/*\\\n", " * doc\n", " */\n"]
        assert list(check_doc_comment(lines)) == []

    def test_indented_doc_comment(self):
        """
        Verify detection of indented doc comment blocks.
        """
        lines = ["  /*\\\n"]
        assert list(check_doc_comment(lines)) == []


class TestCheckDescriptionTag:
    """
    Tests for the deprecated [Description] tag rule.
    """

    def test_with_description_tag(self):
        """
        Verify finding when [Description] is used.
        """
        lines = [" * [Description]\n"]
        results = list(check_description_tag(lines))
        assert len(results) == 1
        assert results[0][0] == 1

    def test_without_description_tag(self):
        """
        Verify no finding when [Description] is absent.
        """
        lines = [" * Some description text\n"]
        assert list(check_description_tag(lines)) == []


class TestCheckTstTestHeader:
    """
    Tests for the test header rule.
    """

    def test_old_header_only(self):
        """
        Verify finding when only test.h is included.
        """
        lines = ['#include "test.h"\n']
        results = list(check_tst_test_header(lines))
        assert len(results) == 1

    def test_new_header(self):
        """
        Verify no finding when tst_test.h is included.
        """
        lines = ['#include "tst_test.h"\n']
        assert list(check_tst_test_header(lines)) == []

    def test_both_headers(self):
        """
        Verify no finding when both headers are included.
        """
        lines = ['#include "test.h"\n', '#include "tst_test.h"\n']
        assert list(check_tst_test_header(lines)) == []


class TestCheckNoMain:
    """
    Tests for the unexpected main() rule.
    """

    def test_main_without_no_default(self):
        """
        Verify finding when main() is defined without TST_NO_DEFAULT_MAIN.
        """
        lines = ["int main(void) {\n", "}\n"]
        results = list(check_no_main(lines))
        assert len(results) == 1
        assert results[0][0] == 1

    def test_main_with_no_default(self):
        """
        Verify no finding when TST_NO_DEFAULT_MAIN is set.
        """
        lines = ["#define TST_NO_DEFAULT_MAIN\n", "int main(void) {\n"]
        assert list(check_no_main(lines)) == []

    def test_void_main(self):
        """
        Verify finding for void main() variant.
        """
        lines = ["void main(int argc) {\n"]
        results = list(check_no_main(lines))
        assert len(results) == 1

    def test_no_main(self):
        """
        Verify no finding when main() is not present.
        """
        lines = ["static void run(void) {\n", "}\n"]
        assert list(check_no_main(lines)) == []


class TestCheckStructTstTest:
    """
    Tests for the missing struct tst_test rule.
    """

    def test_missing_struct(self):
        """
        Verify finding when struct tst_test is absent.
        """
        lines = ["static void run(void) {}\n"]
        results = list(check_struct_tst_test(lines))
        assert len(results) == 1

    def test_present_struct(self):
        """
        Verify no finding when struct tst_test is defined.
        """
        lines = ["static struct tst_test test = {\n"]
        assert list(check_struct_tst_test(lines)) == []

    def test_no_default_main_skips(self):
        """
        Verify no finding when TST_NO_DEFAULT_MAIN is set.
        """
        lines = ["#define TST_NO_DEFAULT_MAIN\n", "int main(void) {}\n"]
        assert list(check_struct_tst_test(lines)) == []



class TestCheckFdInit:
    """
    Tests for the FD initialization rule.
    """

    def test_uninitialized_fd(self):
        """
        Verify finding when static int fd is not initialized.
        """
        lines = ["static int fd;\n"]
        results = list(check_fd_init(lines))
        assert len(results) == 1
        assert "-1" in results[0][1]

    def test_initialized_fd(self):
        """
        Verify no finding when fd is initialized to -1.
        """
        lines = ["static int fd = -1;\n"]
        assert list(check_fd_init(lines)) == []

    def test_non_fd_variable(self):
        """
        Verify no finding for non-fd static ints.
        """
        lines = ["static int count;\n"]
        assert list(check_fd_init(lines)) == []

    def test_fd_suffix(self):
        """
        Verify finding for variables with fd in the name.
        """
        lines = ["static int dev_fd;\n"]
        results = list(check_fd_init(lines))
        assert len(results) == 1
        assert "dev_fd" in results[0][1]


class TestCheckFdValidity:
    """
    Tests for the FD validity check rule.
    """

    def test_fd_gte_zero(self):
        """
        Verify finding for fd >= 0 check.
        """
        lines = ["\tif (fd >= 0)\n"]
        results = list(check_fd_validity(lines))
        assert len(results) == 1
        assert "!= -1" in results[0][1]

    def test_fd_gt_zero(self):
        """
        Verify finding for fd > 0 check.
        """
        lines = ["\tif (fd > 0)\n"]
        results = list(check_fd_validity(lines))
        assert len(results) == 1

    def test_fd_neq_minus_one(self):
        """
        Verify no finding for correct fd != -1 check.
        """
        lines = ["\tif (fd != -1)\n"]
        assert list(check_fd_validity(lines)) == []

    def test_comment_skipped(self):
        """
        Verify that fd checks in comments are ignored.
        """
        lines = ["// if (fd >= 0)\n"]
        assert list(check_fd_validity(lines)) == []


class TestCheckFdResetAfterSafeClose:
    """
    Tests for the redundant fd reset after SAFE_CLOSE rule.
    """

    def test_redundant_reset(self):
        """
        Verify finding when fd = -1 follows SAFE_CLOSE(fd).
        """
        lines = ["\tSAFE_CLOSE(fd);\n", "\tfd = -1;\n"]
        results = list(check_fd_reset_after_safe_close(lines))
        assert len(results) == 1
        assert "redundant" in results[0][1]

    def test_no_reset(self):
        """
        Verify no finding when SAFE_CLOSE is not followed by reset.
        """
        lines = ["\tSAFE_CLOSE(fd);\n", "\treturn;\n"]
        assert list(check_fd_reset_after_safe_close(lines)) == []

    def test_different_fd(self):
        """
        Verify no finding when reset is for a different fd.
        """
        lines = ["\tSAFE_CLOSE(fd);\n", "\tfd2 = -1;\n"]
        assert list(check_fd_reset_after_safe_close(lines)) == []

    def test_whitespace_variation(self):
        """
        Verify finding when fd = -1 has irregular whitespace.
        """
        lines = ["\tSAFE_CLOSE(fd_out);\n", "\tfd_out  =  -1 ;\n"]
        results = list(check_fd_reset_after_safe_close(lines))
        assert len(results) == 1
        assert "redundant" in results[0][1]

    def test_safe_close_last_line(self):
        """
        Verify no crash when SAFE_CLOSE is on the last line.
        """
        lines = ["\tSAFE_CLOSE(fd);\n"]
        assert list(check_fd_reset_after_safe_close(lines)) == []


class TestCheckHaveGuardPlacement:
    """
    Tests for the HAVE_* guard placement rule.
    """

    def test_guard_inside_function(self):
        """
        Verify finding when #ifdef HAVE_* is inside a function body.
        """
        lines = [
            "void run(void) {\n",
            "#ifdef HAVE_SYS_XATTR_H\n",
            "\tdo_something();\n",
            "#endif\n",
            "}\n",
        ]
        results = list(check_have_guard_placement(lines))
        assert len(results) == 1
        assert "file level" in results[0][1]

    def test_guard_at_file_level(self):
        """
        Verify no finding when #ifdef HAVE_* is at file level.
        """
        lines = [
            "#ifdef HAVE_SYS_XATTR_H\n",
            "void run(void) {\n",
            "}\n",
            "#endif\n",
        ]
        assert list(check_have_guard_placement(lines)) == []

    def test_non_have_ifdef(self):
        """
        Verify no finding for non-HAVE_* ifdefs inside functions.
        """
        lines = [
            "void run(void) {\n",
            "#ifdef DEBUG\n",
            "\tlog();\n",
            "#endif\n",
            "}\n",
        ]
        assert list(check_have_guard_placement(lines)) == []


class TestCheckNeedsTmpdir:
    """
    Tests for the .needs_tmpdir rule.
    """

    def test_safe_creat_without_tmpdir(self):
        """
        Verify finding when SAFE_CREAT is used without .needs_tmpdir.
        """
        lines = ["\tSAFE_CREAT(fname, 0644);\n"]
        results = list(check_needs_tmpdir(lines))
        assert len(results) == 1
        assert ".needs_tmpdir" in results[0][1]

    def test_safe_open_create_without_tmpdir(self):
        """
        Verify finding when SAFE_OPEN with O_CREAT is used without .needs_tmpdir.
        """
        lines = ["\tSAFE_OPEN(fname, O_CREAT | O_RDWR, 0644);\n"]
        results = list(check_needs_tmpdir(lines))
        assert len(results) == 1

    def test_with_tmpdir(self):
        """
        Verify no finding when .needs_tmpdir is set.
        """
        lines = [
            "\tSAFE_CREAT(fname, 0644);\n",
            "\t.needs_tmpdir = 1,\n",
        ]
        assert list(check_needs_tmpdir(lines)) == []

    def test_with_mntpoint(self):
        """
        Verify no finding when .mntpoint is set.
        """
        lines = [
            "\tSAFE_CREAT(fname, 0644);\n",
            "\t.mntpoint = MNTPOINT,\n",
        ]
        assert list(check_needs_tmpdir(lines)) == []

    def test_with_needs_device(self):
        """
        Verify no finding when .needs_device is set.
        """
        lines = [
            "\tSAFE_CREAT(fname, 0644);\n",
            "\t.needs_device = 1,\n",
        ]
        assert list(check_needs_tmpdir(lines)) == []

    def test_safe_open_readonly(self):
        """
        Verify no finding for SAFE_OPEN without create flags.
        """
        lines = ["\tSAFE_OPEN(fname, O_RDONLY);\n"]
        assert list(check_needs_tmpdir(lines)) == []

    def test_safe_open_wronly_no_creat(self):
        """
        Verify no finding for SAFE_OPEN with O_WRONLY but no O_CREAT
        (opening existing file like /proc or /sys).
        """
        lines = ['\tSAFE_OPEN("/proc/sys/net/foo", O_WRONLY);\n']
        assert list(check_needs_tmpdir(lines)) == []

    def test_safe_open_rdwr_no_creat(self):
        """
        Verify no finding for SAFE_OPEN with O_RDWR but no O_CREAT.
        """
        lines = ["\tSAFE_OPEN(devpath, O_RDWR);\n"]
        assert list(check_needs_tmpdir(lines)) == []


class TestCheckExitInChild:
    """
    Tests for the exit() vs _exit() rule.
    """

    def test_exit_used(self):
        """
        Verify no finding when exit(0) is used.
        """
        lines = ["\t\texit(0);\n"]
        assert list(check_exit_in_child(lines)) == []

    def test_underscore_exit_flagged(self):
        """
        Verify finding when _exit() is used.
        """
        lines = ["\t\t_exit(0);\n"]
        results = list(check_exit_in_child(lines))
        assert len(results) == 1
        assert "exit()" in results[0][1]

    def test_underscore_exit_nonzero(self):
        """
        Verify finding when _exit(1) is used.
        """
        lines = ["\t\t_exit(1);\n"]
        results = list(check_exit_in_child(lines))
        assert len(results) == 1

    def test_comment_skipped(self):
        """
        Verify that _exit in comments is ignored.
        """
        lines = ["// _exit(0);\n"]
        assert list(check_exit_in_child(lines)) == []

    def test_doc_comment_skipped(self):
        """
        Verify that _exit in doc comments is ignored.
        """
        lines = [" * _exit(0) should not be used\n"]
        assert list(check_exit_in_child(lines)) == []


class TestCheckCleanupFnParam:
    """
    Tests for the legacy cleanup_fn parameter rule.
    """

    def test_with_cleanup_fn(self):
        """
        Verify finding for safe_* with cleanup_fn parameter.
        """
        lines = [
            "void *safe_mysyscall(const char *file, const int lineno,"
            " void (*cleanup_fn)(void), size_t size)\n"
        ]
        results = list(check_cleanup_fn_param(lines))
        assert len(results) == 1
        assert "legacy" in results[0][1]

    def test_without_cleanup_fn(self):
        """
        Verify no finding for safe_* without cleanup_fn.
        """
        lines = [
            "void *safe_mysyscall(const char *file, const int lineno, size_t size)\n"
        ]
        assert list(check_cleanup_fn_param(lines)) == []

    def test_comment_skipped(self):
        """
        Verify that cleanup_fn in comments is ignored.
        """
        lines = ["// safe_foo(file, line, cleanup_fn, size)\n"]
        assert list(check_cleanup_fn_param(lines)) == []


class TestCheckTstSyscall:
    """
    Tests for the tst_syscall vs raw syscall() rule.
    """

    def test_raw_syscall(self):
        """
        Verify finding for plain syscall() call.
        """
        lines = ["\tsyscall(__NR_foo, arg1, arg2);\n"]
        results = list(check_tst_syscall(lines))
        assert len(results) == 1
        assert "tst_syscall" in results[0][1]

    def test_tst_syscall_ok(self):
        """
        Verify no finding when tst_syscall() is used.
        """
        lines = ["\ttst_syscall(__NR_foo, arg1, arg2);\n"]
        assert list(check_tst_syscall(lines)) == []

    def test_exempt_in_test_macro(self):
        """
        Verify no finding for syscall() inside TEST().
        """
        lines = ["\tTEST(syscall(__NR_foo, arg1));\n"]
        assert list(check_tst_syscall(lines)) == []

    def test_comment_skipped(self):
        """
        Verify that syscall in comments is ignored.
        """
        lines = ["// syscall(__NR_foo);\n"]
        assert list(check_tst_syscall(lines)) == []


class TestCheckSupportedArchs:
    """
    Tests for the .supported_archs rule.
    """

    def test_arch_guard_without_supported_archs(self):
        """
        Verify finding when #if defined(__x86_64__) is used without
        .supported_archs.
        """
        lines = ["#if defined(__x86_64__)\n"]
        results = list(check_supported_archs(lines))
        assert len(results) == 1
        assert ".supported_archs" in results[0][1]

    def test_with_supported_archs(self):
        """
        Verify no finding when .supported_archs is set.
        """
        lines = [
            "#if defined(__x86_64__)\n",
            '\t.supported_archs = (const char *const []){"x86_64", NULL},\n',
        ]
        assert list(check_supported_archs(lines)) == []

    def test_non_framework_arch(self):
        """
        Verify no finding for architectures not in the framework list.
        """
        lines = ["#if defined(__riscv)\n"]
        assert list(check_supported_archs(lines)) == []


class TestCheckNeedsKconfigs:
    """
    Tests for the .needs_kconfigs rule.
    """

    def test_manual_config_check(self):
        """
        Verify finding when TCONF with CONFIG_ string is used.
        """
        lines = ['\ttst_brk(TCONF, "CONFIG_BLK_DEV_INTEGRITY is not enabled");\n']
        results = list(check_needs_kconfigs(lines))
        assert len(results) == 1
        assert ".needs_kconfigs" in results[0][1]

    def test_with_needs_kconfigs(self):
        """
        Verify no finding when .needs_kconfigs is set.
        """
        lines = [
            '\ttst_brk(TCONF, "CONFIG_BLK_DEV_INTEGRITY is not enabled");\n',
            '\t.needs_kconfigs = (const char *[]){"CONFIG_BLK_DEV_INTEGRITY=y", NULL},\n',
        ]
        assert list(check_needs_kconfigs(lines)) == []

    def test_non_config_tconf(self):
        """
        Verify no finding for TCONF without CONFIG_ reference.
        """
        lines = ['\ttst_brk(TCONF, "feature not supported");\n']
        assert list(check_needs_kconfigs(lines)) == []

    def test_comment_skipped(self):
        """
        Verify that CONFIG_ in comments is ignored.
        """
        lines = ['// tst_brk(TCONF, "CONFIG_FOO not set");\n']
        assert list(check_needs_kconfigs(lines)) == []
