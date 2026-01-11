# Filtering and Querying

Complete guide for filtering, searching, and querying data with SQLModel.

## Basic Filtering

### Single Condition

```python
from sqlmodel import select, Session

@app.get("/tasks/by-status/{status}")
def filter_by_status(status: str, session: Session = Depends(get_session)):
    statement = select(TaskDB).where(TaskDB.status == status)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(t) for t in tasks]
```

### Multiple Conditions (AND)

```python
@app.get("/tasks/search")
def search_tasks(
    status: str,
    priority: int,
    session: Session = Depends(get_session)
):
    statement = select(TaskDB).where(
        TaskDB.status == status,
        TaskDB.priority == priority
    )
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(t) for t in tasks]
```

### Multiple Conditions (OR)

```python
from sqlmodel import or_

@app.get("/tasks/search")
def search_tasks(
    session: Session = Depends(get_session)
):
    statement = select(TaskDB).where(
        or_(
            TaskDB.status == "urgent",
            TaskDB.priority >= 4
        )
    )
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(t) for t in tasks]
```

## Dynamic Filtering

### Optional Filters

```python
from typing import Optional
from fastapi import Query

@app.get("/tasks/search")
def search_tasks(
    status: Optional[str] = None,
    priority: Optional[int] = None,
    title_contains: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(TaskDB)

    if status:
        statement = statement.where(TaskDB.status == status)
    if priority is not None:
        statement = statement.where(TaskDB.priority == priority)
    if title_contains:
        statement = statement.where(TaskDB.title.contains(title_contains))

    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(t) for t in tasks]
```

### Dynamic Filter Builder

```python
from sqlmodel import col

def build_filters(model, filters: dict):
    statement = select(model)
    for key, value in filters.items():
        if value is not None and hasattr(model, key):
            statement = statement.where(col(model.key) == value)
    return statement

@app.get("/tasks/search")
def search_tasks(
    status: Optional[str] = None,
    priority: Optional[int] = None,
    session: Session = Depends(get_session)
):
    filters = {"status": status, "priority": priority}
    statement = build_filters(TaskDB, filters)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(t) for t in tasks]
```

## Comparison Operators

### Equal / Not Equal

```python
# Equal
statement = select(TaskDB).where(TaskDB.status == "pending")

# Not equal
statement = select(TaskDB).where(TaskDB.status != "completed")
```

### Greater / Less Than

```python
from sqlmodel import col

# Greater than
statement = select(TaskDB).where(col(TaskDB.priority) > 3)

# Greater than or equal
statement = select(TaskDB).where(col(TaskDB.priority) >= 3)

# Less than
statement = select(TaskDB).where(col(TaskDB.priority) < 5)

# Less than or equal
statement = select(TaskDB).where(col(TaskDB.priority) <= 5)
```

### In List

```python
statuses = ["pending", "in_progress"]
statement = select(TaskDB).where(col(TaskDB.status).in_(statuses))
```

### Not In List

```python
statuses = ["completed", "cancelled"]
statement = select(TaskDB).where(col(TaskDB.status).not_in(statuses))
```

### Between

```python
from datetime import datetime, timedelta

cutoff = datetime.now(timezone.utc) - timedelta(days=7)
statement = select(TaskDB).where(
    col(TaskDB.created_at).between(cutoff, datetime.now(timezone.utc))
)
```

### Is Null / Is Not Null

```python
# Is null
statement = select(TaskDB).where(TaskDB.description.is_(None))

# Is not null
statement = select(TaskDB).where(TaskDB.description.is_not(None))
```

## String Matching

### Contains

```python
# Case-sensitive
statement = select(TaskDB).where(TaskDB.title.contains("urgent"))

# Case-insensitive (PostgreSQL)
statement = select(TaskDB).where(TaskDB.title.ilike("%urgent%"))
```

### Starts With

```python
# Case-insensitive
statement = select(TaskDB).where(TaskDB.title.ilike("report%"))
```

### Ends With

```python
# Case-insensitive
statement = select(TaskDB).where(TaskDB.title.ilike("%final"))
```

### Like Pattern

```python
# % matches any characters, _ matches single character
statement = select(TaskDB).where(TaskDB.title.like("BUG-%"))
```

## Date/Time Filtering

### Date Range

```python
from datetime import datetime, timedelta, timezone

@app.get("/tasks/recent")
def recent_tasks(
    days: int = Query(7, ge=1, le=365),
    session: Session = Depends(get_session)
):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    statement = select(TaskDB).where(TaskDB.created_at >= cutoff_date)
    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(t) for t in tasks]
```

### Before/After

```python
from datetime import datetime, timezone

# Created before
statement = select(TaskDB).where(TaskDB.created_at < datetime.now(timezone.utc))

# Created after
statement = select(TaskDB).where(TaskDB.created_at > datetime(2024, 1, 1))
```

