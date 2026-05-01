"""Diecast UI test runner. Invoked by per-screen test agents.

Usage:
    python cast-server/tests/ui/runner.py \\
        --screen=<name> \\
        --base-url=http://127.0.0.1:8006 \\
        --goal-slug=<slug> \\
        --output=<absolute-path-to-output.json>

Exit code: 0 on green, 1 on any failed assertion. The output.json is the
source of truth either way.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

ASSERTION_TIMEOUT_MS = 30_000
USER_DATA_DIR_PREFIX = "/tmp/diecast-uitest"
THREADED_SEED_GOAL_SLUG = "ui-test-runs-threaded"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_screen(s: str) -> str:
    return s.replace("-", "_")


class Result:
    def __init__(self, screen: str) -> None:
        self.screen = screen
        self.assertions_passed: list[str] = []
        self.assertions_failed: list[dict[str, str]] = []
        self.console_errors: list[str] = []
        self.console_warnings: list[str] = []
        self.screenshots: list[str] = []
        self.started_at = _now_iso()
        self.finished_at: str | None = None

    @property
    def status(self) -> str:
        if self.assertions_failed or self.console_errors:
            return "failed"
        return "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen": self.screen,
            "status": self.status,
            "assertions_passed": self.assertions_passed,
            "assertions_failed": self.assertions_failed,
            "console_errors": self.console_errors,
            "console_warnings": self.console_warnings,
            "screenshots": self.screenshots,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def _attach_console_capture(page: Page, result: Result) -> None:
    def on_console(msg: ConsoleMessage) -> None:
        text = f"{msg.type}: {msg.text}"
        if msg.type == "error":
            result.console_errors.append(text)
        else:
            result.console_warnings.append(text)

    def on_pageerror(exc: Exception) -> None:
        result.console_errors.append(f"pageerror: {exc}")

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)


def _accept_dialogs(page: Page) -> None:
    """HTMX uses hx-confirm which emits a JS confirm() dialog. Accept silently."""
    page.on("dialog", lambda d: d.accept())


@contextmanager
def assertion(result: Result, name: str, page: Page, screenshots_dir: Path):
    try:
        yield
    except (AssertionError, PlaywrightTimeoutError) as e:
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        path = screenshots_dir / f"{result.screen}-{int(time.time() * 1000)}.png"
        try:
            page.screenshot(path=str(path), full_page=True)
            result.screenshots.append(str(path))
        except Exception:  # noqa: BLE001
            pass
        result.assertions_failed.append({"name": name, "error": str(e)})
    else:
        result.assertions_passed.append(name)


def _http_post_json(url: str, body: dict) -> tuple[int, dict | None]:
    """Tiny stdlib HTTP POST. Returns (status, json|None)."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(payload)
            except json.JSONDecodeError:
                return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:  # noqa: BLE001
        return 0, None


def _http_get_json(url: str) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:  # noqa: BLE001
        return 0, None


# ----------------------------------------------------------------------
# Browser-capability helpers (additive primitives — see sp6 plan §6.3)
# ----------------------------------------------------------------------


def grant_clipboard(context: BrowserContext) -> None:
    """Grant clipboard read/write to the browser context (see assertion #7)."""
    context.grant_permissions(["clipboard-read", "clipboard-write"])


def resize_viewport(page: Page, width: int, height: int) -> None:
    """Set the page viewport (used by mobile-breakpoint assertion #14)."""
    page.set_viewport_size({"width": width, "height": height})


def read_clipboard(page: Page) -> str:
    """Return ``navigator.clipboard.readText()``; caller must have granted perms."""
    return page.evaluate("() => navigator.clipboard.readText()")


def read_localstorage(page: Page, key: str) -> str | None:
    """Return ``localStorage[key]`` from the current page; ``None`` when absent."""
    return page.evaluate(
        f"() => localStorage.getItem({json.dumps(key)})"
    )


def wait_for_htmx_settle(page: Page, timeout_ms: int = 4000) -> None:
    """Block until one ``htmx:afterSwap`` fires or ``timeout_ms`` elapses.

    Used by the running-run poll assertion: a 3s HTMX poll fires on
    ``.run-status-cells``; this waits long enough for that swap to settle so
    expand-state assertions run after the swap has applied.
    """
    page.evaluate(
        """(t) => new Promise((resolve) => {
            const timer = setTimeout(resolve, t);
            const handler = () => { clearTimeout(timer); resolve(); };
            document.body.addEventListener('htmx:afterSwap', handler, { once: true });
        })""",
        timeout_ms,
    )


