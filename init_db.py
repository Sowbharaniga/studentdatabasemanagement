# init_db.py
from app import Base, engine

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
