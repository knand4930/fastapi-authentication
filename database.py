#database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import settings
# Load environment variables from .env file
load_dotenv()

# Correct way to format the DATABASE_URL with the driver
DATABASE_URL = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_NAME}"

# Create an engine
engine = create_engine(DATABASE_URL,
    pool_size=20,   # Increase the number of connections
    max_overflow=10,  # Allow additional overflow
    pool_timeout=30,  # Time to wait before giving up
    pool_recycle=1800  # Recycle connections after 30 minutes
                       )


# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()