### Date Part

```python
from sqlalchemy import extract

# Tasks created this month
statement = select(TaskDB).where(
    extract('month', TaskDB.created_at) == datetime.now(timezone.utc).month,
    extract('year', TaskDB.created_at) == datetime.now(timezone.utc).year
)
```

## Ordering

### Single Order By

```python
from sqlmodel import asc, desc

# Ascending
statement = select(TaskDB).order_by(asc(TaskDB.created_at))

# Descending
statement = select(TaskDB).order_by(desc(TaskDB.created_at))
```

### Multiple Order By

```python
statement = select(TaskDB).order_by(
    desc(TaskDB.priority),
    asc(TaskDB.created_at)
)
```

## Pagination

### Offset/Limit

```python
@app.get("/tasks")
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session)
):
    statement = select(TaskDB).offset(skip).limit(limit)
    tasks = session.exec(statement).all()

    total = len(session.exec(select(TaskDB)).all())

    return {
        "items": [TaskPublic.model_validate(t) for t in tasks],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total
    }
```

### Cursor-based Pagination

```python
@app.get("/tasks")
def list_tasks(
    cursor: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session)
):
    statement = select(TaskDB).order_by(asc(TaskDB.id)).limit(limit)

    if cursor:
        statement = statement.where(TaskDB.id > cursor)

    tasks = session.exec(statement).all()

    next_cursor = tasks[-1].id if tasks else None

    return {
        "items": [TaskPublic.model_validate(t) for t in tasks],
        "next_cursor": next_cursor
    }
```

## Counting

### Count All

```python
@app.get("/tasks/count")
def count_tasks(session: Session = Depends(get_session)):
    count = len(session.exec(select(TaskDB)).all())
    return {"total": count}
```

### Count with Filter

```python
from sqlalchemy import func

@app.get("/tasks/count")
def count_tasks(
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(func.count(TaskDB.id))
    if status:
        statement = statement.where(TaskDB.status == status)

    count = session.exec(statement).one()
    return {"total": count}
```

### Group By Count

```python
from sqlalchemy import func

@app.get("/tasks/by-status")
def tasks_by_status(session: Session = Depends(get_session)):
    statement = select(
        TaskDB.status,
        func.count(TaskDB.id)
    ).group_by(TaskDB.status)

    results = session.exec(statement).all()

    return [{"status": s, "count": c} for s, c in results]
```

## Aggregation

### Sum

```python
from sqlalchemy import func

statement = select(func.sum(OrderDB.amount))
total = session.exec(statement).one()
```

### Average

```python
statement = select(func.avg(TaskDB.priority))
avg = session.exec(statement).one()
```

### Min/Max

```python
# Min
statement = select(func.min(TaskDB.created_at))

# Max
statement = select(func.max(TaskDB.created_at))
```

## Join Queries

### Inner Join

```python
from sqlmodel import join

statement = select(TaskDB, UserDB).join(
    UserDB, TaskDB.assignee_id == UserDB.id
)

results = session.exec(statement).all()
for task, user in results:
    print(f"{task.title} - {user.username}")
```

### Left Join

```python
from sqlalchemy import left

statement = select(TaskDB).select_from(
    left(TaskDB, UserDB, TaskDB.assignee_id == UserDB.id)
)
```

### Join with Filter

```python
@app.get("/tasks")
def get_tasks_with_users(
    username: Optional[str] = None,
    session: Session = Depends(get_session)
):
    statement = select(TaskDB)

    if username:
        statement = statement.join(UserDB).where(UserDB.username == username)

    tasks = session.exec(statement).all()
    return [TaskPublic.model_validate(t) for t in tasks]
```

## Complex Queries

### Subquery

```python
from sqlalchemy import exists

# Find users who have tasks
statement = select(UserDB).where(
    exists().where(UserDB.id == TaskDB.assignee_id)
)
```

### Union

```python
from sqlalchemy import union_all

statement1 = select(TaskDB).where(TaskDB.status == "pending")
statement2 = select(TaskDB).where(TaskDB.status == "urgent")

combined = union_all(statement1, statement2)
```

### Having Clause

```python
from sqlalchemy import func, having

statement = select(
    TaskDB.status,
    func.count(TaskDB.id)
).group_by(TaskDB.status).having(
    func.count(TaskDB.id) > 5
)

results = session.exec(statement).all()
```

## Best Practices

1. **Use index on filtered columns** - Add `index=True` to Field
2. **Limit result sets** - Always use pagination for large tables
3. **Count efficiently** - Use `func.count()` instead of `len()`
4. **Use ilike for search** - Case-insensitive matching
5. **Filter at database** - Don't filter in Python
6. **Eager load relationships** - Use selectinload with joins
7. **Use col() for comparisons** - Better type inference
8. **Test complex queries** - Verify SQL generation
