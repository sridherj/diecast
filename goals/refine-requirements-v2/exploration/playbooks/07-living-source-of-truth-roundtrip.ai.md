# Living Source of Truth — Round-Trip Write-Back — Playbook

> **Step 7 of Refine Requirements v2.** How downstream phases (exploration, planning, execution)
> write requirement-affecting changes *back* into the requirements artifact — with provenance,
> notification, change-summary inclusion, and conflict surfacing instead of silent overwrite
> (US7, FR-018→FR-020, SC-006).
>
> **Strategy: GO BROAD.** This recommends the best end-state design unconstrained by today's code,
> then names the migration cost. The headline: **the best design is mostly an *assembly* of
> primitives Steps 2 and 4 already produce — it is not a greenfield subsystem.**

## TL;DR

Build round-trip as **"propose + notify + gate," never "auto-sync."** A downstream phase does not
edit a requirement; it `POST`s a first-class **`change_request`** carrying *where it came from*
(`origin`) and *what it assumed* (`base_version_id`) to a DB the **server owns**, then a single
**writeback agent** (the sole file-writer, mirroring `cast-update-spec`) applies accepted changes to
the requirements file. Conflict detection is a deterministic three-way-merge predicate against
`base_version_id` (optimistic concurrency, `conflictDetection: VERSION`); provenance is **W3C PROV's
Entity/Activity/Agent triple** stored as plain columns; notification rides a **transactional outbox**
so the change and its alert commit atomically. **The key insight that beats the obvious design:
silent two-way sync of a source-of-truth document is *worse* than drift — it is untraceable
overwrite of human intent** (US7 S4). Truth must be *governed*, not eventually-consistent. Net-new
code is thin: one entity, one PROV triple, one outbox, one conflict predicate — everything else is
reused from Steps 2 (stable IDs + versions) and 4 (element diff + same-door API + append-only trail).

## Recommended Stack

