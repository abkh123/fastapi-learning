from fastapi import FastAPI
from app.routers import items

app = FastAPI(
    title="FastAPI CRUD with PostgreSQL",
    description="A production-ready API with PostgreSQL database",
    version="1.0.0"
)

# Include routers
app.include_router(items.router)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "FastAPI CRUD API with PostgreSQL",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
