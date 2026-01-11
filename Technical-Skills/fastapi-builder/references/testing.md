# Testing FastAPI Applications

Test your APIs with pytest and FastAPI's TestClient.

## Installation

```bash
pip install pytest pytest-asyncio httpx
# or with uv
uv add --dev pytest pytest-asyncio httpx
```

## Basic Testing with TestClient

**tests/test_main.py:**

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item():
    response = client.post(
        "/items",
        json={"name": "Test Item", "price": 10.99}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 10.99
```

---

## Test Structure

Organize tests by feature:

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_main.py         # Main app tests
├── test_users.py        # User endpoint tests
├── test_items.py        # Item endpoint tests
└── test_auth.py         # Authentication tests
```

---

## Fixtures

Reuse setup code with pytest fixtures.

**tests/conftest.py:**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

**tests/test_users.py:**

```python
def test_create_user(client):
    response = client.post(
        "/users",
        json={"email": "test@example.com", "username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_get_user(client):
    # Create user first
    create_response = client.post(
        "/users",
        json={"email": "test@example.com", "username": "testuser", "password": "testpass"}
    )
    user_id = create_response.json()["id"]

    # Get user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

---

## Async Testing

Test async endpoints with pytest-asyncio.

**tests/test_async.py:**

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users")
        assert response.status_code == 200
```

**pytest.ini:**

```ini
[pytest]
asyncio_mode = auto
```

---

## Mocking Database Operations

Mock database calls for isolated tests.

```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_get_user_mock():
    mock_user = {"id": 1, "email": "test@example.com", "username": "testuser"}

    with patch('crud.get_user', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/users/1")
            assert response.status_code == 200
            assert response.json() == mock_user
```

---

## Testing Authentication

**tests/test_auth.py:**

```python
import pytest

@pytest.fixture
def test_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "testpass123"}
    )
    return response.json()

@pytest.fixture
def auth_token(client, test_user):
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    return response.json()["access_token"]

def test_protected_endpoint(client, auth_token):
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

def test_protected_endpoint_no_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401
```

---

## Parametrized Tests

Test multiple scenarios efficiently.

```python
import pytest

@pytest.mark.parametrize("email,username,password,expected_status", [
    ("valid@example.com", "validuser", "validpass123", 201),
    ("invalid-email", "validuser", "validpass123", 422),  # Invalid email
    ("valid@example.com", "ab", "validpass123", 422),     # Username too short
    ("valid@example.com", "validuser", "123", 422),       # Password too short
])
def test_user_creation_validation(client, email, username, password, expected_status):
    response = client.post(
        "/users",
        json={"email": email, "username": username, "password": password}
    )
    assert response.status_code == expected_status
```

---

## Coverage

Measure test coverage with pytest-cov.

```bash
# Install
pip install pytest-cov

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

**pytest.ini:**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term
```

---

## Test Database Patterns

### Pattern 1: Fresh Database Per Test

```python
@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
```

### Pattern 2: Transactions (Rollback After Test)

```python
@pytest.fixture(scope="function")
def test_db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### Pattern 3: Async Database

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()
```

---

## Best Practices

1. **Use separate test database** - Never run tests against production
2. **Isolate tests** - Each test should be independent
3. **Use fixtures** - Reuse setup code with pytest fixtures
4. **Test edge cases** - Not just happy paths
5. **Mock external services** - Don't call real APIs in tests
6. **Aim for high coverage** - Target 80%+ code coverage
7. **Keep tests fast** - Use in-memory databases (SQLite)
8. **Test authentication** - Verify protected routes work correctly
9. **Use parametrized tests** - Test multiple scenarios efficiently
10. **Clean up after tests** - Drop tables or rollback transactions

---

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_users.py

# Run specific test
pytest tests/test_users.py::test_create_user

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app

# Run in parallel (faster)
pip install pytest-xdist
pytest -n auto
```

## Learn More

- **Database Testing:** See `references/database.md` for database-specific testing patterns
- **Authentication Testing:** See `references/authentication.md` for auth test examples
