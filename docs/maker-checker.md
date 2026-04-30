# cast-crud — Maker-Checker Walkthrough

> Diecast's reference family for scaffolding a CRUD subsystem from a single
> entity definition. This walkthrough builds a complete `Widget` table
> end-to-end using only the cast-crud agents — no manual prompt edits, no
> bespoke glue code.

## What you'll build

A full CRUD subsystem for a `Widget` entity:

```yaml
entity_name: Widget
fields:
  id: int
  name: str
  sku: str          # unique
  price_cents: int
  created_at: datetime
```

…delivered as schema → entity → repository → service → controller, with
tests (repository, service, controller, integration) and seeded test/dev
data. Total wall-clock: ~5 minutes; total Claude API cost: see
§ "Cost & Cadence" below.

## Prerequisites

- Diecast installed (`pip install diecast` or repo-local invocation).
- A goal directory with empty `agents/`, `tests/`, `db/` subdirs.
- The Widget DDL anchor file at `references/` (shipped with diecast).

## Step 1 — Dispatch the orchestrator

```bash
/cast-crud-orchestrator
```

You'll be asked for the entity shape. Provide:

```yaml
entity_name: Widget
fields:
  id: int
  name: str
  sku: str
  price_cents: int
  created_at: datetime
```

The orchestrator's data-driven delegate list (top of
`agents/cast-crud-orchestrator/cast-crud-orchestrator.md`) drives the
dispatch order:

```yaml
delegates:
  - cast-schema-creation
  - cast-entity-creation
  - cast-repository
  - cast-service
  - cast-controller
  - cast-custom-controller   # included in v1 (green per coupling-spike)
```

Real dispatch log (from `tests/cast-crud-worked-example/dry_run_widget.md`):

```
cast-schema-creation → cast-entity-creation → cast-repository
  → cast-service → cast-controller → cast-custom-controller (included v1)
```

## Step 2 — Schema creation

`cast-schema-creation` runs first. It produces the per-entity Pydantic
schema plus 11 API request/response schemas.

Real output — `src/inventory/schemas/widget_schema.py` (excerpt, captured
verbatim from the sp2 dry-run):

```python
class WidgetSchema(BaseModel):
    # Identifiers
    id: Annotated[int, Field(description='Unique widget identifier')]
    tenant_id: Annotated[str, Field(description='Tenant ID')]
    bu_id: Annotated[str, Field(description='Business unit ID')]

    # Basic Information
    name: Annotated[str, Field(description='Widget name')]
    sku: Annotated[str, Field(description='Stock-keeping unit (unique)')]

    # Pricing
    price_cents: Annotated[int, Field(description='Price in cents')]

    # System Timestamps
    created_at: Annotated[datetime, Field(description='Creation timestamp')]

    model_config = ConfigDict(from_attributes=True)
```

The 11 generated API schemas are: `ListWidgetsRequestSchema`,
`ListWidgetsResponseSchema`, `CreateWidgetRequestSchema`,
`CreateWidgetResponseSchema`, `CreateWidgetsRequestSchema`,
`CreateWidgetsResponseSchema`, `UpdateWidgetRequestSchema`,
`UpdateWidgetResponseSchema`, `GetWidgetByIdRequestSchema`,
`GetWidgetByIdResponseSchema`, `DeleteWidgetByIdRequestSchema`.

## Step 3 — Entity creation

`cast-entity-creation` runs next, producing the SQLAlchemy ORM mapping.

Real output — `src/inventory/entities/widget_entity.py` (excerpt):

```python
class WidgetEntity(TenantBuMixin, BaseEntity):
    __tablename__ = 'widget'
    id_prefix = 'widget'

    name: Mapped[str] = mapped_column(String, comment='Widget name')
    sku: Mapped[str] = mapped_column(String, unique=True, comment='Stock-keeping unit (unique)')
    price_cents: Mapped[int] = mapped_column(Integer, comment='Price in cents')
```

