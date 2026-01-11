---
name: tdd-pytest
description: Test Driven Development with pytest. Use when writing tests, implementing TDD workflow (Red-Green-Refactor), or adding test coverage. Supports pytest fixtures, parametrize, TestClient for FastAPI, mocking, async tests, coverage reporting, and test organization patterns.
---

# TDD with pytest

Test-driven development workflow using pytest: write failing tests first, implement minimal code, then refactor.

## Quick Start

### Run Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest test_main.py

# Run with coverage
pytest --cov=app --cov-report=html
```

## TDD Workflow

### 1. Red - Write Failing Test
Write the test first, describing the desired behavior:

```python
# test_calculator.py
def test_add_two_numbers():
    result = add(2, 3)
    assert result == 5
```

Run and confirm it fails:
```bash
pytest test_calculator.py  # Should fail - function doesn't exist
```

### 2. Green - Make Test Pass
Implement minimal code to pass the test:

```python
# calculator.py
def add(a, b):
    return a + b
```

Run and confirm it passes:
```bash
pytest test_calculator.py  # Should pass
```

### 3. Refactor - Improve Code
Clean up the code while keeping tests green:

```python
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

Run tests again to ensure refactoring didn't break anything.

## Core Patterns

### Pytest Fixtures

Use `@pytest.fixture` for reusable test setup:

```python
import pytest

@pytest.fixture
def sample_data():
    return {"name": "Test", "value": 42}

def test_with_fixture(sample_data):
    assert sample_data["value"] == 42
```

**Fixture with cleanup:**
```python
@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.close()  # Cleanup after test
```

### Parametrize

Run the same test with multiple inputs:

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

### FastAPI TestClient

Test FastAPI endpoints without starting a server:

```python
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
```

### Async Tests

Use `pytest-asyncio` for async endpoints:

```python
import pytest

@pytest.mark.asyncio
async def test_async_endpoint():
    result = await async_function()
    assert result is not None
```

Install: `pip install pytest-asyncio`

Configure in `pyproject.toml` or `pytest.ini`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Mocking and Patching

Replace dependencies with test doubles:

```python
from unittest.mock import patch, MagicMock

def test_with_mock():
    mock_db = MagicMock()
    mock_db.query.return_value = [{"id": 1}]

    with patch("app.database.get_db", return_value=mock_db):
        result = get_items()
        assert len(result) == 1
```

## Test Organization

### Directory Structure
```
project/
├── app/
│   └── main.py
└── tests/
    ├── conftest.py      # Shared fixtures
    ├── test_main.py
    └── test_auth.py
```

### conftest.py
Place shared fixtures in `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user():
    return {"id": 1, "name": "Test User"}
```

## Coverage Reporting

### Install pytest-cov
```bash
pip install pytest-cov
```

### Generate Coverage Report
```bash
# Terminal report
pytest --cov=app

# HTML report (opens in browser)
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Coverage Configuration
In `pyproject.toml`:
```toml
[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*"]

[tool.coverage.report]
fail_under = 80
```

## Best Practices

1. **Test one thing per test** - Each test should verify a single behavior
2. **Use descriptive names** - `test_login_with_invalid_credentials_returns_401`
3. **Arrange-Act-Assert** - Structure tests clearly:
   ```python
   def test_purchase():
       # Arrange
       cart = Cart()
       item = Item("Widget", price=10)

       # Act
       cart.add(item)

       # Assert
       assert cart.total() == 10
   ```
4. **Avoid testing implementation** - Test behavior, not internals
5. **Mock external dependencies** - Database, APIs, file system
6. **Keep tests fast** - Slow tests discourage running them frequently

## Common Patterns

### Testing API Endpoints
```python
def test_create_item(client):
    response = client.post("/items", json={"name": "Widget"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Widget"
    assert "id" in data
```

### Testing Error Cases
```python
def test_get_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### Testing with Authentication
```python
def test_protected_endpoint(client):
    response = client.get("/admin")
    assert response.status_code == 401

    # With valid token
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/admin", headers=headers)
    assert response.status_code == 200
```

## Reference Files

For advanced patterns and detailed guides:

- **FastAPI Testing**: See `references/fastapi-testing.md` for TestClient patterns, dependency overrides, and async test setup
- **Mocking Patterns**: See `references/mocking.md` for patching, fixtures, and test doubles
- **Coverage**: See `references/coverage.md` for configuration and reporting options
- **Test Organization**: See `references/organization.md` for structuring large test suites
