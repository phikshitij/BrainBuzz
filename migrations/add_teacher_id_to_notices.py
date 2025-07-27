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

def add_teacher_id_column():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Check if teacher_id column exists
        cursor.execute("SHOW COLUMNS FROM notices LIKE 'teacher_id';")
        result = cursor.fetchone()
        if not result:
            cursor.execute('''
                ALTER TABLE notices ADD COLUMN teacher_id INT;
            ''')
            print("Added teacher_id column to notices table.")
        else:
            print("teacher_id column already exists in notices table.")
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
    add_teacher_id_column() 