import pandas as pd
import argparse
import os
from backtest import run_backtest

def main():
    # 1. Setup Command Line Arguments
    parser = argparse.ArgumentParser(description="Run Trading Bot Backtest")
    parser.add_argument(
        "--file", 
        type=str, 
        default="XRP-USD_candles.csv", 
        help="The CSV file to use for historical data"
    )
    args = parser.parse_args()

    # 2. Check if file exists
    if not os.path.exists(args.file):
        print(f"❌ Error: Could not find file '{args.file}'")
        return

    # 3. Load the data
    print(f"📂 Loading data from {args.file}...")
    df = pd.read_csv(args.file)

    # --- THE CRITICAL FIX ---
    # We must assign the sorted result back to 'df' 
    # and use 'inplace=True' or 'df = ...'
    if 'start' in df.columns:
        df['start'] = pd.to_numeric(df['start']) # Ensure timestamps are numbers
        df = df.sort_values(by='start', ascending=True).reset_index(drop=True)
        print("✅ Data sorted chronologically (Oldest to Newest).")
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_numeric(df['timestamp'])
        df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        print("✅ Data sorted chronologically by timestamp.")

    # 4. Convert Rows to Dictionaries
    candle_list = []
    
    if list(df.columns) == ['0']:
        print("❌ Error: The CSV file has no headers.")
        return

    for _, row in df.iterrows():
        candle_list.append({
            'start': row.get('start', row.get('timestamp', row.get('time'))),
            'low': float(row.get('low', row.get('price_low'))),
            'high': float(row.get('high', row.get('price_high'))),
            'open': float(row.get('open', row.get('price_open'))),
            'close': float(row.get('close', row.get('price_close'))),
            'volume': float(row.get('volume', row.get('base_volume')))
        })

    # 5. Run the Backtest
    print(f"🚀 Starting simulation on {len(candle_list)} candles...")
    trades = run_backtest(candle_list, initial_balance=1000, risk_percent=1.0)
    
    print("✅ Backtest complete. Check trade_journal.csv for details.")

if __name__ == "__main__":
    main()