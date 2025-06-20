import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('app.log')  # File handler
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Get the absolute path of the app directory
APP_DIR = Path(__file__).resolve().parent

# Log the initialization
logger.info("Initializing application...")
# logger.info("Application directory: {APP_DIR}")

# Import key components to make them available when importing the package
from . import models
from . import schemas
from . import database
from . import grading

logger.info("Application initialization complete!")
