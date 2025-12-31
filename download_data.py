import csv
import time
import datetime as dt
from datetime import timezone
from client import public_client

PRODUCT = 'ETH-USD'
DAYS_BACK = 14 
# Granularity in seconds (300 = 5 minutes)
GRANULARITY_SECONDS = 300 
# Max candles per request allowed by Coinbase
MAX_CANDLES = 300 

def download_history():
    print(f"Downloading last {DAYS_BACK} days of data for {PRODUCT} in chunks...")
    
    all_candles = []
    end_date = dt.datetime.now(timezone.utc)
    start_date = end_date - dt.timedelta(days=DAYS_BACK)
    
    # We move 'current_start' forward chunk by chunk
    current_start = start_date
    
    while current_start < end_date:
        # Calculate end of this specific chunk (300 candles later)
        chunk_end = current_start + dt.timedelta(seconds=MAX_CANDLES * GRANULARITY_SECONDS)
        
        # Ensure we don't request the future
        if chunk_end > end_date:
            chunk_end = end_date
            
        print(f"Fetching: {current_start.strftime('%Y-%m-%d %H:%M')} to {chunk_end.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            raw = public_client.get_candles(
                product_id=PRODUCT,
                start=str(int(current_start.timestamp())),
                end=str(int(chunk_end.timestamp())),
                granularity='FIVE_MINUTE'
            )
            
            if hasattr(raw, 'candles') and raw.candles:
                all_candles.extend(raw.candles)
            
            # Move start time forward for next loop
            current_start = chunk_end
            
            # Small pause to avoid hitting Coinbase rate limits
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"Error in chunk: {e}")
            break

    # Save to CSV
    if all_candles:
        # Sort by timestamp to ensure chronological order
        all_candles.sort(key=lambda x: int(x.start))
        
        with open('historical_data.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'low', 'high', 'open', 'close', 'volume'])
            for c in all_candles:
                writer.writerow([c.start, c.low, c.high, c.open, c.close, c.volume])
        
        print(f"Success! Saved {len(all_candles)} candles to historical_data.csv")
    else:
        print("No data collected.")

if __name__ == "__main__":
    download_history()