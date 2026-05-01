# sp2.4 — Port `TestContinueAgentRun` (Continuation File Delivery)

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Cover US1.S10: `continue_agent_run(run_id, message)` writes the message verbatim
to `.agent-<run_id>.continue`, sends a tmux instruction containing `Read <path>`
(NOT pasting the message body), and raises `ValueError("...no longer exists...")`
if the tmux session is missing.

This is a security-relevant assertion — terminal injection attack surface.

## Dependencies

- **Requires completed:** sp2.1.
- **Assumed codebase state:** `continue_agent_run` exists in `agent_service.py`
  or a sibling module; tmux interface is mockable (likely a `tmux_send` helper).

## Scope

**In scope:**
- `TestContinueAgentRun` with three methods covering write-first, tmux-instruction-shape,
  and missing-session.

**Out of scope (do NOT do these):**
- Test the tmux session lifecycle. Mock the tmux interface entirely.
- Test continuation file cleanup — that's covered by `TestFinalizeCleanup` (sp2.2).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Append 1 class (3 methods) | Has prior sp2 classes |

## Detailed Steps

### Step 2.4.1: Locate the tmux send helper

Find the function `continue_agent_run` calls to send to tmux. Likely names:
`tmux_send`, `_send_to_tmux_session`, or similar. This is the mock target.

### Step 2.4.2: Implement the three test methods

```python
class TestContinueAgentRun:
    """SECURITY-RELEVANT: tmux instruction MUST NOT contain the message body.
    
    The message is written to .continue file; tmux is instructed to read that
    file. Pasting the message into the terminal opens a terminal-injection
    attack surface (US1.S10).
    """
    
    def test_message_written_to_continue_file(self, monkeypatch, tmp_path):
        # Setup: pre-existing tmux session (mocked as alive)
        sent_calls = []
        monkeypatch.setattr(<tmux_send_target>, lambda session, payload: sent_calls.append((session, payload)))
        # Drive
        continue_agent_run(run_id="abc", message="hello world", goal_dir=str(tmp_path))
        # Assert
        cont_path = tmp_path / ".agent-abc.continue"
        assert cont_path.exists()
        assert cont_path.read_text() == "hello world"

    def test_tmux_instruction_uses_read_path_not_message_body(self, monkeypatch, tmp_path):
        sent_calls = []
        monkeypatch.setattr(<tmux_send_target>, lambda session, payload: sent_calls.append((session, payload)))
        continue_agent_run(run_id="abc", message="EVIL_INJECTION_TOKEN", goal_dir=str(tmp_path))
        # Assert tmux saw `Read <path>`, NOT the message body
        assert len(sent_calls) >= 1
        all_payload = "\n".join(p for _, p in sent_calls)
        assert "Read " in all_payload
        assert ".agent-abc.continue" in all_payload
        assert "EVIL_INJECTION_TOKEN" not in all_payload   # <-- the security assertion

    def test_missing_session_raises_value_error(self, monkeypatch, tmp_path):
        # Mock the tmux-session-exists check to return False
        monkeypatch.setattr(<tmux_session_exists_target>, lambda session: False)
        with pytest.raises(ValueError, match="no longer exists"):
            continue_agent_run(run_id="abc", message="m", goal_dir=str(tmp_path))
```

Adapt the mock targets to actual diecast symbol names.

### Step 2.4.3: Make `test_tmux_instruction_uses_read_path_not_message_body` the
FIRST method in the class

Per design-review flag: visibility for the most security-relevant assertion.
Document in class docstring.

### Step 2.4.4: Update equivalence-map docstring

Replace `<TODO sp2.4>` with `TestContinueAgentRun`.

## Verification

### Automated Tests (permanent)

```
pytest cast-server/tests/integration/test_child_delegation.py -k "ContinueAgentRun"
```

### Validation Scripts (temporary)

```bash
grep -A 1 "class TestContinueAgentRun" \
  cast-server/tests/integration/test_child_delegation.py
```
First method shown should be the security-relevant one.

### Manual Checks

- Class docstring explicitly calls out the security relevance.
- The "EVIL_INJECTION_TOKEN" sentinel (or any uniquely-recognizable substring) is
  used to assert the message body is NOT pasted into tmux.

### Success Criteria

- [ ] One class with three methods.
- [ ] Security-relevant test method first (visibility).
- [ ] Class docstring documents US1.S10's security intent.
- [ ] Three methods cover: file write, tmux-instruction shape, missing-session error.
- [ ] Equivalence map updated.

## Execution Notes

- **Spec-linked files:** `agent_service.py` (or wherever `continue_agent_run`
  lives). Read `docs/specs/cast-delegation-contract.collab.md` for the
  continuation-file contract.
- US1.S10 is unambiguous: the message MUST NOT be pasted. This test is the
  guardrail — do not water down the assertion.
- If `continue_agent_run` does not currently match the spec (e.g., it pastes the
  message), this test will fail. That's a real US2 finding — flag at Gate B for
  sp4b (contract drift).
