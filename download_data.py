import argparse
import os
import time
import pandas as pd
from datetime import datetime

# 1. IMPORT THE CLIENT (Ensure auth.py exists in the same folder)
try:
    from auth import client
except ImportError:
    print("❌ Error: Could not find 'auth.py'. Make sure it's in the same folder.")
    exit()

def download_data(product_id, start_date, end_date, granularity=300):
    """
    Downloads historical data in chunks and saves to a CSV.
    """
    # Setup File Path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, f"{product_id}_candles.csv")

    # Convert Dates to Unix Timestamps (Strings for Coinbase API)
    start_ts = str(int(datetime.strptime(start_date, "%Y-%m-%d").timestamp()))
    end_ts = str(int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()))
    
    all_candles = []
    current_start = int(start_ts)
    final_end = int(end_ts)

    print(f"🚀 Starting download for {product_id}...")
    print(f"Range: {start_date} to {end_date}")

    while current_start < final_end:
        # Calculate chunk end (300 candles max)
        chunk_end = min(current_start + (300 * granularity), final_end)
        
        try:
            # 2. UPDATED API CALL (Using str for timestamps as required by SDK)
            response = client.get_candles(
                product_id=product_id, 
                start=str(current_start), 
                end=str(chunk_end), 
                granularity="FIVE_MINUTE" # Standardizes the 300 (5min) granularity
            )
            
            # 3. EXTRACT DATA FROM RESPONSE OBJECT
            # The SDK returns an object; candles are inside the 'candles' key/attribute
            candles = response.get('candles', []) if isinstance(response, dict) else response.candles
            
            if candles:
                all_candles.extend(candles)
                print(f"✅ Fetched: {datetime.fromtimestamp(current_start)} -> {datetime.fromtimestamp(chunk_end)}")
            else:
                print(f"⚠️ Empty response for chunk starting {datetime.fromtimestamp(current_start)}")
                
        except Exception as e:
            print(f"❌ API Error: {e}")
            break
            
        current_start = chunk_end
        time.sleep(0.4) # Avoid Rate Limiting

   # 4. Save to CSV
    if all_candles:
        candle_data = [c.__dict__ if hasattr(c, '__dict__') else c for c in all_candles]
        df = pd.DataFrame(candle_data)
        
        # --- ADD THIS: Ensure data is saved oldest-to-newest ---
        if 'start' in df.columns:
            df['start'] = pd.to_numeric(df['start'])
            df = df.sort_values(by='start', ascending=True)
        
        df.to_csv(filename, index=False, header=True)
        print(f"\n📂 SUCCESS! Saved {len(df)} candles chronologically.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coinbase Data Downloader")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--pair", type=str, default="ETH-USD", help="Trading pair (default: ETH-USD)")
    
    args = parser.parse_args()
    download_data(args.pair, args.start, args.end)