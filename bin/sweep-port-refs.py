#!/usr/bin/env python3
"""Internal use; not on user PATH. Markdown-aware sweep for port/host literals.

Rewrites `localhost:8000` / `127.0.0.1:8000` references in Markdown files,
preserving the distinction between executable code (uses `${CAST_*:-default}`
env-var substitution so future cloud deploys flip with no skill edits) and
narrative prose (uses literal `localhost:8005` / `127.0.0.1:8005`).

A line is treated as code when (a) we are inside a fenced ```bash / ```sh /
```shell block, or (b) the host:port literal appears inside an inline backtick
span on that line and the same span contains `curl` (an executable invocation,
not a bare display URL).

Usage:
    bin/sweep-port-refs.py [--check | --apply] PATH...

--check exits non-zero if any change would be made (CI-friendly).
--apply writes in place and reports modified files to stdout.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Code-context replacements (env-var substitution).
CODE_LOCALHOST = (re.compile(r"http://localhost:8000\b"),
                  "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}")
CODE_LOOPBACK = (re.compile(r"http://127\.0\.0\.1:8000\b"),
                 "http://${CAST_BIND_HOST:-127.0.0.1}:${CAST_PORT:-8005}")

# Prose replacements (literal default port).
PROSE_LOCALHOST = (re.compile(r"http://localhost:8000\b"), "http://localhost:8005")
PROSE_LOOPBACK = (re.compile(r"http://127\.0\.0\.1:8000\b"), "http://127.0.0.1:8005")

FENCE_OPEN = re.compile(r"^\s*```(?:bash|sh|shell)\b", re.IGNORECASE)
FENCE_CLOSE = re.compile(r"^\s*```\s*$")
ANY_FENCE = re.compile(r"^\s*```")
INLINE_SPAN = re.compile(r"`([^`\n]+)`")


def _rewrite_inline_spans(line: str) -> str:
    """Apply code-context replacements only inside backtick spans containing curl."""
    def repl(match: re.Match[str]) -> str:
        span = match.group(1)
        if "curl" not in span:
            return match.group(0)
        new = CODE_LOCALHOST[0].sub(CODE_LOCALHOST[1], span)
        new = CODE_LOOPBACK[0].sub(CODE_LOOPBACK[1], new)
        return f"`{new}`"
    return INLINE_SPAN.sub(repl, line)


def rewrite(text: str) -> str:
    out: list[str] = []
    in_shell_fence = False
    in_other_fence = False
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\n")
        if not (in_shell_fence or in_other_fence) and FENCE_OPEN.match(stripped):
            in_shell_fence = True
            out.append(line)
            continue
        if not (in_shell_fence or in_other_fence) and ANY_FENCE.match(stripped):
            in_other_fence = True
            out.append(line)
            continue
        if (in_shell_fence or in_other_fence) and FENCE_CLOSE.match(stripped):
            in_shell_fence = False
            in_other_fence = False
            out.append(line)
            continue

        if in_shell_fence:
            new = CODE_LOCALHOST[0].sub(CODE_LOCALHOST[1], line)
            new = CODE_LOOPBACK[0].sub(CODE_LOOPBACK[1], new)
            out.append(new)
        elif in_other_fence:
            # Non-bash fenced block — treat as prose (e.g. ```python, ```yaml).
            new = PROSE_LOCALHOST[0].sub(PROSE_LOCALHOST[1], line)
            new = PROSE_LOOPBACK[0].sub(PROSE_LOOPBACK[1], new)
            out.append(new)
        else:
            # Prose: first rewrite qualifying inline `code` spans, then the rest.
            new = _rewrite_inline_spans(line)
            new = PROSE_LOCALHOST[0].sub(PROSE_LOCALHOST[1], new)
            new = PROSE_LOOPBACK[0].sub(PROSE_LOOPBACK[1], new)
            out.append(new)
    return "".join(out)


def iter_targets(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_file() and p.suffix == ".md":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()

    files = iter_targets(args.paths)
    changed: list[Path] = []
    for f in files:
        try:
            original = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        new = rewrite(original)
        if new != original:
            changed.append(f)
            if args.apply:
                f.write_text(new)

    if args.check:
        if changed:
            for f in changed:
                print(f)
            return 1
        return 0

    for f in changed:
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
