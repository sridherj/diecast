# Test Cases — cast-preso-what-worker

## TC-1: Happy path — information slide

**Input:**
- Stub: `presentation/what/05-agent-resume.stub.md` with 3 L1 items, 2 L2 items, 3 content
  pointers (all local file paths).
- Narrative: `presentation/narrative.collab.md` exists.

**Expected output:**
- `presentation/what/05-agent-resume.md` (note: `.md`, not `.stub.md`).
- First four sections (Slide Info, Top-Level Outcome, Narrative Fit, Slide Type Guidance)
  and L1/L2 match the stub verbatim.
- Resources section has at least 2 concrete local file references with line ranges.
- Data Points section has exact numbers (not "~X" or "approx").
- Verification Criteria section has ≥3 checkable items.

**Pass criteria:**
- Doc written to the right path.
- Verbatim sections identical to stub (diff-clean).
- No vague pointers ("see X") in Resources.

## TC-2: Happy path — hook slide with web research

**Input:**
- Stub for a hook slide with one open question: "confirm current AI company count".

**Expected output:**
- Web search or WebFetch attempted for the count.
- Data Points section contains the resolved number with a source URL in External References.
- Worker Open Questions section either empty or lists any remaining gaps.

**Pass criteria:** External References section has ≥1 entry. The stub's open question
is addressed in Data Points OR escalated in Worker Open Questions.

## TC-3: Missing stub

**Input:** Delegation context points to a slide ID whose stub file doesn't exist.

**Expected output:**
- Agent FAILs with error: `"Stub not found at {path} — planner must run first."`
- Output contract `status: "failed"`, no partial doc written.

**Pass criteria:** No file at `presentation/what/{slide_id}.md`.

## TC-4: Rework mode — fix one doc

**Input:**
- Existing `presentation/what/05-agent-resume.md` written by a previous invocation.
- Delegation context: `mode: "rework"`, `slide_id: "05-agent-resume"`, feedback:
  `{failing_checks: ["verification_criteria_specific"], feedback_detail: "Criterion 2 is subjective", what_worked: ["resources", "data_points", "L1/L2"]}`.

**Expected output:**
- Same doc path overwritten.
- Verification Criteria section rewritten; Resources and Data Points sections unchanged.
- First four sections still match the stub verbatim.

**Pass criteria:** Only the failing section changed. `what_worked` sections preserved.

## TC-5: Worker respects stub — does NOT rewrite outcome

**Input:**
- Stub has a top-level outcome the worker disagrees with (e.g., worker thinks the L1
  items don't serve the stated outcome).

**Expected output:**
- Top-level outcome and L1/L2 copied verbatim from the stub.
- Disagreement logged in Worker Open Questions section.

**Pass criteria:** The stub's outcome text appears verbatim in the output doc. Worker
Open Questions contains the disagreement.

## TC-6: Content pointer file missing

**Input:**
- Stub points to `nonexistent/file.md:15-30` as a content pointer.

**Expected output:**
- Worker logs the missing file in Worker Open Questions.
- Worker continues, fills the doc from other pointers or web search.
- Status = `"completed"` (not `"failed"`) — a single missing pointer is recoverable.

**Pass criteria:** Doc is produced. Open Questions lists the missing file. `human_action_needed`
true only if the missing file was the *only* source.
