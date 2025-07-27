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

def print_notices_and_recipients():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("\n--- notices ---")
        cursor.execute("SELECT * FROM notices;")
        for row in cursor.fetchall():
            print(row)
        print("\n--- notice_recipients ---")
        cursor.execute("SELECT * FROM notice_recipients;")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print_notices_and_recipients() 