import sqlite3, json
from datetime import datetime
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, timestamp TEXT,
        event_type TEXT, data TEXT, risk_score REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, timestamp TEXT,
        alert_type TEXT, message TEXT, severity TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS live_data (
        key TEXT PRIMARY KEY, value TEXT, ts TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE, start_time TEXT)""")

    # Clear old data every time app starts fresh
    c.execute("DELETE FROM live_data")
    c.execute("DELETE FROM alerts")

    conn.commit()
    conn.close()

def create_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO sessions (session_id, start_time) VALUES (?,?)",
              (session_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def set_live(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO live_data (key,value,ts) VALUES(?,?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value,ts=excluded.ts""",
        (key, json.dumps(value), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_live(key, default=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM live_data WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else default

def log_event(session_id, event_type, data, risk_score=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO events VALUES(NULL,?,?,?,?,?)",
        (session_id, datetime.now().isoformat(),
         event_type, json.dumps(data), risk_score))
    conn.commit()
    conn.close()

def log_alert(session_id, alert_type, message, severity):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO alerts VALUES(NULL,?,?,?,?,?)",
        (session_id, datetime.now().isoformat(),
         alert_type, message, severity))
    conn.commit()
    conn.close()

def get_recent_alerts(limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT timestamp, alert_type, message, severity
                 FROM alerts ORDER BY id DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows