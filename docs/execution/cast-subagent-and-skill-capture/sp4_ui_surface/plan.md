# Sub-phase 4: Surface — L2 chip-list + L3 detail in runs UI

> **Pre-requisite:** Read
> `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` and
> complete sp1, sp2, sp3 before starting.

## Outcome

The `/runs` page renders skills used by each cast-* run as a compact chip
row at L2 (e.g. `"3 skills: detailed-plan, spec-checker, +1"`) and as a
full list with timestamps and invocation counts when expanded to L3.
Empty `skills_used` hides the chip row entirely.

## Dependencies

- **Requires completed:** sub-phases 1-3 (data must be flowing for
  visual verification).
- **Assumed codebase state:** `agent_runs.skills_used` is populated by
  the real hook→service→DB flow; the threaded-tree plan's L1/L2/L3
  partials exist (sibling shipped).

## Estimated effort

1 session.

## Scope

**In scope:**

- Locate existing `/runs` L1/L2/L3 partials and identify the chip-row
  insertion point (mirror sibling threaded-tree conventions).
- New `cast-server/cast_server/templates/partials/run_skills_chips.html`
  partial — L2 chip row (first 2 chips + `+N` overflow badge).
- New `cast-server/cast_server/templates/partials/run_skills_detail.html`
  partial — L3 table (Skill, First invoked, Count) with server-side
  aggregation.
- `/runs` route handler in `cast-server/cast_server/routes/pages.py`
  parses `skills_used` JSON when serializing each run; defensive
  `try/except (json.JSONDecodeError, TypeError) → []`.
- CSS for `.skills-chips` matching existing chip/pill pattern if one
  exists; otherwise small rounded rect with subtle border.
- Test file `cast-server/tests/ui/test_runs_skills_chips.py` with the 5
  named tests below.

**Out of scope (do NOT do):**

- Service or endpoint changes (sp2).
- Hook layer changes (sp3).
- Spec authoring (sp5).
- Click-through interactivity for chips (Open Question O3 — explicitly
  punted to v2 in refined requirements).
- Skill argument display (Open Question O4 — punted to v2).

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `cast-server/cast_server/templates/partials/run_skills_chips.html` | Create | L2 partial; first 2 chips + `+N` overflow badge; `{% if skills_used %}…{% endif %}`. |
| `cast-server/cast_server/templates/partials/run_skills_detail.html` | Create | L3 table: Skill, First invoked, Count. |
| `cast-server/cast_server/routes/pages.py` | Modify | `/runs` handler parses `skills_used` JSON and aggregates; wraps parse in `try/except (json.JSONDecodeError, TypeError) → []`. |
| `cast-server/cast_server/static/css/<runs CSS file>` | Modify | `.skills-chips` styles. |
| `cast-server/tests/ui/test_runs_skills_chips.py` | Create | 5 named tests below. |

## Detailed Steps

### Step 4.1: Locate templates

```bash
find cast-server/cast_server/templates -name "*run*"
```

Find the existing L1/L2/L3 partials shipped by the threaded-tree plan.
Mirror their conventions and slot the chip row appropriately at L2 (and
the detail table at L3). Read the partials before authoring ours so
naming, indentation, class conventions match.

### Step 4.2: L2 chip row partial

Create `cast-server/cast_server/templates/partials/run_skills_chips.html`:

```jinja
{% if skills_used %}
<div class="skills-chips">
  <span class="skills-count">{{ skills_used | length }} skill{{ 's' if skills_used | length != 1 else '' }}:</span>
  {% for skill in skills_used[:2] %}
    <span class="skill-chip">{{ skill.name }}</span>
  {% endfor %}
  {% if skills_used | length > 2 %}
    <span class="skill-overflow">+{{ skills_used | length - 2 }}</span>
  {% endif %}
</div>
{% endif %}
```

Wrap in `{% if skills_used %}…{% endif %}` so empty hides entirely (no
"0 skills" placeholder).

### Step 4.3: L3 detail partial

Create `cast-server/cast_server/templates/partials/run_skills_detail.html`:

```jinja
{% if skills_aggregated %}
<table class="skills-detail">
  <thead><tr><th>Skill</th><th>First invoked</th><th>Count</th></tr></thead>
  <tbody>
  {% for row in skills_aggregated %}
    <tr>
      <td>{{ row.name }}</td>
      <td>{{ row.first_invoked }}</td>
      <td>{{ row.count }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}
```

Server-side aggregation: group `skills_used` JSON list by `name`, count
occurrences, take `min(invoked_at)`.

### Step 4.4: Route handler

In `cast-server/cast_server/routes/pages.py`, in the `/runs` handler:

- Parse `skills_used` JSON for each run row when serializing.
  Defensive:

  ```python
  try:
      skills_used = json.loads(row["skills_used"] or "[]")
  except (json.JSONDecodeError, TypeError):
      skills_used = []
  ```

  A row with malformed JSON should render as "no skills", not crash
  the page.
