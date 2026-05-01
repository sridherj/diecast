# SPDX-License-Identifier: Apache-2.0
"""Run all test suites before committing.

Usage:
    precommit-tests                   # unit + integration (default)
    precommit-tests --suite unit
    precommit-tests --suite integration
    precommit-tests --suite ui
    precommit-tests -m "not slow"     # extra pytest marker filter
    precommit-tests -x                # stop after first suite failure
    precommit-tests --all             # include live suites (ui)

Each suite may run pytest more than once (one invocation per test root,
because the repo has two `tests` packages — `tests/` and
`cast-server/tests/` — that collide if collected in a single pytest run).
"""
import subprocess
import sys
import time
from pathlib import Path

import click

# precommit_tests.py -> dev_tools -> cast_server -> cast-server -> repo root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

SUITES = [
    {
        "name": "unit",
        "label": "Unit tests",
        "runs": [
            {
                "label": "tests/",
                "args": [
                    "pytest", "tests/", "-q", "--tb=short",
                    "--override-ini=addopts=",
                    "-m", "not integration",
                ],
                "cwd": PROJECT_ROOT,
            },
            {
                "label": "cast-server/tests/",
                "args": [
                    "pytest", "tests/", "-q", "--tb=short",
                    "--override-ini=addopts=",
                    "--ignore=tests/ui",
                    "-m", "not integration",
                ],
                "cwd": PROJECT_ROOT / "cast-server",
            },
        ],
    },
    {
        "name": "integration",
        "label": "Integration tests",
        "runs": [
            {
                "label": "tests/",
                "args": [
                    "pytest", "tests/", "-q", "--tb=short",
                    "--override-ini=addopts=",
                    "-m", "integration",
                ],
                "cwd": PROJECT_ROOT,
            },
            {
                "label": "cast-server/tests/",
                "args": [
                    "pytest", "tests/", "-q", "--tb=short",
                    "--override-ini=addopts=",
                    "--ignore=tests/ui",
                    "-m", "integration",
                ],
                "cwd": PROJECT_ROOT / "cast-server",
            },
        ],
    },
    {
        "name": "ui",
        "label": "UI tests (Playwright)",
        "live_only": True,
        "runs": [
            {
                "label": "cast-server/tests/ui/",
                "args": [
                    "pytest", "tests/ui/", "-v", "--tb=short",
                    "--override-ini=addopts=",
                ],
                "cwd": PROJECT_ROOT / "cast-server",
            },
        ],
    },
]

ALL_SUITE_NAMES = [s["name"] for s in SUITES]


def _run_one(run: dict, extra_args: list[str] | None) -> bool:
    cmd = [sys.executable, "-m"] + run["args"]
    if extra_args:
        cmd.extend(extra_args)
    click.echo(f"  $ ({run['label']}) {' '.join(run['args'])}")
    result = subprocess.run(cmd, cwd=run["cwd"])
    return result.returncode == 0


def run_suite(suite: dict, extra_args: list[str] | None = None) -> tuple[bool, float]:
    """Run a suite's invocations sequentially. Returns (passed, duration_seconds)."""
    click.echo()
    click.secho("=" * 60, fg="cyan")
    click.secho(f"  {suite['label']}", fg="cyan", bold=True)
    click.secho("=" * 60, fg="cyan")
    click.echo()

    start = time.time()
    all_passed = True
    for run in suite["runs"]:
        passed = _run_one(run, extra_args)
        if not passed:
            all_passed = False
    duration = time.time() - start

    return all_passed, duration


@click.command(name="precommit-tests")
@click.option(
    "--suite", "-s",
    type=click.Choice(ALL_SUITE_NAMES),
    help="Run only this suite.",
)
@click.option(
    "-m", "--marker",
    help="Extra pytest marker expression appended to the suite's default.",
)
@click.option(
    "--failfast", "-x",
    is_flag=True,
    help="Stop after the first suite failure.",
)
@click.option(
    "--all", "run_all",
    is_flag=True,
    help="Include live suites (ui) excluded by default.",
)
def precommit_tests(suite, marker, failfast, run_all):
    """Run test suites before pushing. Default: unit + integration."""
    extra_args = []
    if marker:
        extra_args.extend(["-m", marker])

    if suite:
        suites_to_run = [s for s in SUITES if s["name"] == suite]
    elif run_all:
        suites_to_run = SUITES
    else:
        suites_to_run = [s for s in SUITES if not s.get("live_only")]

    results: list[tuple[str, str, bool, float]] = []
    for s in suites_to_run:
        passed, duration = run_suite(s, extra_args)
        results.append((s["name"], s["label"], passed, duration))
        if not passed and failfast:
            break

    click.echo()
    click.secho("=" * 60, bold=True)
    click.secho("  RESULTS", bold=True)
    click.secho("=" * 60, bold=True)

    total = 0.0
    all_passed = True
    for name, label, passed, duration in results:
        total += duration
        if passed:
            click.secho(f"  [+] {label:<38} PASS  ({duration:.1f}s)", fg="green")
        else:
            click.secho(f"  [X] {label:<38} FAIL  ({duration:.1f}s)", fg="red")
            all_passed = False

    click.echo(f"\n  Total: {total:.1f}s")

    if all_passed:
        click.secho("\n  All suites passed!\n", fg="green", bold=True)
    else:
        failed = [name for name, _, passed, _ in results if not passed]
        click.secho(f"\n  Failed: {', '.join(failed)}", fg="red")
        click.echo(f"  Re-run: precommit-tests --suite {failed[0]}\n")
        sys.exit(1)


if __name__ == "__main__":
    precommit_tests()
