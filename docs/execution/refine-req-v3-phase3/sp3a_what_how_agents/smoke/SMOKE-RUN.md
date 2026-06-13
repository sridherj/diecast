# sp3a Smoke-Run Note — cast-requirements-what / cast-requirements-how

> NOT a CI test. LLM output is gated by 3b's `maker_gate.py`, not snapshot-asserted. This note
> records a one-shot hand-run that proves both agents emit contract-shaped output. The sample
> artifacts beside this file are discardable eyeball references, not fixtures.

- **Date:** 2026-06-12
- **Goal exercised:** `refine-requirements-better-rendering-v3` (`new_initiative` family, conf 0.9)
- **Source:** `docs/goal/refine-requirements-better-rendering-v3/refined_requirements.collab.md`
  (`source_hash` head `cb3971de16bc`, 31 canonical refs: US1–US7, FR-001–FR-016, SC-001–SC-008)
- **Invocation pattern (mirrors the 3c runner):**
  `env -u CLAUDECODE claude -p "<inlined inputs>" --append-system-prompt <agent>.md --model opus --tools ""`
  (clean child env per the `agent_service.py` precedent; `--tools ""` makes "maker never writes
  the canonical source" structural).

## WHAT agent — PASS

`cast-requirements-what` produced one `cast-requirements-what/v1` doc. Programmatic checks:

- Front matter parses as YAML; `contract`, `goal_slug`, `family`, `source_hash` carried verbatim.
- **Total id-mapping:** all 31 inventory refs mapped across 9 sections' `block_refs`, each exactly
  once — 0 duplicates, 0 missing, 0 invented. `unmapped_refs: []`.
- `gaps: []` (reserved Phase-5 seam, empty, zero behavior).
- **No section titled after a US/FR/SC slot** — titles are communication-intent
  ("What every reader must get in seconds", "The bet — a cast-preso-style WHAT-then-HOW maker", …).

Sample: `what_doc.sample.md`.

## HOW agent — PASS

`cast-requirements-how` produced one self-contained HTML document between
`<!-- BEGIN RENDER -->` / `<!-- END RENDER -->`. Strict extraction yielded 35,883 bytes
(`<!doctype html>` … `</html>`). DOM-contract checks:

- **Zero `id=`, zero `data-block-anchor`** (logical-only id backbone).
- **Self-contained:** CSS inline; no external/CDN `<link>`; only the two FR-028-sanctioned scripts
  `/static/htmx.min.js` + `/static/requirements_comments.js`; `data-goal-slug="…"` on `<body>`.
- **Anchor labels:** every canonical id present as a visible `<span class="anchor">` label.
- **No `GAPS-DETECTED`** inside the render window (Phase-3 documentation-only seam respected).

**Honest note (gate is the arbiter):** a byte-grep counted `US1` twice — but one occurrence is an
HTML *comment* (`<!-- ABOVE THE FOLD (US1 Scenario 1) -->`, invisible, dropped by 3b's
container-text walker) and the other is the single real `<span class="anchor">US1</span>`. Exactly
one rendered anchor label; the verbatim-carriage / one-label-per-id obligation is checked precisely
by 3b's `check_html`, which operates on container text, not raw bytes including comments.

Sample: `render_extracted.sample.html`.

## Verdict

Both agents speak the fixed contracts. WHAT-doc YAML parses and maps every id once; HOW HTML
extracts cleanly from sentinels and honors the DOM/self-containment/anchor rules. Ready for 3b
(gate), 3c (runner), 3d (route), 3e (spec) to build on these contracts.
