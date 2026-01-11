# FastAPI Testing Patterns

Complete guide for testing FastAPI applications with pytest.

## Installation

```bash
pip install fastapi[standard] pytest pytest-asyncio httpx
```

## Basic TestClient Setup

### Simple Example

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

### TestClient Options

```python
@pytest.fixture
def client():
    # Use raise_server_exceptions=False to test error handlers
    return TestClient(app, raise_server_exceptions=False)

@pytest.fixture
def client_with_base_url():
    # Set base URL for relative paths
    return TestClient(app, base_url="http://testserver")
```

## Testing Endpoints

### GET Requests

```python
def test_get_all_items(client):
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_item_by_id(client):
    response = client.get("/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "name" in data
```

### POST Requests

```python
def test_create_item(client):
    payload = {"name": "Widget", "price": 9.99}
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == "Widget"

def test_create_item_validation_error(client):
    payload = {"name": ""}  # Invalid: empty name
    response = client.post("/items", json=payload)
    assert response.status_code == 422
```

### PUT/PATCH Requests

```python
def test_update_item(client):
    payload = {"name": "Updated Widget"}
    response = client.put("/items/1", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Widget"
```

### DELETE Requests

```python
def test_delete_item(client):
    response = client.delete("/items/1")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()
```

### Query Parameters

```python
def test_with_query_params(client):
    response = client.get("/items", params={"skip": 0, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10
```

### Path Parameters

```python
def test_path_parameter(client):
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json()["id"] == 42
```

### Headers

```python
def test_with_headers(client):
    headers = {"Authorization": "Bearer token123"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
```

### Cookies

```python
def test_with_cookies(client):
    client.cookies.set("session_id", "abc123")
    response = client.get("/profile")
    assert response.status_code == 200
```

## Dependency Overrides

### Override Single Dependency

```python
from main import app, get_db

def get_test_db():
    # Return test database session
    return test_session

def test_with_dependency_override(client):
    # Override before test
    app.dependency_overrides[get_db] = get_test_db

    response = client.get("/items")

    # Clean up after test
    app.dependency_overrides.clear()

    assert response.status_code == 200
```

### Override with Fixture

```python
@pytest.fixture
def client_with_mock_db():
    def mock_db():
        return MagicMock()

    app.dependency_overrides[get_db] = mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_with_mock_db(client_with_mock_db):
    response = client_with_mock_db.get("/items")
    assert response.status_code == 200
```

### Override Authentication

```python
@pytest.fixture
def authenticated_client():
    def mock_auth():
        return {"user_id": 1, "username": "testuser"}

    app.dependency_overrides[get_current_user] = mock_auth
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_protected_route(authenticated_client):
    response = authenticated_client.get("/admin")
    assert response.status_code == 200
```

## Async Tests

### Basic Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_endpoint():
    from httpx import AsyncClient, ASGITransport
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/async-endpoint")
        assert response.status_code == 200
```

### Async Test Fixture

```python
@pytest.fixture
async def async_client():
    from httpx import AsyncClient, ASGITransport
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_with_fixture(async_client):
    response = await async_client.get("/async-endpoint")
    assert response.status_code == 200
```

### pytest.ini Configuration

```ini
[pytest]
asyncio_mode = auto
```

Or in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## Testing Error Responses

### 404 Not Found

```python
def test_item_not_found(client):
    response = client.get("/items/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### 401 Unauthorized

```python
def test_unauthorized_access(client):
    response = client.get("/admin")
    assert response.status_code == 401
```

### 422 Validation Error

```python
def test_invalid_input(client):
    response = client.post("/items", json={"price": -10})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("price" in err["loc"] for err in errors)
```

### 500 Server Error

```python
def test_server_error_handling(client):
    # Simulate server error
    response = client.get("/error")
    assert response.status_code == 500
```

## Testing Response Models

### Validate Response Structure

```python
def test_response_model(client):
    response = client.get("/items/1")
    assert response.status_code == 200

    data = response.json()
    required_fields = ["id", "name", "price", "created_at"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
```

### Pydantic Model Validation

```python
from pydantic import ValidationError
from schemas import ItemResponse

def test_response_matches_schema(client):
    response = client.get("/items/1")
    data = response.json()

    # Validate against Pydantic model
    item = ItemResponse(**data)
    assert item.id == 1
```

## Testing File Upload

```python
def test_upload_file(client):
    file_content = b"test file content"
    files = {"file": ("test.txt", file_content, "text/plain")}

    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert "filename" in response.json()
```

## Testing Form Data

```python
def test_form_submission(client):
    data = {"username": "testuser", "password": "secret"}
    response = client.post("/login", data=data)
    assert response.status_code == 200
    assert "token" in response.json()
```

## Testing Webhooks

```python
def test_webhook_endpoint(client):
    payload = {"event": "user.created", "user_id": 123}
    response = client.post("/webhooks", json=payload)
    assert response.status_code == 202
```

## Testing Background Tasks

```python
def test_background_task(client):
    response = client.post("/tasks", json={"email": "test@example.com"})
    assert response.status_code == 202

    # Background task executes after response
    # Verify side effects (e.g., email sent)
```

## Testing Streaming Responses

```python
def test_streaming_response(client):
    response = client.get("/stream")
    assert response.status_code == 200

    chunks = []
    for chunk in response.iter_bytes():
        chunks.append(chunk)

    assert len(chunks) > 0
```

## Testing CORS

```python
def test_cors_headers(client):
    response = client.options("/items", headers={"Origin": "http://example.com"})
    assert "access-control-allow-origin" in response.headers
```

## Best Practices

1. **Use fixtures for setup** - Create reusable test clients and data
2. **Override dependencies** - Don't use real databases in tests
3. **Test edge cases** - Empty results, invalid IDs, boundary values
4. **Use descriptive test names** - `test_get_item_returns_404_when_not_found`
5. **Clean up after tests** - Clear dependency overrides, close sessions
6. **Test authentication and authorization** - Verify protected routes
7. **Mock external services** - Don't call real APIs or databases