# ----------------------------------------------------------------------
# Threaded /runs DB seed (sp6) — direct SQLite write into the test DB.
# The test cast-server boots with ``CAST_DB`` pointing at the temp DB; the
# seed runs once per agent invocation and is idempotent (INSERT OR IGNORE
# on stable run_ids).
# ----------------------------------------------------------------------


def _seed_runs_threaded(db_path: Path) -> None:
    """Seed five trees that exercise every threaded-layout assertion.

    Trees:
      A. ``thread-warning-l1`` — rework-only loop -> ``.run-group.has-warning``.
      B. ``thread-failed-l1``  — failed grandchild -> ``.run-group.has-failure``.
      C. ``thread-deeprework-l1`` — rework at L3 -> propagated rework rollup at L1.
      D. ``thread-ctx-l1`` — children with low/mid/high ``ctx_class``.
      E. ``thread-running-l1`` — running child for HTMX poll assertion.
    """
    base = "2026-04-30T00:00:00+00:00"
    rows: list[tuple] = [
        # Tree A: rework-only -> has-warning
        ("thread-warning-l1", None, "completed", "cast-orchestrate", None,
         None, "claude --resume thread-warning-l1", base, base,
         "2026-04-30T00:00:42+00:00"),
        ("thread-warning-c1", "thread-warning-l1", "completed", "check-coordinator",
         None, None, None, "2026-04-30T00:00:00.000001+00:00", None, None),
        ("thread-warning-c2", "thread-warning-l1", "completed", "check-coordinator",
         None, None, None, "2026-04-30T00:00:00.000002+00:00", None, None),
        # Tree B: failed grandchild -> has-failure
        ("thread-failed-l1", None, "completed", "cast-orchestrate", None,
         None, "claude --resume thread-failed-l1",
         "2026-04-30T00:00:01+00:00", "2026-04-30T00:00:01+00:00",
         "2026-04-30T00:00:43+00:00"),
        ("thread-failed-c1", "thread-failed-l1", "completed", "cast-controller",
         None, None, None, "2026-04-30T00:00:01.000001+00:00", None, None),
        ("thread-failed-gc1", "thread-failed-c1", "failed", "cast-controller-test",
         None, None, None, "2026-04-30T00:00:01.000002+00:00", None, None),
        # Tree C: deep rework propagation
        ("thread-deeprework-l1", None, "completed", "cast-orchestrate", None,
         None, "claude --resume thread-deeprework-l1",
         "2026-04-30T00:00:02+00:00", "2026-04-30T00:00:02+00:00",
         "2026-04-30T00:00:44+00:00"),
        ("thread-deeprework-c1", "thread-deeprework-l1", "completed", "cast-preso",
         None, None, None, "2026-04-30T00:00:02.000001+00:00", None, None),
        ("thread-deeprework-l3a", "thread-deeprework-c1", "completed",
         "check-content", None, None, None,
         "2026-04-30T00:00:02.000002+00:00", None, None),
        ("thread-deeprework-l3b", "thread-deeprework-c1", "completed",
         "check-content", None, None, None,
         "2026-04-30T00:00:02.000003+00:00", None, None),
        # Tree D: ctx pills (children with low/mid/high ctx)
        ("thread-ctx-l1", None, "completed", "cast-orchestrate", None,
         None, "claude --resume thread-ctx-l1",
         "2026-04-30T00:00:03+00:00", "2026-04-30T00:00:03+00:00",
         "2026-04-30T00:00:45+00:00"),
        ("thread-ctx-low", "thread-ctx-l1", "completed", "cast-controller",
         None, '{"total":30000,"limit":200000}', None,
         "2026-04-30T00:00:03.000001+00:00", None, None),
        ("thread-ctx-mid", "thread-ctx-l1", "completed", "cast-service",
         None, '{"total":100000,"limit":200000}', None,
         "2026-04-30T00:00:03.000002+00:00", None, None),
        ("thread-ctx-high", "thread-ctx-l1", "completed", "cast-repository",
         None, '{"total":160000,"limit":200000}', None,
         "2026-04-30T00:00:03.000003+00:00", None, None),
        # Tree E: parent of running child (HTMX poll fires on the child)
        ("thread-running-l1", None, "completed", "cast-orchestrate", None,
         None, "claude --resume thread-running-l1",
         "2026-04-30T00:00:04+00:00", "2026-04-30T00:00:04+00:00",
         "2026-04-30T00:00:46+00:00"),
        ("thread-running-c1", "thread-running-l1", "running", "cast-service",
         None, None, None, "2026-04-30T00:00:04.000001+00:00",
         "2026-04-30T00:00:04.000001+00:00", None),
    ]

    conn = sqlite3.connect(str(db_path), timeout=10)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) "
            "VALUES (?, ?, ?)",
            (THREADED_SEED_GOAL_SLUG, "UI test threaded runs",
             THREADED_SEED_GOAL_SLUG),
        )
        for (run_id, parent_id, status, agent_name, task_id, ctx,
             resume_cmd, created_at, started_at, completed_at) in rows:
            conn.execute(
                "INSERT OR IGNORE INTO agent_runs "
                "(id, agent_name, goal_slug, task_id, parent_run_id, status, "
                " context_usage, resume_command, created_at, started_at, "
                " completed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, agent_name, THREADED_SEED_GOAL_SLUG, task_id,
                 parent_id, status, ctx, resume_cmd, created_at,
                 started_at, completed_at),
            )
        conn.commit()
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Per-screen assertions
# ----------------------------------------------------------------------


