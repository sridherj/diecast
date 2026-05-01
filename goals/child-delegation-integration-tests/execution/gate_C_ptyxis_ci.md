# Gate C: T2 ptyxis CI Strategy

> **Context:** Read sp5.1, sp5.2, sp5.3 — these author T2 test code that runs locally
> on a host with cast-server bin + ptyxis. The CI workflow YAML (sp5.4) depends on
> this decision; the test code itself is workflow-agnostic.

## Decision Criteria

T2 launches ptyxis windows for parent/child terminals. Headless CI runners typically
lack ptyxis. Three strategies, all valid; choice depends on CI infra availability.

## Options

### Option A (recommended): Self-hosted nightly runner with ptyxis
- **Condition:** Org has a self-hosted runner (or can stand one up) with ptyxis,
  cast-server bin, and Linux desktop session.
- **Action:** sp5.4 authors `.github/workflows/cast-delegation-e2e-nightly.yml` with
  `runs-on: [self-hosted, ptyxis]` (or equivalent label) on a nightly schedule.
- **Rationale:** Most faithful to production cadence; no environmental shims.
- **Cost:** Runner setup is external work, may delay sp5.4 indefinitely.

### Option B: `xvfb-run` wrap + no-ptyxis fallback
- **Condition:** Self-hosted runner unavailable, but virtual framebuffer is
  acceptable.
- **Action:** sp5.4 authors workflow that runs T2 under `xvfb-run`. Document the
  shim in workflow comments — make it explicit that this is virtual display, not
  real ptyxis.
- **Rationale:** Works on standard hosted runners; no infra ask.
- **Cost:** Behavioral parity with production is degraded; some terminal-visibility
  assertions may need conditional logic.

### Option C: Graceful-degrade when ptyxis missing
- **Condition:** No CI infra investment desired; T2 runs locally only.
- **Action:** sp5.4 authors workflow that detects ptyxis presence and skips
  terminal-visibility checks (asserts only filesystem + DB) when missing. Document
  the gap.
- **Rationale:** Lowest cost; T2 still runs nightly with reduced coverage.
- **Cost:** SC-002 ("nightly E2E green") is satisfied by a weaker test set;
  document as a known limitation.

## How to Proceed

1. Confirm chosen option with user.
2. Update `_manifest.md`: set `GC` status to `Done`, write decision in Notes.
3. Dispatch sp5.4 with the chosen option's workflow shape.
4. If Option A and runner setup blocks indefinitely: park sp5.4 with the test code
   already-shipped status; the goal can close at sp7.4 with sp5.4 Skipped (note
   that SC-002 then requires manual verification post-close).
