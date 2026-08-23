import sqlite3
import csv
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "enrichment.db"
DDL_PATH = BASE_DIR / "config" / "enriched_rows_ddl.sql"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    from backend.schemas import GOLDEN_RECORD_COLUMNS
    headers = GOLDEN_RECORD_COLUMNS

    # 2. Generate DDL
    ddl_lines = [
        "CREATE TABLE IF NOT EXISTS enriched_rows (",
        "  row_id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "  project_id INTEGER,",
        "  status TEXT,",
        "  confidence_score REAL,",
        "  needs_human_review INTEGER,",
        "  review_reason TEXT,"
    ]
    for h in headers:
        # Quote column names to handle spaces
        ddl_lines.append(f"  \"{h}\" TEXT,")
    
    # Remove trailing comma on last line
    ddl_lines[-1] = ddl_lines[-1].rstrip(',')
    ddl_lines.append(");")
    
    ddl = "\n".join(ddl_lines)
    
    os.makedirs(DDL_PATH.parent, exist_ok=True)
    with open(DDL_PATH, "w", encoding='utf-8') as f:
        f.write(ddl)

    # 3. Create tables
    conn = get_db()
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        filename TEXT,
        status TEXT,
        total_rows INTEGER,
        processed_rows INTEGER,
        confirmed_mapping TEXT,
        created_at TEXT
    );
    """)
    
    cursor.execute(ddl)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        row_id INTEGER,
        field_name TEXT,
        source_type TEXT,
        source_url TEXT,
        field_confidence REAL
    );
    """)
    
    conn.commit()
    conn.close()

def insert_row(table: str, data: dict) -> int:
    conn = get_db()
    cursor = conn.cursor()
    columns = ', '.join(f'"{k}"' for k in data.keys())
    placeholders = ', '.join('?' for _ in data)
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.execute(query, tuple(data.values()))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id

def update_row_status(row_id: int, status: str, needs_human_review: int = 0, review_reason: str = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE enriched_rows SET status=?, needs_human_review=?, review_reason=? WHERE row_id=?",
        (status, needs_human_review, review_reason, row_id)
    )
    conn.commit()
    conn.close()

def get_project_rows(project_id: int, limit: int = 50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enriched_rows WHERE project_id=? LIMIT ?", (project_id, limit))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_all_projects():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects

def update_project_status(project_id: int, status: str, total_rows: int = None):
    conn = get_db()
    cursor = conn.cursor()
    if total_rows is not None:
        cursor.execute("UPDATE projects SET status=?, total_rows=? WHERE project_id=?", (status, total_rows, project_id))
    else:
        cursor.execute("UPDATE projects SET status=? WHERE project_id=?", (status, project_id))
    conn.commit()
    conn.close()

def update_project_filename(project_id: int, filename: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET filename=? WHERE project_id=?", (filename, project_id))
    conn.commit()
    conn.close()

def update_project_mapping(project_id: int, mapping_json: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET confirmed_mapping=? WHERE project_id=?", (mapping_json, project_id))
    conn.commit()
    conn.close()
