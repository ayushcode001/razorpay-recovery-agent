"""
SQLAlchemy Engine & Session configuration for Razorpay Recovery Agent.
Reads DATABASE_URL from environment with postgres:// compatibility fix for Render.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Render provides 'postgres://', which SQLAlchemy 1.4+ deprecated in favor of 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        print(f"[DB] Warning: Failed to create database engine from DATABASE_URL: {e}")
        engine = None
        SessionLocal = None


def is_db_configured() -> bool:
    """Returns True if a valid database connection is available."""
    return SessionLocal is not None


@contextmanager
def get_db_session():
    """Context manager for safe SQLAlchemy session lifecycle management."""
    if not is_db_configured():
        raise RuntimeError("Database is not configured. Set DATABASE_URL environment variable.")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
