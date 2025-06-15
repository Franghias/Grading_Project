import os
from app.database import Base, engine
from app.models import *  # This imports all models
from app.migrations.add_class_columns import upgrade

def run_migrations():
    print("Starting database migrations...")
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Run specific migrations
    print("Running additional migrations...")
    upgrade()
    
    print("All migrations completed successfully!")

if __name__ == "__main__":
    run_migrations() 