from sqlmodel import SQLModel, create_engine, Session
from config import get_settings
from models import TaskDB  # Import so metadata is registered

settings = get_settings()

# Create engine with connection pooling for production
engine = create_engine(
    settings.database_url,
    echo=False,
    # Pool settings for PostgreSQL
    pool_size=10,           # Number of connections to maintain
    max_overflow=20,         # Additional connections beyond pool_size
    pool_pre_ping=True,      # Test connections before using
    pool_recycle=3600,       # Recycle connections after 1 hour
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session