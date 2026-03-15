import os
import sqlite3

# Absolute path for the database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "sentry.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Create the security_alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_alerts (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_ip TEXT,
            raw_payload TEXT,
            ai_analysis TEXT,
            mitre_mapping TEXT,
            severity TEXT,
            human_action TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

def insert_alert(id: str, source_ip: str, raw_payload: str, ai_analysis: str, mitre_mapping: str, severity: str, human_action: str = 'PENDING'):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO security_alerts (id, source_ip, raw_payload, ai_analysis, mitre_mapping, severity, human_action)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (id, source_ip, raw_payload, ai_analysis, mitre_mapping, severity, human_action))
    conn.commit()
    conn.close()

def update_human_action(id_val: str, action: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE security_alerts SET human_action = ? WHERE id = ?
    ''', (action, id_val))
    conn.commit()
    conn.close()

def get_alert_by_id(id_val: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM security_alerts WHERE id = ?
    ''', (id_val,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_latest_alerts(limit: int = 50):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM security_alerts ORDER BY timestamp DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def check_duplicate_alert(source_ip: str, raw_payload: str, seconds: int = 60):
    """Checks if an identical alert from the same IP was received in the last N seconds."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Using datetime with '-' modifier to look back in time
    cursor.execute('''
        SELECT id FROM security_alerts 
        WHERE source_ip = ? AND raw_payload = ? AND timestamp > datetime('now', ?)
    ''', (source_ip, raw_payload, f'-{seconds} seconds'))
    duplicate = cursor.fetchone()
    conn.close()
    return duplicate is not None

if __name__ == "__main__":
    init_db()
    print("Database sentry.db initialized successfully.")

