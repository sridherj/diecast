# Sub-phase 7: README "Run the server" subsection + mental-model postscript

> **Pre-requisite:** Read `docs/execution/cast-server-first-run-launch/_shared_context.md` before starting.

## Objective

Close the README's "no how to start the server" gap (§C) with a new "Run the server" subsection covering the auto-launch behavior, restart commands, and env-var seam. Include the §H step 6 mental-model postscript ("only `cast-server` is on `$PATH`; everything else is `/cast-*`") in the same edit so README ownership is consolidated to a single sub-phase.

## Dependencies

- **Requires completed:** sp1 (port seam) — needs the new `8005` default and the `CAST_HOST` / `CAST_BIND_HOST` / `CAST_PORT` env-var conventions.
- **Assumed codebase state:** sp1 has shifted port to 8005 and swept all README literal port references. `README.md` Quick Start fence still ends at the existing `:62–64` location with "That's the chain…" prose, followed by `---` and `## What you get` heading at `:66–68`.

## Scope

**In scope:**
- Insert a new `### Run the server` subsection in `README.md` directly after the Quick Start fence at `:62–64`, before the `---` and `## What you get` heading.
- Update `README.md:55` install blurb to mention the auto-launch behavior.
- Add the §H step 6 mental-model postscript inside the new subsection.

**Out of scope (do NOT do these):**
- `cast-server/README.md` — sp1's sweep handles it.
- `bin/README.md` — sp6 owns the rewrite.
- Any other `*.md` file — sp1 sweeps the rest.
- The §H bin-docstring sweep — sp6 owns it.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `README.md` | Modify | Quick Start fence at `:62–64`, install blurb at `:55`. No "Run the server" section anywhere. |

## Detailed Steps

### Step 7.1: Update install blurb at `README.md:55`

Find the existing line (something like "drops cast-* skills + agents into ~/.claude/, puts cast-server on your PATH"). Append the auto-launch behavior:

> "drops cast-* skills + agents into `~/.claude/`, puts `cast-server` on your `$PATH`, **and starts it on first install**."

The exact phrasing should match the surrounding voice — eyeball the current sentence and minimize stylistic drift.

### Step 7.2: Insert "Run the server" subsection

Location: directly after the Quick Start fence (line `:62–64`'s "That's the chain…" prose), before the `---` rule and `## What you get` heading at `:66–68`.

New content (~22 lines, including the §H step 6 postscript):

````markdown
### Run the server

`./setup` starts cast-server in the background and opens the dashboard on first
install. To start it again after a reboot or shell restart:

```bash
cast-server                            # http://localhost:8005, on $PATH after ./setup
./bin/cast-server                      # equivalent, from a fresh clone
CAST_PORT=8080 cast-server             # custom port (8005 is the default)
CAST_BIND_HOST=0.0.0.0 cast-server     # server-side bind for LAN access
CAST_HOST=cast.example.com cast-server # client-side connect target (future cloud)
```

cast-server is a single user-level daemon — one instance per machine, shared
across every project you cd into. State lives in `~/.cast/diecast.db`; logs at
`~/.cache/diecast/server.log` (bootstrap output at `bootstrap.log`).
`CAST_HOST` / `CAST_PORT` are the *client-side* connect target (used by skills
calling the server); `CAST_BIND_HOST` controls the *server-side* bind. Each
goal binds to one repo via its `external_project_dir` column.

Only `cast-server` is on your `$PATH`. Every other Diecast operation is a
`/cast-*` slash command inside Claude Code (run `/cast-doctor` to diagnose,
`/cast-init` to scaffold, `/cast-runs` for the dashboard, etc.).
````

The final paragraph is the §H step 6 mental-model postscript.

### Step 7.3: Verify rendering

After saving, look at the file rendered on github.com (or run `glow README.md` / `mdcat README.md` locally) to confirm:

- The `### Run the server` heading lands between Quick Start and `## What you get` without breaking the surrounding `---` rules.
- The bash fence renders correctly.
- The mental-model postscript reads as a natural conclusion to the subsection, not as orphan content.

## Verification

### Automated Tests (permanent)
- No automated test. README content is human-verified.

### Validation Scripts (temporary)

```bash
# 1. Subsection placement is correct:
grep -n '^### Run the server' README.md
grep -n '^## What you get' README.md
# Expect: "Run the server" line number < "What you get" line number.

# 2. Quick Start fence still terminates correctly:
# Eyeball the file at the insertion point.

# 3. Port number is consistent:
grep -F '8005' README.md | wc -l
# Expect: ≥4 (in the bash block + prose references).

# 4. Old port is gone:
grep -E '\b(8000)\b' README.md
# Expect: no hits (sp1 already swept).

# 5. Mental-model postscript present:
grep -F 'Only `cast-server` is on your' README.md
# Expect: 1 hit.
```

### Manual Checks
- Open the file on github.com after pushing — confirms markdown renders cleanly with no broken structure.
- Grep for `cast-server` in the install blurb area — confirms the "and starts it on first install" addition lands.
- Eyeball the bash block — env-vars are spelled correctly (`CAST_HOST`, `CAST_BIND_HOST`, `CAST_PORT`).

### Success Criteria
- [ ] README has a `### Run the server` subsection between Quick Start and `## What you get`.
- [ ] The subsection includes the bash block with all four env-var examples.
- [ ] The subsection includes the §H step 6 mental-model postscript.
- [ ] `README.md:55` install blurb mentions "**and starts it on first install**".
- [ ] No `:8000` literal anywhere in `README.md`.
- [ ] Markdown renders cleanly on github.com.

## Execution Notes

- **Single owner of `README.md`:** this sub-phase is the only one that edits `README.md`. sp1's sweep does NOT include `README.md` for the new subsection's content (sp1 only handles existing references). sp6's bin-docstring sweep does NOT touch `README.md`. If you find another sub-phase appearing to edit README.md, halt and reconcile before proceeding.
- The mental-model postscript references `/cast-doctor`, `/cast-init`, and `/cast-runs`. `/cast-doctor` is introduced by sp6, but sp7 doesn't depend on sp6 — the README references it as a future state, and sp6 lands in the same PR.
- Don't add any other sections, links, or restructuring to README. Surgical edit.
- The bash fence inside the markdown content needs careful escaping — note the `````` triple-backtick fence around the embedded ```` ```bash ```` block in step 7.2 above. Inside the file, it's a normal triple-backtick.

**Spec-linked files:** None.
