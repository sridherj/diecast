#!/usr/bin/env bash
# run-tests.sh — cast-explore-workflow unit tests (review #7 + review #9).
# These exercise the JS engine's PURE helpers (degradedPlaceholder, resolveSurvivingNotes)
# via Node with injected Workflow-tool runtime-global stubs. No live Workflow tool needed.
# Exit 0 = all pass.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fail=0
for t in test_barrier_glob_intersection.mjs test_all_hats_fail_placeholder.mjs; do
  echo "=== $t ==="
  if ! node "$HERE/$t"; then fail=1; fi
  echo
done
if [ "$fail" -ne 0 ]; then echo "SOME TESTS FAILED" >&2; exit 1; fi
echo "ALL cast-explore-workflow TESTS PASSED"