It also patches `entities/__init__.py`, `db_session_manager.py`,
`migrations/env.py`, `dev_tools/db/validate_orm.py`, and creates an
alembic migration for the new table.

## Step 4 — Repository

`cast-repository` produces the data-access layer. Filter specs are
inferred from the schema's `unique` constraints and free-text fields.

Real output — `src/inventory/repositories/widget_repository.py`:

```python
class WidgetRepository(BaseRepository[WidgetEntity, WidgetSortByFields]):
    _entity_class = WidgetEntity
    _default_sort_field = 'created_at'
    _entity_name = 'widget'

    def _get_filter_specs(self) -> List[FilterSpec]:
        return [
            FilterSpec('sku', 'eq'),
            FilterSpec('search', 'ilike', entity_field='name'),
        ]
```

The repository owns transactions; write methods run inside a
`with self.db.transaction():` block so the service layer can compose
multiple writes into one atomic unit. (See
`tests/cast-crud/checker-negative-fixtures.md` Fixture 2 for the
violation this rule guards against.)

## Step 5 — Service

`cast-service` produces the business-logic layer. The service returns
**schemas, not entities** — leaking entities past the service boundary
is the #1 MVCS violation the checker catches.

Real output — `src/inventory/services/widget_service.py`:

```python
class WidgetService(BaseService[WidgetEntity, WidgetSchema, WidgetRepository]):
    _repository_class = WidgetRepository
    _schema_class = WidgetSchema
    _entity_class = WidgetEntity
    _entity_name = 'widget'
    _entity_id_field = 'widget_id'

    def _extract_filter_kwargs(self, list_request): ...
    def _create_entity_from_request(self, create_request): ...
    def _update_entity_from_request(self, entity, update_request): ...
```

## Step 6 — Controller

`cast-controller` wires the HTTP layer onto the service. The router is
configured declaratively — `create_crud_router` builds all five CRUD
endpoints from the config block.

Real output — `src/inventory/widget/controllers/widget_controller.py`:

```python
_config = CRUDRouterConfig(
    prefix='/tenants/{tenant_id}/bus/{bu_id}/widgets',
    tags=['widgets'],
    service_class=WidgetService,
    entity_name='widget',
    entity_name_plural='widgets',
    # ...11 schemas wired in here...
    meta_fields=['name', 'sku', 'sort_by', 'sort_order'],
)
_result = create_crud_router(_config)
widgets_router = _result.router
_get_widget_service = _result.get_service
_get_write_widget_service = _result.get_write_service
```

`cast-custom-controller` then runs (included in v1 per the green spike
score) and adds an example status-transition endpoint (e.g.,
archive/unarchive) on the same router using the hybrid pattern — without
re-implementing CRUD.

## Step 7 — Run the checker

```bash
/cast-crud-compliance-checker
```

The checker walks the generated maker output and reports MVCS
violations. On a clean Widget run, expected output:

```
cast-crud-compliance-checker: PASS
- src/inventory/services/widget_service.py — services return schemas (not entities) ✓
- src/inventory/repositories/widget_repository.py — repository owns transactions ✓
- src/inventory/widget/controllers/widget_controller.py — controller depends on service (not repository) ✓
0 violations.
```

To convince yourself the checker actually catches violations, point it
at the negative fixtures in `tests/cast-crud/checker-negative-fixtures.md`
— each fixture deliberately breaks one MVCS rule and the checker should
flag it with `file:line` and a rule name (e.g.
`mvcs.service.return_type_must_be_schema`).

## Step 8 — Generate tests

```bash
/cast-integration-test-orchestrator
```

This orchestrator dispatches `cast-repository-test`, `cast-service-test`,
`cast-controller-test`, and `cast-integration-test-creator` for the
Widget shape. Real generated test files land under
`tests/cast-crud-worked-example/` and follow `cast-pytest-best-practices`.

```bash
pytest tests/cast-crud-worked-example/
```

