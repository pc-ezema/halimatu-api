# scripts/create_tables.py
from app.database.database import Base, engine

Base.metadata.create_all(bind=engine)
print("Database tables created successfully.")