import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Get database configuration from environment variables
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_HOST = os.getenv("MYSQL_HOST")
DB_NAME = os.getenv("MYSQL_DB")

def upgrade():
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        with connection.cursor() as cursor:
            # Check if column exists
            cursor.execute("SHOW COLUMNS FROM answers LIKE 'is_peer_review'")
            if not cursor.fetchone():
                # Add is_peer_review column
                cursor.execute("""
                    ALTER TABLE answers 
                    ADD COLUMN is_peer_review BOOLEAN DEFAULT FALSE
                """)
                print("Successfully added is_peer_review column")
            else:
                print("Column is_peer_review already exists")
        
        # Commit the changes
        connection.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    upgrade() 