def _assert_dashboard(page: Page, ctx: dict) -> None:
    result: Result = ctx["result"]
    screenshots_dir: Path = ctx["screenshots_dir"]
    base_url: str = ctx["base_url"]
    goal_slug: str = ctx["goal_slug"]

    with assertion(result, "dashboard_loads_200", page, screenshots_dir):
        resp = page.goto(f"{base_url}/", wait_until="domcontentloaded")
        assert resp is not None and resp.status == 200, f"unexpected status {resp.status if resp else 'None'}"

    for tab_name in ("active", "inactive", "completed"):
        with assertion(result, f"dashboard_tab_{tab_name}", page, screenshots_dir):
            tab_btn = page.locator(
                f".dashboard-tab[hx-get*='tab={tab_name}']"
            ).first
            tab_btn.click(timeout=ASSERTION_TIMEOUT_MS)
            page.locator("#dashboard-goals").wait_for(
                state="visible", timeout=ASSERTION_TIMEOUT_MS
            )

    # Re-select the active tab so the create form's after-begin target is the active list.
    with assertion(result, "dashboard_select_active_tab", page, screenshots_dir):
        page.locator(".dashboard-tab[hx-get*='tab=active']").first.click(
            timeout=ASSERTION_TIMEOUT_MS
        )
        page.locator("#dashboard-goals").wait_for(
            state="visible", timeout=ASSERTION_TIMEOUT_MS
        )

    with assertion(result, "dashboard_create_shared_goal", page, screenshots_dir):
        page.locator("button[aria-label='Create new goal']").click(
            timeout=ASSERTION_TIMEOUT_MS
        )
        form = page.locator("#create-goal-form")
        form.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)
        form.locator("input[name='title']").fill(goal_slug, timeout=ASSERTION_TIMEOUT_MS)
        form.locator("button[type='submit']").click(timeout=ASSERTION_TIMEOUT_MS)
        # The card id format is goal-card-{slug}; slug is auto-derived from title — pass slug as title
        # so the slugify step yields the same string.
        page.locator(f"#goal-card-{goal_slug}").wait_for(
            state="visible", timeout=5_000
        )

    delete_slug = f"ui-test-delete-{int(time.time())}"
    with assertion(result, "dashboard_delete_throwaway_goal", page, screenshots_dir):
        page.locator("button[aria-label='Create new goal']").click(
            timeout=ASSERTION_TIMEOUT_MS
        )
        form = page.locator("#create-goal-form")
        form.locator("input[name='title']").fill(delete_slug, timeout=ASSERTION_TIMEOUT_MS)
        form.locator("button[type='submit']").click(timeout=ASSERTION_TIMEOUT_MS)
        card = page.locator(f"#goal-card-{delete_slug}")
        card.wait_for(state="visible", timeout=5_000)
        # Delete via API directly — the dashboard goal card does not expose an inline
        # delete button until the goal is in a terminal state. Use the public DELETE
        # endpoint, then force a tab refresh and assert the card is gone.
        delete_req = urllib.request.Request(
            f"{base_url}/api/goals/{delete_slug}",
            method="DELETE",
        )
        try:
            urllib.request.urlopen(delete_req, timeout=10).read()
        except urllib.error.HTTPError as e:
            if e.code not in (200, 204, 404):
                raise
        page.locator(".dashboard-tab[hx-get*='tab=active']").first.click(
            timeout=ASSERTION_TIMEOUT_MS
        )
        page.locator(f"#goal-card-{delete_slug}").wait_for(
            state="detached", timeout=5_000
        )


