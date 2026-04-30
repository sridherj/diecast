# Review Summary: Terminal Intelligent Defaults

Lightweight review of the 2 sub-phase plan files (small-change mode: max 1 issue per section).

## Open Questions

These need SJ's decision **before sp1 starts** because they affect `_SUPPORTED` membership, which sp2's parity test asserts on.

1. **Add `foot` and/or `konsole` to `_SUPPORTED`?**
   The plan says "add `foot`/`konsole` to `_SUPPORTED` if approved" (`docs/plan/2026-04-30-terminal-intelligent-defaults.collab.md:67`) but defers the decision. Adding them broadens auto-detect coverage to KDE-first / Wayland-first users. Skipping them keeps the canonical list at 6 entries (today's value). Either way, the parity test in sp2 will enforce that `bin/cast-doctor`'s fallback array exactly matches `_SUPPORTED.keys()` — so the answer must be settled before sp1 modifies the table.
   **Recommendation:** add `foot` (modern Wayland-native, increasingly common); skip `konsole` for v1 (KDE users are a small slice and `konsole`'s `--workdir` flag has historical quirks worth deferring to a follow-up).

2. **`config.headless=True` warning text — keep, soften, or remove?**
   Plan says "the existing `config.interactive` / `config.headless` flags stay as-is. Until a real headless mechanism is built, `config.headless=True` continues to take the existing interactive path; the warning at `agent_service.py:1704-1708` keeps describing today's behavior accurately." The warning today reads "interactive overrides headless" — accurate but hides the fact that `headless=True` alone is also de-facto interactive (no real headless dispatch exists). No action required if SJ is fine with the message as-is; a one-line clarifying tweak is in scope for sp1 if desired.
   **Recommendation:** leave as-is for this PR; flag for the follow-up effort that explores real headless dispatch.

3. **`cast-server` `sys.path` fix — preferred location?**
   sp1 Step 1.5 prefers fixing `sys.path` once in `cast_server/__init__.py` over keeping the duplicate file. If the dev box already imports `agents` cleanly (e.g., via the editable install root), no change is needed. Verify locally with the validation script in sp1 before committing.
   **Recommendation:** verify first; only add the `sys.path.insert` if the cold-import test fails.

## Review Notes by Sub-Phase

### sp1_resolver_fixes
- **Architecture:** Clean separation. `_autodetect()` is added in sp1 but only consumed in sp2 (and tests) — keeping all terminal probing logic in `agents/_shared/terminal.py` is the right call.
- **Code Quality:** `ResolutionError` message wording is verified by an existing test (`test_unset_raises_with_docs_link`) for the substrings `$CAST_TERMINAL`, `$TERMINAL`, `terminal_default`, `supported-terminals.md`. The new test in Step 1.8 adds `bin/cast-doctor --fix-terminal`. Both must pass — flagged in plan Execution Notes.
- **Tests:** Coverage extends in place, reusing the existing `clean_env`/`tmp_path` scaffolding. KDE/`konsole` test is gated on `_SUPPORTED` membership so it auto-skips when the open question resolves "no."
- **Performance:** Negligible. Resolver runs once per dispatch.

### sp2_cast_doctor_fix_terminal
- **Architecture:** Bash + Python heredoc for the YAML write is a justified compromise — pure-bash YAML editing is a footgun. Falls back to a single-line write when `python3` is missing (install-time edge case).
- **Code Quality:** Drops `wezterm` and `iterm2` (incorrect canonical key) from the existing hardcoded list — this is a behavioral change worth calling out in the commit message.
- **Tests:** Subprocess tests skip on macOS (`uname` mocking is messy in bash). Coverage is preserved because sp1's `_autodetect()` unit tests inject `system="Darwin"` explicitly. The parity test (`test_fallback_list_matches_supported`) runs unconditionally.
- **Performance:** Not relevant — `--fix-terminal` is a one-time setup command.

## Resolution Status

- [ ] Open Question #1 — `foot`/`konsole` decision
- [ ] Open Question #2 — `config.headless` warning text (low priority)
- [ ] Open Question #3 — `cast-server` `sys.path` fix verified locally before sp1 commit
