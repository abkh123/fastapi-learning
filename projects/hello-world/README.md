# FastAPI Hello World

A minimal FastAPI application demonstrating basic CRUD operations with in-memory storage.

## Features

- ✅ Basic CRUD operations (Create, Read, Update, Delete)
- ✅ In-memory storage (no database required)
- ✅ Request/response validation with Pydantic
- ✅ Interactive API documentation
- ✅ Health check endpoint
- ✅ Docker support

## Quick Start

### Option 1: Run Locally with Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload
```

### Option 2: Run Locally with uv

```bash
# Install uv if you haven't already
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the application
uv run uvicorn main:app --reload
```

### Option 3: Run with Docker

```bash
# Build the Docker image
docker build -t fastapi-hello-world .

# Run the container
docker run -p 8000:8000 fastapi-hello-world
```

## Access the API

- **API Documentation (Swagger):** http://localhost:8000/docs
- **Alternative Documentation (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## API Endpoints

### GET /
Welcome message with links to documentation

### GET /health
Health check endpoint

### GET /items
List all items

### GET /items/{item_id}
Get a specific item by ID

### POST /items
Create a new item

**Request body:**
```json
{
  "name": "Item name",
  "description": "Optional description",
  "price": 9.99
}
```

### PUT /items/{item_id}
Update an existing item

### DELETE /items/{item_id}
Delete an item

## Example Usage

```bash
# Create an item
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "description": "A powerful laptop", "price": 999.99}'

# Get all items
curl http://localhost:8000/items

# Get specific item
curl http://localhost:8000/items/1

# Update item
curl -X PUT "http://localhost:8000/items/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Laptop", "description": "An even better laptop", "price": 1299.99}'

# Delete item
curl -X DELETE http://localhost:8000/items/1
```

## Project Structure

```
hello-world/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration (for uv)
├── Dockerfile          # Docker configuration
└── README.md           # This file
```

## Next Steps

This is a minimal starter template. To build production-ready applications:

1. **Add a Database:** See the `crud-postgres` template for PostgreSQL integration
2. **Add Authentication:** Implement JWT-based authentication
3. **Add Tests:** Write tests with pytest and TestClient
4. **Environment Configuration:** Use `.env` files for configuration
5. **Deployment:** Deploy to production with Docker Compose or Kubernetes

## Learn More

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **FastAPI Builder Skill:** Use the skill's reference files for advanced patterns
  - `references/core-patterns.md` - FastAPI fundamentals
  - `references/database.md` - Database integration
  - `references/authentication.md` - User authentication
  - `references/testing.md` - Testing patterns
  - `references/deployment.md` - Deployment strategies
