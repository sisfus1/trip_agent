import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use a local SQLite database file in the project directory
SQLALCHEMY_DATABASE_URL = "sqlite:///./trip_db.sqlite"

# By default, sqlite only allows one thread to communicate with it, but FastAPI uses multiple threads
# Check_same_thread=False overrides this behavior
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
