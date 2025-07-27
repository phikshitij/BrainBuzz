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

def add_notice_tables():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Create notices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200),
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                teacher_id INT,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB;
        ''')
        # Create notice_recipients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notice_recipients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                notice_id INT,
                student_id INT,
                FOREIGN KEY (notice_id) REFERENCES notices(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        ''')
        conn.commit()
        print("Successfully added notices and notice_recipients tables.")
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
    add_notice_tables() 