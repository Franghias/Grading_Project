from migrations.add_class_columns import upgrade
from app.database import engine
from sqlalchemy import text

def run_prompt_migration():
    with engine.connect() as conn:
        # Rename table if it exists
        conn.execute(text('''
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'grading_codes') THEN
                    ALTER TABLE grading_codes RENAME TO grading_prompts;
                END IF;
            END$$;
        '''))
        # Rename column if it exists
        conn.execute(text('''
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'grading_prompts' AND column_name = 'code') THEN
                    ALTER TABLE grading_prompts RENAME COLUMN code TO prompt;
                END IF;
            END$$;
        '''))

if __name__ == "__main__":
    print("Running database migration...")
    upgrade()
    run_prompt_migration()
    print("Migration completed successfully!") 