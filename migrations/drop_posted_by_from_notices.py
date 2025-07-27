import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'piazza_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'PiazzaPass123!'),
    'db': os.getenv('MYSQL_DB', 'piazza')
}

def drop_posted_by_column():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Check if posted_by column exists
        cursor.execute("SHOW COLUMNS FROM notices LIKE 'posted_by';")
        result = cursor.fetchone()
        if result:
            # Find and drop the foreign key constraint
            cursor.execute("SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME='notices' AND COLUMN_NAME='posted_by' AND CONSTRAINT_SCHEMA=DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL;")
            fk = cursor.fetchone()
            if fk:
                constraint_name = fk[0]
                cursor.execute(f"ALTER TABLE notices DROP FOREIGN KEY {constraint_name};")
                print(f"Dropped foreign key constraint {constraint_name} on posted_by.")
            cursor.execute('''
                ALTER TABLE notices DROP COLUMN posted_by;
            ''')
            print("Dropped posted_by column from notices table.")
        else:
            print("posted_by column does not exist in notices table.")
        conn.commit()
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
    drop_posted_by_column() 