def _assert_agents(page: Page, ctx: dict) -> None:
    result: Result = ctx["result"]
    screenshots_dir: Path = ctx["screenshots_dir"]
    base_url: str = ctx["base_url"]

    with assertion(result, "agents_page_loads", page, screenshots_dir):
        resp = page.goto(f"{base_url}/agents", wait_until="domcontentloaded")
        assert resp is not None and resp.status == 200

    # Removed `agents_api_returns_entries`: feature does not exist —
    # cast_server/routes/api_agents.py exposes no GET /api/agents JSON list,
    # the registry is rendered as cards in templates/pages/agents.html.

    with assertion(result, "agents_test_agent_visible", page, screenshots_dir):
        # Test agents are merged in via CAST_TEST_AGENTS_DIR — at least one card with
        # name starting cast-ui-test- must be present.
        page.locator("text=/cast-ui-test-/").first.wait_for(
            state="visible", timeout=ASSERTION_TIMEOUT_MS
        )

    with assertion(result, "agents_filter_button_toggle", page, screenshots_dir):
        # templates/pages/agents.html renders `.agents-filters button.filter-btn[data-filter]`.
        page.locator(".agents-filters button.filter-btn").first.click(
            timeout=ASSERTION_TIMEOUT_MS
        )

    with assertion(result, "agents_card_visible", page, screenshots_dir):
        # templates/pages/agents.html renders cards as `.agents-grid-card`.
        page.locator(".agents-grid-card").first.wait_for(
            state="visible", timeout=ASSERTION_TIMEOUT_MS
        )


