import os
import sys
import sqlite3

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import DB_NAME

def nuke_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM security_alerts;")
        conn.commit()
        conn.close()
        print(f"DATABASE CLEANED ({DB_NAME}). SENTRY is now in a clean state.")
    except Exception as e:
        print(f"Error nuking database: {e}")

if __name__ == "__main__":
    nuke_db()
