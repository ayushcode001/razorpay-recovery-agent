"""
Database Initialization & Seeding Script.
Idempotent script to create tables and seed default merchant + threshold configuration.
Safe to run on every deploy.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.db import engine, SessionLocal, is_db_configured
from agent.db_models import Base, Merchant, ThresholdConfig, PolicyChangeProposal, AuditTrailEntry


def init_database():
    """Creates tables and seeds default merchant and configuration."""
    if not is_db_configured() or engine is None:
        print("[Init DB] DATABASE_URL not set or invalid. Skipping database initialization.")
        return

    print("[Init DB] Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    print("[Init DB] Tables verified/created successfully.")

    session = SessionLocal()
    try:
        # 1. Seed demo merchant
        demo_merchant = session.query(Merchant).filter_by(id=1).first()
        if not demo_merchant:
            demo_merchant = Merchant(id=1, name="demo_merchant")
            session.add(demo_merchant)
            session.commit()
            print("[Init DB] Seeded default merchant: 'demo_merchant' (id=1).")
        else:
            print(f"[Init DB] Default merchant already exists: '{demo_merchant.name}' (id={demo_merchant.id}).")

        # 2. Seed threshold config
        config = session.query(ThresholdConfig).filter_by(merchant_id=1).first()
        if not config:
            config = ThresholdConfig(
                merchant_id=1,
                success_threshold=0.47,
                uplift_gate_threshold=0.05,
            )
            session.add(config)
            session.commit()
            print("[Init DB] Seeded default threshold configuration (success=0.47, uplift=0.05).")
        else:
            print(f"[Init DB] Threshold configuration exists (success={config.success_threshold}, uplift={config.uplift_gate_threshold}).")

    except Exception as e:
        session.rollback()
        print(f"[Init DB] Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_database()
