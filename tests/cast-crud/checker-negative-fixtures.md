# cast-crud-compliance-checker negative-test fixtures

These fixtures are deliberately broken maker-chain outputs. Each fixture should fire a distinct violation when `cast-crud-compliance-checker` runs against it. Used by Sub-phase 5.3a verification step (c) and re-used by sp4's manual end-to-end test.

The `widget` entity is the canonical worked-example shape (see `tests/cast-crud-worked-example/`). These fixtures use the same shape so the checker has a known-good entity to anchor against.

## Fixture 1: Service returning entity instead of schema

```python
# tests/cast-crud/fixtures/violation-service-returns-entity/widget_service.py
from .widget_repository import WidgetRepository
from .widget import Widget  # ENTITY — wrong return type for service layer


class WidgetService:
    def __init__(self, repo: WidgetRepository):
        self.repo = repo

    def get_widget(self, id: int) -> Widget:  # WRONG — should return WidgetSchema
        return self.repo.get(id)
```

**Expected checker output:** flag `widget_service.py:9` with rule `mvcs.service.return_type_must_be_schema`.

**Why this is a violation:** The service layer is the boundary between the entity world (repository-internal) and the schema world (controller-facing). Leaking a raw entity past the service layer means callers can mutate ORM-managed state directly and bypass the schema's validation rules.

## Fixture 2: Repository missing transaction context

```python
# tests/cast-crud/fixtures/violation-repo-no-transaction/widget_repository.py
from .widget import Widget


class WidgetRepository:
    def __init__(self, db):
        self.db = db

    def update(self, id: int, name: str) -> Widget:
        # WRONG — no `with self.db.transaction():` wrapper around the write.
        row = self.db.execute("UPDATE widgets SET name=? WHERE id=?", [name, id])
        return Widget.from_row(row)
```

**Expected checker output:** flag `widget_repository.py:10` with rule `mvcs.repository.write_methods_require_transaction`.

**Why this is a violation:** The repository must run write operations inside a transaction so that the service layer can compose multiple writes into one atomic unit. A raw `db.execute(...)` without a transaction breaks that contract — partial writes can land if a later operation in the same service method fails.

## Fixture 3: Controller bypassing service

```python
# tests/cast-crud/fixtures/violation-controller-bypass-service/widget_controller.py
from .widget_repository import WidgetRepository  # WRONG — controller should depend on WidgetService


class WidgetController:
    def __init__(self, repo: WidgetRepository):  # WRONG — controllers depend on services, not repositories
        self.repo = repo

    def get(self, id: int):
        return self.repo.get(id)  # WRONG — bypassing the service layer
```

**Expected checker output:** flag `widget_controller.py:5` with rule `mvcs.controller.must_depend_on_service`.

**Why this is a violation:** The controller's only collaborator should be a service. When a controller reaches into the repository directly, business-logic rules that live in the service layer (validation, cross-entity orchestration, schema conversion) are silently skipped.

## How to run these fixtures against the checker

```bash
cd /data/workspace/diecast
for fixture in tests/cast-crud/fixtures/violation-*/; do
  # Invoke /cast-crud-compliance-checker pointed at "$fixture"
  # Expect: at least one violation flagged with file:line reference
  # matching the "Expected checker output" stanza above.
  echo "Running checker against $fixture"
done
```

## How to extend

Add a new fixture file under `tests/cast-crud/fixtures/violation-<short-slug>/` with:

1. The deliberately broken maker-chain output (one or more `.py` files, or a missing-file scenario).
2. An "Expected checker output" stanza in this document with the exact rule name and `file:line` the checker should flag.
3. A "Why this is a violation" paragraph so a reviewer can understand the rule without reading the checker prompt.

Keep fixtures minimal — one violation per fixture, no incidental noise.
