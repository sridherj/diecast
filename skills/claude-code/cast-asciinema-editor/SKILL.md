---
name: cast-asciinema-editor
description: "Edit asciinema .cast recordings for demo videos. Trims sections, compresses spinner/thinking animations, speeds up typing, and keeps visual coherence. Use when: the user wants to edit, trim, speed up, or polish a .cast terminal recording."
license: Apache-2.0
metadata:
  author: sanjay3290
  version: "2.0"
---

# Asciinema Cast Editor

Edit `.cast` terminal recordings into polished demo videos.

## Phase 0: Locate the recording

Ask the user for the `.cast` file path. Verify it exists and read the header + last event to get duration and event count.

## Phase 1: Analyze and present content map

**1.1** Read all events from the file. Each line after the header is `[timestamp, "o", text]`.

**1.2** Strip ANSI escape sequences to extract visible text:

```python
def strip_ansi(text):
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    clean = re.sub(r'\x1b\][^\x07]*\x07', '', clean)
    clean = re.sub(r'\[[\?0-9;>]*[a-zA-Z]', '', clean)
    clean = re.sub(r'[\x00-\x08\x0e-\x1f]', '', clean)
    return clean.strip()
```

**1.3** Window events into ~8s chunks. For each window, collect cleaned text and produce a one-line summary.

**1.4** Find all user prompt lines (search for `❯` in cleaned text).

**1.5** Present a **numbered content breakdown table** to the user:

```
| # | Time       | What's happening              | Duration |
|---|------------|-------------------------------|----------|
| 1 | 0:00-0:12  | Launch command                | ~12s     |
| 2 | 0:12-0:30  | Skill autocomplete            | ~18s     |
| 3 | 0:30-0:50  | User: "find devrel folks"     | ~20s     |
```

Ask: "Which sections should I cut, compress, or keep?"

## Phase 2: Cut sections

For each section the user wants removed, filter events by **original** timestamp range:

```python
filtered = [e for e in events if not (cut_start < e[0] < cut_end)]
```

After all cuts, re-zero timestamps:

```python
offset = filtered[0][0]
for e in filtered:
    e[0] -= offset
```

## Phase 3: Classify events into timing tiers

For each event, classify into one of these tiers. **Order matters — check in this sequence:**

| Step | Tier | Detection | Target gap |
|------|------|-----------|------------|
| 1 | `spinner` | Contains spinner words (Catapulting, Enchanting, Photosynthesizing, Generating, Levitating), spinner chars (✶✻✽✢●·*✳), "thinking with high effort", or is a title bar update (`\x1b]0;`) | **5ms** |
| 2 | `backspace` | Raw text contains cursor-back (`\x1b[\d+D`) AND cleaned visible text is empty. These are actual character deletions — the user typed something wrong and is deleting it. Also mark the N typing events immediately preceding a backspace run as `backspace` (the mistaken text being deleted). | **5ms** |
| 3 | `typing` | Single visible printable character (not a spinner char) | **30ms** |
| 4 | `results` | Any Claude response content the viewer should read: tables (box-drawing chars `│┼┤├`), explanatory prose (>40 chars without SQL/tool keywords), numbered recommendations, suggestion bullets. Basically everything that IS the demo output. | **800ms** (readable scroll) |
| 5 | `important` | Contains `❯` (user prompt) — the user's input lines | **800ms max** |
| 6 | `fast` | Bash tool calls (`Bash(`), raw SQL output (`full_name|`, `crawled_profile_id`), status displays (`tokens`, `ctrl+o`), or anything else | **50ms max** |

### Why this order

- **Results before important:** Claude Code's TUI re-renders the `❯` prompt alongside result tables. If you check `❯` first, all table rows get misclassified as prompts.
- **Results before fast:** Some table events contain keywords like `headline` that match fast rules.
- **`│` (U+2502 box-drawing) vs `|` (ASCII pipe):** Raw SQL uses pipe `|`. Rendered tables use box-drawing `│`. Don't confuse them.

## Phase 4: Apply timing compression

**Never drop frames.** Terminal recordings are stateful — each frame depends on prior cursor positions and escape sequences. Dropping frames causes visual glitches (text jumping). Only adjust timestamps.

```python
adjusted = 0.0
prev_ts = 0.0
for e in events:
    orig_gap = e[0] - prev_ts
    target = target_gaps[classify(e)]  # from tier table above
    new_gap = min(orig_gap, target) if tier in ('results', 'important', 'fast') else target
    adjusted += orig_gap - new_gap
    prev_ts = e[0]
    e[0] = round(e[0] - adjusted, 6)
```

## Phase 5: Verify and report

After every edit pass:

1. Report duration: `"1m 12s (was 8m 17s)"`
2. Report classification counts: `"spinner=3076, results=51, typing=441, important=36, fast=469"`
3. **Verify all user queries survived** — search for `❯` with user input text. Report count.
4. Tell user to play: `asciinema play <file>`

If the user wants further adjustments, go back to Phase 2 or 3. **Always rebuild from the original file** — don't stack compression passes.

## Rules

- **Never drop frames.** Compress timing only.
- **Always rebuild from the original .cast file** when re-editing.
- **Verify user queries after every edit.**
- **Use original timestamps for section cuts** — not previously compressed timestamps.
- **Cursor-back (`\x1b[\d+D`) is NOT backspace.** Claude Code's TUI uses cursor-back for all rendering. Nearly every event contains it — don't use it as a signal.
