import csv
import datetime as dt
from datetime import timezone
from client import public_client

PRODUCT = 'ETH-USD'
# How many days of data do you want?
DAYS_BACK = 14 

def download_history():
    print(f"Downloading last {DAYS_BACK} days of data for {PRODUCT}...")
    
    end_time = dt.datetime.now(timezone.utc)
    start_time = end_time - dt.timedelta(days=DAYS_BACK)
    
    try:
        raw = public_client.get_candles(
            product_id=PRODUCT,
            start=str(int(start_time.timestamp())),
            end=str(int(end_time.timestamp())),
            granularity='FIVE_MINUTE'
        )
        
        # Sort by timestamp (oldest first)
        candles = sorted(raw.candles, key=lambda x: int(x.start))
        
        with open('historical_data.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['timestamp', 'low', 'high', 'open', 'close', 'volume'])
            
            for c in candles:
                writer.writerow([c.start, c.low, c.high, c.open, c.close, c.volume])
        
        print(f"Success! Saved {len(candles)} candles to historical_data.csv")
        
    except Exception as e:
        print(f"Failed to download: {e}")

if __name__ == "__main__":
    download_history()