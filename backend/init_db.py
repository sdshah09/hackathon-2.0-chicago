#!/usr/bin/env python3
"""Initialize the database by running schema.sql"""

from utils.db import init_db

if __name__ == "__main__":
    print("Initializing database...")
    try:
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