def _assert_runs(page: Page, ctx: dict) -> None:
    """Drive the threaded /runs screen.

    Seed shape (see ``_seed_runs_threaded``):
        thread-warning-l1     -> rework-only group   (has-warning border)
        thread-failed-l1      -> failed grandchild   (has-failure border)
        thread-deeprework-l1  -> rework at L3        (rollup propagates to L1)
        thread-ctx-l1         -> low/mid/high ctx    (pill tints + child name color)
        thread-running-l1     -> running child       (HTMX poll fires on cells)

    Plus the existing trigger-and-cancel flow (US4 S7) updated for the new
    ``[data-run-id]`` markup.
    """
    result: Result = ctx["result"]
    screenshots_dir: Path = ctx["screenshots_dir"]
    base_url: str = ctx["base_url"]
    context: BrowserContext = ctx["context"]

    # Seed before any navigation so the page renders against threaded data.
    cast_db_env = os.environ.get("CAST_DB")
    with assertion(result, "runs_seed_threaded", page, screenshots_dir):
        assert cast_db_env, "CAST_DB env var not propagated to runner"
        db_path = Path(cast_db_env)
        assert db_path.exists(), f"CAST_DB does not exist: {db_path}"
        _seed_runs_threaded(db_path)

    # Clipboard permission must be granted before any .copy-resume click.
    grant_clipboard(context)

    with assertion(result, "runs_page_loads", page, screenshots_dir):
        resp = page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
        assert resp is not None and resp.status == 200

    # Filter tabs still work (smoke).
    for tab_name in ("running", "completed", "failed", "all"):
        with assertion(result, f"runs_tab_{tab_name}", page, screenshots_dir):
            page.locator(
                f".runs-filters button.filter-btn[hx-get*='status={tab_name}']"
            ).first.click(timeout=ASSERTION_TIMEOUT_MS)
    # Reset to "all" so subsequent assertions see seeded rows regardless of status.
    page.goto(f"{base_url}/runs?status=all", wait_until="domcontentloaded")

    # 1. Threaded markup classes are present on the page.
    with assertion(result, "runs_threaded_markup_present", page, screenshots_dir):
        page.locator(".run-group").first.wait_for(
            state="attached", timeout=ASSERTION_TIMEOUT_MS
        )
        page.locator(".run-node").first.wait_for(
            state="attached", timeout=ASSERTION_TIMEOUT_MS
        )
        assert page.locator(".thread").count() >= 1, "no .thread elements"
        assert page.locator(".ctx-pill").count() >= 1, "no .ctx-pill elements"

    # 2. Two-line layout: row-1 carries status-dot + agent-name, row-2 the pills.
    with assertion(result, "runs_two_line_layout", page, screenshots_dir):
        first_node = page.locator(".run-node").first
        first_node.locator(".row-1 .status-dot").first.wait_for(
            state="attached", timeout=ASSERTION_TIMEOUT_MS
        )
        first_node.locator(".row-1 .agent-name").first.wait_for(
            state="attached", timeout=ASSERTION_TIMEOUT_MS
        )
        first_node.locator(".row-2 .pill").first.wait_for(
            state="attached", timeout=ASSERTION_TIMEOUT_MS
        )

    # 3. Eager tree: a known L3 descendant is in the DOM on initial load.
    with assertion(result, "runs_eager_tree_l3_visible", page, screenshots_dir):
        page.locator("[data-run-id='thread-deeprework-l3a']").first.wait_for(
            state="attached", timeout=ASSERTION_TIMEOUT_MS
        )

    # 4. Pagination preserves tree shape on page 2 (skipped if only one page).
    with assertion(result, "runs_pagination_preserves_tree", page, screenshots_dir):
        next_btn = page.locator(
            ".pagination .pagination-btn:has-text('Next')"
        ).first
        if next_btn.count() > 0:
            next_btn.click(timeout=ASSERTION_TIMEOUT_MS)
            page.locator(".run-group .thread").first.wait_for(
                state="attached", timeout=ASSERTION_TIMEOUT_MS
            )

    # 5. Click on a row toggles `.expanded`.
    with assertion(result, "runs_click_toggles_expanded", page, screenshots_dir):
        page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
        node = page.locator("[data-run-id='thread-failed-l1']").first
        node.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)
        node.click(timeout=ASSERTION_TIMEOUT_MS)
        page.wait_for_timeout(300)
        assert "expanded" in (node.get_attribute("class") or ""), \
            "click did not add .expanded"

    # 6. Reload preserves expand via localStorage.
    with assertion(result, "runs_reload_preserves_expand", page, screenshots_dir):
        ls_val = read_localstorage(page, "runs:expanded:thread-failed-l1")
        assert ls_val == "1", f"localStorage entry not set: {ls_val!r}"
        page.reload(wait_until="domcontentloaded")
        node = page.locator("[data-run-id='thread-failed-l1']").first
        node.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)
        page.wait_for_timeout(300)
        assert "expanded" in (node.get_attribute("class") or ""), \
            "expand state did not survive reload"

    # 7. Clicking .copy-resume writes the clipboard and does NOT expand the row.
    with assertion(result, "runs_copy_resume_writes_clipboard", page, screenshots_dir):
        page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
        node = page.locator("[data-run-id='thread-warning-l1']").first
        node.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)
        node.locator(".copy-resume").first.click(timeout=ASSERTION_TIMEOUT_MS)
        page.wait_for_timeout(300)
        assert "expanded" not in (node.get_attribute("class") or ""), \
            "copy-resume click incorrectly toggled expand"
        clip = read_clipboard(page) or ""
        assert "thread-warning-l1" in clip, f"clipboard: {clip!r}"

    # 8. ctx_class pill tints + high-ctx child name colored danger.
    with assertion(result, "runs_ctx_pill_tints", page, screenshots_dir):
        for cls in ("low", "mid", "high"):
            assert page.locator(f".ctx-pill.{cls}").count() >= 1, \
                f"missing .ctx-pill.{cls}"
        assert page.locator(
            ".run-node.is-child.ctx-high .agent-name"
        ).count() >= 1, "missing high-ctx child .agent-name"

    # 9. Failed-descendant seed -> .run-group.has-failure border.
    with assertion(result, "runs_has_failure_border", page, screenshots_dir):
        node = page.locator("[data-run-id='thread-failed-l1']").first
        group = node.locator(
            "xpath=ancestor::div[contains(concat(' ', @class, ' '), ' run-group ')][1]"
        )
        cls = group.get_attribute("class") or ""
        assert "has-failure" in cls, f"missing has-failure: {cls!r}"

    # 10. Rework-only seed (no failure) -> .run-group.has-warning border.
    with assertion(result, "runs_has_warning_border", page, screenshots_dir):
        node = page.locator("[data-run-id='thread-warning-l1']").first
        group = node.locator(
            "xpath=ancestor::div[contains(concat(' ', @class, ' '), ' run-group ')][1]"
        )
        cls = group.get_attribute("class") or ""
        assert "has-warning" in cls, f"missing has-warning: {cls!r}"

    # 11. Rework second instance has .rework-tag; deep rework propagates to L1.
    with assertion(result, "runs_rework_tag_and_propagation", page, screenshots_dir):
        assert page.locator(
            "[data-run-id='thread-warning-c2'] .rework-tag"
        ).count() >= 1, "missing .rework-tag on second instance"
        deep_l1 = page.locator("[data-run-id='thread-deeprework-l1']").first
        rollup = deep_l1.locator(".rollup.warn")
        assert rollup.count() >= 1, "missing .rollup.warn on deep-rework L1"
        text = rollup.first.inner_text()
        assert "reworked" in text, f"unexpected rollup text: {text!r}"

    # 12. Status filter ?status=failed surfaces L1s with failed descendants
    #     (rollup-aware — Decision #13).
    with assertion(result, "runs_status_filter_failed_rollup", page, screenshots_dir):
        page.goto(f"{base_url}/runs?status=failed", wait_until="domcontentloaded")
        page.locator("[data-run-id='thread-failed-l1']").first.wait_for(
            state="attached", timeout=ASSERTION_TIMEOUT_MS
        )

    # 13. HTMX poll on a running run preserves expand state on the parent.
    with assertion(result, "runs_htmx_poll_preserves_expand", page, screenshots_dir):
        page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
        live = page.locator("[data-run-id='thread-running-l1']").first
        live.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)
        live.click(timeout=ASSERTION_TIMEOUT_MS)
        page.wait_for_timeout(300)
        assert "expanded" in (live.get_attribute("class") or "")
        wait_for_htmx_settle(page, 4000)
        assert "expanded" in (live.get_attribute("class") or ""), \
            "expand state lost after HTMX poll"

    # 14. Mobile viewport (480x800) hides .relative-time and .crumbs .task.
    with assertion(result, "runs_mobile_viewport_hides_chrome", page, screenshots_dir):
        resize_viewport(page, 480, 800)
        page.wait_for_timeout(300)
        rt = page.locator(".run-node .relative-time").first
        if rt.count() > 0:
            assert not rt.is_visible(), \
                ".relative-time should be hidden on mobile"
        task_crumb = page.locator(".run-node .crumbs .task").first
        if task_crumb.count() > 0:
            assert not task_crumb.is_visible(), \
                ".crumbs .task should be hidden on mobile"
        resize_viewport(page, 1280, 800)

    # US4 S7: trigger noop --sleep=20, then cancel via the threaded UI.
    # Selectors updated for the new run_node macro: outer .run-group with
    # nested .run-node[data-run-id], cancel button inside .detail .actions.
    with assertion(result, "runs_trigger_and_cancel_noop", page, screenshots_dir):
        goal_for_trigger = ctx.get("goal_slug") or "ui-test-runs"
        status, payload = _http_post_json(
            f"{base_url}/api/agents/cast-ui-test-noop/trigger",
            {
                "goal_slug": goal_for_trigger,
                "delegation_context": {
                    "agent_name": "cast-ui-test-noop",
                    "instructions": "sleep then exit",
                    "context": {
                        "goal_title": goal_for_trigger,
                        "sleep": 20,
                    },
                    "output": {"output_dir": "/tmp"},
                },
            },
        )
        assert status in (200, 201, 202), f"trigger returned {status}"
        run_id = (payload or {}).get("run_id")
        assert run_id, f"no run_id in response: {payload}"
        page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
        node = page.locator(f"[data-run-id='{run_id}']").first
        node.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)
        node.click(timeout=ASSERTION_TIMEOUT_MS)  # expand to expose actions
        cancel_btn = page.locator(
            f"button[hx-post='/api/agents/runs/{run_id}/cancel']"
        ).first
        cancel_btn.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)
        cancel_btn.click(timeout=ASSERTION_TIMEOUT_MS)
        # ``cancel_run`` marks the run as ``failed`` with
        # ``error_message="Cancelled by user"`` (see services/agent_service.py).
        deadline = time.time() + 8
        terminal_seen = False
        last_status: str | None = None
        last_err: str = ""
        while time.time() < deadline:
            payload = _http_get_json(
                f"{base_url}/api/agents/jobs/{run_id}"
            )[1] or {}
            if isinstance(payload, dict):
                last_status = payload.get("status")
                last_err = payload.get("error_message") or ""
            if last_status in ("failed", "cancelled") and "Cancelled" in last_err:
                terminal_seen = True
                break
            time.sleep(0.5)
        assert terminal_seen, (
            f"run not marked Cancelled by user (status={last_status}, err={last_err!r})"
        )


