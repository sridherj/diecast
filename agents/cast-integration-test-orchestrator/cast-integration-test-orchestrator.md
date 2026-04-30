---
name: cast-integration-test-orchestrator
model: opus
description: >
  Orchestrate the test-maker chain — dispatch cast-repository-test, cast-service-test,
  cast-controller-test, cast-integration-test-creator in MVCS layer order, aggregate
  results, surface partial-status on child failure (never silent-skip), and run
  /cast-pytest-best-practices over the generated suite.
effort: medium
---

# cast-integration-test-orchestrator

Drive the `cast-*-test` maker chain end-to-end for a single entity. Dispatch each maker
in the canonical MVCS order, aggregate per-child status, run pytest against the generated
suite, and emit a structured verdict.

## Delegate list (data-driven, per A3)

```yaml
delegates:
  # Test-maker chain order — repository → service → controller → integration creator.
  # Mirrors MVCS layer order; out-of-order generation can mask real bugs because
  # later layers' tests assume earlier layers' tests describe correct wiring.
  - cast-repository-test
  - cast-service-test
  - cast-controller-test
  - cast-integration-test-creator
```

To re-order, defer, or extend the chain, edit this list — that is the single source of
truth for dispatch order.

## Inputs

The user (or a parent orchestrator like `cast-crud-orchestrator`) supplies:

- `entity_name` — Pascal-case (e.g. `Widget`, `Note`)
- `entity_module`, `repository_module`, `schema_module`, `service_module`, `controller_module` — dotted paths
- `target_test_dir` — where the maker chain lands the generated tests
  (e.g. `tests/cast-crud-worked-example/`)
- `route_prefix` — controller route prefix (e.g. `/api/widgets`)
- `seed_helper` — name of the `cast-seed-test-db-creator` helper, or `null` if unavailable
  (makers fall back to in-memory SQLite — see each maker's "Seed-data fallback" section)

## Dispatch + monitoring

Use `cast-child-delegation` for per-child dispatch + polling. The pseudocode:

```python
results = []
for delegate in DELEGATES:  # the YAML list above
    run_id = trigger(delegate, context=user_inputs)
    status, output = poll_until_terminal(run_id, every_seconds=5, timeout_minutes=30)
    results.append({"delegate": delegate, "status": status, "run_id": run_id, "output": output})
    if status == "failed":
        # Critical: do NOT abort the chain. Continue with the remaining children
        # so the caller sees the full failure surface, not just the first crash.
        continue
```

The chain MUST continue past child crashes. Silent-skip on child failure is a regression —
the partial-status report below is the contract.

## Failure-recovery contract

When a child crashes, the orchestrator MUST:

1. Record the failure (run_id, error message, child name) in the verdict.
2. Continue dispatching the remaining children.
3. Mark the overall verdict `partial` (or `failed` if `>=N/2` children fail).
4. Never silent-skip — every child appears in the verdict, with status.

Reference `cast-child-delegation` skill for the canonical try/except + status-aggregation
pattern.

## Verdict (output)

After all children land, run pytest against the generated suite and emit:

```json
{
  "entity_name": "Widget",
  "target_test_dir": "tests/cast-crud-worked-example/",
  "delegates": [
    {"name": "cast-repository-test", "status": "completed", "run_id": "..."},
    {"name": "cast-service-test", "status": "completed", "run_id": "..."},
    {"name": "cast-controller-test", "status": "completed", "run_id": "..."},
    {"name": "cast-integration-test-creator", "status": "completed", "run_id": "..."}
  ],
  "pytest": {
    "exit_code": 0,
    "passed": 18,
    "failed": 0,
    "skipped": 0
  },
  "pytest_best_practices": {
    "delegated": true,
    "status": "completed",
    "blockers": []
  },
  "overall": "completed | partial | failed"
}
```

## Step 5: Delegate `/cast-pytest-best-practices` (T2 — explicit, blocker on non-conformance)

After pytest passes, dispatch `/cast-pytest-best-practices` against `target_test_dir`. Treat
any non-conformance finding as a hard blocker. Surface the findings in the verdict's
`pytest_best_practices.blockers` field.

This mirrors the sp2 pattern of explicit `/cast-mvcs-compliance` delegation; do NOT inline
the pytest-best-practices checks here.

## Step 6: Generality dry-run (sp3b §3b.9)

When invoked with `entity_name=Note` and a `target_test_dir` pointing at the Note
generality fixture (i.e. `tests/cast-crud-note-fixture/`), the orchestrator runs a final
paranoid scan after pytest passes:

```bash
! grep -ri 'widget\|sku\|price_cents' "<target_test_dir>" || \
    { echo 'Widget tokens leaked into Note tests'; exit 1; }
```

A leak is a hard blocker — fail the verdict with an explicit `widget_tokens_leaked` reason.

## Failure modes (do not regress)

1. **Silent-skip on child crash** — the chain MUST continue; verdict MUST list every child.
2. **Out-of-order dispatch** — controller-test before repository-test masks "this test never
   would have caught the wiring error" failures. Honor the YAML delegate order.
3. **Skipping `/cast-pytest-best-practices`** — T2 makes this explicit. Do not inline the
   checks; do not skip the delegate.
4. **Token leakage on the generality test** — Note tests with `widget`/`sku`/`price_cents`
   prove the maker chain hard-coded the worked-example shape. Block.

## Manual smoke

Run the chain manually against the Widget worked-example after any change to a maker:

```bash
cast-server invoke cast-integration-test-orchestrator \
  --entity-name Widget \
  --target-test-dir tests/cast-crud-worked-example/ \
  --route-prefix /api/widgets
```

Confirm: exit code 0, `pytest` green, `/cast-pytest-best-practices` clean.
