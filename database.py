"""
InvestIQ Phase 2 - Database Connection

SQLAlchemy engine + session setup, pointed at Supabase's Postgres instance
(Supabase is just managed Postgres underneath - this is standard
SQLAlchemy, nothing Supabase-specific about the connection itself).

Get your connection string from the Supabase dashboard:
    Project Settings > Database > Connection string > URI
    (use the "Session pooler" or "Transaction pooler" string for serverless-
    friendly connections, or the direct connection string for local dev)

Then in .env:
    DATABASE_URL=postgresql://postgres.xxxxx:[password]@aws-0-region.pooler.supabase.com:5432/postgres
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set in .env. Get it from your Supabase dashboard: "
        "Project Settings > Database > Connection string > URI"
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency - yields a DB session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()