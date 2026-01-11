# Test Organization

Complete guide for structuring and organizing large test suites.

## Directory Structure

### Basic Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── services/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── test_main.py
│   ├── test_models.py
│   └── test_services/
│       ├── __init__.py
│       ├── conftest.py      # Service-specific fixtures
│       └── test_user_service.py
└── pyproject.toml
```

### Organized by Feature

```
project/
├── app/
│   ├── features/
│   │   ├── auth/
│   │   ├── users/
│   │   └── products/
└── tests/
    ├── conftest.py
    ├── features/
    │   ├── test_auth.py
    │   ├── test_users.py
    │   └── test_products.py
    └── integration/
        ├── test_user_flows.py
        └── test_checkout.py
```

### Organized by Test Type

```
project/
├── app/
└── tests/
    ├── unit/               # Isolated tests
    │   ├── test_models.py
    │   └── test_services.py
    ├── integration/        # Component tests
    │   ├── test_api.py
    │   └── test_database.py
    ├── e2e/               # End-to-end tests
    │   └── test_user_journey.py
    └── conftest.py
```

## conftest.py

### Root conftest.py

Shared fixtures available to all tests:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)

@pytest.fixture
def test_user():
    """Sample user data for testing."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
    }

@pytest.fixture
def clean_database():
    """Reset database before each test."""
    db.session.execute(text("TRUNCATE TABLE users"))
    db.session.commit()
    yield
    db.session.rollback()
```

### Directory-Specific conftest.py

Fixtures available only to tests in that directory:

```python
# tests/integration/conftest.py
import pytest

@pytest.fixture
def authenticated_client(client):
    """Client with authentication already set up."""
    client.post("/login", json={"username": "test", "password": "test"})
    yield client
    # Cleanup
    client.post("/logout")
```

## Fixture Scopes

### Function Scope (Default)

New fixture for each test function:

```python
@pytest.fixture
def temp_file():
    """Create temporary file for each test."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)
```

### Class Scope

Shared across all test methods in a class:

```python
@pytest.fixture(scope="class")
def database_setup():
    """Setup database once per test class."""
    setup_database()
    yield
    cleanup_database()

class TestUsers:
    def test_create(self, database_setup):
        pass

    def test_delete(self, database_setup):
        pass  # Same database instance
```

### Module Scope

Shared across all tests in a module:

```python
@pytest.fixture(scope="module")
def api_server():
    """Start server once per module."""
    server = start_test_server()
    yield server
    server.stop()
```

### Session Scope

Shared across entire test session:

```python
@pytest.fixture(scope="session")
def global_config():
    """Load configuration once."""
    return load_config("test.yaml")
```

### Package Scope

Shared across all tests in a directory/package:

```python
@pytest.fixture(scope="package")
def package_db():
    """Database for all tests in this package."""
    db = create_test_db()
    yield db
    drop_test_db(db)
```

## Test Discovery

### Naming Conventions

Pytest automatically discovers files matching these patterns:

```
test_*.py
*_test.py
tests/*.py
```

### Test Functions

```python
def test_something():          # Discovered
def something_test():          # NOT discovered

class TestSomething:          # Discovered
    def test_method(self):    # Discovered
    def method_test(self):    # NOT discovered
```

### Custom Discovery

In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
python_files = ["test_*.py", "check_*.py"]
python_classes = ["Test*", "Check*"]
python_functions = ["test_*", "check_*"]
```

### Excluding Files

```bash
# Exclude specific files
pytest --ignore=tests/integration/

# Exclude pattern
pytest --ignore-glob='*/slow/*'

# In pyproject.toml
[tool.pytest.ini_options]
norecursedirs = [
    ".git",
    "venv",
    "build",
    "dist",
    "*.egg-info",
]
```

## Test Organization Patterns

### Arrange-Act-Assert

```python
def test_user_can_purchase_item():
    # Arrange
    user = create_user(balance=100)
    item = create_item(price=50)

    # Act
    result = user.purchase(item)

    # Assert
    assert result.success is True
    assert user.balance == 50
```

### Given-When-Then

```python
def test_purchase_without_funds_fails():
    # Given
    user = create_user(balance=10)
    item = create_item(price=50)

    # When
    result = user.purchase(item)

    # Then
    assert result.success is False
    assert "insufficient funds" in result.error.lower()
