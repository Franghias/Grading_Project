from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import time
import logging
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

logger.info(f"Attempting to connect to database at {POSTGRES_HOST}:{POSTGRES_PORT}")
logger.info(f"Using database: {POSTGRES_DB}")
logger.info(f"Using user: {POSTGRES_USER}")
logger.info(f"Using password: {POSTGRES_PASSWORD}")

# Create engine with connection pool settings and explicit authentication
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,         # Set connection pool size
    max_overflow=10,     # Maximum number of connections that can be created beyond pool_size
    pool_timeout=30,     # Seconds to wait before giving up on getting a connection from the pool
    pool_recycle=1800,   # Recycle connections after 30 minutes
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "application_name": "grading_app",  # Identify our application
        "client_encoding": "utf8",
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """
    Get database session with automatic cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection(max_retries=5, retry_delay=5):
    """
    Test database connection with retries and detailed error reporting.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Testing database connection (attempt {attempt + 1}/{max_retries})")
            # Try to connect to the database
            with engine.connect() as connection:
                # Execute a simple query to verify connection
                connection.execute("SELECT 1")
                logger.info("Database connection successful!")
                return True
        except OperationalError as e:
            error_msg = str(e)
            logger.error(f"Database connection failed (attempt {attempt + 1}/{max_retries})")
            logger.error(f"Error details: {error_msg}")
            
            # Provide specific troubleshooting advice based on the error
            if "password authentication failed" in error_msg.lower():
                logger.error("Authentication failed. Please check:")
                logger.error("1. The POSTGRES_PASSWORD in your .env file")
                logger.error("2. The pg_hba.conf file authentication method")
                logger.error("3. The user permissions in PostgreSQL")
            elif "could not connect to server" in error_msg.lower():
                logger.error("Connection failed. Please check:")
                logger.error("1. PostgreSQL service is running")
                logger.error("2. The POSTGRES_HOST and POSTGRES_PORT in your .env file")
                logger.error("3. Any firewall settings blocking the connection")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Could not connect to database.")
                raise
        except SQLAlchemyError as e:
            logger.error(f"Unexpected database error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {str(e)}")
            raise

# Test the connection when the module is imported
try:
    test_db_connection()
except Exception as e:
    logger.error(f"Failed to establish database connection: {str(e)}")
    raise