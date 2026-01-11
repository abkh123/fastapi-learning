# Deployment Guide

Deploy FastAPI applications from local development to production.

## Local Development

### Running with Uvicorn

```bash
# Development mode (auto-reload on code changes)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With uv
uv run uvicorn main:app --reload
```

### Environment Management

**.env file:**

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
```

**Load environment variables:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

**Never commit .env to git:**

**.gitignore:**

```
.env
__pycache__/
*.pyc
.pytest_cache/
htmlcov/
.coverage
```

---

## Docker

Containerize your FastAPI application for consistent deployment.

### Basic Dockerfile

**Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multi-Stage Dockerfile (Production)

Smaller image size with multi-stage builds:

```dockerfile
# Stage 1: Build
FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Update PATH
ENV PATH=/root/.local/bin:$PATH

# Non-root user (security best practice)
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .dockerignore

Exclude unnecessary files from Docker image:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.pytest_cache/
.coverage
htmlcov/
.git
.gitignore
README.md
.env
*.db
```

### Build and Run

```bash
# Build image
docker build -t fastapi-app .

# Run container
docker run -d --name fastapi-app -p 8000:8000 fastapi-app

# Run with environment variables
docker run -d --name fastapi-app -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  fastapi-app

# View logs
docker logs fastapi-app

# Stop container
docker stop fastapi-app
```

---

## Docker Compose

Orchestrate multiple containers (app + database).

### Basic docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/mydb
      - SECRET_KEY=your-secret-key-change-in-production
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: fastapi-app:latest
    container_name: fastapi-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network

  db:
    image: postgres:15-alpine
    container_name: postgres-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: pgadmin
    restart: unless-stopped
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "5050:80"
    depends_on:
      - db
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
```

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Remove volumes (fresh start)
docker-compose down -v
```

### Database Migrations with Docker

```bash
# Run migrations inside container
docker-compose exec app alembic upgrade head

# Create new migration
docker-compose exec app alembic revision --autogenerate -m "Description"
```

---

## Kubernetes

Deploy to Kubernetes for production-scale applications.

**Note:** Master Docker and Docker Compose first. Kubernetes adds significant complexity.

### Basic Deployment

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: your-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service

**service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  selector:
    app: fastapi
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### ConfigMap and Secrets

**configmap.yaml:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DEBUG: "False"
  LOG_LEVEL: "INFO"
```

**secrets.yaml:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  database-url: postgresql+asyncpg://user:password@postgres-service:5432/mydb
  secret-key: your-super-secret-key-change-this
```

### Deploy to Kubernetes

```bash
# Create secrets
kubectl apply -f secrets.yaml

# Create configmap
kubectl apply -f configmap.yaml

# Deploy application
kubectl apply -f deployment.yaml

# Expose service
kubectl apply -f service.yaml

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/fastapi-app

# Scale deployment
kubectl scale deployment/fastapi-app --replicas=5
```

---

## Production Best Practices

### 1. Use Production-Ready Web Server

**Gunicorn with Uvicorn workers:**

```dockerfile
# Install gunicorn
RUN pip install gunicorn

# Run with Gunicorn
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 3. Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@app.get("/items")
async def get_items():
    logger.info("Fetching items")
    return {"items": []}
```

### 4. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. HTTPS/TLS

Use a reverse proxy (Nginx, Caddy) or cloud load balancer for HTTPS.

**Nginx config:**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. Environment-Specific Settings

```python
from enum import Enum

class Environment(str, Enum):
    DEV = "development"
    STAGING = "staging"
    PROD = "production"

class Settings(BaseSettings):
    environment: Environment = Environment.DEV
    debug: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PROD

settings = Settings()

# Use in app
if not settings.is_production:
    app.add_middleware(...)  # Dev-only middleware
```

---

## Deployment Checklist

- [ ] Use strong SECRET_KEY (32+ random characters)
- [ ] Set DEBUG=False in production
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up logging
- [ ] Add health check endpoint
- [ ] Use Gunicorn with Uvicorn workers
- [ ] Set resource limits (CPU/memory)
- [ ] Configure database connection pooling
- [ ] Set up monitoring and alerts
- [ ] Back up database regularly
- [ ] Use container registry (Docker Hub, ECR, GCR)
- [ ] Implement CI/CD pipeline
- [ ] Set up log aggregation
- [ ] Configure auto-scaling (if using K8s)

## Learn More

- **Database Deployment:** See `references/database.md` for database connection in containers
- **Security:** See `references/authentication.md` for securing production APIs
