#!/usr/bin/env python3
"""Migration script to make s3_bucket and s3_key nullable in files table."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.db import get_connection

def migrate_files_table():
    """Alter files table to make s3_bucket and s3_key nullable."""
    print("Migrating files table...")
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Check if columns are already nullable
                cur.execute("""
                    SELECT column_name, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'files' 
                    AND column_name IN ('s3_bucket', 's3_key')
                """)
                columns = cur.fetchall()
                
                for col in columns:
                    col_name = col['column_name']
                    is_nullable = col['is_nullable']
                    if is_nullable == 'NO':
                        print(f"  Making {col_name} nullable...")
                        cur.execute(f"ALTER TABLE files ALTER COLUMN {col_name} DROP NOT NULL")
                    else:
                        print(f"  {col_name} is already nullable")
                
                print("✅ Migration completed successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_files_table()
    sys.exit(0 if success else 1)

