"""
Migration to add professor grading fields to submissions table
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration with explicit authentication settings
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "grading_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Construct database URL with explicit authentication parameters
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=disable"

def run_migration():
    """Run the migration to add professor grading fields"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # Add new columns
        connection.execute(text("""
            ALTER TABLE submissions 
            ADD COLUMN IF NOT EXISTS ai_grade FLOAT CHECK (ai_grade BETWEEN 0 AND 100),
            ADD COLUMN IF NOT EXISTS professor_grade FLOAT CHECK (professor_grade BETWEEN 0 AND 100),
            ADD COLUMN IF NOT EXISTS ai_feedback TEXT,
            ADD COLUMN IF NOT EXISTS professor_feedback TEXT,
            ADD COLUMN IF NOT EXISTS final_grade FLOAT CHECK (final_grade BETWEEN 0 AND 100)
        """))
        
        # Migrate existing data: move old grade to ai_grade and final_grade
        connection.execute(text("""
            UPDATE submissions 
            SET ai_grade = grade,
                final_grade = grade
            WHERE ai_grade IS NULL AND grade IS NOT NULL
        """))
        
        # Migrate existing feedback to ai_feedback
        connection.execute(text("""
            UPDATE submissions 
            SET ai_feedback = feedback
            WHERE ai_feedback IS NULL AND feedback IS NOT NULL
        """))
        
        # Drop old columns after migration
        connection.execute(text("""
            ALTER TABLE submissions 
            DROP COLUMN IF EXISTS grade,
            DROP COLUMN IF EXISTS feedback
        """))
        
        connection.commit()
        print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration() 