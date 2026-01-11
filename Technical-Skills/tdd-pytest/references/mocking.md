# Mocking and Patching Patterns

Complete guide for mocking dependencies and patching code in tests.

## Basics

### What is Mocking?

Mocking replaces real dependencies with test doubles that simulate behavior without side effects.

**When to mock:**
- External APIs (don't make real HTTP requests)
- Database (don't modify real data)
- File system (don't create real files)
- Time-dependent code (don't wait for real time)
- Randomness (make tests deterministic)

## MagicMock and Mock

### Basic MagicMock

```python
from unittest.mock import MagicMock

def test_with_magic_mock():
    mock_db = MagicMock()
    mock_db.query.return_value = [{"id": 1, "name": "Test"}]

    result = get_items(db=mock_db)
    assert len(result) == 1
```

### Configuring Return Values

```python
mock = MagicMock()
mock.method.return_value = 42
assert mock.method() == 42

# Multiple return values
mock.method.return_value = [1, 2, 3]
assert mock.method() == [1, 2, 3]

# Sequential return values
mock.method.side_effect = [1, 2, 3]
assert mock.method() == 1
assert mock.method() == 2
assert mock.method() == 3
```

### Raising Exceptions

```python
mock.method.side_effect = ValueError("Invalid input")

try:
    mock.method()
except ValueError as e:
    assert str(e) == "Invalid input"
```

### Side Effect with Function

```python
def side_effect_func(value):
    return value * 2

mock.calculate.side_effect = side_effect_func
assert mock.calculate(5) == 10
```

## Patching

### Patching Imports

```python
from unittest.mock import patch

def test_with_patch():
    # Patch where the module imports it, not where it's defined
    with patch("app.database.get_db") as mock_get_db:
        mock_get_db.return_value = MagicMock()

        result = get_items()
        mock_get_db.assert_called_once()
```

### Patching as Decorator

```python
@patch("app.database.get_db")
def test_with_decorator(mock_get_db):
    mock_get_db.return_value = MagicMock()
    result = get_items()
    mock_get_db.assert_called_once()
```

### Patching with Fixture

```python
@pytest.fixture
def mock_database():
    with patch("app.database.get_db") as mock:
        mock.return_value = MagicMock()
        yield mock

def test_with_fixture(mock_database):
    result = get_items()
    mock_database.assert_called_once()
```

### Patching Classes

```python
@patch("app.external_api.APIClient")
def test_api_client(mock_api_client_class):
    # Configure the mock instance
    mock_instance = mock_api_client_class.return_value
    mock_instance.fetch.return_value = {"data": "test"}

    result = fetch_external_data()

    mock_api_client_class.assert_called_once()
    mock_instance.fetch.assert_called_once()
```

### Autospec

Use `autospec=True` to match the signature of the real object:

```python
@patch("app.external_api.APIClient", autospec=True)
def test_with_autospec(mock_api_client):
    # Will fail if API doesn't have correct signature
    result = call_api(mock_api_client)
```

## Common Mock Patterns

### Mock Database Session

```python
@pytest.fixture
def mock_db_session():
    session = MagicMock()

    # Mock query chain
    session.query.return_value.filter.return_value.all.return_value = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ]

    return session

def test_get_items(mock_db_session):
    items = get_items(db=mock_db_session)
    assert len(items) == 2
```

### Mock External API Calls

```python
@patch("httpx.Client.get")
def test_external_api(mock_get):
    # Configure mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"users": [{"id": 1}]}

    mock_get.return_value = mock_response

    result = fetch_users()
    assert len(result) == 1
```

### Mock File Operations

```python
@patch("builtins.open", new_callable=MagicMock)
def test_read_file(mock_open):
    # Configure file content
    mock_file = MagicMock()
    mock_file.read.return_value = "file content"
    mock_open.return_value.__enter__.return_value = mock_file

    result = read_file("test.txt")
    assert result == "file content"
```

### Mock Time and Dates

```python
from unittest.mock import patch
from datetime import datetime

@patch("app.datetime")
def test_with_mocked_datetime(mock_datetime):
    # Freeze time to specific date
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_time
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    result = get_current_time()
    assert result == fixed_time
```

### Mock Environment Variables

```python
@patch.dict("os.environ", {"API_KEY": "test-key", "DEBUG": "true"})
def test_with_env_vars():
    api_key = os.getenv("API_KEY")
    assert api_key == "test-key"
```

### Mock Random Values

```python
@patch("random.randint")
def test_with_mocked_random(mock_randint):
    mock_randint.return_value = 42

    result = roll_dice()
    assert result == 42
```

## Assertion Methods

### Verify Calls

```python
mock = MagicMock()

mock.method("arg1", "arg2")

# Verify called
mock.method.assert_called()

# Verify called with specific args
mock.method.assert_called_with("arg1", "arg2")

# Verify called once
mock.method.assert_called_once()

# Verify called once with specific args
mock.method.assert_called_once_with("arg1", "arg2")
```

### Verify Call Count

```python
mock.method()

assert mock.method.call_count == 1
assert mock.method.call_count >= 1
```

### Check All Calls

```python
mock.method(1)
mock.method(2)
mock.method(3)

# Get list of all calls
print(mock.method.call_args_list)
# [call(1), call(2), call(3)]

# Check specific call
assert mock.method.call_args_list[1] == call(2)
```

### Check Last Call

```python
mock.method(1)
mock.method(2)

# Get last call args
assert mock.method.call_args == call(2)
```

### Reset Mock

```python
mock.method("test")
mock.method.assert_called_once()

mock.reset_mock()
mock.method.assert_not_called()
```

## pytest-mock Plugin

The `pytest-mock` plugin provides cleaner mocking syntax:

```bash
pip install pytest-mock
```

### mocker.fixture

```python
def test_with_pytest_mock(mocker):
    # Create mock
    mock_db = mocker.MagicMock()

    # Patch
    mocker.patch("app.database.get_db", return_value=mock_db)

    # Spy (calls real implementation)
    spy = mocker.spy(app, "function_name")

    # Stub (replace with implementation)
    mocker.patch("app.function", return_value="stubbed")
```

### Mocking with mocker

```python
def test_mock_with_mocker(mocker):
    # Patch and configure in one line
    mock_db = mocker.patch("app.database.get_db")
    mock_db.return_value.query.return_value.all.return_value = []

    result = get_items()
    mock_db.assert_called_once()
```

## Mock OpenAPI Calls

```python
@patch("requests.get")
def test_api_call(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    mock_get.return_value = mock_response

    result = call_external_api()
    assert result == {"data": "test"}
```

## Mock Async Functions

```python
import pytest

@pytest.mark.asyncio
@patch("app.async_function")
async def test_async_mock(mock_async_func):
    mock_async_func.return_value = "mocked result"

    result = await async_function()
    assert result == "mocked result"
```

## Mock Context Managers

```python
@patch("app.DatabaseSession")
def test_context_manager(mock_session_class):
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_session
    mock_session_class.return_value = mock_session

    with DatabaseSession() as session:
        session.query("SELECT * FROM users")

    mock_session.__enter__.assert_called_once()
    mock_session.query.assert_called_once()
```

## Common Pitfalls

### Patch Import Location

Always patch where the module imports it, not where it's defined:

```python
# app.py
from database import get_db  # Imports from database module

def get_items():
    db = get_db()  # Uses the imported reference
    return db.query("SELECT * FROM items")

# test.py
# WRONG - patches at definition
with patch("database.get_db"):  # Won't work

# CORRECT - patches at import
with patch("app.get_db"):  # Works!
```

### Mock Return Value vs Side Effect

```python
mock = MagicMock()

# return_value always returns same value
mock.method.return_value = 42
mock.method()  # 42
mock.method()  # 42
mock.method()  # 42

# side_effect can vary
mock.method.side_effect = [1, 2, 3]
mock.method()  # 1
mock.method()  # 2
mock.method()  # 3
```

### Forgetting to Reset Mocks

```python
def test_forgot_reset(mock_db):
    mock_db.query.return_value = [1, 2, 3]

    result = get_items()

    # Clean up - mock state persists
    mock_db.reset_mock()
```

## Best Practices

1. **Patch at import location** - Not at definition
2. **Use autospec** - Ensures mock matches real signature
3. **Be specific** - Mock only what you need
4. **Don't over-mock** - Mock external dependencies, not your own code
5. **Test behavior, not implementation** - Mock the what, not the how
6. **Use pytest-mock** - Cleaner syntax than unittest.mock
7. **Reset mocks** - Prevent state leakage between tests
