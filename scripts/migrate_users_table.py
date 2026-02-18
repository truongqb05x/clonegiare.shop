import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db import get_db_connection

def migrate_users_table():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    try:
        cursor = conn.cursor()
        print("Migrating users table...")

        # Add fullname column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN fullname VARCHAR(100) DEFAULT NULL")
            print("- Added 'fullname' column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("- 'fullname' column already exists.")
            else:
                print(f"Error adding 'fullname': {e}")

        # Add phone column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT NULL")
            print("- Added 'phone' column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("- 'phone' column already exists.")
            else:
                print(f"Error adding 'phone': {e}")

        # Add telegram_id column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN telegram_id VARCHAR(50) DEFAULT NULL")
            print("- Added 'telegram_id' column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("- 'telegram_id' column already exists.")
            else:
                print(f"Error adding 'telegram_id': {e}")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_users_table()
