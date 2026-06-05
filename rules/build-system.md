<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Build System

This file contains MANDATORY rules for build system files.

## Structure

LTP has one central build system under `include/mk/`. Each leaf test
directory has a small `Makefile` that includes two framework files:

- `testcases.mk` sets up paths, compiler, and default flags.
- `generic_leaf_target.mk` defines how to build, install, and clean the
  directory.

The framework automatically:

- Finds every `.c` file in the directory.
- Builds one binary per `.c` file (same name, no extension).
- Links each binary against `libltp` (`-lltp`).
- Provides `all`, `install`, and `clean` targets.

A test Makefile only needs to:

1. Set `top_srcdir` to point at the LTP root.
2. Include the two framework files.
3. Optionally declare per-target libraries or flags between the includes.

Do not write compile or link recipes by hand; the framework handles them.

## Makefile

### Standard template

Every leaf test directory MUST contain a `Makefile` of this form:

```make
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) <year> <author or company>

top_srcdir		?= ../../../..

include $(top_srcdir)/include/mk/testcases.mk

include $(top_srcdir)/include/mk/generic_leaf_target.mk
```

Rules:

- The first line MUST be the `SPDX-License-Identifier: GPL-2.0-or-later` tag,
  followed by a `Copyright` line.
- `top_srcdir` MUST point to the LTP root. Count `../` segments from the
  Makefile's directory: tests under `testcases/kernel/syscalls/<name>/` use
  `../../../..` (four levels).
- Use tabs (not spaces) for indentation and for aligning `?=` / `:=`.
- `generic_leaf_target.mk` MUST be the LAST include.

### Per-target flags

When a test needs extra libraries or compile flags, add a per-target
assignment between the two includes. Use `LDLIBS` for libraries and `CFLAGS`
or `CPPFLAGS` for compile-time flags:

```make
include $(top_srcdir)/include/mk/testcases.mk

foo01: LDLIBS += -lpthread
foo02: LDLIBS += -lrt
foo03: CFLAGS += -pthread

include $(top_srcdir)/include/mk/generic_leaf_target.mk
```

Rules:

- Use `+=`, never `=`, so framework defaults are preserved.
- One library per assignment line; do NOT bundle unrelated flags together.
- Directory-wide flags (applied to every test) MAY be set without a target
  prefix, e.g. `CFLAGS += -D_FILE_OFFSET_BITS=64`. Prefer per-target flags
  unless every test in the directory truly needs the flag.

### Excluding files and installing helpers

- A non-test helper binary that should be installed but not run as a test
  MUST be added to `INSTALL_TARGETS`, e.g. `INSTALL_TARGETS += test_ioctl`.
- A `.c` file that must NOT be built (e.g. unsupported on a platform) MUST
  be removed via `FILTER_OUT_MAKE_TARGETS += <name>`, guarded by the
  appropriate `ifeq` when conditional.
- Shell-script tests do not need entries in the Makefile; they are picked
  up automatically as long as they are executable.
- A directory may also override the auto-detected list with `MAKE_TARGETS`
  and remove generated files with `CLEAN_TARGETS`. Prefer the defaults; set
  these only when the framework cannot infer the right list.

### Conditional filtering

Guard `FILTER_OUT_MAKE_TARGETS` with the appropriate `ifeq` when a test is
unsupported on a platform:

```make
ifeq ($(ANDROID),1)
FILTER_OUT_MAKE_TARGETS	+= ioctl02
endif
```

### Shared helper `.c` files

When several tests in a directory share a helper `.c` file, filter the
helper out of the test list and add it as an object dependency AFTER the
framework include:

```make
FILTER_OUT_MAKE_TARGETS	:= bpf_common

include $(top_srcdir)/include/mk/generic_leaf_target.mk

$(MAKE_TARGETS): %: bpf_common.o
```

Do NOT write the rule before `generic_leaf_target.mk`; `MAKE_TARGETS` is
not populated yet at that point.

### Linking against LTP-internal libraries

LTP ships helper libraries under `libs/` (for example `libltpvdso`,
`libltpnuma`, `libltpipc`, `libltpswap`). To use one, declare it BEFORE
including `testcases.mk` and link the matching `-lltp<name>` via
`LTPLDLIBS` (NOT `LDLIBS`):

```make
top_srcdir		?= ../../../..

LTPLIBS = vdso

include $(top_srcdir)/include/mk/testcases.mk

LDLIBS += -lrt
clock_gettime04: LTPLDLIBS = -lltpvdso

include $(top_srcdir)/include/mk/generic_leaf_target.mk
```

Rules:

