"""Drop and recreate the development SQLite database."""
import os
import models

if __name__ == "__main__":
    if os.path.exists(models.DB_PATH):
        os.remove(models.DB_PATH)
    models.init_db()
    print(f"Fresh database created at {models.DB_PATH}")
