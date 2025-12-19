import time
import datetime as dt 
from datetime import timezone
from auth import private_client
from client import public_client
# ... other imports remain the same

# Global variable to store our historical "memory"
global_candles = []

def sync_candles():
    """
    Initializes or updates the global candle list.
    """
    global global_candles
    
    # 1. If empty, fetch the initial 24h history
    if not global_candles:
        print("Initializing historical data (24h)...")
        start_time = dt.datetime.now(timezone.utc) - dt.timedelta(hours=24)
        raw = public_client.get_candles(
            product_id=PRODUCT, 
            start=str(int(start_time.timestamp())),
            end=str(int(dt.datetime.now(timezone.utc).timestamp())),
            granularity='FIVE_MINUTE'
        )
        global_candles = sorted(raw.candles, key=lambda x: int(x.start))
        return

    # 2. Otherwise, only fetch the most recent 2 candles to catch the latest close
    try:
        # Fetch a very small window (last 10 mins)
        start_patch = dt.datetime.now(timezone.utc) - dt.timedelta(minutes=10)
        patch_raw = public_client.get_candles(
            product_id=PRODUCT,
            start=str(int(start_patch.timestamp())),
            end=str(int(dt.datetime.now(timezone.utc).timestamp())),
            granularity='FIVE_MINUTE'
        )
        new_candles = sorted(patch_raw.candles, key=lambda x: int(x.start))

        # Merge and remove duplicates based on timestamp
        existing_ts = {c.start for c in global_candles}
        for nc in new_candles:
            if nc.start not in existing_ts:
                global_candles.append(nc)
        
        # Keep only the last 300 candles to save memory
        global_candles = global_candles[-300:]
        
    except Exception as e:
        print(f"Sync Error: {e}")

def run_strategy():
    sync_candles() # Keep our memory up to date
    
    if len(global_candles) < 20: 
        return

    # Now use the global_candles list for strategy
    signal, structural_sl = generate_trade_signal(global_candles)
    # ... rest of your execution logic ...