Expected: green. The repository tests use a transactional in-memory
fixture; the service tests use a mocked repository; the controller
tests use a mocked service; the integration test exercises DB →
repository → service → controller → HTTP end-to-end.

## Step 9 — Seed the database

```bash
/cast-seed-db-creator        # development data (3 Widget rows)
/cast-seed-test-db-creator   # test fixtures parameterized on the entity shape
```

Both seed agents are **idempotent** — re-running them does not insert
duplicates. The idempotency check is part of the cast-crud-compliance
contract (sp3c verification (b)). Re-run them and confirm row counts
stay at 3 / N — duplicates here mean a non-idempotent seed slipped past
the contract.

```bash
/cast-seed-db-creator        # second run — must be no-op
```

Expected output:

```
cast-seed-db-creator: 0 rows inserted (idempotent re-run; 3 widgets already present).
```

## Generality check — different entity, same chain

The maker chain is entity-agnostic. To prove this, the same chain runs
clean against `Note { id, title, body }` with no prompt edits — captured
in `tests/cast-crud-note-fixture/dry_run_note.md`. The Note dispatch
omits `cast-custom-controller` (no status transitions on a Note) via a
one-line skip in the orchestrator's delegate iteration — no prompt
branch needed.

This generality test ran clean before sp3b began (per Phase 5 sp2
verification (g)). If you fork this walkthrough for your own entity and
the chain breaks, that's a regression — file an issue against the maker
agent that produced bad output.

## What to do next

- **New project?** Run `/cast-init` to scaffold the goal directory, then
  come back to Step 1.
- **Different entity?** Substitute your shape in Step 1; the chain is
  parameterized — no maker/checker/seed prompt edits needed. (Verified
  in Phase 5 sp2 against `Note { id, title, body }` and re-exercised in
  sp3b's generality regression test.)
- **Custom non-CRUD endpoints?** See `cast-custom-controller`. The
  hybrid pattern lets you co-locate non-CRUD routes on the same router
  without re-implementing the CRUD basics.

## Cost & Cadence

- **Token usage per full chain (v1, captured during sp2/sp3 dry-runs):**
  ~85k input + ~22k output tokens across the 6 maker dispatches + the
  checker + the test orchestrator + the two seed agents. Source:
  `.agent-run_*.output.json` files emitted during sp2/sp3b/sp3c. The
  exact total varies ±15% by entity field count; capture your own
  number on the first run for your project's baseline.
- **Wall-clock:** ~5 minutes end-to-end (Widget shape, 5 fields).
- **Total estimated_sessions for the Phase 5 fleet rewrite:** 5.75
  sessions (per `docs/audit/cast-crud-rewrite-budget.ai.md`). One agent
  scored red (`cast-integration-test-orchestrator` at 1.5 sessions);
  the other 14 are green or yellow.
- **Regeneration policy:** this document is regenerated against the
  cast-crud agent fleet on **every tagged release**. Maintainers: run
  the regeneration on the release branch before tagging. See
  `docs/release-checklist.md` for the runnable checklist.

## Forward references

- For how cast-crud fits into the larger Diecast picture: see
  [`docs/how-it-fits.md`](how-it-fits.md) (authored in Phase 6.2).
- For the parent-child delegation pattern that
  `cast-crud-orchestrator` uses to dispatch its delegate list: see
  [`docs/delegation-pattern.md`](delegation-pattern.md) (authored in
  Phase 6.2).

> Note: the two forward-reference targets are Phase 6.2 deliverables.
> The links are authored here in Phase 5 sp4 to close the docs cross-link
> loop without creating a Phase 5 ↔ Phase 6 race; the targets land
> before v1 ships.

---

**Last regenerated:** 2026-04-30 (Phase 5 v1 release).
**Maintainers:** regenerate before every tag; record completion in
`docs/release-checklist.md`. The walkthrough plus a manual end-to-end
test before tag is the **US15 coherent-unit acceptance gate** — there
is no CI invariant (`bin/smoke-cast-crud` was dropped 2026-04-30 per
Q#25 + Q#28).