- `LTPLIBS` MUST be set before `testcases.mk` so the build system knows to
  build the dependency first.
- Use `LTPLDLIBS` for `-lltp<name>` flags. Do NOT put them in `LDLIBS`.
- External system libraries still go in `LDLIBS` (e.g. `-lrt`, `-lpthread`).

### What NOT to do

- Do NOT write explicit compile or link rules (`prog: prog.c` with a `cc`
  recipe), pattern rules, or `all:` / `clean:` targets.
- Do NOT add `-lltp` manually - it is linked automatically.
- Do NOT hardcode `-I../../../../include`; rely on `testcases.mk`.
- Do NOT override `CC`, `LD`, or `AR`; this breaks cross-compilation.
- Do NOT include `env_pre.mk` directly in a leaf Makefile; `testcases.mk`
  already includes it. `env_pre.mk` belongs in trunk (non-leaf) Makefiles.

## Trunk (non-leaf) Makefiles

Non-leaf directories that only recurse into subdirectories use the trunk
template:

```make
# SPDX-License-Identifier: GPL-2.0-or-later

top_srcdir		?= ../..

include $(top_srcdir)/include/mk/env_pre.mk
include $(top_srcdir)/include/mk/generic_trunk_target.mk
```

Rules:

- Use `env_pre.mk` + `generic_trunk_target.mk` ONLY in directories that
  contain other directories, never in leaf test directories.
- `top_srcdir` MUST point at the LTP root; count `../` from this Makefile.
- Do NOT mix trunk and leaf includes in the same Makefile.

## Kernel Modules

Tests that need an in-tree `.ko` use `module.mk`. The Makefile is read
twice: once by LTP and once by the kernel kbuild, so it MUST be guarded
with `ifneq ($(KERNELRELEASE),)`.

```make
# SPDX-License-Identifier: GPL-2.0-or-later

ifneq ($(KERNELRELEASE),)

obj-m := finit_module.o

else

top_srcdir		?= ../../../..

include $(top_srcdir)/include/mk/testcases.mk

REQ_VERSION_MAJOR	:= 3
REQ_VERSION_PATCH	:= 8

MAKE_TARGETS		:= finit_module01 finit_module02 finit_module.ko

include $(top_srcdir)/include/mk/module.mk
include $(top_srcdir)/include/mk/generic_leaf_target.mk

endif
```

Rules:

- `module.mk` MUST be included BEFORE `generic_leaf_target.mk`.
- `REQ_VERSION_MAJOR` / `REQ_VERSION_PATCH` declare the minimum kernel
  version for which the module build is attempted.
- `MAKE_TARGETS` MUST list the userspace test binaries AND the `.ko`
  file(s) explicitly; auto-detection does not pick up `.ko`.
- Module build failures are tolerated by design (forward compatibility
  with kernel internal API changes); the userspace test skips at runtime
  when the `.ko` is missing.
- Prerequisites (kernel headers, etc.) are detected by `configure`; do NOT
  hand-roll detection in the Makefile.

## Make Variables Reference

Use these variables instead of hardcoding flags or commands. Always append
with `+=` to preserve framework defaults.

- `CC`, `LD`, `AR`, `RANLIB` - toolchain; never override in a test Makefile.
- `CFLAGS` - C compiler flags (per-target preferred).
- `CPPFLAGS` - preprocessor flags such as `-I` and `-D`.
- `LDFLAGS` - linker flags other than libraries (e.g. `-L`, `-Wl,...`).
- `LDLIBS` - external libraries, e.g. `-lrt`, `-lpthread`, `-lutil`.
- `LTPLIBS` - LTP-internal helper libraries to build first (names from
  `libs/`, without the `libltp` prefix).
- `LTPLDLIBS` - link flags for LTP-internal libraries, e.g. `-lltpvdso`.
- `WCFLAGS` - warning flags (`-Wall`, `-Werror`, ...); set by the framework.
- `OPT_CFLAGS` - optimization flags; set by the framework.
- `DEBUG_CFLAGS` - debug flags (`-g`, ...); set by the framework.
- `MAKE_TARGETS` - binaries to build (auto-populated; override with care).
- `INSTALL_TARGETS` - extra files to install that are not tests.
- `FILTER_OUT_MAKE_TARGETS` - `.c` files to exclude from the build.
- `CLEAN_TARGETS` - extra files removed by `make clean`.

For the authoritative list, see comments in `include/mk/env_pre.mk` and
`include/mk/testcases.mk`.

## Before Committing

Rebuild from a clean tree (`make clean && make`) before sending any patch
that touches the build system. Incremental builds can hide missing
dependencies, ordering bugs, and broken cross-compilation.