```

### Test Class Organization

```python
class TestUserService:
    """Tests for user service operations."""

    def test_create_user_with_valid_data(self):
        pass

    def test_create_user_with_duplicate_email_fails(self):
        pass

    def test_create_user_with_invalid_email_fails(self):
        pass

class TestUserAuthentication:
    """Tests for user authentication."""

    def test_login_with_valid_credentials(self):
        pass

    def test_login_with_invalid_password_fails(self):
        pass
```

### Parametrized Tests

```python
@pytest.mark.parametrize("email,valid", [
    ("user@example.com", True),
    ("user@localhost", True),
    ("invalid", False),
    ("@example.com", False),
    ("user@", False),
])
def test_email_validation(email, valid):
    result = validate_email(email)
    assert result.is_valid == valid
```

## Test Markers

### Custom Markers

```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
```

### Using Markers

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    time.sleep(5)

@pytest.mark.integration
def test_database_integration():
    pass

@pytest.mark.unit
def test_calculation():
    assert add(1, 2) == 3
```

### Running Marked Tests

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run slow and integration tests
pytest -m "slow or integration"

# Run integration but not slow
pytest -m "integration and not slow"
```

### Marker Configuration

In `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "smoke: marks smoke tests that should always pass",
]
```

## Test Classes vs Functions

### When to Use Classes

- **Related tests**: Group tests for a module or feature
- **Shared fixtures**: Use class-level fixtures
- **Inheritance**: Share setup/ teardown logic

```python
class TestDatabaseOperations:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        setup_test_db()
        yield
        cleanup_test_db()

    def test_insert(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass
```

### When to Use Functions

- **Simple tests**: Single assertion or operation
- **Independent tests**: No shared state
- **Flat structure**: Easier to read

```python
def test_addition():
    assert add(1, 2) == 3

def test_subtraction():
    assert subtract(5, 3) == 2
```

## Test File Organization

### By Module

```
tests/
├── test_models.py
├── test_views.py
├── test_services.py
└── test_utils.py
```

### By Feature

```
tests/
├── test_auth.py
├── test_users.py
├── test_products.py
└── test_orders.py
```

### By Layer

```
tests/
├── unit/
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   ├── test_api.py
│   └── test_database.py
└── e2e/
    └── test_flows.py
```

## Fixture Organization

### Fixture Location Strategy

1. **Root conftest.py**: Universal fixtures (client, db, config)
2. **Directory conftest.py**: Domain-specific fixtures (auth fixtures in tests/auth/)
3. **Module fixtures**: Test-specific fixtures (defined in test file)
4. **Class fixtures**: Shared within test class

### Fixture Composition

```python
# conftest.py
@pytest.fixture
def db_session():
    return create_session()

@pytest.fixture
def user_repo(db_session):
    return UserRepository(db_session)

@pytest.fixture
def user_service(user_repo):
    return UserService(user_repo)

# Tests use the composed fixture
def test_create_user(user_service):
    user = user_service.create("test@example.com")
```

## Test Data Management

### Factories

```python
# tests/factories.py
class UserFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "username": "testuser",
            "email": "test@example.com",
        }
        defaults.update(kwargs)
        return User(**defaults)

# In tests
def test_with_factory():
    user = UserFactory.create(username="custom")
```

### Factory Boy

```bash
pip install factory-boy
```

```python
import factory

class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")

# In tests
def test_with_factory_boy():
    user = UserFactory()
    assert user.email.endswith("@example.com")
```

### Fixtures with Variations

```python
@pytest.fixture
def base_user():
    return User(username="test", email="test@example.com")

@pytest.fixture
def admin_user(base_user):
    base_user.is_admin = True
    return base_user

@pytest.fixture
def premium_user(base_user):
    base_user.plan = "premium"
    return base_user
```

## Test Organization Best Practices

1. **One assertion per test** - Tests are more focused and failures are clearer
2. **Descriptive names** - `test_login_with_invalid_credentials_returns_401`
3. **Group related tests** - Use test classes or modules
4. **Use fixtures for setup** - Avoid duplication
5. **Separate test types** - Unit, integration, E2E
6. **Marker strategy** - Mark slow, integration, or platform-specific tests
7. **Avoid deep nesting** - Flat structure is easier to navigate
8. **Keep tests independent** - Each test should run in isolation
