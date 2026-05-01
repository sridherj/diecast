# sp3 Verification Log — Layer A3 Runner `domcontentloaded` Migration

Run: `run_20260501_065019_4ad3db`
File modified: `cast-server/tests/ui/runner.py`

## Edits Applied

### 9 `page.goto(..., wait_until="networkidle")` → `wait_until="domcontentloaded"`

| Line (pre) | Line (post) | Context |
|------------|-------------|---------|
| 162 | 162 | `_assert_dashboard` — `/` |
| 234 | 234 | `_assert_agents` — `/agents` |
| 285 | 285 | `_assert_runs` entry — `/runs` |
| 323 | 323 | `_assert_runs` post-trigger re-nav — `/runs` |
| 349 | 349 | `_assert_scratchpad` — `/scratchpad` |
| 398 | 398 | `_assert_goal_detail` — `/goals/{goal_slug}` |
| 498 | 496 | `_assert_runs` cancel-flow follow-up — `/runs` |
| 510 | 508 | `_assert_focus` — `/focus` |
| 526 | 524 | `_assert_about` — `/about` |

(Line numbers shifted down by 2 after the two `wait_for_load_state` deletions.)

### 2 `page.wait_for_load_state("networkidle", ...)` → DELETED

| Pre-line | Site | Reason for deletion |
|----------|------|---------------------|
| 412 | `_assert_goal_detail` — after `tabs.nth(idx).click(...)` inside the tab-click loop | The trailing operation of the assertion block. The next loop iteration re-issues `tabs.nth(idx+1).click(timeout=ASSERTION_TIMEOUT_MS)`, and Playwright's `click()` auto-waits for actionability. No follow-up that lacks auto-wait. |
| 436 | `_assert_goal_detail` — after `advance_btn.click(...)` | Last statement before falling out of the `if goal_status == "accepted":` branch. The next code (`_assert_goal_detail_focus_toggle` block via `page.locator("button.focus-star").first.count()`) is auto-waited by Playwright. |

Both deletions match the plan's Step 3.2 default ("delete when followed by auto-waiting `expect()`/locator action"). No new abstractions or constants introduced.

## Static Verification

```
$ grep -n "networkidle" cast-server/tests/ui/runner.py
(no output — 0 matches)

$ grep -n "wait_until=" cast-server/tests/ui/runner.py
162:        resp = page.goto(f"{base_url}/", wait_until="domcontentloaded")
234:        resp = page.goto(f"{base_url}/agents", wait_until="domcontentloaded")
285:        resp = page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
323:        page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
349:        resp = page.goto(f"{base_url}/scratchpad", wait_until="domcontentloaded")
398:        resp = page.goto(f"{base_url}/goals/{goal_slug}", wait_until="domcontentloaded")
496:        page.goto(f"{base_url}/runs", wait_until="domcontentloaded")
508:        resp = page.goto(f"{base_url}/focus", wait_until="domcontentloaded")
524:        resp = page.goto(f"{base_url}/about", wait_until="domcontentloaded")

$ grep -n "wait_for_load_state" cast-server/tests/ui/runner.py
(no output — 0 matches)
```

## Acceptance Criteria — Status

| Criterion | Status |
|-----------|--------|
| Zero `networkidle` references remain in `runner.py` | ✅ verified via grep |
| All `page.goto` calls use `wait_until="domcontentloaded"` | ✅ verified via grep |
| `page.wait_for_load_state("networkidle", ...)` calls removed or migrated | ✅ both deleted (default per plan); zero `wait_for_load_state` remain |
| No new abstractions, constants, or helpers | ✅ mechanical edit only |
| Re-running the harness shows zero `networkidle`/goto-timeout entries in any child's `assertions_failed[]` | ⏸ DEFERRED — full-harness dynamic check happens after sp1+sp2+sp3 are merged; sp3 alone passes the static gate. Per shared context (`Sub-Phase Dependency Summary`), sp4 cannot start until all of Layer A is merged. |

## Notes / Risk Acknowledgements

- **No selector or assertion changes were made.** Any remaining red children after this swap are sp4 (Layer B) or sp5 (Layer C) territory.
- **No retries, no `wait_for_timeout` sleeps** added to backfill `networkidle`'s effect. Playwright's per-element auto-wait inside `expect(...)`/`.click(...)`/`.wait_for(...)` is the load-readiness mechanism.
- Per-screen override note: none required. All screens are HTMX-polling-tolerant under `domcontentloaded`.
