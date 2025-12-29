# FastAPI Core Patterns

Essential FastAPI concepts with practical examples.

## Path Operations

Path operations define your API endpoints. Each combines a path (URL) with an HTTP method.

### Basic Path Operations

```python
from fastapi import FastAPI

app = FastAPI()

# GET - Retrieve data
@app.get("/items")
def read_items():
    return [{"id": 1, "name": "Item 1"}]

# POST - Create data
@app.post("/items")
def create_item(item: dict):
    return {"id": 2, **item}

# PUT - Update data (full replacement)
@app.put("/items/{item_id}")
def update_item(item_id: int, item: dict):
    return {"id": item_id, **item}

# PATCH - Partial update
@app.patch("/items/{item_id}")
def patch_item(item_id: int, updates: dict):
    return {"id": item_id, "updated_fields": updates}

# DELETE - Remove data
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"message": f"Item {item_id} deleted"}
```

### Async Operations

Use `async def` for async operations (database queries, external APIs):

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await db.fetch_user(user_id)  # Async database call
    return user

@app.post("/items")
async def create_item(item: dict):
    result = await db.insert(item)
    return result
```

**When to use async:**
- Database queries (with async drivers)
- External API calls
- File I/O operations
- Any I/O-bound operations

**When to use regular def:**
- CPU-bound operations
- Simple synchronous logic
- No I/O operations

---

## Request/Response Models (Pydantic)

Pydantic models provide automatic validation, serialization, and documentation.

### Basic Models

```python
from pydantic import BaseModel, Field
from typing import Optional

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.post("/items", response_model=ItemResponse)
def create_item(item: Item):
    # Item is automatically validated
    return {"id": 1, **item.model_dump()}
```

### Field Validation

```python
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=0, le=120)
    is_active: bool = True

@app.post("/users")
def create_user(user: User):
    return user
```

**Common Field constraints:**
- `min_length`, `max_length` - String length
- `ge`, `le`, `gt`, `lt` - Numeric comparisons (greater/less than)
- `regex` - Pattern matching
- `...` - Required field (no default)

### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class User(BaseModel):
    name: str
    email: EmailStr
    address: Address

@app.post("/users")
def create_user(user: User):
    # Automatically validates nested structure
    return user
```

---

## Path Parameters

Capture dynamic values from the URL path.

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    # user_id is automatically converted to int
    return {"user_id": user_id}

@app.get("/items/{item_id}/reviews/{review_id}")
def get_review(item_id: int, review_id: int):
    return {"item_id": item_id, "review_id": review_id}
```

### Path Parameter Types

```python
from enum import Enum

class Category(str, Enum):
    electronics = "electronics"
    clothing = "clothing"
    food = "food"

@app.get("/items/category/{category}")
def get_by_category(category: Category):
    # Automatically validates against enum values
    return {"category": category.value}
```

---

## Query Parameters

Optional parameters passed in the URL query string.

```python
# /items?skip=0&limit=10
@app.get("/items")
def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# Required query parameter (no default value)
@app.get("/items/search")
def search_items(q: str):
    return {"query": q}

# Optional query parameter
@app.get("/items/filter")
def filter_items(category: Optional[str] = None):
    if category:
        return {"category": category}
    return {"all": "items"}
```

### Query Parameter Validation

```python
from fastapi import Query

