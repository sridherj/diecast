# Narrative Lock: Why Your Team Should Adopt Agent-Based Development

## Target Group
**TG:** Engineering managers and tech leads at Series B+ startups (50-500 engineers) who currently use CI/CD automation but have not adopted AI agents for development workflows.
**NOT TG:** Individual developers looking for personal productivity tools. Enterprise architects at Fortune 500 companies (different procurement and compliance needs). Teams with fewer than 10 engineers (overhead not justified).

## Walk-Away Outcomes
### L1 (Presentation-Level)
- Understand that agent-based development is a team-level capability, not a personal tool — it changes how work is assigned and reviewed
- Feel confident that the approach works at their scale — see evidence from teams of 50-200 engineers with measurable output gains
- Leave with a specific, actionable first step they can take on Monday morning

### L2 (Section-Level)
- The Problem: Recognize that their current automation covers builds and deploys but leaves a gap in specification, implementation, and review
- The Model: Understand the maker-checker-orchestrator pattern and how it maps to their existing team structure (developer=maker, reviewer=checker, PM=orchestrator)
- The Evidence: Know the specific metrics (PR throughput +3.2x, review cycle time -40%, defect escape rate -15%) from three production case studies at 50-200 engineer scale
- The Risks: Understand the three failure modes and how to prevent each — this is not a sales pitch
- The Path Forward: Identify the one workflow in their team where they could pilot agent-based development in under 2 weeks

## Consumption Mode
Offline reading
Slides must stand alone without speaker narration. Each slide carries enough context to be understood independently. Appendix is critical — readers will click through to deep-dives.

## Time Available
Unlimited — offline reading
Core flow targets ~10 slides for focused reading. Appendix provides depth for the curious. No time constraint on slide count, but core flow must stay lean.

## Narrative Flow
| # | Section | Outcome | Slide Type | Hook/Reveal Notes |
|---|---------|---------|------------|-------------------|
| 1 | The Automation Gap | Recognize that CI/CD solved deployment but left implementation untouched | hook | Sets up: "You automated the last mile. What about the first?" |
| 2 | What Teams Actually Do All Day | See the breakdown of where engineering time goes (30% spec, 40% implementation, 20% review, 10% deploy) | information | Data slide — grounds the hook in specifics |
| 3 | The Agent-Shaped Hole | Realize that the 40% implementation time is the highest-leverage target | reveal | Aha 1: "The biggest time sink is the one you haven't automated" |
| 4 | What Agent-Based Development Is | Understand the maker-checker-orchestrator pattern in one diagram | information | No jargon — map to roles they already know (developer, reviewer, PM) |
| 5 | How It Maps to Your Team | See their existing team structure reflected in the agent architecture | information | Side-by-side: human team vs. agent team doing the same workflow |
| 6 | Case Study: Acme Corp (200 eng) | Learn that PR throughput increased 3.2x with 15% fewer defect escapes | information | Specific numbers, not hand-wavy claims |
| 7 | The Surprising Part | Discover that review quality improved (not just speed) because checkers are more consistent than humans at 4pm on Friday | reveal | Aha 2: "Agents don't just make you faster — they make review better" |
| 8 | What Can Go Wrong | Understand the three failure modes (scope creep, checker blindness, orchestration complexity) and how to prevent each | information | Builds trust through honesty — not a sales pitch |
| 9 | The 2-Week Pilot | Know exactly which workflow to start with and what success looks like after 2 weeks | moment | Aha 3: "You can start with one workflow next Monday" |
| 10 | Close | Feel that this is achievable and worth trying — not a massive transformation, but a targeted experiment | hook | Ends with forward tension: "The question isn't whether agents can help your team. It's which workflow you'll automate first." |

## Aha Progression
1. First aha (slide 3): The biggest engineering time sink — implementation — is the one area most teams haven't automated
2. Second aha (slide 7): Agent-based review is more consistent than human review, not just faster
3. Third aha (slide 9): You can start a meaningful pilot in 2 weeks with one workflow, not a company-wide transformation

## Appendix Structure
| Topic | Linked From Core Slide | Deep-Dive Content |
|-------|----------------------|-------------------|
| Maker-Checker Pattern Details | Slide 4 | Full architecture diagram with delegation flows, error handling, rework loops. Covers how checkers validate maker output, escalation paths, and iteration budgets. |
| Three Case Studies Extended | Slide 6 | Acme Corp (200 eng, B2B SaaS), Beta Labs (80 eng, fintech), Gamma Inc (150 eng, developer tools) — full metrics tables with before/after, timeline from pilot to full adoption, team structure changes. |
| Failure Mode Playbook | Slide 8 | Detailed prevention and recovery strategies for each of the three failure modes: scope creep (solution: hard task boundaries), checker blindness (solution: adversarial rotation), orchestration complexity (solution: start simple, add layers). |
| Pilot Workflow Selection Guide | Slide 9 | Decision matrix: rows = common eng workflows (bug triage, PR review, test generation, documentation), columns = team characteristics (size, tool maturity, risk tolerance). Recommends the single best starting workflow per team profile. |

<!-- 
CALIBRATION NOTES FOR CHECKER:
- This gold standard passes all 14 checks
- TG is specific (job titles + company stage + team size range)
- Non-TG is explicit with reasoning
- Every outcome is testable ("could a slide verify this?")
- 10 core slides (within 12 limit)
- 5/10 slides are "information" type (50%, above 30% threshold)
- 3 ahas spaced at slides 3, 7, 9 (at least 2 slides between each)
- Both hooks (slide 1, 10) have corresponding reveals (slide 3, forward-looking)
- Appendix topics each reference a specific core slide
- No visual design language (no layouts, CSS, colors mentioned)
- Time Available is stated with implications
-->
