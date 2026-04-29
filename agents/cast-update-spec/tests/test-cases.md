# Test Cases: cast-update-spec

## TC-1: Add new behavior to existing spec
- Input: "Add bulk delete behavior to the tasks spec"
- Expected: Shows diff, waits for approval, bumps version

## TC-2: Decline proposed change
- Input: Approve prompt → "no"
- Expected: No edits made

## TC-3: Ambiguous spec target
- Input: "Update the spec" (no domain specified)
- Expected: Asks which spec, consulting _registry.md