| Component | Choice | Why (and why not the alternative) |
|-----------|--------|-----------------------------------|
| **Write-back model** | First-class **`change_request{origin, base}`** entity (DB row), *not* a direct file edit | A direct `UPDATE` forgets the two load-bearing fields: `origin` (powers notify+audit) and `base` (powers conflict detect). A proposal carries both. Rejects the `api_artifacts.save_artifact` blind-overwrite path (code G4) outright. |
| **Write-back transport (agent→system)** | Extend the **`output.json` contract** with a `requirements_writeback` artifact type (additive — "parents ignore unknown fields") **+** a `POST /api/specs/{slug}/change-requests` DB endpoint | Reuses the already-test-covered carrier (`tests/test_b5_*`). Additive evolution breaks no existing parent. A human "suggest edit" hits the *same* endpoint — `author_type` is data, satisfying FR-013 by construction. |
| **File writer** | A single **`cast-requirements-writeback` agent** as sole file mutator (mirrors `cast-update-spec`'s "sole write path") | The delegation contract forbids cast-server from writing artifact files (code G7). Server owns the *proposal DB*; an **agent** owns the *file apply*. One writer = one place for provenance + conflict + version-bump. |
| **Stable anchor** | **Step 2's element surrogate + immutable version snapshot** (hard dependency) | A write-back to "FR-014" needs a durable referent. Today `FR-014` is just text in markdown (code G2). No surrogate ⇒ every round-trip op degrades to fragile text matching. **Blocked on Step 2.** |
| **Conflict detection** | **Three-way merge against `base_version_id`** via `difflib.SequenceMatcher` + `hashlib.sha256` content hash | Optimistic concurrency (AWS AppSync `conflictDetection: VERSION` / git 3-way). Reuses `error_memory`'s `compute_pattern_hash` house style. **No CRDT/OT** — co-editing is out of scope (Step 4 killed it); the residual problem is async reconciliation, which 3-way solves deterministically. |
| **Provenance** | **W3C PROV triple** (Entity / Activity / Agent) as denormalized columns; PROV-O/JSON-LD export deferred | PROV is the W3C standard purpose-built for "who changed what, from where, derived from what" — its 3 relations map 1:1 onto FR-020. Borrow the *shape*, not the JSON-LD ceremony (same posture Step 4 took with Web Annotation). Reuses `error_memory.run_ids` append-list style. |
| **Notification reliability** | **Transactional outbox** table drained by a FastAPI lifespan/`BackgroundTasks` polling relay | The write-change-and-notify is a dual write; a crash between them re-introduces drift or fires a phantom. Outbox commits both in one txn → at-least-once delivery → UI dedupes on `change_request_id`. CDC/Debezium is over-engineering at SQLite scale; polling is the right weight. |
| **Notification surface** | Extend the **`needs_attention` rail** with a structured payload **+** a minimal **W3C-LDN-aligned JSON inbox** endpoint | Reuses the existing `_finalize_run` → `needs_attention` → HTMX-badge rail (code 2b). LDN is the agent-native companion to Step 4's Web Annotation Protocol: the spec advertises an Inbox, agents consume the same resource humans see. No SSE/websocket needed for v2. |
| **Change summary** | **Reuse Step 4's stable-ID element diff** verbatim, add a provenance badge column | `+FR-021 — added by planning · agent cast-high-level-planner · derived from plan.collab.md`. No new diff engine — Step 4's `{added, removed, modified}` set arithmetic plus one provenance column. This is the explicit Step 4→Step 7 hand-off. |
| **Audit trail** | Append-only **`change_request_events`** table (generalize Step 4's `comment_events`) | Event-sourcing's core insight: the event store *is* the audit trail (who/what/when/why, reconstructable). Reuses the append-only pattern already in `error_memory` + Step 4. |
| **Graduated-trust gate** | **Additions auto-apply + FYI; modifications gate; conflicts always surface** (per-element configurable) | Tune the gate by *blast radius*, not author. Pure additions can't overwrite human intent (nothing to lose). Mirrors Jama's per-field configurable suspect tracking. Avoids gate fatigue without opening a data-loss lane. |

## Implementation Steps

> Ordered by dependency. Steps 1–2 are the schema spine; 3–5 the write path; 6–7 conflict + notify;
> 8 the end-to-end proof (SC-006). All assume Step 2 has landed stable element surrogates + versions.

### Step 1: Land the `change_request` schema and the append-only event trail
**Impact: High** | **Effort: 0.5 day**

This is the spine — everything else writes to or reads from these tables. Extend Step 4's
`spec_versions` / `spec_elements` with four tables. The two fields that make round-trip *work* are
`origin_*` (enables notify + audit) and `base_version_id` (enables conflict detection); a naive design
forgets both.

```sql
CREATE TABLE change_requests (
  id            TEXT PRIMARY KEY,           -- e.g. cr_<run_id>_<seq>
  goal_slug     TEXT NOT NULL REFERENCES goals(slug),
  target_surrogate TEXT REFERENCES spec_elements(surrogate),  -- NULL ⇒ pure addition (no target)
  base_version_id  TEXT REFERENCES spec_versions(id),         -- the version the change ASSUMED (conflict anchor)
  kind          TEXT NOT NULL CHECK (kind IN ('addition','modification','annotation')),
  proposed_body TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'proposed'
                  CHECK (status IN ('proposed','accepted','rejected','conflicted','superseded','applied')),
  -- provenance (W3C PROV, denormalized for v2) --
  origin_phase       TEXT,   -- PROV Activity class: exploration|planning|execution
  origin_activity_id TEXT,   -- PROV Activity: the downstream agent run id
  origin_artifact_path TEXT, -- wasDerivedFrom source, e.g. plan.collab.md
  author        TEXT NOT NULL,
  author_type   TEXT NOT NULL CHECK (author_type IN ('human','agent')),  -- PROV Agent + wasAttributedTo
  created_at    TEXT NOT NULL, decided_at TEXT, decided_by TEXT, decided_by_type TEXT
);
CREATE TABLE change_request_events (      -- append-only audit (Step 4's comment_events, generalized)
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  change_request_id TEXT NOT NULL REFERENCES change_requests(id),
  event TEXT NOT NULL CHECK (event IN ('proposed','accepted','rejected','conflicted','applied','superseded')),
  actor TEXT, actor_type TEXT, at TEXT NOT NULL, note TEXT
);
CREATE TABLE notifications_outbox (       -- transactional outbox (same txn as the change)
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_slug TEXT NOT NULL, change_request_id TEXT NOT NULL REFERENCES change_requests(id),
  payload TEXT NOT NULL,                  -- JSON: change-summary delta + provenance
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','delivered')),
  created_at TEXT NOT NULL, delivered_at TEXT
);
```
Create via `db/connection.py` migration (the project's house style for tables absent from
`schema.sql`, per `error_memory`). PROV triples can fold into `change_requests` columns for v2; a
separate `provenance` table is forward-compat, not a v2 need.

### Step 2: Pydantic model the write-back payload (the `output.json` rider)
**Impact: High** | **Effort: 0.5 day**

Define a `RequirementsWriteback` pydantic v2 model and register `requirements_writeback` as an
artifact `type`. Because the output-json contract is additive ("parents MUST ignore unknown fields"),
a downstream agent can emit this *today* without breaking any existing parent.

```python
class RequirementsWriteback(BaseModel):           # rides in AgentOutput.artifacts[] payload
    target_surrogate: str | None                  # None ⇒ pure addition
    kind: Literal["addition", "modification", "annotation"]
    proposed_body: str
    base_version_id: str                           # the version the agent read
    origin_phase: Literal["exploration", "planning", "execution"]
    origin_artifact_path: str                      # wasDerivedFrom
    rationale: str                                 # for the human gate + audit note
```
This is the cheapest possible seam: it reuses the test-covered carrier (`tests/test_b5_atomic_write`,
`test_b5_file_polling`) and the `synthetic_child.py` harness for round-trip tests.

### Step 3: Open the same-door endpoint — `POST /api/specs/{slug}/change-requests`
**Impact: High** | **Effort: 0.5 day**

One endpoint. A human "suggest an edit" action and a downstream agent's write-back are the *identical*
`POST`; `author_type` is **data, not a code branch**. This is FR-013's forcing function (the same
first-principles rule Step 4 derived for its comment API) — the UI must have **no privileged write
path the agent lacks**, or FR-013 is violated by construction. The endpoint writes a `change_request`
row + a `change_request_events('proposed')` row + (Step 7) the outbox row, all in **one transaction**.

> **Architectural reconciliation (web Lens 5 vs. code G7):** the server writing a `change_request`
> *DB row* is allowed; the delegation contract only forbids the server writing artifact *files*. The
> file apply (Step 5) is performed by an **agent**. Server owns the proposal store; agent owns the file.

### Step 4: Implement the graduated-trust router (additions vs. modifications vs. conflicts)
**Impact: High** | **Effort: 0.5 day**

On receipt, branch by *blast radius*, not by author:
- **Pure addition** (`target_surrogate` is NULL, a new FR from a genuine discovery) → fast-track:
  status `applied`, appended as a new element, **FYI notification**. Nothing is overwritten, so the
  blast radius is bounded.
- **Modification / annotation** of an existing **human-authored** element → status `proposed`;
  **never** mutate in place. Surface through the same `AskUserQuestion` gate `cast-update-spec` uses.
- **Conflict** (diverged from `base`) → status `conflicted` → always surface (Step 6).

For v2, recommend **gate-everything-except-pure-additions**, exposed as per-element configuration
(Jama-style), not hardcoded — so an owner can relax it later without a code change.

### Step 5: Build the `cast-requirements-writeback` agent — surgical apply, not file rewrite
**Impact: High** | **Effort: 1.5 days**

The sole file writer. On an accepted/auto-applied change it: resolves `target_surrogate` → anchor,
runs the conflict predicate (Step 6), applies as a **targeted addition/annotation** leaving the rest
of the file byte-identical, appends provenance, bumps the version, emits the change summary.

Reuse `orchestration_service.update_manifest_status()` (`services/orchestration_service.py:218-259`)
as the *exact* template for surgical in-place edit-by-ID — it already rewrites one ID-keyed row and
leaves the rest of a markdown document untouched. That is FR-018's "additions/annotations, not silent
rewrites" already implemented; lift its approach. **Do not** build on `api_artifacts.save_artifact`'s
`write_text` overwrite (code G4) — that reproduces the silent-drift bug US7 exists to kill.

### Step 6: Conflict detection — the three-way predicate against `base_version_id`
**Impact: High** | **Effort: 1 day**

At apply time, compare the target element's *current* body against its body *at `base_version_id`*:

```python
def detect_conflict(element_surrogate, base_version_id, proposed_body):
    current = element_body_at(element_surrogate, "HEAD")
    base    = element_body_at(element_surrogate, base_version_id)
    if sha256(current) == sha256(base):
        return "clean"                              # unchanged since base → apply
    # diverged since base: a human (or another change) touched it
    return "conflicted"                             # → surface, NEVER overwrite (US7 S4)
```
Reuse `error_memory`'s `hashlib.sha256` content-addressing. Conflict UX = the review surface rendered
as a 3-way choice: **accept-incoming / keep-current / merge** (borrowing Jama's *suspect-link*
semantics — the element is flagged suspect until a human *clears* it). For prose elements, "merge"
surfaces both versions + a free edit field; **do not** build an auto-textual-merge for v2 (element
granularity from Step 2 keeps conflicts small). Log every transition in `change_request_events`.

### Step 7: Wire notification — transactional outbox → relay → `needs_attention` + LDN inbox
**Impact: Medium** | **Effort: 1 day**

In the **same transaction** that commits the change, insert a `notifications_outbox` row whose
`payload` is the change-summary delta + provenance (solves the dual-write trap). A FastAPI
lifespan-managed background task polls `WHERE status='pending'`, delivers, and marks `delivered`.
Delivery is at-least-once → the UI dedupes on `change_request_id`.

Surface two ways, both reusing existing rails: (1) extend `_finalize_run`'s
`needs_attention`/`human_action_needed` with a **structured** descriptor (today it carries only a
boolean + prose), so the HTMX badge can show *"requirements updated from planning: +FR-021"*;
(2) a minimal **W3C-LDN-aligned** `GET/POST /api/specs/{slug}/inbox` JSON endpoint so watching agents
consume the same notification resource. The payload answers both FR-019 questions in one shape:
**what changed** (the element diff) + **from where** (the provenance).

### Step 8: Prove it end-to-end with a simulated downstream change (SC-006)
**Impact: High** | **Effort: 0.5 day**

v2 builds the *receiving* mechanism and validates it with a **simulated** downstream change — real
planning/execution agents emitting write-backs is out of scope (per US6/Constraints). Use
`tests/fixtures/synthetic_child.py` to emit a valid `requirements_writeback`, then assert the full
chain: change_request row → conflict verdict → file apply (surgical) → version bump → change summary
with provenance badge → outbox row → notification surfaced. This is SC-006's "trace one downstream
change end-to-end into the files + notification." Mirror `error_memory`'s upsert/escalation test style.

## Architecture / Process Flow

```
 DOWNSTREAM PHASE (planner / executor / explorer agent)
   │ discovers a requirement-affecting change
   ▼
 output.json  artifacts[]: {type:"requirements_writeback", target_surrogate, kind,
   │                        proposed_body, base_version_id, origin_phase, origin_artifact_path}
   │              (additive — output-json contract: parents ignore unknown fields)
   ▼
 POST /api/specs/{slug}/change-requests   ◄────── SAME DOOR ─────  human "suggest edit" (author_type=human)
   │   (author_type=agent)                                         UI has NO privileged path (FR-013)
   ▼
 ┌─────────────────── ONE DB TRANSACTION (server owns the proposal DB; never writes files — G7) ──┐
 │  change_requests(status=proposed, origin_*, base_version_id)                                     │
 │  change_request_events('proposed')          notifications_outbox('pending', payload)             │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼  GRADUATED-TRUST ROUTER  (branch by blast radius, not author)
   ├─ pure addition ───────────────► auto-apply + FYI ──┐
   ├─ modification/annotation ─────► AskUserQuestion gate ─ accept ─┐
   └─ (later) ─────────────────────────────────────────────────────┤
                                                                    ▼
                                       cast-requirements-writeback AGENT  (SOLE file writer)
                                         │  resolve target_surrogate → anchor  [needs Step 2 IDs]
                                         │  CONFLICT PREDICATE vs base_version_id
                                         │     sha256(current)==sha256(base)?  ── no ──► status=conflicted
                                         │           │ yes                              ► SURFACE (US7 S4)
                                         │           ▼                                    suspect-link UX:
                                         │  surgical apply  (update_manifest_status style)  accept-incoming/
                                         │     append/annotate, rest byte-identical (FR-018) keep-current/merge
                                         │  append PROV triple (wasGeneratedBy/AttributedTo/DerivedFrom)
                                         │  bump version + element-diff change summary + provenance badge (FR-020)
                                         ▼
                                       requirements file  (e.g. +FR-021 appended) — always current truth
   ┌──────────────────────────────────────────────────────────────────────────────────────────┐
   │ OUTBOX RELAY (FastAPI background poll) ─► needs_attention badge (HTMX)  +  /inbox (W3C LDN) │
   │   "requirements updated from planning: +FR-021 · cast-high-level-planner · plan.collab.md"  │
   └──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Decisions

| Decision | Recommendation | Rationale (and the trade-off) |
|----------|---------------|-------------------------------|
| Auto-sync vs. propose+gate | **Propose + notify + gate** | Silent auto-overwrite of a source-of-truth doc is untraceable data loss (US7 S4) — *worse* than drift. Trade: a human/gate step in the loop, accepted because truth must be governed. |
| Server writes the file vs. agent writes | **Agent is sole file writer; server owns proposal DB** | Delegation contract forbids server file writes (G7). Reconciles the API-endpoint design with the contract; trade: one extra hop (DB proposal → agent apply). |
| Direct edit vs. `change_request` entity | **`change_request{origin, base}` entity** | The two fields a direct edit forgets are exactly what powers notify (origin) + conflict (base). Trade: one more table. |
| Conflict engine | **3-way merge / optimistic concurrency**, no CRDT | CRDT/OT are for concurrent co-editing — explicitly out of scope. Async reconciliation against a known base is deterministic with 3-way. Trade: requires version identity per element (Step 2). |
| Provenance depth | **Denormalized PROV columns now; PROV-O export later** | PROV's 3 relations map 1:1 onto FR-020; full JSON-LD is ceremony with no v2 consumer. Trade: a later export task if interop is ever required. |
| Notification transport | **Transactional outbox + polling relay**, no broker/SSE | Outbox solves the dual-write atomically on the existing FastAPI+SQLite stack. Broker/CDC/websocket is scale-up, not a v2 need. Trade: at-least-once → must dedupe on `change_request_id`. |
| Auto-apply policy | **Additions auto-apply + FYI; modifications gate; conflicts surface** | Gates keyed to blast radius beat a uniform gate (which causes rubber-stamping or disabling). Trade: a thin policy config surface (Jama-style per-element). |
| Change-summary engine | **Reuse Step 4 element diff + provenance badge** | Building a second diff engine double-pays for Step 4. Trade: hard dependency on Step 4 landing its diff. |
| Re-anchoring a change semantically | **Anchor to the stable surrogate; similarity only as a human-confirmed hint** | Embedding/semantic re-anchor is non-deterministic and un-auditable (same reason Step 4 rejected it for comments). Trade: if the target was deleted, fall back to a *confirmed* hint, not an auto-guess. |
| v2 build boundary | **Build the *inbound* receiver; simulate the downstream emitter** | Wiring real planning/execution emitters is out of scope (US6). Build the contract + conflict + notify; prove with `synthetic_child`. Trade: real emitters are a later goal. |

## Pitfalls to Avoid

1. **Building round-trip on `api_artifacts.save_artifact`'s `write_text` overwrite (code G4).** It is
   the *exact* silent-overwrite/drift bug US7 exists to kill — no diff, no version, no provenance, no
   conflict check. Any round-trip inheriting this path inherits the bug. Use the surgical-edit pattern
   (`update_manifest_status`) through the writeback *agent* instead.

2. **Putting the file write in cast-server.** This *contradicts a ratified spec* — the delegation
   contract states "cast-server… never writes [artifact files]." The writer must be an agent; the
   server only owns the proposal DB and observes the files. FR-013's "agent-as-source" is therefore
   not just future-facing — it is *architecturally mandatory* here.

3. **Treating "living source of truth" as automatic two-way sync.** The reflexive fix for doc drift is
   "automate the sync," but for a source-of-truth document silent auto-sync overwrites human intent
   untraceably. The right model is suggesting-mode / PR: propose, attribute, notify, gate.

4. **Reaching for a CRDT/merge engine.** CRDT/OT solve concurrent multi-cursor co-editing — explicitly
   out of scope (single-writer, async). Importing them here is a category error; three-way merge
   against `base_version_id` is the whole mechanism.

5. **The dual-write trap.** Committing the requirement change and the notification as *separate*
   writes admits a crash window that either loses the alert (drift returns) or fires a phantom. Write
   both in one transaction via the outbox, then relay.

6. **Scoping round-trip as a from-scratch subsystem.** It is a *composition* of Step 2 (surrogates +
   versions) and Step 4 (diff + same-door API + append-only trail). Anyone re-inventing diff,
   identity, or the comment API is double-paying for that work.

7. **Anchoring a write-back by text match or embedding instead of the stable surrogate.** Text anchors
   break on re-render; embeddings are non-deterministic and un-auditable. Without Step 2's surrogate
   there is no durable anchor — which is why Step 7 is *blocked* on Step 2 (code G2).

8. **Gate fatigue.** If *every* trivial agent addition demands sign-off, owners rubber-stamp (defeating
   the gate) or disable it (defeating the feature). Graduate trust by blast radius: auto-apply pure
   additions, gate modifications, always surface conflicts.

9. **Coarse element granularity.** Conflict precision = element granularity. If Step 2 lands
   element-level (not clause-level) surrogates, a downstream change to one clause conflicts the whole
   element. Reinforce Step 4's request for scenario/clause-level surrogates.

10. **A boolean, content-thin notification.** Today's `needs_attention` is just a flag. FR-019 demands
    *what changed + from where*. Extend the payload with a structured descriptor (element diff +
    provenance), not another bare boolean — this is a content gap, not an architecture gap.

## Success Metrics

- **End-to-end round-trip (SC-006):** a simulated downstream change appears in the requirements file
  *and* triggers a notification, with **0** requirement changes living only in a downstream artifact.
  Target: 1/1 traced changes land in both file + notification.
- **Provenance completeness:** **100%** of applied write-backs carry all three PROV nuclei
  (origin_activity_id, author/author_type, origin_artifact_path) and render a provenance badge in the
  change summary. A write-back missing any of the three fails validation.
- **Zero silent overwrites:** **0** modifications to human-authored elements applied without either a
  passed gate or a surfaced conflict. Measured by asserting every `applied` modification has a
  preceding `accepted` (or auto-apply-addition) event in `change_request_events`.
- **Conflict surfacing accuracy:** for a seeded set of N changes where K diverged from base, the
  predicate flags exactly K as `conflicted` (no false-clean, no false-conflict). Target: precision =
  recall = 1.0 on the seed set.
- **Notification reliability:** after an injected crash between change-commit and relay, **0** lost
  and **0** duplicate-surfaced notifications (outbox replays; UI dedupes on `change_request_id`).
- **Same-door parity (FR-013):** the agent write-back and a human "suggest edit" exercise the
  *identical* endpoint and code path; a test asserts no `author_type`-gated branch exists in the write
  path. Target: 0 privileged-path branches.
- **Carrier non-regression:** the additive `requirements_writeback` field breaks **0** existing
  output-json parents (`tests/test_b5_*`, `test_us14_*` stay green).

## Impact Rating: 9/10

**Justification:** This is the step that makes Diecast's requirements *canonical* rather than merely
*initial* — the third strategic thread ("living source of truth") and the payoff that ties Step 2's
store and Step 4's diff together (US7, FR-018→020, SC-006). It is rated 9 not 10 only because it is
*gated by Step 2's stable element identity* (no surrogate ⇒ every round-trip op degrades to fragile
text matching) and demonstrated against a *simulated* emitter in v2; the real downstream emitters are
a later goal. But the design risk is fully retired here: the mechanism is a thin, well-precedented
assembly (one entity + one PROV triple + one outbox + one conflict predicate over existing primitives),
the hard architectural tension (server-vs-agent file writes) is cleanly reconciled, and every
sub-problem already has a working analog in the codebase (`error_memory`, `update_manifest_status`,
`cast-update-spec`, the `output.json` carrier). Without this step, requirements are a pretty README
that is wrong by the second planning session.

---

### Hand-offs for planning & later steps
- **Hard dependency on Step 2** (stable element surrogate + immutable version) — the write target *and*
  the conflict unit. Step 7 cannot start its conflict/provenance work until surrogates exist.
- **Hard dependency on Step 4** (element-diff change summary + same-door API + append-only trail) —
  Step 7 reuses all three verbatim; coordinate the notification-surface decision with Step 4's open
  question #4 so comments and round-trip notifications share **one** surface (LDN inbox + HTMX badge).
- **Owner decisions to confirm at plan review:** (a) gate-everything-except-pure-additions for v2,
  policy as config not hardcode; (b) denormalized PROV columns now, PROV-O export deferred; (c) v2
  builds the inbound receiver + simulated emitter only (defer real downstream emitters); (d) "merge"
  on prose = surface-both + free edit field, no auto-textual-merge in v2.

### Sources
- W3C PROV-DM (Entity/Activity/Agent; wasGeneratedBy/wasAttributedTo/wasDerivedFrom): https://www.w3.org/TR/prov-dm/ · "URI-per-version suited for document provenance": https://www.w3.org/2012/10/prov-dm
- W3C Linked Data Notifications (Inbox; sender/receiver/consumer): https://www.w3.org/TR/ldn/
- Jama — Suspect Tracking (flag-on-upstream-change, human clears): https://www.jamasoftware.com/blog/2025/09/13/the-importance-of-suspect-tracking-in-requirements-management/ · Bidirectional Traceability (ISO 16404): https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/bidirectional-traceability/
- AWS — Transactional Outbox (atomic write + relay): https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html · AppSync conflict detection (`conflictDetection: VERSION`): https://docs.aws.amazon.com/appsync/latest/devguide/conflict-detection-and-resolution.html
- Event Sourcing — Azure Architecture Center (append-only audit; who/when/why metadata): https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
- Google Docs — Suggest edits / suggesting mode (propose, accept/reject): https://support.google.com/docs/answer/6033474
- ReadMe — AI Writer detecting doc drift (LLM proposes, human approves): https://readme.com/resources/ai-writer-detecting-doc-drift
- Martraire — Living Documentation (Reliable/Low-Effort principles): https://leanpub.com/livingdocumentation
- **Internal:** `error_memory_service.py` (provenance/`run_ids`, `pattern_hash` conflict, escalation), `orchestration_service.py:218-259` (`update_manifest_status` surgical edit), `agents/cast-update-spec` (diff→approve→version-bump protocol), `models/agent_output.py` + `docs/specs/cast-output-json-contract.collab.md` (additive carrier), `docs/specs/cast-delegation-contract.collab.md` (server-never-writes-files constraint).
