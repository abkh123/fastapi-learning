# Migrations with Alembic

Complete guide for database schema migrations using Alembic with SQLModel.

## Installation

```bash
pip install alembic
# or with uv
uv add alembic
```

## Initial Setup

### Initialize Alembic

```bash
alembic init alembic
```

This creates:
```
alembic/
├── env.py           # Migration configuration
├── script.py.mako   # Migration template
└── versions/        # Migration files
alembic.ini          # Alembic configuration
```

### Configure alembic/env.py

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from sqlmodel import SQLModel
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import all models so SQLModel.metadata is populated
from models import TaskDB, UserDB, ItemDB

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = SQLModel.metadata

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = os.getenv("DATABASE_URL")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
        )

        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Configure alembic.ini

```ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
sqlalchemy.url = postgresql://user:pass@localhost:5432/mydb

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

## Creating Migrations

### Autogenerate Migration

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Add tasks table"
```

### Manual Migration

```bash
# Create empty migration file
alembic revision -m "Custom migration"
```

Edit the generated file:

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Apply changes
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Revert changes
    op.drop_table('tasks')
```

## Running Migrations

### Upgrade to Latest

```bash
alembic upgrade head
```

### Upgrade to Specific Version

```bash
alembic upgrade <revision_id>
```

### Downgrade One Step

```bash
alembic downgrade -1
```

### Downgrade to Specific Version

```bash
alembic downgrade <revision_id>
```

### Downgrade to Base (Empty)

```bash
alembic downgrade base
```

## Common Migration Operations

### Add Column

```python
def upgrade():
    op.add_column('tasks', sa.Column('priority', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('tasks', 'priority')
```

### Alter Column Type

```python
def upgrade():
    op.alter_column('tasks', 'title',
                   existing_type=sa.String(),
                   type_=sa.String(200),
                   nullable=False)

def downgrade():
    op.alter_column('tasks', 'title',
                   existing_type=sa.String(200),
                   type_=sa.String(),
                   nullable=False)
```

### Add Index

```python
def upgrade():
    op.create_index('ix_tasks_status', 'tasks', ['status'])

def downgrade():
    op.drop_index('ix_tasks_status', table_name='tasks')
```

### Add Foreign Key

```python
def upgrade():
    op.create_foreign_key(
        'fk_tasks_owner_id',
        'tasks', 'users',
        ['owner_id'], ['id']
    )

def downgrade():
    op.drop_constraint('fk_tasks_owner_id', 'tasks', type_='foreignkey')
```

### Rename Column

```python
def upgrade():
    op.alter_column('tasks', 'old_name',
                   new_column_name='new_name')

def downgrade():
    op.alter_column('tasks', 'new_name',
                   new_column_name='old_name')
```

### Rename Table

```python
def upgrade():
    op.rename_table('old_tasks', 'tasks')

def downgrade():
    op.rename_table('tasks', 'old_tasks')
```

### Add Unique Constraint

```python
def upgrade():
    op.create_unique_constraint('uq_tasks_title', 'tasks', ['title'])

def downgrade():
    op.drop_constraint('uq_tasks_title', 'tasks', type_='unique')
```

## Data Migrations

### Migrate Existing Data

```python
from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    # Add new column
    op.add_column('tasks', sa.Column('status', sa.String(), nullable=True))

    # Migrate existing data
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE tasks SET status = 'pending' WHERE status IS NULL")
    )

    # Make column non-nullable
    op.alter_column('tasks', 'status', nullable=False)

def downgrade():
    op.drop_column('tasks', 'status')
```

### Seed Initial Data

```python
def upgrade():
    connection = op.get_bind()

    # Insert default user
    connection.execute(
        sa.text(
            "INSERT INTO users (username, email) VALUES "
            "('admin', 'admin@example.com')"
        )
    )

def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM users WHERE username = 'admin'"))
```

## Migration Workflow

### Development Workflow

1. **Modify models** in `models.py`
2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
3. **Review migration** in `alembic/versions/`
4. **Apply migration**:
   ```bash
   alembic upgrade head
   ```
5. **Test changes** in application

### Production Workflow

1. **Generate migration** in development
2. **Review migration** carefully
3. **Test migration** on staging database
4. **Backup production database**
5. **Apply migration**:
   ```bash
   alembic upgrade head
   ```
6. **Verify application** works

## Current Version

### Check Current Version

```bash
alembic current
```

### Show History

```bash
alembic history
```

### Show Latest Version

```bash
alembic heads
```

## Troubleshooting

### Autogenerate Not Detecting Changes

**Cause:** Models not imported in `alembic/env.py`

**Solution:**
```python
# In alembic/env.py, import ALL models
from models import TaskDB, UserDB, ItemDB  # Import all models
```

### Foreign Key Detected as Change

**Cause:** Type mismatch or missing relationship

**Solution:** Ensure `foreign_key` matches table name exactly:
```python
class ItemDB(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.id")  # Must match table name
```

### Migration Conflicts

**Cause:** Multiple branches of migrations

**Solution:**
```bash
# Create merge migration
alembic merge -m "Merge branches" <revision1> <revision2>
```

### Database Out of Sync

**Cause:** Database state doesn't match migration history

**Solution:**
```bash
# Stamp database to specific version (no changes applied)
alembic stamp <revision_id>

# Stamp to head (mark as current)
alembic stamp head
```

### Reset Database

```bash
# Drop all tables
alembic downgrade base

# Recreate from migrations
alembic upgrade head
```

## Testing Migrations

### Test Migration Script

```python
# test_migrations.py
import pytest
from alembic import command
from alembic.config import Config

def test_upgrade_downgrade():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///:memory:")

    # Upgrade
    command.upgrade(alembic_cfg, "head")

    # Downgrade
    command.downgrade(alembic_cfg, "base")

    # Upgrade again
    command.upgrade(alembic_cfg, "head")
```

## Best Practices

1. **Always review autogenerate** - Don't blindly apply migrations
2. **Use descriptive messages** - Explain what migration does
3. **Test migrations** - Run upgrade/downgrade cycles
4. **Backup before production** - Always have a rollback plan
5. **Version control migrations** - Commit all migration files
6. **Never modify existing migrations** - Create new ones instead
7. **Use data migrations sparingly** - Prefer application code
8. **Keep migrations reversible** - Always implement downgrade()