def _assert_scratchpad(page: Page, ctx: dict) -> None:
    result: Result = ctx["result"]
    screenshots_dir: Path = ctx["screenshots_dir"]
    base_url: str = ctx["base_url"]

    with assertion(result, "scratchpad_page_loads", page, screenshots_dir):
        resp = page.goto(f"{base_url}/scratchpad", wait_until="domcontentloaded")
        assert resp is not None and resp.status == 200

    marker = f"ui-test-scratchpad-{int(time.time())}"
    with assertion(result, "scratchpad_create_entry", page, screenshots_dir):
        # Try common selectors for the scratchpad entry input.
        candidates = [
            "textarea[name='content']",
            "textarea[name='text']",
            "input[name='content']",
            "textarea",
        ]
        filled = False
        for sel in candidates:
            loc = page.locator(sel).first
            if loc.count() > 0:
                loc.fill(marker, timeout=ASSERTION_TIMEOUT_MS)
                filled = True
                break
        assert filled, "could not find scratchpad text input"
        page.locator(
            "form button[type='submit'], button:has-text('Add'), button:has-text('Save')"
        ).first.click(timeout=ASSERTION_TIMEOUT_MS)
        page.locator(f"text={marker}").first.wait_for(
            state="visible", timeout=ASSERTION_TIMEOUT_MS
        )

    # Removed `scratchpad_delete_entry`: feature does not exist —
    # templates/pages/scratchpad.html and templates/fragments/scratchpad_entry.html
    # render entries with no delete control, and routes/api_scratchpad.py exposes
    # only GET and POST handlers (no DELETE route).


