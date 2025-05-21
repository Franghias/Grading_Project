from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get database URL with fallback
DATABASE_URL = os.getenv("POSTGRESQL_URL")
if not DATABASE_URL:
    # Fallback to default development database URL
    DATABASE_URL = "postgresql://grading_user:securepassword@localhost:5432/grading_db"
    print(f"Warning: DATABASE_URL not found in environment, using default: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    # Test the connection
    with engine.connect() as conn:
        print("Successfully connected to the database!")
except Exception as e:
    print(f"Error connecting to database: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()