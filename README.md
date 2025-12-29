# FastAPI Learning Repository

A comprehensive learning resource for building FastAPI applications, from hello-world to production-ready APIs.

## 📚 Contents

### Skill: FastAPI Builder
Located in `skill/` - A Claude Code skill for building FastAPI projects.

**Features:**
- Hello World template for learning
- CRUD + PostgreSQL template for production apps
- Comprehensive reference documentation (core patterns, database, auth, testing, deployment)
- Docker and Docker Compose support

**Documentation:** See [skill/SKILL.md](skill/SKILL.md)

### Project: Hello World Example
Located in `projects/hello-world/` - A working FastAPI application.

**Features:**
- Basic CRUD API with in-memory storage
- Pydantic validation
- Docker support
- Interactive API documentation
- Health check endpoint

**Quick start:**
```bash
cd projects/hello-world
uv run uvicorn main:app --reload
# Visit http://localhost:8000/docs
```

## 🚀 Getting Started

1. **Explore the skill documentation** in `skill/SKILL.md`
2. **Try the hello-world project** in `projects/hello-world/`
3. **Build your own FastAPI app** using the skill templates

## 📖 Learning Path

1. **Beginner:** Start with `projects/hello-world/` - understand basic FastAPI
2. **Intermediate:** Use `skill/assets/crud-postgres/` template for database projects
3. **Advanced:** Add authentication, testing, deployment using skill references

## 🛠️ Requirements

- Python 3.11+
- uv package manager (recommended) or pip
- Docker (optional, for containerization)
- PostgreSQL (for CRUD template)

## 📄 License

This is a learning resource. Feel free to use and modify as needed.

## 🤝 Contributing

This is a personal learning repository. Feel free to fork and adapt for your own learning!
