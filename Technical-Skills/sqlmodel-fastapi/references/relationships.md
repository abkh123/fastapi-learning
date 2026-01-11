# Relationships

Complete guide for defining and querying relationships in SQLModel.

## One-to-Many

### Model Definition

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class UserDB(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str = Field(index=True)

    # Relationship: One user has many items
    items: List["ItemDB"] = Relationship(back_populates="owner")

class ItemDB(SQLModel, table=True):
    __tablename__ = "items"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    owner_id: int = Field(foreign_key="users.id")

    # Relationship: Many items belong to one user
    owner: UserDB = Relationship(back_populates="items")
```

### Create with Relationship

```python
@app.post("/items", response_model=ItemPublic)
def create_item(item: ItemCreate, session: Session = Depends(get_session)):
    # Verify owner exists
    owner = session.get(UserDB, item.owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    db_item = ItemDB.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return ItemPublic.model_validate(db_item)
```

### Query with Relationship

```python
from sqlmodel import selectinload

@app.get("/items/{item_id}", response_model=ItemPublic)
def get_item(item_id: int, session: Session = Depends(get_session)):
    # Eager load owner relationship
    item = session.exec(
        select(ItemDB)
        .options(selectinload(ItemDB.owner))
        .where(ItemDB.id == item_id)
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return ItemPublic.model_validate(item)
```

### Response with Nested Data

```python
class ItemPublic(SQLModel):
    id: int
    name: str
    owner_id: int
    owner: Optional["UserPublic"] = None  # Nested relationship

class UserPublic(SQLModel):
    id: int
    username: str
    email: str
```

### Query Parent from Child

```python
@app.get("/items/{item_id}/owner")
def get_item_owner(item_id: int, session: Session = Depends(get_session)):
    item = session.exec(
        select(ItemDB)
        .options(selectinload(ItemDB.owner))
        .where(ItemDB.id == item_id)
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return UserPublic.model_validate(item.owner)
```

### Query Children from Parent

```python
@app.get("/users/{user_id}/items", response_model=List[ItemPublic])
def get_user_items(user_id: int, session: Session = Depends(get_session)):
    user = session.exec(
        select(UserDB)
        .options(selectinload(UserDB.items))
        .where(UserDB.id == user_id)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return [ItemPublic.model_validate(item) for item in user.items]
```

## Many-to-Many

### Link Table Definition

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class UserDB(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

    # Many-to-many relationship
    teams: List["TeamDB"] = Relationship(
        back_populates="users",
        link_model=TeamMemberLink
    )

class TeamDB(SQLModel, table=True):
    __tablename__ = "teams"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Many-to-many relationship
    users: List["UserDB"] = Relationship(
        back_populates="teams",
        link_model=TeamMemberLink
    )

class TeamMemberLink(SQLModel, table=True):
    __tablename__ = "team_members"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    team_id: int = Field(foreign_key="teams.id", primary_key=True)
    role: str = "member"
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Add to Relationship

```python
@app.post("/teams/{team_id}/members/{user_id}")
def add_team_member(
    team_id: int,
    user_id: int,
    role: str = "member",
    session: Session = Depends(get_session)
):
    team = session.get(TeamDB, team_id)
    user = session.get(UserDB, user_id)

    if not team or not user:
        raise HTTPException(status_code=404, detail="Team or user not found")

    # Create link
    link = TeamMemberLink(user_id=user_id, team_id=team_id, role=role)
    session.add(link)
    session.commit()

    return {"message": "Member added to team"}
```

### Query Many-to-Many

```python
from sqlmodel import selectinload

@app.get("/teams/{team_id}", response_model=TeamPublic)
def get_team(team_id: int, session: Session = Depends(get_session)):
    team = session.exec(
        select(TeamDB)
        .options(selectinload(TeamDB.users))
        .where(TeamDB.id == team_id)
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return TeamPublic.model_validate(team)
```

### Response with Link Attributes

```python
class TeamMemberPublic(SQLModel):
    user_id: int
    username: str
    role: str
    joined_at: datetime

class TeamPublic(SQLModel):
    id: int
    name: str
    members: List[TeamMemberPublic] = []

@app.get("/teams/{team_id}/members")
def get_team_members(team_id: int, session: Session = Depends(get_session)):
    team = session.get(TeamDB, team_id)
    if not team:
        raise HTTPException(status_code=404)

    # Query through link table
    links = session.exec(
        select(TeamMemberLink, UserDB)
        .join(UserDB, TeamMemberLink.user_id == UserDB.id)
        .where(TeamMemberLink.team_id == team_id)
    ).all()

    members = []
    for link, user in links:
        members.append(TeamMemberPublic(
            user_id=user.id,
            username=user.username,
            role=link.role,
            joined_at=link.joined_at
        ))

    return members
```

## One-to-One

### Model Definition

```python
class UserDB(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

    # One-to-one relationship
    profile: Optional["ProfileDB"] = Relationship(back_populates="user")

class ProfileDB(SQLModel, table=True):
    __tablename__ = "profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    bio: str
    user_id: int = Field(foreign_key="users.id", unique=True)  # unique makes it 1:1

    user: UserDB = Relationship(back_populates="profile")
```

### Create One-to-One

```python
@app.post("/users/{user_id}/profile", response_model=ProfilePublic)
def create_profile(
    user_id: int,
    profile: ProfileCreate,
    session: Session = Depends(get_session)
):
    user = session.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if profile already exists
    existing = session.exec(
        select(ProfileDB).where(ProfileDB.user_id == user_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")

    db_profile = ProfileDB(**profile.model_dump(), user_id=user_id)
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)

    return ProfilePublic.model_validate(db_profile)
```

## Self-Referential Relationships

### Tree Structure (Parent-Child)

```python
class CategoryDB(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id")

    # Self-referential relationships
    parent: Optional["CategoryDB"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs=dict(remote_side="CategoryDB.id")
    )
    children: List["CategoryDB"] = Relationship(back_populates="parent")
```

### Query Tree Structure

```python
from sqlmodel import selectinload

@app.get("/categories/{category_id}/children")
def get_category_children(category_id: int, session: Session = Depends(get_session)):
    category = session.exec(
        select(CategoryDB)
        .options(selectinload(CategoryDB.children))
        .where(CategoryDB.id == category_id)
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return [CategoryPublic.model_validate(c) for c in category.children]
```

## Cascade Operations

### Cascade Delete

```python
from sqlalchemy.orm import relationship as sa_relationship

class UserDB(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

    # Delete items when user is deleted
    items: List["ItemDB"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs=dict(cascade="all, delete-orphan")
    )
```

### Manual Cascade

```python
@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete related items first
    items = session.exec(
        select(ItemDB).where(ItemDB.owner_id == user_id)
    ).all()
    for item in items:
        session.delete(item)

    # Then delete user
    session.delete(user)
    session.commit()

    return {"message": "User deleted"}
```

## Eager Loading Strategies

### selectinload (Default)

```python
from sqlmodel import selectinload

# Good for one-to-many
users = session.exec(
    select(UserDB).options(selectinload(UserDB.items))
).all()
```

### joinedload

```python
from sqlalchemy.orm import joinedload

# Good for one-to-one, reduces queries
users = session.exec(
    select(UserDB).options(joinedload(UserDB.profile))
).all()
```

### subqueryload

```python
from sqlalchemy.orm import subqueryload

# Alternative for large collections
users = session.exec(
    select(UserDB).options(subqueryload(UserDB.items))
).all()
```

## Performance Tips

1. **Always eager load relationships** - Avoid N+1 queries
2. **Use selectinload for collections** - Most efficient for lists
3. **Use joinedload for single items** - Reduces query count
4. **Limit relationship depth** - Don't load nested relationships
5. **Consider pagination** - For large collections

```python
# BAD: N+1 query problem
users = session.exec(select(UserDB)).all()
for user in users:
    print(user.items)  # Separate query for each user

# GOOD: Eager load
users = session.exec(
    select(UserDB).options(selectinload(UserDB.items))
).all()
for user in users:
    print(user.items)  # No additional queries
```

## Best Practices

1. **Define relationships on both sides** - Use back_populates
2. **Use foreign_key explicitly** - Clear relationship definition
3. **Eager load when accessing** - Avoid lazy loading in FastAPI
4. **Use unique for one-to-one** - Ensures single relationship
5. **Link model for many-to-many** - Add attributes to link table
6. **Cascade manually** - More control than automatic cascades
7. **Test relationship queries** - Verify eager loading works
