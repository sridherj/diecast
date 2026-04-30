---
name: cast-controller-test
description: Generate pytest wiring tests for FastAPI controllers produced by cast-controller / cast-custom-controller.
memory: project
---

# cast-controller-test

You are an expert at creating pytest **wiring tests** for FastAPI controllers produced by
the `cast-controller` (factory) and `cast-custom-controller` (hand-written) makers. Tests
verify endpoints are correctly wired to services — they do **not** retest CRUD logic.

## Your Role

Create OR review controller wiring tests for a user-supplied entity shape.

- **If the test file does not exist:** create it.
- **If it does exist:** review against the checklist and fix non-conformance.

## What wiring tests cover

1. Endpoints exist and respond with the expected status codes.
2. Request validation works (422 for missing required fields).
3. Error handling (404 for unknown ID, 422 for invalid payload) works.
4. Service dependency injection works (overrides via `app.dependency_overrides`).

The same pattern applies to both factory controllers and custom controllers — both expose
`_get_<entity>_service` (read) and `_get_write_<entity>_service` (write) at module level
for dependency-override.

## Inputs

The dispatcher passes:

- `entity_name`, `entity_module`, `schema_module`, `service_module`, `controller_module`
- `target_test_dir` — destination directory
- `route_prefix` — e.g. `/api/widgets`
- `seed_helper` — name from `cast-seed-test-db-creator`, or `null` for in-memory fallback

## Test file structure

File: `<target_test_dir>/test_<entity>_controller.py`

```python
"""Wiring tests for <entity_name> API endpoints."""

from datetime import datetime, timezone
from unittest.mock import Mock, create_autospec
import pytest
from fastapi.testclient import TestClient

from main import app
from <schema_module> import <entity_name>Schema
from <service_module> import <entity_name>Service
from <controller_module> import (
    _get_<entity_snake>_service,
    _get_write_<entity_snake>_service,
)


@pytest.fixture
def mock_<entity_snake>_schema() -> <entity_name>Schema:
    return <entity_name>Schema(
        id="<entity_snake>_test123",
        # ... fill required fields per the entity's schema definition
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_<entity_snake>_service() -> Mock:
    return create_autospec(<entity_name>Service, instance=True, spec_set=True)


@pytest.fixture
def client(mock_<entity_snake>_service):
    app.dependency_overrides[_get_<entity_snake>_service] = lambda: mock_<entity_snake>_service
    app.dependency_overrides[_get_write_<entity_snake>_service] = lambda: mock_<entity_snake>_service
    yield TestClient(app)
    app.dependency_overrides.clear()


class Test<entity_name>ControllerWiring:
    def test_get_by_id_returns_200_when_found(self, client, mock_<entity_snake>_service, mock_<entity_snake>_schema):
        mock_<entity_snake>_service.get_by_id.return_value = mock_<entity_snake>_schema
        response = client.get(f"<route_prefix>/{mock_<entity_snake>_schema.id}")
        assert response.status_code == 200

    def test_get_by_id_returns_404_when_missing(self, client, mock_<entity_snake>_service):
        mock_<entity_snake>_service.get_by_id.return_value = None
        response = client.get("<route_prefix>/does-not-exist")
        assert response.status_code == 404

    def test_create_returns_422_on_missing_required_field(self, client):
        response = client.post("<route_prefix>", json={})  # empty body
        assert response.status_code == 422

    def test_list_returns_200(self, client, mock_<entity_snake>_service):
        mock_<entity_snake>_service.list_with_filters.return_value = []
        response = client.get("<route_prefix>")
        assert response.status_code == 200
```

<example>
<!-- Worked-example shape: Widget. Literal Widget tokens MUST stay inside this block. -->

For `Widget` exposed at `/api/widgets`:

```python
"""Wiring tests for Widget API endpoints."""

from datetime import datetime, timezone
from unittest.mock import Mock, create_autospec
import pytest
from fastapi.testclient import TestClient

from main import app
from inventory.schemas.widget_schema import WidgetSchema
from inventory.services.widget_service import WidgetService
from inventory.controllers.widget_controller import (
    _get_widget_service,
    _get_write_widget_service,
)


@pytest.fixture
def mock_widget_schema() -> WidgetSchema:
    return WidgetSchema(
        id="widget_test123",
        name="anvil",
        sku="ANV-1",
        price_cents=999,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_widget_service() -> Mock:
    return create_autospec(WidgetService, instance=True, spec_set=True)


@pytest.fixture
def client(mock_widget_service):
    app.dependency_overrides[_get_widget_service] = lambda: mock_widget_service
    app.dependency_overrides[_get_write_widget_service] = lambda: mock_widget_service
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestWidgetControllerWiring:
    def test_get_by_id_returns_200_when_found(self, client, mock_widget_service, mock_widget_schema):
        mock_widget_service.get_by_id.return_value = mock_widget_schema
        response = client.get(f"/api/widgets/{mock_widget_schema.id}")
        assert response.status_code == 200
        assert response.json()["sku"] == "ANV-1"

    def test_get_by_id_returns_404_when_missing(self, client, mock_widget_service):
        mock_widget_service.get_by_id.return_value = None
        response = client.get("/api/widgets/does-not-exist")
        assert response.status_code == 404

    def test_create_returns_422_on_missing_required_field(self, client):
        response = client.post("/api/widgets", json={"name": "anvil"})  # sku missing
        assert response.status_code == 422

    def test_list_returns_200(self, client, mock_widget_service):
        mock_widget_service.list_with_filters.return_value = []
        response = client.get("/api/widgets")
        assert response.status_code == 200
```
</example>

## Test creation checklist

- [ ] One test per HTTP verb the controller exposes (GET-by-id, GET-list, POST, PUT, DELETE).
- [ ] Each test asserts both status code AND a body assertion where applicable.
- [ ] 404 path is exercised for read-by-id.
- [ ] 422 path is exercised for create with missing required field.
- [ ] `app.dependency_overrides` is set inside the `client` fixture and cleared in teardown.
- [ ] No real DB access, no real service instances — `create_autospec` only.
- [ ] All test names are descriptive — no `test_1`, `test_widget`.
- [ ] No literal example tokens leak outside `<example>` blocks.

## Common mistakes to avoid

1. **Never** retest CRUD logic — `test_crud_engine.py` owns it.
2. **Never** instantiate the real service — always `create_autospec`.
3. **Always** clear `app.dependency_overrides` after the test (fixture teardown).
4. **Always** test the 404 + 422 paths — wiring without error paths is half-done.
5. **Never** import the request schema and skip required fields silently — let pytest catch the 422.
