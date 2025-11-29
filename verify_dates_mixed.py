import asyncio
import pandas as pd
import sqlite3
import datetime
from io import BytesIO

# Mock data
DB_FILE = "test_db_dates_mixed.sqlite"

def init_test_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS count_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_username TEXT NOT NULL,
            inventory_stage INTEGER NOT NULL DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            item_code TEXT NOT NULL,
            item_description TEXT,
            counted_qty INTEGER NOT NULL,
            counted_location TEXT NOT NULL,
            bin_location_system TEXT,
            username TEXT,
            FOREIGN KEY(session_id) REFERENCES count_sessions(id)
        )
    ''')
    
    # Insert mock data
    cursor.execute("INSERT INTO count_sessions (user_username, inventory_stage) VALUES ('user1', 1)")
    session_id = cursor.lastrowid
    
    # 1. Valid timestamp
    cursor.execute(f'''
        INSERT INTO stock_counts (session_id, timestamp, item_code, item_description, counted_qty, counted_location, bin_location_system, username)
        VALUES ({session_id}, '{datetime.datetime.now().isoformat()}', 'ITEM001', 'Valid Date', 10, 'LOC1', 'BIN1', 'user1')
    ''')
    
    # 2. Invalid timestamp (should be preserved)
    cursor.execute(f'''
        INSERT INTO stock_counts (session_id, timestamp, item_code, item_description, counted_qty, counted_location, bin_location_system, username)
        VALUES ({session_id}, 'INVALID-DATE-STRING', 'ITEM002', 'Invalid Date', 5, 'LOC2', 'BIN2', 'user1')
    ''')
    
    # 3. Empty timestamp (should be preserved as empty)
    cursor.execute(f'''
        INSERT INTO stock_counts (session_id, timestamp, item_code, item_description, counted_qty, counted_location, bin_location_system, username)
        VALUES ({session_id}, '', 'ITEM003', 'Empty Date', 2, 'LOC3', 'BIN3', 'user1')
    ''')
    
    # 4. Mixed formats (ISO with Z and Naive) - THIS CAUSED THE ISSUE
    cursor.execute(f'''
        INSERT INTO stock_counts (session_id, timestamp, item_code, item_description, counted_qty, counted_location, bin_location_system, username)
        VALUES ({session_id}, '2025-11-28T20:09:33.987Z', 'ITEM004', 'ISO Date', 1, 'LOC4', 'BIN4', 'user1')
    ''')
    cursor.execute(f'''
        INSERT INTO stock_counts (session_id, timestamp, item_code, item_description, counted_qty, counted_location, bin_location_system, username)
        VALUES ({session_id}, '2025-11-28 15:09:54', 'ITEM005', 'Naive Date', 1, 'LOC5', 'BIN5', 'user1')
    ''')

    conn.commit()
    conn.close()

async def test_export_logic():
    print("Testing export logic with mixed date fix...")
    
    # 1. Simulate fetching data
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT 
            sc.id, sc.session_id, sc.timestamp, sc.item_code, sc.item_description, 
            sc.counted_qty, sc.counted_location, sc.bin_location_system, sc.username,
            cs.inventory_stage 
        FROM 
            stock_counts sc
        JOIN 
            count_sessions cs ON sc.session_id = cs.id
        ORDER BY sc.id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("DataFrame is empty!")
        return

    # Mock logic
    session_map = {1: 'user1'}
    df['username'] = df['username'].fillna(df['session_id'].map(session_map))
    
    # Timestamp Logic (The Fix applied in script to verify)
    tz = "America/Bogota"
    try:
        original_ts = df['timestamp'].copy()
        
        # USE format='mixed' HERE
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce', format='mixed')
        
        converted_ts = df['timestamp_dt'].dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df['timestamp'] = converted_ts.fillna(original_ts)
        
    except Exception as e:
        print(f"TZ Error: {e}")

    # Illegal chars
    illegal_chars_pattern = r'[\x00-\x08\x0B\x0C\x0E-\x1F]'
    str_cols = df.select_dtypes(include=['object']).columns
    if not str_cols.empty:
        df[str_cols] = df[str_cols].replace(illegal_chars_pattern, ' ', regex=True)
        
    print("DataFrame processed successfully:")
    print(df[['item_code', 'timestamp']])
    
    # Verify results
    item4_ts = df[df['item_code'] == 'ITEM004']['timestamp'].iloc[0]
    item5_ts = df[df['item_code'] == 'ITEM005']['timestamp'].iloc[0]
    
    print(f"ITEM004 TS: {item4_ts}")
    print(f"ITEM005 TS: {item5_ts}")
    
    # Check if ITEM004 was converted (should NOT be the original ISO string)
    assert 'T' not in item4_ts, "ITEM004 should be formatted (no T)"
    assert 'Z' not in item4_ts, "ITEM004 should be formatted (no Z)"
    
    # Check if ITEM005 was converted (should be formatted)
    assert 'T' not in item5_ts, "ITEM005 should be formatted"
    
    print("Verification Passed!")

if __name__ == "__main__":
    init_test_db()
    asyncio.run(test_export_logic())
