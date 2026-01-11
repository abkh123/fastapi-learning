from database import engine
from sqlalchemy import text

# Add missing columns directly
with engine.connect() as conn:
    print("Adding status column...")
    conn.execute(text("ALTER TABLE task ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'pending'"))
    conn.commit()

    print("Adding created_at column...")
    conn.execute(text("ALTER TABLE task ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    conn.commit()

print("Columns added successfully!")
