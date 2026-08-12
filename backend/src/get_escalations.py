import os
import sqlite3
import json
import db

def main():
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # Check if escalations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='escalations'")
        if not cursor.fetchone():
            print("[]")
            return
        
        cursor.execute("SELECT * FROM escalations ORDER BY created_at DESC")
        rows = [dict(row) for row in cursor.fetchall()]
        print(json.dumps(rows))
    except Exception as e:
        print(json.dumps([]))
    finally:
        conn.close()

if __name__ == "__main__":
    main()
