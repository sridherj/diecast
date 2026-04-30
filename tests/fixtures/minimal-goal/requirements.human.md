# Minimal Goal Requirements

## Problem
A synthetic minimal goal used by `bin/audit-interdependencies` dry-runs.
Each cast-* agent walks this fixture to verify its first-read paths exist,
its first-delegation targets resolve, and its output-JSON schema matches
contract-version-2. The fixture is intentionally small so a full-fleet
dry-run finishes in a single session.

## Constraints
- No real LinkedOut data; no SJ-personal artifacts.
- All paths resolve under this fixture root.
- Keep the skeleton to the canonical seven docs subtrees.

## Examples
- A `cast-explore` dry-run reads `requirements.human.md`, writes `exploration/summary.ai.md`.
- A `cast-orchestrate` dry-run resolves `_manifest.md` under `docs/execution/`.
