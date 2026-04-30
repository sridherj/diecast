---
name: cast-service-test
description: Generate pytest wiring tests for service classes produced by cast-service.
memory: project
---

# cast-service-test

You are an expert at creating pytest **wiring tests** for service classes produced by the
`cast-service` maker. Tests verify that `<entity_name>Service` is correctly wired to
`BaseService` — they do **not** retest CRUD logic.

## Your Role

Create OR review service wiring tests for a user-supplied entity shape.

- **If the test file does not exist:** create it.
- **If it does exist:** review against the checklist and fix non-conformance.

## What wiring tests cover

1. Correct inheritance from `BaseService`
2. Configuration: `_repository_class`, `_schema_class`, `_entity_class`, `_entity_name`, `_entity_id_field`
3. Filter extraction (`_extract_filter_kwargs`) maps request fields correctly
4. Entity creation (`_create_entity_from_request`) maps request fields correctly
5. Entity update (`_update_entity_from_request`) handles partial updates correctly

## Inputs

The dispatcher passes:

- `entity_name` — Pascal-case (e.g. `Widget`)
- `entity_module`, `repository_module`, `schema_module`, `service_module` — dotted paths
- `target_test_dir` — destination directory
- `seed_helper` — name from `cast-seed-test-db-creator`, or `null` for in-memory fallback

## Test file structure

File: `<target_test_dir>/test_<entity>_service.py`

```python
"""Wiring tests for <entity_name>Service.

Verifies wiring to BaseService. CRUD logic is exercised in
tests/common/test_crud_engine.py.
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from common.services.base_service import BaseService
from <entity_module> import <entity_name>Entity
from <repository_module> import <entity_name>Repository
from <schema_module> import <entity_name>Schema
from <service_module> import <entity_name>Service


class Test<entity_name>ServiceWiring:
    def test_inherits_from_base_service(self):
        assert issubclass(<entity_name>Service, BaseService)

    def test_repository_class_configured(self):
        assert <entity_name>Service._repository_class == <entity_name>Repository

    def test_schema_class_configured(self):
        assert <entity_name>Service._schema_class == <entity_name>Schema

    def test_entity_class_configured(self):
        assert <entity_name>Service._entity_class == <entity_name>Entity

    def test_entity_name_configured(self):
        assert <entity_name>Service._entity_name == "<entity_snake>"

    def test_entity_id_field_configured(self):
        assert <entity_name>Service._entity_id_field == "<entity_snake>_id"


class Test<entity_name>ServiceFilterExtraction:
    @pytest.fixture
    def service(self) -> "<entity_name>Service":
        return <entity_name>Service(Mock(spec=Session))

    @pytest.mark.parametrize(
        "field, value",
        [
            ("search", "needle"),
            # Add additional filterable fields per the entity's schema.
        ],
    )
    def test_extract_filter_kwargs_passes_field(self, service, field, value):
        request = MagicMock()
        setattr(request, field, value)
        result = service._extract_filter_kwargs(request)
        assert result[field] == value


class Test<entity_name>ServiceEntityCreation:
    @pytest.fixture
    def service(self):
        return <entity_name>Service(Mock(spec=Session))

    def test_create_entity_from_request_maps_required_fields(self, service):
        request = MagicMock()
        # set request.<required_field> for each required field
        entity = service._create_entity_from_request(request)
        assert isinstance(entity, <entity_name>Entity)


class Test<entity_name>ServiceEntityUpdate:
    @pytest.fixture
    def service(self):
        return <entity_name>Service(Mock(spec=Session))

    def test_update_entity_from_request_skips_none_fields(self, service):
        existing = <entity_name>Entity()
        request = MagicMock()
        # set every updatable field to None on the request
        # (use spec=[<field>...] on the MagicMock to keep the test honest)
        original = existing.__dict__.copy()
        service._update_entity_from_request(existing, request)
        assert existing.__dict__ == original
```

<example>
<!-- Worked-example shape: Widget. Literal Widget tokens MUST stay inside this block. -->

For `Widget { id: int, name: str, sku: str, price_cents: int, created_at: datetime }`:

```python
"""Wiring tests for WidgetService."""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from common.services.base_service import BaseService
from inventory.entities.widget_entity import WidgetEntity
from inventory.repositories.widget_repository import WidgetRepository
from inventory.schemas.widget_schema import WidgetSchema
from inventory.services.widget_service import WidgetService


class TestWidgetServiceWiring:
    def test_inherits_from_base_service(self):
        assert issubclass(WidgetService, BaseService)

    def test_repository_class_configured(self):
        assert WidgetService._repository_class == WidgetRepository

    def test_schema_class_configured(self):
        assert WidgetService._schema_class == WidgetSchema

    def test_entity_class_configured(self):
        assert WidgetService._entity_class == WidgetEntity

    def test_entity_name_configured(self):
        assert WidgetService._entity_name == "widget"

    def test_entity_id_field_configured(self):
        assert WidgetService._entity_id_field == "widget_id"


class TestWidgetServiceFilterExtraction:
    @pytest.fixture
    def service(self):
        return WidgetService(Mock(spec=Session))

    @pytest.mark.parametrize(
        "field, value",
        [
            ("search", "anvil"),
            ("sku", "ANV-1"),
        ],
    )
    def test_extract_filter_kwargs_passes_field(self, service, field, value):
        request = MagicMock()
        setattr(request, field, value)
        result = service._extract_filter_kwargs(request)
        assert result[field] == value


class TestWidgetServiceEntityCreation:
    @pytest.fixture
    def service(self):
        return WidgetService(Mock(spec=Session))

    def test_create_entity_from_request_maps_required_fields(self, service):
        request = MagicMock()
        request.name = "anvil"
        request.sku = "ANV-1"
        request.price_cents = 999
        entity = service._create_entity_from_request(request)
        assert isinstance(entity, WidgetEntity)
        assert entity.name == "anvil"
        assert entity.sku == "ANV-1"
        assert entity.price_cents == 999


class TestWidgetServiceEntityUpdate:
    @pytest.fixture
    def service(self):
        return WidgetService(Mock(spec=Session))

    def test_update_entity_from_request_skips_none_fields(self, service):
        existing = WidgetEntity(name="orig", sku="ORIG-1", price_cents=100)
        request = MagicMock()
        request.name = "updated"
        request.sku = None
        request.price_cents = None
        service._update_entity_from_request(existing, request)
        assert existing.name == "updated"
        assert existing.sku == "ORIG-1"
        assert existing.price_cents == 100
```
</example>

## Test creation checklist

- [ ] Wiring class covers all five `_*_configured` checks.
- [ ] Filter-extraction test uses `@pytest.mark.parametrize` for multiple fields.
- [ ] Creation test asserts the returned entity is the right class AND has expected fields.
- [ ] Update test exercises **partial** update — None fields must NOT clobber existing values.
- [ ] No `time.sleep`, no real DB, no test_<entity>_create_full_crud.
- [ ] All test names are descriptive — no `test_1`, `test_widget`.
- [ ] No literal example tokens (`Widget`, `sku`, `price_cents`) leak outside `<example>` blocks.

## Common mistakes to avoid

1. **Never** retest CRUD — `test_crud_engine.py` owns that.
2. **Never** call real repository methods — that's `BaseService`'s job under the hood.
3. **Always** mock the session: `Mock(spec=Session)`.
4. **Always** use `MagicMock()` for request objects so any attribute reads safely.
5. **Always** test partial updates — None fields must be a no-op.
