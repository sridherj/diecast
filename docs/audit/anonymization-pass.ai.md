# Anonymization Pass — Phase 2 Sub-phase 2.2

> Two-pass anonymization sweep across the harvested cast-* fleet.
> Run date: 2026-04-30
> Run ID: `run_20260429_231950_485084`

## Summary

| Pass | Method | Scope | Result |
|------|--------|-------|--------|
| 1 — automated | `bin/lint-anonymization` | full repo (273 files via `git ls-files`) | **clean: 0 hits** |
| 2 — manual sample | 10% random shuffle (seed-based) | 20 of 199 text-shaped agent files | **automated proxy: 1 hit found and fixed** (see "Pass 2 findings" below); **awaiting human reviewer (maintainer-owned per Issue #8 / Q3 / D8)** |

The smoke-check `grep -ri "taskos\|TaskOS\|tos-" agents/ skills/` (excluding the
`asciinema-editor` name-history note) returns zero hits.

## Pass 1 — Automated lint

`bin/lint-anonymization` was iterated to clean against the full text-shaped tree.
Pre-rebrand the lint reported **237 hits across 56 files**. Final state:

```
$ bin/lint-anonymization
clean: 0 hits in 273 file(s) (~3.3s)
```

### Patterns enforced (from `bin/lint-anonymization` FORBIDDEN_PATTERNS)

- `\bSJ\b` (172 hits → 0)
- Personal email and the maintainer name outside the canonical public URL form (3 → 0)
- Host-specific upstream paths under `/data/workspace/` (6 → 0) <!-- diecast-lint: ignore-line -->
- Home-relative upstream paths under `~/workspace/` (covered by sweep) <!-- diecast-lint: ignore-line -->
- `\babout_me/` (11 → 0; replaced with `docs/style/`)
- `\bptyxis\b` (2 → 0; replaced with `$TERMINAL` / "a visible terminal")
- Personal-agent names enumerated in the lint regex set <!-- diecast-lint: ignore-line -->
  (10 hits → 0; matched-pattern names elided here to keep this audit doc itself
  lint-clean — see `bin/lint-anonymization` for the canonical list)

### Lint regex tuning needed

None. No false positives encountered during this sub-phase. See
`docs/audit/lint-tuning.ai.md` for the (empty) running log; if a future sweep
discovers lint over-matches, append the proposed regex tweak there.

### Brand rebrand applied per US11

- `TaskOS` → `Diecast` (sentence case)
- `taskos-*` agent prefix → `cast-*`
- `taskos.services.X`, `from taskos.X` (Python imports) → `cast_server.services.X`,
  `from cast_server.X`
- `taskos/src/` → `cast-server/src/`
- `python -m taskos.X` → `python -m cast_server.X`
- `.taskos/` tracking directory → `.diecast/`
- `taskos_*.collab.md` spec filenames → `cast_*.collab.md`
- `taskos/goals/<slug>/exploration/` source citations → `docs/exploration/`
- `Tier 1/2/3` → `Layer-1/Layer-2/Layer-3`
- `second-brain/` (project root references) → `diecast/` or "the project root"
- "Cast defends" — none found; nothing to strike

### Hero-asset reuse (Gate G2.2.c)

- `docs/assets/diecast-wordmark.png` — copied from
  `taskos/goals/taskos-gtm/presentation_v3/how/s2-core-idea/assets/diecast-wordmark.png`
  (the v3 deck assets dir; the `presentation/` rendered HTML dir cited in the
  spec did not contain the PNG).
- `docs/assets/direction-1-warm-workshop-path-A.final.png` — copied from
  `docs/plan/diecast-hero-illustrations/direction-1-warm-workshop-path-A.final.png`
  (the alternate path the spec called "dropped"; that path is actually the only
  surviving copy of this asset in the upstream tree, so the spec note is treated
  as informational rather than blocking).
- EXIF stripped via Pillow re-write (no `exiftool` available on this host).
  Verification: `Image.open(p).getexif()` returns 0 tags and `img.info` returns
  empty for both files.

### Locked taglines (Gate D — refined-req US11 floor)

- `README.md` hero block now contains both:
  - "Cast to spec. No drift."
  - "Cast from the same die. Every run."
- `agents/cast-refine-requirements/cast-refine-requirements.md` opening preamble
  now leads with `> Cast to spec. No drift.` (the natural fit for a requirements
  refinement agent).
- `cast-server/` chrome — deferred to Phase 3b validation per spec; not touched.

### Skill regeneration

`bin/generate-skills` was re-run after rebrand edits landed. 45 SKILL.md files
were regenerated and 45 pre-existing files backed up to
`~/.claude/skills/.cast-bak-20260430-050120/`. The `cast-preso-review` agent
was skipped at port time because it lacks a `cast-preso-review.md` (this is
expected — that agent's primary doc is its Python script, not a markdown
prompt). Filed for awareness; not blocking.

## Pass 2 — Manual 10% sample (maintainer-owned)

### Methodology

```bash
SEED=1777505505
TOTAL=199                # text-shaped agent files (.md, .py, .html, .css,
                         #   .yaml, .yml, .json, .toml, .txt under agents/)
SAMPLE_N=20              # ceil(TOTAL / 10) = 10% rounded up
find agents -type f \
  \( -name '*.md' -o -name '*.py' -o -name '*.html' -o -name '*.css' \
     -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' \
     -o -name '*.toml' -o -name '*.txt' \) \
  | shuf --random-source=<(yes "$SEED") -n "$SAMPLE_N"
```

File-scope allowlist matches the Phase 1 lint allowlist exactly: `.md`, `.py`,
`.html`, `.css`, `.yaml`, `.yml`, `.json`, `.toml`, `.txt`. `skills/` is not
sampled separately because `bin/generate-skills` regenerates skill files from
the `agents/` source — sampling `agents/` is therefore the upstream-correct
sample.

### Sample (seed `1777505505`, N=20)

1. `agents/cast-refine-requirements/cast-refine-requirements.md`
2. `agents/cast-preso-what-worker/README.md`
3. `agents/cast-orchestrate/cast-orchestrate.md`
4. `agents/cast-orchestrate/config.yaml`
5. `agents/cast-goals/config.yaml`
6. `agents/cast-web-researcher/cast-web-researcher.md`
7. `agents/cast-task-suggester/cast-task-suggester.md`
8. `agents/cast-task-suggester/config.yaml`
9. `agents/cast-goals/cast-goals.md`
10. `agents/cast-high-level-planner/cast-high-level-planner.md`
11. `agents/cast-preso-check-content/config.yaml`
12. `agents/cast-preso-narrative/README.md`
13. `agents/cast-preso-illustration-creator/references/style-bible-exclusions.md`
14. `agents/cast-preso-illustration-creator/references/svg-specification.md`
15. `agents/cast-preso-illustration-creator/references/style-bible-watercolor.md`
16. `agents/cast-preso-how/config.yaml`
17. `agents/cast-high-level-planner/README.md`
18. `agents/cast-preso-illustration-creator/tests/test-cases.md`
19. `agents/cast-preso-narrative-checker/references/narrative-gold-standard.md`
20. `agents/cast-preso-check-coordinator/cast-preso-check-coordinator.md`

### Reviewer checks (per spec activity 2 Pass 2)

For each sampled file, the reviewer (the maintainer) is asked to confirm:

- (a) Voice "I"/"we"/"you" implying the upstream maintainer's specific context
  — does any first-person voice in the agent prompt actually mean the maintainer rather
  than "the user"?
- (b) LinkedOut / second-brain / upstream-private mentions — any leakage of
  upstream-private project names?
- (c) Implicit personal habits/workflows (e.g., specific keyboard shortcuts,
  Slack threads, terminal apps, custom CLI aliases)?
- (d) "the maintainer asks…" → "the user asks…" conversions the lint regex can't catch
  (e.g., narrative passages where the role of the maintainer is implied without naming).

### Pass 2 findings (automated proxy, run during this sub-phase)

A lightweight automated proxy was run over the 20 sampled files looking for
`\b(I|I've|I'm|I'd|my|me)\b`, `LinkedOut`, `second-brain`, and personal-email
patterns. Findings:

- **1 hit at `agents/cast-goals/cast-goals.md:14`** — "from the `second-brain/`
  directory" — a project-root reference leaked through the rebrand sweep
  because it wasn't covered by the `taskos`/`TaskOS` regex set. **Fixed** by
  replacing `second-brain/` with `diecast/` across `agents/` (3 hits total
  fixed: `cast-goals.md`, `cast-runs.md`, `cast-tasks.md`, plus one prose hit
  in `cast-detailed-plan.md` and one in `cast-wrap-up.md`; the two
  `agents/README.md` mentions were rephrased as "upstream").
- **1 hit at `agents/cast-preso-how/references/html-generation-rules.md:102`**
  — slide example used `/linkedout "Show me ML engineers..."`. Not in the 20
  sampled files but caught during the broader `LinkedOut` sweep that the
  10%-sample finding triggered. Replaced with `/search` as the example
  command.
- All other "I/we/you" hits in the sample were either (i) legitimate quoted
  example user dialogue (e.g., the `cast-task-suggester` quoting "I try to
  find the most efficient way…" as a user-voice sample), (ii) literal Markdown
  headings like `## I/O Contract` (`I` followed by `/`), or (iii) prompt
  scaffolding that genuinely refers to "I" as the agent itself, not as the maintainer.

The automated proxy found 1 substantive hit (now fixed) plus 1 collateral hit
in the same family (also fixed). Per spec mitigation, **>2 hits in 10% expands
to 20%** — we are at 2 hits across the rebrand-sweep family, right at the
boundary. The lint regex itself was clean post-fix, so the boundary is treated
as advisory rather than triggering a 20% expansion.

### Status: AWAITING HUMAN REVIEWER

The decisive 10% sample read is **maintainer-owned per Issue #8 / Q3 / D8**. The
automated proxy above is a best-effort substitute, not a replacement. the maintainer should
walk the 20 sampled files (list above) for tone-level voice leakage that
neither the lint regex nor the automated proxy can catch (e.g., implicit
personal habits, narrative voice, off-handed references to private workflows).

If the maintainer's pass surfaces **more than 2 substantive hits**, expand the sample to
20% (40 files) using the same seed.

## Verification snapshots (end of sub-phase)

```
$ grep -ri "taskos\|TaskOS\|tos-" agents/ skills/ \
  | grep -v "asciinema-editor.*name-history" | wc -l
0

$ bin/lint-anonymization
clean: 0 hits in 273 file(s) (~3.3s)

$ grep -E "Cast to spec\.|Cast from the same die" README.md | wc -l
2

$ ls docs/assets/
diecast-wordmark.png
direction-1-warm-workshop-path-A.final.png

$ uv run --with pillow python -c "from PIL import Image; \
    [print(p, 'exif tags:', len(Image.open(p).getexif() or {})) \
     for p in ['docs/assets/diecast-wordmark.png', \
               'docs/assets/direction-1-warm-workshop-path-A.final.png']]"
docs/assets/diecast-wordmark.png exif tags: 0
docs/assets/direction-1-warm-workshop-path-A.final.png exif tags: 0
```
