---
name: cast-interactive-questions
description: >
  Standard protocol for asking users questions via AskUserQuestion tool.
  One question at a time, structured options, recommendation first with grounded reasoning.
  Referenced by all interactive Diecast agents.
---

# Interactive Question Protocol

When you need user input during an interactive workflow, ALWAYS use the **AskUserQuestion tool**.
Never ask questions as plain conversational text -- the tool provides structured rendering with
options, recommendations, and clear formatting that plain text cannot match.

## Rules

### 1. One question at a time

Ask the single most important question, wait for the answer, then proceed or ask the next.
**NEVER batch multiple questions or issues into one AskUserQuestion call.** Even if you have
5 issues to raise, present them one by one. This lets the user focus, give thoughtful answers,
and change direction early without wading through a wall of text.

### 2. Structured options

When there are discrete choices, present them as **lettered options** (A, B, C). Include
"do nothing" or "defer" as an option where reasonable.

### 3. Recommendation first

Lead with your recommended option marked **(Recommended)** and explain **WHY** with grounded
reasoning. "Grounded" means you cite evidence from artifacts you've actually read -- exploration
results, requirements, code patterns, spec behavior, task history -- not generic advice.

### 4. Grounded reasoning per option

Each option gets a 1-2 sentence rationale based on what you've observed. Bad: "This is simpler."
Good: "The exploration playbook rated this approach 9/10 impact and the codebase already has
a `ServiceBase` pattern at `services/base.py` that this would extend naturally."

### 5. Sequential numbering

Number questions **#1, #2, #3** sequentially across the entire session so the user can
reference them later ("go with A on #3").

### 6. Priority ordering

Ask the most consequential question first. Priority:
1. **Decisions that change the plan shape** (scope mode, architecture approach)
2. **High-risk unknowns** (things that invalidate work if wrong)
3. **Scope ambiguity** (unclear boundaries that could cause 2x effort)
4. **Edge cases and preferences** (nice to resolve but recoverable if wrong)

## Format Template

Use this structure in every AskUserQuestion call:

```
**Question #N: [Topic]**

[1-2 sentences of context: why this matters, what you found that makes it ambiguous]

- **Option A -- [short description] (Recommended):** [grounded rationale]
- **Option B -- [short description]:** [grounded rationale]
- **Option C -- [short description]:** [grounded rationale]
```

For yes/no questions or open-ended input where options don't apply, simplify:

```
**Question #N: [Topic]**

[Context and what you need from the user. State your recommendation if you have one.]
```

## Anti-Patterns

1. **The Wall of Text** -- Batching 4+ issues into one AskUserQuestion. The user skims,
   gives shallow answers, or misses items. Fix: one question per call.

2. **The Ungrounded Option** -- "Option A is better because it's cleaner." Says nothing.
   Fix: cite specific evidence from artifacts, code, or exploration.

3. **The Plain Text Question** -- Asking in regular conversation instead of AskUserQuestion.
   The user misses it, can't distinguish it from commentary, and the tool's structured
   rendering is wasted. Fix: always use the tool.

4. **The Leading Question** -- Presenting only one real option and a strawman. Fix: every
   option should be genuinely viable, even if you have a clear recommendation.

5. **The Premature Question** -- Asking before you've read enough to form a recommendation.
   Fix: read artifacts first, form an opinion, THEN ask. The user wants your informed
   take, not a delegation of thinking.

6. **The Redundant Question** -- Asking about something the requirements or exploration
   already answered clearly. Fix: check artifacts before asking. Only ask when genuinely
   ambiguous.