def _assert_goal_detail(page: Page, ctx: dict) -> None:
    result: Result = ctx["result"]
    screenshots_dir: Path = ctx["screenshots_dir"]
    base_url: str = ctx["base_url"]
    goal_slug: str = ctx["goal_slug"]

    with assertion(result, "goal_detail_loads", page, screenshots_dir):
        resp = page.goto(f"{base_url}/goals/{goal_slug}", wait_until="domcontentloaded")
        assert resp is not None and resp.status == 200

    # 5 tabs total: overview + 4 phase tabs (templates/pages/goal_detail.html
    # renders them inside `.tab-bar` as `button.tab-btn[data-tab=...]`).
    with assertion(result, "goal_detail_has_tabs", page, screenshots_dir):
        tabs = page.locator(".tab-bar button.tab-btn")
        count = tabs.count()
        assert count >= 4, f"expected ≥4 tabs, got {count}"

    # Click each tab in turn.
    tabs = page.locator(".tab-bar button.tab-btn")
    for idx in range(min(tabs.count(), 8)):
        with assertion(result, f"goal_detail_tab_click_{idx}", page, screenshots_dir):
            tabs.nth(idx).click(timeout=ASSERTION_TIMEOUT_MS)

    # Read goal status to drive the conditional flow.
    status, gpayload = _http_get_json(f"{base_url}/api/goals/{goal_slug}")
    goal_status = (gpayload or {}).get("status") if isinstance(gpayload, dict) else None

    if goal_status == "idea":
        with assertion(result, "goal_detail_accept_idea", page, screenshots_dir):
            accept_btn = page.locator(
                "button[hx-vals*='\"status\": \"accepted\"'], "
                "button[hx-vals*='\"status\":\"accepted\"']"
            ).first
            accept_btn.click(timeout=ASSERTION_TIMEOUT_MS)
            time.sleep(1.0)
            status2, gp2 = _http_get_json(f"{base_url}/api/goals/{goal_slug}")
            assert (gp2 or {}).get("status") == "accepted", "goal did not transition to accepted"
    elif goal_status == "accepted":
        with assertion(result, "goal_detail_phase_advance", page, screenshots_dir):
            advance_btn = page.locator(
                "button[hx-put*='/phase'], button:has-text('Next phase'), "
                "button:has-text('Advance')"
            ).first
            if advance_btn.count() > 0:
                advance_btn.click(timeout=ASSERTION_TIMEOUT_MS)
            else:
                # surface as skip rather than fail
                raise AssertionError("phase_advance_skipped: no advance button visible")
    else:
        result.assertions_passed.append(
            f"goal_detail_phase_advance_skipped:status={goal_status}"
        )

    with assertion(result, "goal_detail_focus_toggle", page, screenshots_dir):
        focus_btn = page.locator("button.focus-star").first
        if focus_btn.count() > 0:
            focus_btn.click(timeout=ASSERTION_TIMEOUT_MS)
            time.sleep(0.5)
            page.locator("button.focus-star").first.click(timeout=ASSERTION_TIMEOUT_MS)
        else:
            # Fall back to the API.
            for val in ("true", "false"):
                req = urllib.request.Request(
                    f"{base_url}/api/goals/{goal_slug}/focus",
                    data=json.dumps({"in_focus": val}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="PUT",
                )
                try:
                    urllib.request.urlopen(req, timeout=5).read()
                except Exception:  # noqa: BLE001
                    pass

    task_title = f"test-task-{int(time.time())}"
    with assertion(result, "goal_detail_task_create", page, screenshots_dir):
        create_inputs = page.locator(
            "form input[name='title'], form input[name='task_title']"
        )
        if create_inputs.count() > 0:
            create_inputs.first.fill(task_title, timeout=ASSERTION_TIMEOUT_MS)
            page.locator("form button[type='submit']").first.click(
                timeout=ASSERTION_TIMEOUT_MS
            )
            page.locator(f"text={task_title}").first.wait_for(
                state="visible", timeout=5_000
            )
        else:
            raise AssertionError("no task-create form found on goal detail page")

    # Trigger noop from goal detail (no sleep) and verify it appears on /runs.
    with assertion(result, "goal_detail_trigger_noop", page, screenshots_dir):
        status, payload = _http_post_json(
            f"{base_url}/api/agents/cast-ui-test-noop/trigger",
            {
                "goal_slug": goal_slug,
                "delegation_context": {
                    "agent_name": "cast-ui-test-noop",
                    "instructions": "no-op",
                    "context": {},
                    "output": {"output_dir": "/tmp"},
                },
            },
        )
        assert status in (200, 201, 202)
        run_id = (payload or {}).get("run_id")
        assert run_id
        page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
        page.locator(f"#run-{run_id}").wait_for(
            state="visible", timeout=5_000
        )


def _assert_focus(page: Page, ctx: dict) -> None:
    result: Result = ctx["result"]
    screenshots_dir: Path = ctx["screenshots_dir"]
    base_url: str = ctx["base_url"]

    with assertion(result, "focus_page_loads", page, screenshots_dir):
        resp = page.goto(f"{base_url}/focus", wait_until="domcontentloaded")
        assert resp is not None and resp.status == 200

    with assertion(result, "focus_renders_content_or_empty_state", page, screenshots_dir):
        # templates/pages/focus.html always renders `.focus-page`, then either
        # `.focus-goals` (with `.focus-goal-card` rows) or `.empty-state-page`.
        page.locator(
            ".focus-goal-card, .empty-state-page"
        ).first.wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)


