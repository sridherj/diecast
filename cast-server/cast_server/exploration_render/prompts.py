"""The exploration maker prompt builders (forked from requirements with provenance).

The WHAT/HOW/checker prompts inline the exploration inputs. They stay FORKED from the requirements
maker prompts (the content genuinely differs — N×M hat substrate vs a canonical-id doc), housed in
this exploration-specific module (NOT render_common) with provenance. Each takes the job state (duck-
typed: `goal_slug`, `source_digest`, `steps`, `hat_matrix`, `summary_text`, `what_doc`) so this module
need not import the service.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from cast_server.render_common.quality_loop import FeedbackItem
from cast_server.render_common.sentinel import _BEGIN_SENTINEL, _END_SENTINEL
from cast_server.requirements_render.zero_click import extract_zero_click_view

from .verdict import CHECKER_CONTRACT

if TYPE_CHECKING:  # pragma: no cover
    StateT = Any

_WHAT_AGENT = "cast-exploration-what"


def hat_matrix_label(state: Any) -> str:
    """A compact per-step applicable-hat label — what the checker uses to judge criterion 1 WITHOUT
    seeing the source md."""
    return json.dumps(
        [{"step": s["slug"], "name": s["name"], "applicable_hats": state.hat_matrix.get(s["slug"], []),
          "degraded": s["degraded"]} for s in state.steps],
        indent=2,
    )


def render_feedback(prompt: str, feedback: list[FeedbackItem] | None,
                    score_history: str | None = None) -> str:
    """Append provenance-separated feedback (structural hard fixes vs quality nudges) to a prompt."""
    if not feedback and not score_history:
        return prompt
    structural = [i.text for i in (feedback or []) if i.provenance == "structural"]
    quality = [i.text for i in (feedback or []) if i.provenance == "quality"]
    parts = [prompt]
    if structural:
        parts.append("Structural fixes (required) — fix EVERY one and re-emit the COMPLETE output:")
        parts.extend(f"- {t}" for t in structural)
    if quality:
        parts.append("Quality improvements (guidance) — raise comprehension / distinctness / visual:")
        parts.extend(f"- {t}" for t in quality)
    if score_history:
        parts.append(score_history)
    return "\n".join(parts) + "\n"


def build_what_prompt(state: Any, feedback: list[FeedbackItem] | None = None) -> str:
    steps_payload = [{
        "nn": s["nn"], "slug": s["slug"], "name": s["name"], "degraded": s["degraded"],
        "playbook_md": s["playbook_text"],
        "hat_notes": [{"hat_id": h["hat_id"], "status": h["status"], "md": h["text"]}
                      for h in s["hat_notes"]],
    } for s in state.steps]
    prompt = (
        f"Produce the WHAT doc (contract {_WHAT_AGENT}/v1) for this exploration.\n"
        f"goal_slug: {state.goal_slug}\n"
        f"source_digest: {state.source_digest}\n"
        "Per step: decide ONE opinionated POV outcome (the collation, drawn from the playbook) and, "
        "for EACH surviving hat note, a DISTINCT one-line take in that hat's voice (never blended). "
        "Mark each hat present | dropped | gated; a dropped always-on hat is a visible degradation, "
        "never omitted. Sections are named after STEPS, not hat ids.\n"
        f"\n----- BEGIN HAT MATRIX (applicable hats per step) -----\n{hat_matrix_label(state)}\n"
        "----- END HAT MATRIX -----\n"
        f"\n----- BEGIN STEP CORPUS -----\n{json.dumps(steps_payload, indent=2)}\n"
        "----- END STEP CORPUS -----\n"
        f"\n----- BEGIN SUMMARY -----\n{state.summary_text}\n----- END SUMMARY -----\n"
    )
    return render_feedback(prompt, feedback)


def build_how_prompt(state: Any, feedback: list[FeedbackItem] | None = None,
                     score_history: str | None = None) -> str:
    corpus = "\n\n".join(
        f"----- STEP {s['nn']} {s['slug']} -----\n{s['playbook_text']}\n"
        + "\n".join(f"[hat:{h['hat_id']} status:{h['status']}]\n{h['text']}" for h in s["hat_notes"])
        for s in state.steps
    )
    prompt = (
        f"Produce the self-contained HTML render between the {_BEGIN_SENTINEL} / {_END_SENTINEL} "
        "sentinels, per your contract. Reuse the cast-preso visual-toolkit style tokens so the page "
        "is family-shaped, not generic AI-slop.\n"
        f"goal_slug: {state.goal_slug}\n"
        "LAYOUT CONTRACT (FR-017 criterion 3 — the heart of this render): per step, render the "
        "opinionated POV as the DOMINANT, zero-click-legible element; then the DISTINCT hat takes "
        "BENEATH it as individually-attributed SEPARATE units (each hat in its own card/labelled "
        "block, NEVER blended into one paragraph). The always-on hats "
        "(contrarian/first-principles/90-10) get consistent recognizable treatment across steps. A "
        "null/dropped hat is shown as an explicit 'this lens was attempted and dropped' marker "
        "(surface, don't suppress); a gated-out hat is simply absent. Each hat take / POV is a clean "
        "selectable text unit in its OWN container (US7 one-unit-one-container, no stable ids).\n"
        f"\n----- BEGIN WHAT DOC -----\n{state.what_doc}\n----- END WHAT DOC -----\n"
        f"\n----- BEGIN SOURCE MD CORPUS -----\n{corpus}\n----- END SOURCE MD CORPUS -----\n"
    )
    return render_feedback(prompt, feedback, score_history)


def build_checker_prompt(state: Any, html: str) -> str:
    """The checker sees ONLY the rendered page + the step/hat-matrix label — never the source md."""
    zero_click = extract_zero_click_view(html)
    return (
        f"Grade this rendered exploration page. Emit ONE bare JSON verdict (contract "
        f"{CHECKER_CONTRACT}) — no prose, no code fences. Grade FR-017's 4 locked criteria: "
        "(1) hat_coverage_ok — every APPLICABLE hat (per the matrix label) visible per step; "
        "(2) pov_legible — each step's opinionated POV legible at the zero-click surface; "
        "(3) distinctness_ok — hat takes stay DISTINCT, individually attributable, not blended; "
        "(4) visual_ok — quality work, not generic AI-slop. Name any failed criterion in missing[] "
        "using the tokens pov/distinctness/hat_coverage/visual.\n"
        f"\n----- BEGIN HAT MATRIX (the applicable hats per step) -----\n{hat_matrix_label(state)}\n"
        "----- END HAT MATRIX -----\n"
        f"\n----- BEGIN ZERO-CLICK VIEW -----\n{zero_click}\n----- END ZERO-CLICK VIEW -----\n"
        f"\n----- BEGIN FULL RENDERED HTML -----\n{html}\n----- END FULL RENDERED HTML -----\n"
    )
