from migrations.add_class_columns import upgrade

if __name__ == "__main__":
    print("Running database migration...")
    upgrade()
    print("Migration completed successfully!") 