@app.get("/items")
def read_items(
    q: Optional[str] = Query(None, min_length=3, max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    return {"q": q, "skip": skip, "limit": limit}
```

---

## Request Body

Send data in the request body using Pydantic models.

```python
class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
def create_item(item: Item):
    return {"name": item.name, "price": item.price}
```

### Multiple Body Parameters

```python
class Item(BaseModel):
    name: str
    price: float

class User(BaseModel):
    username: str

@app.post("/items")
def create_item(item: Item, user: User):
    return {"item": item, "owner": user}
```

### Body with Path and Query Parameters

```python
@app.put("/items/{item_id}")
def update_item(
    item_id: int,  # Path parameter
    item: Item,    # Request body
    q: Optional[str] = None  # Query parameter
):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result["query"] = q
    return result
```

---

## Response Status Codes

Control HTTP status codes for different scenarios.

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    # 204 means no content returned
    pass
```

### Common Status Codes

```python
from fastapi import status

# Success codes
status.HTTP_200_OK           # Default for GET, PUT, PATCH
status.HTTP_201_CREATED      # Resource created (POST)
status.HTTP_204_NO_CONTENT   # Success but no content (DELETE)

# Client error codes
status.HTTP_400_BAD_REQUEST       # Invalid request
status.HTTP_401_UNAUTHORIZED      # Not authenticated
status.HTTP_403_FORBIDDEN         # Authenticated but no permission
status.HTTP_404_NOT_FOUND         # Resource doesn't exist
status.HTTP_422_UNPROCESSABLE_ENTITY  # Validation error

# Server error codes
status.HTTP_500_INTERNAL_SERVER_ERROR
status.HTTP_503_SERVICE_UNAVAILABLE
```

---

## Error Handling

Handle errors with HTTPException.

```python
from fastapi import HTTPException, status

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    return items_db[item_id]
```

### Custom Error Responses

```python
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)}
    )

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id < 0:
        raise ValueError("Item ID must be positive")
    return {"item_id": item_id}
```

---

## Dependency Injection

Reuse logic across endpoints using dependencies.

### Basic Dependency

```python
from fastapi import Depends

def get_db():
    db = DatabaseConnection()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
def get_users(db = Depends(get_db)):
    return db.query_users()
```

### Dependency with Parameters

```python
def pagination(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/items")
def read_items(pagination_params: dict = Depends(pagination)):
    skip = pagination_params["skip"]
    limit = pagination_params["limit"]
    return {"skip": skip, "limit": limit}
```

### Class-based Dependencies

```python
class CommonQueryParams:
    def __init__(self, q: Optional[str] = None, skip: int = 0, limit: int = 10):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items")
def read_items(commons: CommonQueryParams = Depends()):
    return commons
```

### Nested Dependencies

```python
def get_db():
    return Database()

def get_current_user(db = Depends(get_db)):
    return db.get_user()

@app.get("/profile")
def get_profile(user = Depends(get_current_user)):
    # get_current_user depends on get_db
    return user
```

---

## Validation

FastAPI automatically validates requests using Pydantic.

### Automatic Validation

```python
class Item(BaseModel):
    name: str
    price: float = Field(..., gt=0)  # Must be positive
    quantity: int = Field(..., ge=1, le=1000)

@app.post("/items")
def create_item(item: Item):
    # If validation fails, FastAPI returns 422 automatically
    return item
```

**Validation happens automatically for:**
- Path parameters (type conversion)
- Query parameters (type conversion, constraints)
- Request body (Pydantic models)

### Custom Validators

```python
from pydantic import BaseModel, validator

class Item(BaseModel):
    name: str
    price: float

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.title()  # Capitalize first letter

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
```

### Validation Error Response

When validation fails, FastAPI returns:

```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

## Response Models

Define what data is returned (and exclude sensitive fields).

```python
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    # No password field!

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    # Save user with password
    saved_user = save_to_db(user)
    # Response automatically excludes password
    return saved_user
```

### Multiple Response Models

```python
from fastapi import Response

@app.get("/items/{item_id}")
def get_item(item_id: int, response: Response):
    if item_id not in items_db:
        response.status_code = 404
        return {"error": "Item not found"}
    return items_db[item_id]
```

---

## Learn More

- **Database Integration:** See `references/database.md` for SQLAlchemy patterns, migrations, and async support
- **Authentication:** See `references/authentication.md` for JWT, OAuth2, and protected routes
- **Testing:** See `references/testing.md` for pytest and TestClient patterns
- **Deployment:** See `references/deployment.md` for Docker, Docker Compose, and Kubernetes
