from database import engine
from sqlmodel import SQLModel

# Drop all tables and recreate them
print("Dropping all tables...")
SQLModel.metadata.drop_all(engine)

print("Creating tables...")
SQLModel.metadata.create_all(engine)

print("Database reset complete!")
