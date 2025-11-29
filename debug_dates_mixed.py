import pandas as pd
import datetime

def test_dates_mixed():
    print("Testing mixed date formats with format='mixed'...")
    
    dates = [
        "2025-11-28 15:09:54",          
        "2025-11-28T20:09:33.987Z",     
        "2025-11-28T20:04:12.544Z",     
        "2025-11-28 15:04:11",          
        "2025-11-28T15:00:00Z"          
    ]
    
    df = pd.DataFrame({'timestamp': dates})
    
    try:
        # Try with format='mixed'
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce', format='mixed')
        
        print("\nConverted (DT):")
        print(df['timestamp_dt'])
        
        if df['timestamp_dt'].isna().any():
            print("\nWARNING: Some dates still failed!")
        else:
            print("\nSUCCESS: All dates parsed with format='mixed'.")
            
    except Exception as e:
        print(f"\nError with format='mixed': {e}")
        print("Trying manual cleanup strategy...")
        
        # Fallback strategy: Clean string first
        # Remove T and Z
        df['timestamp_clean'] = df['timestamp'].astype(str).str.replace('T', ' ').str.replace('Z', '')
        print("\nCleaned strings:")
        print(df['timestamp_clean'])
        
        df['timestamp_dt'] = pd.to_datetime(df['timestamp_clean'], utc=True, errors='coerce')
        print("\nConverted (DT) after cleanup:")
        print(df['timestamp_dt'])

if __name__ == "__main__":
    test_dates_mixed()
