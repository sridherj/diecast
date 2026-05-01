# sp2.3 — Preamble-Builder Classes + DispatchModeValidator

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Five test classes targeting `_build_agent_prompt` and `AgentConfig` exclusively
(pure-function tests, no DB/filesystem). Includes the SC-004 mixed-transport
invariant and the Review #8 dispatch_mode silent-fallback pin.

## Dependencies

- **Requires completed:** sp2.1.
- **Assumed codebase state:** `_build_agent_prompt` exists in `agent_service.py`
  (locate it; signature may differ from second-brain). `AgentConfig` dispatch_mode
  validator at `agent_config.py:36-41`.

## Scope

**In scope:**
- `TestPreambleAntiInline` (US1.S7) — block presence/absence by `allowed_delegations`.
- `TestPromptBuilder` (US1.S7+S8) — interactive block + delegation-instruction.
- `TestMixedTransportPreamble` (US1.S9) — both blocks emit, anti-inline phrase
  exactly once, child names whole-word-scoped via `\b<name>\b`.
- `TestDispatchModeValidator` (US2 silent-failure surface) — pin the documented
  silent fallback to `http`.

**Out of scope (do NOT do these):**
- Modify `_build_agent_prompt`. If structure has diverged from second-brain
  (Risk #3), document the divergence in the equivalence-map docstring as
  justified deviation, do NOT change `_build_agent_prompt`.
- Test runtime dispatch behavior — that's covered by sp2.1's allowlist tests.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Append 4 classes | Has sp2.1, sp2.2 classes |

## Detailed Steps

### Step 2.3.1: Read `_build_agent_prompt` carefully

Locate the function in `agent_service.py`. Note:
- Inputs: at least `allowed_delegations`, `interactive`, possibly `dispatch_mode`
  (per-agent or per-child).
- Outputs: the rendered prompt string.
- Block structure: HTTP-dispatch block, Subagent-dispatch block, anti-inline
  rule, interactive block.

If diecast structure has diverged from second-brain (e.g., different anti-inline
phrase wording), DOCUMENT the divergence in the equivalence-map docstring under
`TestMixedTransportPreamble`. Do NOT alter the function.

### Step 2.3.2: `TestPreambleAntiInline` (US1.S7)

```python
class TestPreambleAntiInline:
    def test_block_present_with_non_empty_allowlist(self):
        out = _build_agent_prompt(allowed_delegations=["child"], ...)
        assert "CRITICAL" in out  # or whatever the diecast phrase is
        assert "NEVER inline" in out  # or diecast equivalent
        assert "child" in out

    def test_block_absent_with_empty_allowlist(self):
        out = _build_agent_prompt(allowed_delegations=[], ...)
        assert "CRITICAL" not in out
        assert "NEVER inline" not in out

    def test_block_absent_with_none_allowlist(self):
        out = _build_agent_prompt(allowed_delegations=None, ...)
        assert "NEVER inline" not in out
```

### Step 2.3.3: `TestPromptBuilder` (US1.S7+S8)

Parametrize `interactive=True/False`:
- `INTERACTIVE SESSION` block present iff `interactive=True`.
- Delegation-instruction block present iff `allowed_delegations` non-empty.

### Step 2.3.4: `TestMixedTransportPreamble` (US1.S9, SC-004)

Build a prompt for a parent whose `allowed_delegations` mix HTTP and subagent
children. Assertions:
- HTTP block present.
- Subagent block present.
- `out.count("NEVER inline") == 1` (or diecast equivalent — pin in test).
- Each child name appears scoped to its block via `\b<name>\b` regex
  (whole-word match, NOT substring).

Use the second-brain regex pattern verbatim for SC-004 compliance:
```python
import re
http_block_match = re.search(r"HTTP[\s\S]*?(?=Subagent|$)", out)
subagent_block_match = re.search(r"Subagent[\s\S]*?$", out)
assert re.search(rf"\b{http_child_name}\b", http_block_match.group())
assert not re.search(rf"\b{http_child_name}\b", subagent_block_match.group())
# and the symmetric assertion for the subagent child
```

### Step 2.3.5: `TestDispatchModeValidator` (Review #8 / US2)

Three methods pinning the intentional silent-fallback semantics:

```python
class TestDispatchModeValidator:
    def test_valid_subagent_preserved(self):
        cfg = AgentConfig(agent_id="x", dispatch_mode="subagent",
                          allowed_delegations=[], model="haiku", trust_level="readonly")
        assert cfg.dispatch_mode == "subagent"

    def test_typo_falls_back_to_http_silently(self):
        cfg = AgentConfig(agent_id="x", dispatch_mode="subagnet",  # intentional typo
                          allowed_delegations=["a", "b"], model="haiku",
                          trust_level="readonly")
        assert cfg.dispatch_mode == "http"
        assert cfg.allowed_delegations == ["a", "b"]  # sibling fields preserved
        assert cfg.model == "haiku"
        assert cfg.trust_level == "readonly"

    def test_valid_http_preserved(self):
        cfg = AgentConfig(agent_id="x", dispatch_mode="http", ...)
        assert cfg.dispatch_mode == "http"
```

This pins the design choice that distinguishes a `str + validator` from a
`Literal[...]` annotation. Future "fix the typo handling" changes will fail
these tests loudly — the test IS the documentation.

### Step 2.3.6: Update equivalence-map docstring

- Replace `<TODO sp2.3>` markers for the three second-brain-mapped classes.
- Add `TestDispatchModeValidator` under "Diecast-only additions".
- Document any structural divergence in `_build_agent_prompt` as justified
  deviation.

## Verification

### Automated Tests (permanent)

```
pytest cast-server/tests/integration/test_child_delegation.py \
       -k "PreambleAntiInline or PromptBuilder or MixedTransport or DispatchModeValidator"
```

### Validation Scripts (temporary)

SC-004 explicit assertion: confirm `out.count("NEVER inline") == 1` (or pinned
diecast equivalent string) appears in the test code.

### Manual Checks

- Mixed-transport regex uses `\b<name>\b`, NOT substring `in`.
- `TestDispatchModeValidator::test_typo_falls_back_to_http_silently` asserts ALL
  sibling fields (`allowed_delegations`, `model`, `trust_level`) are preserved,
  not degraded to defaults.

### Success Criteria

- [ ] Four classes added.
- [ ] SC-004 invariant pinned.
- [ ] Silent-fallback pin documented.
- [ ] Equivalence map updated with TestDispatchModeValidator under "diecast-only".
- [ ] FR-008 grep clean.

## Execution Notes

- **Spec-linked files:** `agent_service.py` (`_build_agent_prompt`),
  `agent_config.py` (`AgentConfig`). Read
  `docs/specs/cast-delegation-contract.collab.md` §Subagent Dispatch and the
  preamble structure expectations before writing assertions.
- **SC-004 is non-negotiable.** Use the regex form, not substring `in`. Substring
  matching is exactly the bug second-brain hit historically.
- If the diecast preamble's anti-inline phrase differs from second-brain's
  ("NEVER inline"), pin the diecast phrase in the test verbatim — do not
  generalize. The test is the contract.
