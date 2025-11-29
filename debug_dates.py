import pandas as pd
import datetime

def test_dates():
    print("Testing mixed date formats...")
    
    # Mixed formats:
    # 1. ISO with milliseconds and Z (from screenshot)
    # 2. Naive string (from screenshot successful ones?)
    # 3. ISO without milliseconds
    
    dates = [
        "2025-11-28 15:09:54",          # Naive-looking (maybe already converted?)
        "2025-11-28T20:09:33.987Z",     # ISO with millis + Z
        "2025-11-28T20:04:12.544Z",     # ISO with millis + Z
        "2025-11-28 15:04:11",          # Naive-looking
        "2025-11-28T15:00:00Z"          # ISO no millis + Z
    ]
    
    df = pd.DataFrame({'timestamp': dates})
    
    print("Original:")
    print(df)
    
    try:
        # Attempt conversion as in app.py
        # utc=True is key here
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
        
        print("\nConverted (DT):")
        print(df['timestamp_dt'])
        
        # Check for NaT
        if df['timestamp_dt'].isna().any():
            print("\nWARNING: Some dates failed to parse!")
            print(df[df['timestamp_dt'].isna()])
        else:
            print("\nAll dates parsed successfully.")
            
        # Convert to TZ
        tz = "America/Bogota"
        df['timestamp_final'] = df['timestamp_dt'].dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        print("\nFinal (Bogota):")
        print(df['timestamp_final'])
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_dates()
