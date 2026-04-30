"""US13 close-out discipline — deterministic harness.

The full cast-refine-requirements agent is LLM-driven. This harness mirrors
the close-out discipline rule encoded in
`skills/claude-code/cast-interactive-questions/SKILL.md`
(§ "Close-out Discipline (US13)") so the rule itself can be exercised by
tests without an LLM in the loop.

The mirror is explicit -- when the skill's discipline changes, this module
MUST be updated to match (and the prompt-artifact regression guards in
`tests/test_us13_no_open_questions.py` catch drift).

Behavior modeled (one full pass per scenario):

  1. Enumerate the agent's "open ambiguities" list (loaded from a fixture).
  2. For each ambiguity, render an AskUserQuestion via the (stub) user-answer
     queue. The answer determines the resolution path:
       * answer that does NOT start with one of the close-out tags ->
         the ambiguity is resolved interactively and folded into the body
         (it does NOT appear in the trailing Open Questions section).
       * answer that starts with `[EXTERNAL]` or `[USER-DEFERRED]` ->
         the ambiguity is rendered into the trailing Open Questions
         section with that tag and the remainder of the answer used as
         the Reason.
  3. Write the artifact (preamble + folded resolutions + trailing Open
     Questions section iff any tagged items exist).
  4. Build a contract-v2 terminal output JSON:
       * `human_action_needed = True` iff any item carries `[EXTERNAL]`.
       * `human_action_items[]` lists the verbatim `[EXTERNAL]` items.
       * `[USER-DEFERRED]` items stay in the artifact only.

`run_refine_with_buggy_close_out_fixture` is a deliberate violation path
used by `test_us13_untagged_open_question_is_a_violation`: it punts every
ambiguity into the Open Questions section without applying a tag.

`find_untagged_open_question_lines` is the validator helper a CI gate
would use to flag violators downstream.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import yaml

CLOSE_OUT_TAGS: Tuple[str, ...] = ("[EXTERNAL]", "[USER-DEFERRED]")
_TAG_LINE_RE = re.compile(
    r"^- \*\*\[(EXTERNAL|USER-DEFERRED)\]\*\* .+\. Reason: .+\.$"
)


# ---------------------------------------------------------------------------
# Stub user-answer queue
# ---------------------------------------------------------------------------


@dataclass
class StubUserAnswers:
    """FIFO queue of (prompt_substring, answer) tuples used by the harness.

    The harness pops the first entry whose prompt_substring appears in the
    rendered question prompt. Mirrors how a test scripts the AskUserQuestion
    side of an interactive flow.
    """

    _entries: List[Tuple[str, str]] = field(default_factory=list)

    def queue(self, entries: Iterable[Tuple[str, str]]) -> None:
        self._entries.extend(entries)

    def pop_for(self, prompt: str) -> Optional[str]:
        for idx, (needle, answer) in enumerate(self._entries):
            if needle.lower() in prompt.lower():
                self._entries.pop(idx)
                return answer
        return None


# ---------------------------------------------------------------------------
# Trace returned to tests
# ---------------------------------------------------------------------------


@dataclass
class CloseOutTrace:
    artifact_path: Path
    terminal_output: dict
    rendered_questions: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tag parsing
# ---------------------------------------------------------------------------


def _detect_tag(answer: str) -> Optional[str]:
    """Return the tag prefix in `answer` iff it starts with a close-out tag."""
    stripped = answer.strip()
    for tag in CLOSE_OUT_TAGS:
        if stripped.upper().startswith(tag):
            return tag
    return None


def _parse_tagged_answer(answer: str) -> Tuple[str, str]:
    """Split a tagged answer into (tag, reason)."""
    tag = _detect_tag(answer)
    assert tag is not None, "answer is not tagged"
    reason = answer.strip()[len(tag):].strip()
    if reason.startswith(":"):
        reason = reason[1:].strip()
    return tag, reason or "no reason supplied"


# ---------------------------------------------------------------------------
# Validator helper (used by CI-gate-style assertions)
# ---------------------------------------------------------------------------


def find_untagged_open_question_lines(terminal_output: dict) -> List[str]:
    """Return any list-item lines in the artifact's Open Questions section
    that lack a recognized close-out tag in the documented format.

    Lines that don't begin with `- ` are ignored (allow blank lines and
    explanatory paragraphs). Tagged-but-malformed lines are still violations
    because they break the contract-v2 consumer's parser.
    """
    artifact_path = Path(terminal_output["artifacts"][0]["path"])
    text = artifact_path.read_text()
    if "Open Questions" not in text:
        return []
    section = text.split("Open Questions", 1)[1]
    violations: List[str] = []
    for raw in section.splitlines():
        line = raw.rstrip()
        if not line.startswith("- "):
            continue
        if not _TAG_LINE_RE.match(line):
            violations.append(line)
    return violations


# ---------------------------------------------------------------------------
# Internal: write artifact + terminal output
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _write_artifact(
    artifact_path: Path,
    preamble: str,
    resolved: List[Tuple[str, str]],
    tagged: List[Tuple[str, str, str]],
) -> None:
    """Write the refined-requirements artifact.

    `resolved`: list of (id, answer) folded into the body.
    `tagged`: list of (id, tag, reason) emitted in Open Questions.
    """
    parts: List[str] = [preamble.rstrip(), ""]
    if resolved:
        parts.append("## Resolved Ambiguities")
        parts.append("")
        for ambiguity_id, answer in resolved:
            parts.append(f"- **{ambiguity_id}** -> {answer}")
        parts.append("")
    if tagged:
        parts.append("## Open Questions")
        parts.append("")
        for ambiguity_id, tag, reason in tagged:
            parts.append(f"- **{tag}** {ambiguity_id}. Reason: {reason}.")
        parts.append("")
    artifact_path.write_text("\n".join(parts))


def _build_terminal_output(
    artifact_path: Path,
    tagged: List[Tuple[str, str, str]],
) -> dict:
    external_items = [
        f"{tag} {amb_id}. Reason: {reason}."
        for amb_id, tag, reason in tagged
        if tag == "[EXTERNAL]"
    ]
    return {
        "contract_version": "2",
        "agent_name": "cast-refine-requirements",
        "task_title": "Synthetic refine close-out scenario",
        "status": "completed",
        "summary": (
            "Synthetic refine run used by US13 tests to exercise close-out "
            "discipline. Resolved ambiguities are folded into the body; "
            "tagged ambiguities are emitted in Open Questions per spec."
        ),
        "artifacts": [
            {
                "path": str(artifact_path),
                "type": "plan",
                "description": "Refined requirements artifact (synthetic).",
            }
        ],
        "errors": [],
        "next_steps": [],
        "human_action_needed": bool(external_items),
        "human_action_items": external_items,
        "started_at": _now_iso(),
        "completed_at": _now_iso(),
    }


def _load_scenario(fixture_dir: Path) -> dict:
    return yaml.safe_load((fixture_dir / "scenario.yaml").read_text())


def _resolve_artifact_path(fixture_dir: Path, scenario: dict) -> Path:
    return fixture_dir / scenario["artifact_path"]


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def run_refine_with_close_out_fixture(
    fixture_dir: str | Path,
    stub_user_answers: StubUserAnswers,
) -> CloseOutTrace:
    """Drive a full close-out pass against a fixture directory.

    Honors the close-out discipline:

      * Untagged answers fold into the body and are NOT in Open Questions.
      * Tagged answers (`[EXTERNAL]` / `[USER-DEFERRED]`) flow to Open
        Questions with a Reason line; `[EXTERNAL]` items lift to
        `human_action_items[]`.

    Raises `RuntimeError` if the scenario references an ambiguity for which
    no scripted answer was queued -- this catches forgotten test setup.
    """
    fixture_dir = Path(fixture_dir)
    scenario = _load_scenario(fixture_dir)
    artifact_path = _resolve_artifact_path(fixture_dir, scenario)
    rendered: List[str] = []
    resolved: List[Tuple[str, str]] = []
    tagged: List[Tuple[str, str, str]] = []

    for ambiguity in scenario["ambiguities"]:
        prompt = ambiguity["prompt"]
        rendered.append(prompt)
        answer = stub_user_answers.pop_for(prompt)
        if answer is None:
            raise RuntimeError(
                f"no scripted answer for ambiguity {ambiguity['id']!r} "
                f"(prompt={prompt!r})"
            )
        if _detect_tag(answer):
            tag, reason = _parse_tagged_answer(answer)
            tagged.append((ambiguity["id"], tag, reason))
        else:
            resolved.append((ambiguity["id"], answer))

    _write_artifact(
        artifact_path, scenario["artifact_preamble"], resolved, tagged
    )
    terminal_output = _build_terminal_output(artifact_path, tagged)
    return CloseOutTrace(
        artifact_path=artifact_path,
        terminal_output=terminal_output,
        rendered_questions=rendered,
    )


def run_refine_with_buggy_close_out_fixture(
    fixture_dir: str | Path,
) -> CloseOutTrace:
    """Drive a deliberately-buggy close-out -- punts every ambiguity into
    Open Questions WITHOUT applying a tag. Used to assert that the
    validator helper flags untagged lines.
    """
    fixture_dir = Path(fixture_dir)
    scenario = _load_scenario(fixture_dir)
    artifact_path = _resolve_artifact_path(fixture_dir, scenario)

    parts: List[str] = [scenario["artifact_preamble"].rstrip(), ""]
    parts.append("## Open Questions")
    parts.append("")
    for ambiguity in scenario["ambiguities"]:
        # Note: NO tag. NO Reason. This is the violation path.
        parts.append(f"- {ambiguity['id']}: {ambiguity['prompt']}")
    parts.append("")
    artifact_path.write_text("\n".join(parts))

    terminal_output = {
        "contract_version": "2",
        "agent_name": "cast-refine-requirements",
        "task_title": "Synthetic buggy close-out",
        "status": "completed",
        "summary": "Buggy close-out used by US13 violation-detection tests.",
        "artifacts": [
            {
                "path": str(artifact_path),
                "type": "plan",
                "description": "Refined requirements artifact (buggy synthetic).",
            }
        ],
        "errors": [],
        "next_steps": [],
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": _now_iso(),
        "completed_at": _now_iso(),
    }
    return CloseOutTrace(
        artifact_path=artifact_path,
        terminal_output=terminal_output,
        rendered_questions=[a["prompt"] for a in scenario["ambiguities"]],
    )


def run_refine_with_external_only_fixture(
    fixture_dir: str | Path | None = None,
) -> CloseOutTrace:
    """Convenience wrapper: drive the standard fixture with both ambiguities
    answered as `[EXTERNAL]`. Used by the human_action_needed test.
    """
    if fixture_dir is None:
        fixture_dir = Path(__file__).resolve().parent.parent / "fixtures" / "refine_with_open_ambiguities"
    answers = StubUserAnswers()
    answers.queue(
        [
            (
                "ambiguity 1",
                "[EXTERNAL] vendor not yet committed",
            ),
            (
                "ambiguity 2",
                "[EXTERNAL] requires API key from third party",
            ),
        ]
    )
    return run_refine_with_close_out_fixture(fixture_dir, answers)


# ---------------------------------------------------------------------------
# Pretty-printer for debugging (used by some assertions when they fail)
# ---------------------------------------------------------------------------


def dump_terminal_output(trace: CloseOutTrace) -> str:
    return json.dumps(trace.terminal_output, indent=2, sort_keys=True)