- Compute `skills_aggregated` by grouping on `name`:
  - count occurrences,
  - take `min(invoked_at)` as `first_invoked`.
- Pass both `skills_used` (raw, for L2 chips) and `skills_aggregated`
  (for L3 table) to the template context per run.

### Step 4.5: CSS

Add `.skills-chips`, `.skill-chip`, `.skill-overflow`, `.skills-count`,
and `.skills-detail` styles to the runs page CSS — match existing
chip/pill pattern if one exists; otherwise small rounded rect with
subtle border.

Ensure no overflow at 1280px viewport with 5 skills rendered.

### Step 4.6: Tests

Create `cast-server/tests/ui/test_runs_skills_chips.py` with the
following named tests:

```python
def test_skills_chip_row_renders_for_user_invocation_with_skills(client, db)
    # Decision #1 — slash command shows chips even without Task() subagents
def test_skills_chip_row_renders_for_subagent_with_skills(client, db)
def test_skills_chip_row_hidden_when_skills_used_empty(client, db)
def test_skills_chip_overflow_indicator_shows_plus_n_after_two_chips(client, db)
def test_l3_detail_aggregates_repeated_skill_invocations_into_count(client, db)
```

Seed three runs (5 skills, 1 skill, 0 skills); assert chip-row presence
/ absence and the `+N` overflow indicator at exactly the right
threshold. Include a slash-command-only run with skills (no Task()
subagent) to verify per Decision #1 that user-invocation rows get
chips too.

### Step 4.7: Best-practices delegation

→ Delegate: `/cast-pytest-best-practices` over the new UI test. Verify:

- zero-residue (test runs leave no DB rows behind),
- no real-DB writes,
- deterministic skill ordering for assertions (insertion order, fixed
  `invoked_at` timestamps).

### Step 4.8: Run the test suite

```bash
cd cast-server && uv run pytest tests/ui/test_runs_skills_chips.py -v
```

All 5 tests must pass.

### Step 4.9: Manual visual verification

```bash
# In a session with ≥3 cast-* subagent dispatches each invoking ≥2 skills:
xdg-open http://127.0.0.1:8005/runs
```

- Each cast-* row's L2 line shows the skill chip-row.
- Expanding to L3 shows the full timestamped list with counts.
- A cast-* row with `skills_used=[]` shows no chip row at L2.
- Visual check at 1280px confirms no layout overflow with 5 skills
  rendered.

## Verification

### Automated Tests (permanent)

- `pytest cast-server/tests/ui/test_runs_skills_chips.py` green:
  - `test_skills_chip_row_renders_for_user_invocation_with_skills`
    (Decision #1 — slash command shows chips even without Task()
    subagents)
  - `test_skills_chip_row_renders_for_subagent_with_skills`
  - `test_skills_chip_row_hidden_when_skills_used_empty`
  - `test_skills_chip_overflow_indicator_shows_plus_n_after_two_chips`
  - `test_l3_detail_aggregates_repeated_skill_invocations_into_count`

### Manual Checks

- See Step 4.9.

### Success Criteria

- [ ] L2 chip row partial exists; renders first 2 chips + `+N` badge.
- [ ] L3 detail partial exists; aggregates by name with count + min
      `invoked_at`.
- [ ] `/runs` route parses `skills_used` defensively.
- [ ] Empty `skills_used` hides chip row entirely (no "0 skills"
      placeholder).
- [ ] User-invocation rows get chips too (not just subagents).
- [ ] No layout overflow at 1280px with 5 skills.
- [ ] All 5 sp4 tests pass.

## Design Review

- **Architecture:** mirrors existing partial → route → page pattern;
  no new layer. ✓
- **Naming:** `skills_used` consistent with `artifacts`, `directories`.
  `run_skills_chips` partial name follows existing `run_*` partial
  convention.
- **Spec consistency:** the chip-row insertion point must respect the
  `cast-runs-threaded-tree` L2 row anatomy (sibling shipped).
  Cross-check at impl time.
- **Error & rescue:** malformed JSON in `skills_used` (shouldn't
  happen but possible if hand-edited) → empty list, no chip row. Page
  never crashes.
- **Security:** skill names go straight to template via Jinja default
  autoescape; do not use `|safe`. Skill names are agent-controlled but
  never user-controlled.

## Execution Notes

- **Spec-linked files:** sp5 covers the spec — don't write spec yet.
- **Threaded-tree dependency:** the L1/L2/L3 row anatomy is already
  shipped. Find and read the existing partials BEFORE authoring;
  mirror their conventions exactly so styling is consistent.
- **Aggregation responsibility:** server-side aggregation in the route
  keeps the partial dumb. The partial just iterates the
  `skills_aggregated` list.
- **Skill ordering in chips:** use insertion order (the order they
  appear in the JSON array). Tests should pin this with fixed
  `invoked_at` timestamps so assertions are deterministic.
- **Live data verification:** before manual visual check, run a real
  Claude Code session with at least 3 cast-* subagent dispatches to
  populate `skills_used` for both user-invocation and subagent rows.
