# Lint Regex Tuning Log

> Running log of false positives discovered against `bin/lint-anonymization`'s
> `FORBIDDEN_PATTERNS` and the proposed regex tweaks. The lint runs in CI on
> every push and PR, so every entry here represents a public-output decision.

## 2026-04-30 — Phase 2 Sub-phase 2.2

No false positives encountered. The lint cleared from 237 hits → 0 hits via
content edits alone; no pattern in `bin/lint-anonymization` needed tuning.

## Procedure for adding entries

If a future sweep finds a forbidden-pattern match that is genuinely safe to
publish:

1. Confirm the hit is a true false positive (not just an embarrassing leak).
2. Decide the smallest regex change that exempts only the safe form. Prefer
   negative lookbehind/lookahead over broad exemptions.
3. Open a short entry below with: file/line, current regex, proposed regex,
   one-sentence justification.
4. Land the regex change in `bin/lint-anonymization` only after the entry is
   recorded here.
