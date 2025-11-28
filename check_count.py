import sqlite3
import os

db_path = 'inbound_log.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock_counts")
    count = cursor.fetchone()[0]
    print(f"Total rows in stock_counts: {count}")
    conn.close()
else:
    print("Database file not found.")
