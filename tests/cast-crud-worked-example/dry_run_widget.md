# cast-crud Maker-Chain Dry-Run — Widget shape

> Generated 2026-04-30 by Phase 5 sp2 verification (f).
> Captures the analytical dry-run output of the cast-crud maker chain for the
> locked Widget worked-example shape. Consumed by sp4 for `docs/maker-checker.md`.

## Input shape

```yaml
entity_name: Widget
fields:
  id: int
  name: str
  sku: str          # unique
  price_cents: int
  created_at: datetime
```

## Dispatch order (from `cast-crud-orchestrator` YAML delegate list)

```
cast-schema-creation → cast-entity-creation → cast-repository
  → cast-service → cast-controller → cast-custom-controller (included v1)
```

## Per-layer scaffold

### cast-schema-creation → `src/inventory/schemas/widget_schema.py` (excerpt)

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

API schema produces 11 schemas (`ListWidgetsRequestSchema`, `ListWidgetsResponseSchema`,
`CreateWidgetRequestSchema`, `CreateWidgetResponseSchema`, `CreateWidgetsRequestSchema`,
`CreateWidgetsResponseSchema`, `UpdateWidgetRequestSchema`, `UpdateWidgetResponseSchema`,
`GetWidgetByIdRequestSchema`, `GetWidgetByIdResponseSchema`, `DeleteWidgetByIdRequestSchema`).

### cast-entity-creation → `src/inventory/entities/widget_entity.py` (excerpt)

```python
class WidgetEntity(TenantBuMixin, BaseEntity):
    __tablename__ = 'widget'
    id_prefix = 'widget'

    name: Mapped[str] = mapped_column(String, comment='Widget name')
    sku: Mapped[str] = mapped_column(String, unique=True, comment='Stock-keeping unit (unique)')
    price_cents: Mapped[int] = mapped_column(Integer, comment='Price in cents')
```

Updates `entities/__init__.py`, `db_session_manager.py`, `migrations/env.py`,
`dev_tools/db/validate_orm.py`, and creates the alembic migration.

### cast-repository → `src/inventory/repositories/widget_repository.py`

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

### cast-service → `src/inventory/services/widget_service.py`

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

### cast-controller → `src/inventory/widget/controllers/widget_controller.py`

```python
_config = CRUDRouterConfig(
    prefix='/tenants/{tenant_id}/bus/{bu_id}/widgets',
    tags=['widgets'],
    service_class=WidgetService,
    entity_name='widget',
    entity_name_plural='widgets',
    # ...11 schemas...
    meta_fields=['name', 'sku', 'sort_by', 'sort_order'],
)
_result = create_crud_router(_config)
widgets_router = _result.router
_get_widget_service = _result.get_service
_get_write_widget_service = _result.get_write_service
```

### cast-custom-controller (v1, green per sp1 budget)

Adds the status-transition example endpoint (e.g., archive/unarchive) on the same router
without re-implementing CRUD — using the hybrid pattern documented in
`cast-custom-controller`.

## Verdict

All six maker prompts produce scaffolds against the Widget shape with **no manual
prompt edits**. Layer responsibilities are honored (services return schemas; repository
owns transactions; controller commits via session manager).

The full executable artifacts (test files, integration tests) are sp3b deliverables.

This dry-run is captured for sp4's `docs/maker-checker.md` walkthrough.