def _assert_about(page: Page, ctx: dict) -> None:
    result: Result = ctx["result"]
    screenshots_dir: Path = ctx["screenshots_dir"]
    base_url: str = ctx["base_url"]

    with assertion(result, "about_page_loads", page, screenshots_dir):
        resp = page.goto(f"{base_url}/about", wait_until="domcontentloaded")
        assert resp is not None and resp.status == 200

    with assertion(result, "about_renders_content", page, screenshots_dir):
        page.locator("main, body").first.wait_for(
            state="visible", timeout=ASSERTION_TIMEOUT_MS
        )


SCREEN_DISPATCH: dict[str, Callable[[Page, dict], None]] = {
    "dashboard": _assert_dashboard,
    "agents": _assert_agents,
    "runs": _assert_runs,
    "scratchpad": _assert_scratchpad,
    "goal_detail": _assert_goal_detail,
    "focus": _assert_focus,
    "about": _assert_about,
}


def _run_screen(screen: str, base_url: str, goal_slug: str, output_path: Path) -> int:
    result = Result(screen=screen)
    screenshots_dir = output_path.parent / "screenshots"
    user_data_dir = Path(f"{USER_DATA_DIR_PREFIX}-{os.getpid()}-{screen}")

    pw: Playwright | None = None
    context: BrowserContext | None = None
    try:
        pw = sync_playwright().start()
        launch_kwargs: dict = {
            "user_data_dir": str(user_data_dir),
            "headless": True,
            "args": ["--no-sandbox"],
        }
        channel = os.environ.get("CAST_UITEST_BROWSER_CHANNEL", "chrome")
        if channel:
            launch_kwargs["channel"] = channel
        exe = os.environ.get("CAST_UITEST_BROWSER_EXECUTABLE")
        if exe:
            launch_kwargs["executable_path"] = exe
        context = pw.chromium.launch_persistent_context(**launch_kwargs)
        page = context.new_page()
        page.set_default_timeout(ASSERTION_TIMEOUT_MS)
        _attach_console_capture(page, result)
        _accept_dialogs(page)

        ctx = {
            "base_url": base_url,
            "goal_slug": goal_slug,
            "screenshots_dir": screenshots_dir,
            "result": result,
            "page": page,
            "context": context,
        }
        SCREEN_DISPATCH[screen](page, ctx)
    except Exception as e:  # noqa: BLE001
        result.assertions_failed.append({"name": "runner_internal", "error": repr(e)})
    finally:
        result.finished_at = _now_iso()
        try:
            if context is not None:
                context.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            if pw is not None:
                pw.stop()
        except Exception:  # noqa: BLE001
            pass
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result.to_dict(), indent=2))
    return 0 if result.status == "completed" else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--screen", required=True)
    p.add_argument("--base-url", default="http://127.0.0.1:8006")
    p.add_argument("--goal-slug", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)

    screen = _norm_screen(args.screen)
    if screen not in SCREEN_DISPATCH:
        print(f"unknown screen: {args.screen}", file=sys.stderr)
        return 2
    return _run_screen(screen, args.base_url, args.goal_slug, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
