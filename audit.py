import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_MODE, DB_NAME, SUPABASE_URL, SUPABASE_KEY

def _get_sb():
    if DB_MODE == "supabase" and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except:
            pass
    return None

def _ensure_tenant_col(conn):
    try:
        conn.execute("ALTER TABLE audit_log ADD COLUMN tenant_id INTEGER DEFAULT 1")
        conn.commit()
    except:
        pass

def log_audit(username, action, table_name, record_id="", details="", tenant_id=None):
    ts = str(datetime.now())
    tid = tenant_id if tenant_id is not None else 1
    if DB_MODE == "supabase":
        sb = _get_sb()
        if sb:
            try:
                sb.table("audit_log").insert({
                    "timestamp": ts, "username": username, "action": action,
                    "table_name": table_name, "record_id": str(record_id),
                    "details": str(details), "tenant_id": tid
                }).execute()
                return
            except:
                pass
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS audit_log ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, username TEXT, "
        "action TEXT, table_name TEXT, record_id TEXT, details TEXT, "
        "tenant_id INTEGER DEFAULT 1)")
    _ensure_tenant_col(conn)
    c.execute(
        "INSERT INTO audit_log VALUES (NULL,?,?,?,?,?,?,?)",
        (ts, username, action, table_name, str(record_id), str(details), tid))
    conn.commit()
    conn.close()

def get_audit_log(tenant_id=None, limit=500):
    if DB_MODE == "supabase":
        sb = _get_sb()
        if sb:
            try:
                q = sb.table("audit_log").select("*").order("timestamp", desc=True).limit(limit)
                if tenant_id is not None:
                    q = q.eq("tenant_id", tenant_id)
                r = q.execute()
                return pd.DataFrame(r.data)
            except:
                pass
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS audit_log ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, username TEXT, "
        "action TEXT, table_name TEXT, record_id TEXT, details TEXT, "
        "tenant_id INTEGER DEFAULT 1)")
    _ensure_tenant_col(conn)
    if tenant_id is not None:
        df = pd.read_sql_query(
            "SELECT * FROM audit_log WHERE tenant_id=? ORDER BY timestamp DESC LIMIT ?",
            conn, params=(tenant_id, limit))
    else:
        df = pd.read_sql_query(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            conn, params=(limit,))
    conn.close()
    return df