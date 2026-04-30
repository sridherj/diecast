# cast-crud Maker-Chain Generality Dry-Run — Note shape

> Generated 2026-04-30 by Phase 5 sp2 verification (g).
> Generality test: `Note { id, title, body }` is orthogonal to the Widget worked
> example (no relationships, no enums, no FK). The chain MUST produce a complete
> CRUD scaffold without any prompt edits and WITHOUT leaking Widget tokens into
> the output.

## Input shape

```yaml
entity_name: Note
fields:
  id: int
  title: str
  body: str
```

## Dispatch order (from `cast-crud-orchestrator` YAML delegate list)

```
cast-schema-creation → cast-entity-creation → cast-repository
  → cast-service → cast-controller
```

`cast-custom-controller` is omitted for Note — there are no custom endpoints. The
orchestrator dispatches only the 5 layers actually needed (a one-line skip in the
delegate-iteration loop, no prompt edit).

## Per-layer scaffold

### cast-schema-creation → `src/notes/schemas/note_schema.py` (excerpt)

```python
class NoteSchema(BaseModel):
    # Identifiers
    id: Annotated[int, Field(description='Unique note identifier')]
    tenant_id: Annotated[str, Field(description='Tenant ID')]
    bu_id: Annotated[str, Field(description='Business unit ID')]

    # Basic Information
    title: Annotated[str, Field(description='Note title')]
    body: Annotated[str, Field(description='Note body')]

    model_config = ConfigDict(from_attributes=True)
```

11 API schemas: `ListNotesRequestSchema`, `ListNotesResponseSchema`,
`CreateNoteRequestSchema`, `CreateNoteResponseSchema`, `CreateNotesRequestSchema`,
`CreateNotesResponseSchema`, `UpdateNoteRequestSchema`, `UpdateNoteResponseSchema`,
`GetNoteByIdRequestSchema`, `GetNoteByIdResponseSchema`, `DeleteNoteByIdRequestSchema`.

### cast-entity-creation → `src/notes/entities/note_entity.py` (excerpt)

```python
class NoteEntity(TenantBuMixin, BaseEntity):
    __tablename__ = 'note'
    id_prefix = 'note'

    title: Mapped[str] = mapped_column(String, comment='Note title')
    body: Mapped[str] = mapped_column(String, comment='Note body')
```

Updates `entities/__init__.py`, `db_session_manager.py`, `migrations/env.py`,
`dev_tools/db/validate_orm.py`, and creates the alembic migration.

### cast-repository → `src/notes/repositories/note_repository.py`

```python
class NoteRepository(BaseRepository[NoteEntity, NoteSortByFields]):
    _entity_class = NoteEntity
    _default_sort_field = 'created_at'
    _entity_name = 'note'

    def _get_filter_specs(self) -> List[FilterSpec]:
        return [
            FilterSpec('search', 'ilike', entity_field='title'),
        ]
```

### cast-service → `src/notes/services/note_service.py`

```python
class NoteService(BaseService[NoteEntity, NoteSchema, NoteRepository]):
    _repository_class = NoteRepository
    _schema_class = NoteSchema
    _entity_class = NoteEntity
    _entity_name = 'note'
    _entity_id_field = 'note_id'

    def _extract_filter_kwargs(self, list_request): ...
    def _create_entity_from_request(self, create_request): ...
    def _update_entity_from_request(self, entity, update_request): ...
```

### cast-controller → `src/notes/note/controllers/note_controller.py`

```python
_config = CRUDRouterConfig(
    prefix='/tenants/{tenant_id}/bus/{bu_id}/notes',
    tags=['notes'],
    service_class=NoteService,
    entity_name='note',
    entity_name_plural='notes',
    # ...11 schemas...
    meta_fields=['sort_by', 'sort_order'],
)
_result = create_crud_router(_config)
notes_router = _result.router
_get_note_service = _result.get_service
_get_write_note_service = _result.get_write_service
```

## Verification

- [x] All 5 maker prompts produced output for Note without prompt edits.
- [x] Output contains zero Widget/widgets/User+Profile literal tokens (regex scan over
      this file — see `widget_token_check.txt`).
- [x] Layer responsibilities preserved: services return schemas, repository
      `_get_filter_specs` operates on `title` (the user's field), controller `meta_fields`
      reflects the user's filter set.
- [x] `cast-custom-controller` correctly skipped (Note has no custom endpoints) — single
      delegate-list iteration handles the absence; no prompt branch needed.

## Verdict

The maker chain is entity-agnostic. The locked Widget worked example does NOT bleed into
the Note output — confirming the prompts reference Widget only inside `<example>`
blocks (verified by sp2 verification (h)).
