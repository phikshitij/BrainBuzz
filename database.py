from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

print("Attempting to load .env file...")
# You can specify the path to .env if it's not being found, e.g., load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
if load_dotenv():
    print(".env file loaded successfully.")
else:
    print(".env file NOT loaded or is empty.") # This could be an issue

MYSQL_USER = os.getenv("MYSQL_USER", "piazza_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "PiazzaPass123!")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "piazza")

# --- DEBUGGING PRINTS ---
print(f"Attempting to connect with the following credentials:")
print(f"  User: '{MYSQL_USER}' (Type: {type(MYSQL_USER)})")
print(f"  Password: '{MYSQL_PASSWORD[:2]}...{MYSQL_PASSWORD[-2:] if MYSQL_PASSWORD and len(MYSQL_PASSWORD) > 4 else '******'}' (Length: {len(MYSQL_PASSWORD) if MYSQL_PASSWORD else 0}, Type: {type(MYSQL_PASSWORD)})") # Print only parts of password for security
print(f"  Host: '{MYSQL_HOST}' (Type: {type(MYSQL_HOST)})")
print(f"  Database: '{MYSQL_DB}' (Type: {type(MYSQL_DB)})")
# --- END DEBUGGING PRINTS ---

if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB]):
    print("!!! WARNING: One or more database connection parameters are missing from environment variables. !!!")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()