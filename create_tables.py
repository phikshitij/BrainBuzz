# c:/Users/kshit/OneDrive/Desktop/Piazza/backend/create_tables.py
from database import Base, engine
import models # Make sure models.py is in the same directory or accessible

print("Attempting to create tables...")
Base.metadata.create_all(bind=engine)
print("All tables should be created (if they didn't exist already)!")
