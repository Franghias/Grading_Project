from sqlalchemy import create_engine, text
from ..database import SQLALCHEMY_DATABASE_URL

def upgrade():
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Add new columns
    with engine.connect() as connection:
        # Add prerequisites column
        connection.execute(text("""
            ALTER TABLE classes 
            ADD COLUMN IF NOT EXISTS prerequisites TEXT;
        """))
        
        # Add learning_objectives column
        connection.execute(text("""
            ALTER TABLE classes 
            ADD COLUMN IF NOT EXISTS learning_objectives TEXT;
        """))
        
        connection.commit()

if __name__ == "__main__":
    upgrade() 