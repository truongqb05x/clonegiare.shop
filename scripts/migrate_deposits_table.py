import mysql.connector
from src.config import Config

def migrate():
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()
        
        print("Checking deposits table structure...")
        
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM deposits LIKE 'is_notified'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding is_notified column...")
            cursor.execute("""
                ALTER TABLE deposits 
                ADD COLUMN is_notified BOOLEAN DEFAULT FALSE
            """)
            conn.commit()
            print("Migration successful: Added is_notified column.")
        else:
            print("Column is_notified already exists.")
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate()
