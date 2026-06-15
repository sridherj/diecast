## Phase 5: Living Source of Truth — Round-Trip Write-Back
**Outcome:** A downstream phase's requirement-affecting change lands **back in the requirements file**
with provenance (which phase/agent, derived from what), the user is notified (what changed + from
where), the change appears in the version change summary, and a change that conflicts with current
content is **surfaced, never silently overwritten**. v2 builds the *receiving* mechanism and proves it
with a *simulated* downstream emitter (real planner/executor emitters are a later goal).
**Dependencies:** Phase 1 (block anchors + write target) + Phase 4 (change-summary diff, versioning,
same-door API, append-only trail — all reused verbatim).
**Estimated effort:** 3-4 sessions
**Verification:** **SC-006** — a simulated downstream change (via `tests/fixtures/synthetic_child.py`)
traces end-to-end: `change_request` row → conflict verdict → surgical file apply → version bump →
change summary with provenance badge → outbox row → notification surfaced. Assert **0** modifications
to existing content applied without a passed gate or surfaced conflict; **0** lost/duplicate
notifications after an injected crash between commit and relay.

Key activities:
- **Model write-back as "propose + notify + gate," never auto-sync.** Land a first-class
  `change_request{origin, base}` entity + append-only `change_request_events` + `notifications_outbox`
  (house migration pattern). The two load-bearing fields a naive design forgets: `origin_*` (powers
  notify + audit, the W3C-PROV Activity/Agent/Entity triple as denormalized columns) and
  `base_version_id` (powers conflict detection).
- **One same-door endpoint** `POST /api/specs/{slug}/change-requests`: a human "suggest edit" and an
  agent write-back are the *identical* POST; `author_type` is data, not a code branch (FR-013).
- **Extend the `output.json` contract additively** with a `requirements_writeback` artifact type
  (parents ignore unknown fields — breaks no existing parent; reuses the test-covered carrier).
- **Conflict detection = three-way predicate against `base_version_id`** using the retained
  deterministic spine: the downstream change carries the version it read; compare the target region's
  content vs its content at that base version via content hash; diverged ⇒ `conflicted` ⇒ surface
  (accept-incoming / keep-current / merge-with-free-edit). This is the one place the hash spine earns
  its keep — a missed conflict is silent overwrite (US7 S4). **No CRDT/OT** (co-editing is out of scope).
- **Build the `cast-requirements-writeback` agent as the SOLE file writer** (the delegation contract
  forbids cast-server writing artifact files — server owns the proposal DB, an agent owns the file
  apply). The agent locates the target region by quote (same subagent skill as comment re-anchoring) and
  applies a surgical addition/annotation leaving the rest of the file byte-identical; lift
  `orchestration_service.update_manifest_status()` as the surgical-edit template. **Do not** build on
  `api_artifacts.save_artifact`'s whole-file overwrite — that is the silent-drift bug US7 exists to kill.
- **Graduated-trust gate by blast radius** (resolved at plan review): pure additions auto-apply + FYI;
  modifications to existing content gate via `AskUserQuestion`; conflicts always surface. Policy lives in
  config so it can be loosened later without a code change.
- **Notification via transactional outbox** (change + alert commit in one txn) → polling relay → the
  **unified notification surface shared with Phase 4** (resolved at plan review): one HTMX
  `needs_attention` badge carrying a **structured** payload (today it's a bare boolean) + an optional
  W3C-LDN-aligned `/inbox` JSON endpoint so agents consume the same notification humans see. Comment
  notifications and round-trip notifications use this one surface, not two.

