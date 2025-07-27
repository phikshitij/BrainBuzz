import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'piazza_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'PiazzaPass123!'),
    'db': os.getenv('MYSQL_DB', 'piazza')
}

def add_timestamp_column():
    try:
        # Connect to MySQL
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Add the timestamp column
        cursor.execute("""
            ALTER TABLE answers 
            ADD COLUMN timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        
        # Commit the changes
        conn.commit()
        print("Successfully added timestamp column")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_timestamp_column() 