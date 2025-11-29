import asyncio
import pandas as pd
import sqlite3
import datetime
from io import BytesIO

# Mock data
DB_FILE = "test_db.sqlite"

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
    
    cursor.execute(f'''
        INSERT INTO stock_counts (session_id, timestamp, item_code, item_description, counted_qty, counted_location, bin_location_system, username)
        VALUES ({session_id}, '{datetime.datetime.now().isoformat()}', 'ITEM001', 'Test Item', 10, 'LOC1', 'BIN1', 'user1')
    ''')
    
    conn.commit()
    conn.close()

async def test_export_logic():
    print("Testing export logic...")
    
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

    # 2. Mock master_qty_map
    master_qty_map = {'ITEM001': 5}
    
    # 3. Apply logic (copied from app.py)
    # Mock session map
    session_map = {1: 'user1'}
    df['username'] = df['username'].fillna(df['session_id'].map(session_map))
    
    # System Qty
    df['system_qty'] = df['item_code'].map(master_qty_map)
    df['counted_qty'] = pd.to_numeric(df['counted_qty'], errors='coerce').fillna(0).astype(int)
    df['system_qty_numeric'] = pd.to_numeric(df['system_qty'], errors='coerce')
    df['difference'] = df['counted_qty'] - df['system_qty_numeric']
    del df['system_qty_numeric']
    
    # Timestamp (Simulate TZ)
    tz = "America/Bogota"
    try:
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
        df['timestamp'] = df['timestamp_dt'].dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"TZ Error: {e}")

    # Illegal chars
    illegal_chars_pattern = r'[\x00-\x08\x0B\x0C\x0E-\x1F]'
    str_cols = df.select_dtypes(include=['object']).columns
    if not str_cols.empty:
        df[str_cols] = df[str_cols].replace(illegal_chars_pattern, ' ', regex=True)
        
    # Reorder
    columns_order = [
        'id', 'session_id', 'inventory_stage', 'username', 'timestamp', 
        'item_code', 'item_description', 'counted_location', 
        'counted_qty', 'system_qty', 'difference', 'bin_location_system'
    ]
    for col in columns_order:
        if col not in df.columns:
            df[col] = None
    df = df[columns_order]
    
    print("DataFrame processed successfully:")
    print(df.head())
    
    # Verify Excel generation
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Conteos')
    print("Excel generated successfully.")

if __name__ == "__main__":
    init_test_db()
    asyncio.run(test_export_logic())
