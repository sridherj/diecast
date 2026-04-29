# Test Cases: playbook-synthesizer

## Scenario 1: Synthesize from full 7-angle research
**Input:** Complete research notes from web-researcher on "building a developer tool"
**Expected:** Playbook with all sections filled. Opinionated, not a summary. Impact rating justified. Tools table has real tools.
**Status:** Not tested

## Scenario 2: Synthesize from partial research
**Input:** Research notes with some angles missing (e.g., contrarian failed)
**Expected:** Playbook still produced. Missing angles noted but don't block output.
**Status:** Not tested

## Scenario 3: Quality of opinions
**Input:** Research on a topic with conflicting advice
**Expected:** Playbook takes a clear stand, doesn't hedge with "it depends". Contrarian section highlights the tension.
**Status:** Not tested

## Scenario 4: File output
**Input:** Research + output directory + step number
**Expected:** Playbook saved as `<NN>-<step-slug>-playbook.md`
**Status:** Not tested
