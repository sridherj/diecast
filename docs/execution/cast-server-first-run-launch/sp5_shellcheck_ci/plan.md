# Sub-phase 5: Shellcheck CI — shebang-aware sweep over `setup` + `bin/*`

> **Pre-requisite:** Read `docs/execution/cast-server-first-run-launch/_shared_context.md` before starting.

## Objective

Add shellcheck coverage for every bash script in `setup` + `bin/*` so the new launch logic, port pre-flight probe, cast-doctor wire-up, PATH check, and existing renumber-the-step-counter sed land with verified syntax. Shebang-aware sweep (Decision #17) auto-includes future bash scripts without CI maintenance. Initial cleanup commit fixes the inevitable `SC2086`/`SC2155` violations in existing scripts.

## Dependencies

- **Requires completed:** None (independent — does not touch business logic).
- **Assumed codebase state:** `setup` and several `bin/*` scripts already exist with bash shebangs. No `.github/workflows/shellcheck.yml` exists.

## Scope

**In scope:**
- New `.github/workflows/shellcheck.yml` (or extend existing CI workflow if one already exists in `.github/workflows/`).
- Shebang-aware sweep: `for f in setup bin/*; do head -1 "$f" | grep -q 'bash' && shellcheck "$f"; done`.
- Fix initial violations (likely a handful of `SC2086` unquoted-var and `SC2155` declare-and-assign) in `setup` and `bin/*` bash scripts.

**Out of scope (do NOT do these):**
- Adding bats integration tests for `./setup --dry-run` (explicit out-of-scope per plan).
- Editing the new step8 logic — sp8 owns it; this sub-phase pre-stages the CI gate.
- Editing Python scripts in `bin/` (`migrate-*.py`, `run-migrations.py`, `set-proactive-defaults.py`) — out of scope; only bash scripts matter for shellcheck.
- Touching `bin/_lib.sh` semantically — only fix violations, do not refactor.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `.github/workflows/shellcheck.yml` | Create (or extend an existing workflow) | Likely doesn't exist. |
| `setup` | Modify (only to fix violations) | Existing bash; current state contains likely SC2086/SC2155 hits. |
| `bin/cast-server` | Modify (only to fix violations) | Existing bash. |
| `bin/_lib.sh` | Modify (only to fix violations) | Existing bash helpers. |
| Other `bin/*` bash scripts | Modify (only to fix violations) | Same. |

## Detailed Steps

### Step 5.1: Inventory bash scripts

```bash
for f in /data/workspace/diecast/setup /data/workspace/diecast/bin/*; do
  [ -f "$f" ] || continue
  head -1 "$f" | grep -q 'bash' && echo "$f"
done
```

Record the list — these are the in-scope shellcheck targets.

### Step 5.2: Run shellcheck locally before CI

For each in-scope script, run `shellcheck` and collect violations:

```bash
for f in /data/workspace/diecast/setup /data/workspace/diecast/bin/*; do
  [ -f "$f" ] || continue
  head -1 "$f" | grep -q 'bash' && shellcheck "$f"
done
```

Categorize the output:
- **`SC2086` (Double quote to prevent globbing/word-splitting)**: typically `$VAR` should be `"$VAR"`.
- **`SC2155` (Declare and assign separately to avoid masking return values)**: `local foo=$(cmd)` → `local foo; foo=$(cmd)`.
- **`SC1091` (Not following sourced file)**: harmless but noisy; suppress with `# shellcheck disable=SC1091` above the `source`/`.` line ONLY when the file genuinely cannot be followed (e.g. dynamic path).
- **`SC2034` (variable appears unused)**: investigate — may indicate dead code, or may need `# shellcheck disable=SC2034 # exported via ...`.

Fix every violation in this commit. Do not refactor surrounding logic. If a fix is non-trivial (e.g., quoting changes string-splitting semantics), note it inline with `# shellcheck` directive and explain.

### Step 5.3: Author the workflow

Create `.github/workflows/shellcheck.yml`:

```yaml
name: shellcheck
on:
  pull_request:
    paths:
      - "setup"
      - "bin/**"
      - ".github/workflows/shellcheck.yml"
  push:
    branches: [main]

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run shellcheck on bash scripts
        run: |
          set -euo pipefail
          fail=0
          for f in setup bin/*; do
            [ -f "$f" ] || continue
            if head -1 "$f" | grep -q 'bash'; then
              echo "::group::shellcheck $f"
              shellcheck "$f" || fail=1
              echo "::endgroup::"
            fi
          done
          exit $fail
```

Notes:
- Shellcheck is preinstalled on `ubuntu-latest` runners — no install step needed.
- The shebang-aware sweep auto-includes future scripts; no CI updates when new bash lands in `bin/`.
- `paths` trigger limits the workflow to PRs that actually touch shell scripts.
- `set -euo pipefail` ensures we don't silently miss failures.

If a CI workflow already exists in `.github/workflows/`, extend it with an extra job rather than adding a new file — match the existing convention.

### Step 5.4: Verify the workflow file passes

Run the same loop locally one final time:

```bash
fail=0
for f in setup bin/*; do
  [ -f "$f" ] || continue
  if head -1 "$f" | grep -q 'bash'; then
    shellcheck "$f" || fail=1
  fi
done
echo "fail=$fail"   # expect 0
```

### Step 5.5: Confirm intentional-failure detection

To prove the gate actually catches violations, temporarily introduce a known violation (e.g. `foo=$bar` with unquoted `$bar` where word-splitting matters), run the loop, confirm it fails, then revert. Document this manual verification step in the PR description; do not commit the bug.

## Verification

### Automated Tests (permanent)
- No pytest changes. The CI workflow itself IS the permanent gate.

### Validation Scripts (temporary)

```bash
# 1. Local shellcheck sweep passes:
fail=0
for f in setup bin/*; do
  [ -f "$f" ] || continue
  head -1 "$f" | grep -q 'bash' && { shellcheck "$f" || fail=1; }
done
[ "$fail" -eq 0 ] && echo OK

# 2. Workflow file is syntactically valid YAML:
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/shellcheck.yml'))"

# 3. CI runs on a draft PR and goes green.
```

### Manual Checks
- Push the branch, open a draft PR — confirm the `shellcheck` job runs and exits 0.
- Introduce a deliberate `SC2086` violation in a fork-test branch, push, confirm CI fails. Revert before merge.

### Success Criteria
- [ ] `.github/workflows/shellcheck.yml` exists (or equivalent extension to an existing workflow).
- [ ] Workflow uses shebang-aware sweep over `setup` + `bin/*`.
- [ ] All current bash scripts pass shellcheck (no violations on main).
- [ ] CI fails on intentionally-introduced violation (smoke-tested before merge).
- [ ] No business logic changed — only quoting, variable declaration patterns, and shellcheck disables.

## Execution Notes

- Be conservative with `# shellcheck disable=SCxxxx` directives. Each disable is a future maintenance burden — only suppress when fixing the violation would change semantics or harm readability.
- `bin/_lib.sh` is sourced, not executed. Shellcheck handles sourced libs fine but may emit `SC2148` (no shebang) — leave the file shebang-less if that's the convention; suppress the warning at the top: `# shellcheck shell=bash`.
- Coordinate file boundaries: sp8 will add new bash to `setup` and rely on shellcheck to catch errors. Land sp5 first if possible so sp8's CI run already has the gate active. (The manifest dependency graph allows sp5 to run anytime.)
- Don't reformat existing code beyond shellcheck-required changes. A separate cleanup pass is out of scope.

**Spec-linked files:** None.
