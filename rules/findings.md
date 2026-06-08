<!-- SPDX-License-Identifier: GPL-2.0-or-later -->

# Findings Usage

This document defines rules for the unified artifacts that collect linter
and reviewer findings during a review session.

## Schema

```json
{
  "version": 1,
  "scope": "file",
  "findings": [
    {
      "file": "testcases/kernel/syscalls/foo/foo01.c",
      "line": 1,
      "rule_id": "LTP-C001",
      "confidence": "mechanical",
      "source": "linter",
      "message": "Missing SPDX header",
      "detail": "first line must contain SPDX-License-Identifier",
      "commit": "abc123def012"
    },
    {
      "file": "testcases/kernel/syscalls/foo/foo01.c",
      "line": 47,
      "rule_id": "REV-001",
      "confidence": "semantic",
      "source": "reviewer",
      "message": "Missing cleanup handler",
      "detail": "tst_brk(TBROK) after mmap but no munmap in cleanup",
      "commit": "abc123def012"
    }
  ]
}
```

## Field Reference

### Top-level

| Field      | Type     | Description                       |
| ---------- | -------- | --------------------------------- |
| `version`  | integer  | Schema version, currently `1`     |
| `scope`    | string   | Lint scope: `"file"` or `"patch"` |
| `findings` | object[] | Array of finding objects          |

### Finding object

| Field        | Type           | Required | Description                                      |
| ------------ | -------------- | -------- | ------------------------------------------------ |
| `file`       | string         | yes      | Path to the file relative to repo root           |
| `line`       | integer        | yes      | Line number in the file                          |
| `rule_id`    | string         | yes      | Stable identifier (linter rule ID or `REV-NNN`)  |
| `confidence` | string         | yes      | One of: `mechanical`, `semantic`, `experimental` |
| `source`     | string         | yes      | Who produced this finding                        |
| `message`    | string         | yes      | Short summary of the issue                       |
| `detail`     | string         | yes      | Explanation with enough context to act on        |
| `commit`     | string         | yes      | Short commit hash that introduced the line       |

### `source` values

| Value        | Meaning                          | False-positive check    |
| ------------ | -------------------------------- | ----------------------- |
| `"linter"`   | Produced by deterministic linter | Skip - already verified |
| `"reviewer"` | Produced by LLM during review    | Required                |

### `confidence` values

| Value            | Meaning                                            |
| ---------------- | -------------------------------------------------- |
| `"mechanical"`   | Regex/AST check, deterministic, no judgment needed |
| `"semantic"`     | Requires understanding of code logic               |
| `"experimental"` | Heuristic, may have high false-positive rate       |

## Workflow Contract

- ALL issues found by the linter MUST have `"source": "linter"`.
- ALL issues found by the reviewer MUST have `"source": "reviewer"`.
- ALL issues marked with `mechanical` confidence MUST be considered errors
  and they must NOT be verified by the reviewer.
- ALL issues marked with `semantic` or `experimental` confidence MUST be
  always verified by the reviewer.

## Rule ID Convention

- Linter rules use their registered IDs: `LTP-C001`, `LTP-S002`,
  `LTP-O003`, etc.
- Reviewer findings use `REV-NNN` where NNN is a sequential number starting
  from 001 within a single review session.
