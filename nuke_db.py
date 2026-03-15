import sqlite3

DB_NAME = "sentry.db"

def nuke_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM security_alerts;")
        conn.commit()
        conn.close()
        print("DATABASE CLEANED. SENTRY is now in a clean state.")
    except Exception as e:
        print(f"Error nuking database: {e}")

if __name__ == "__main__":
    nuke_db()
