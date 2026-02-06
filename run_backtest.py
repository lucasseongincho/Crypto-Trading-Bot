import argparse
import os
import pandas as pd
from backtest import run_backtest

def main():
    # 1. Setup Command Line Arguments
    parser = argparse.ArgumentParser(description="Universal SMC Strategy Backtest")
    parser.add_argument(
        "--file", 
        type=str, 
        default="BTC-USD_candles.csv", 
        help="The CSV file to use for historical data"
    )
    args = parser.parse_args()

    # 2. Check if file exists
    if not os.path.exists(args.file):
        print(f"❌ Error: Could not find file '{args.file}'")
        return

    # --- 3. UNIVERSAL ASSET DETECTION ---
    # Extracts "BTC-USD" from "BTC-USD_candles.csv"
    base_name = os.path.basename(args.file).replace(".csv", "")
    pair = base_name.split('_')[0].upper() 
    
    print(f"📂 Loading data for: {pair} from {args.file}...")
    df = pd.read_csv(args.file)

    # 4. Sorting logic (Ensures oldest data is first)
    if 'start' in df.columns:
        df['start'] = pd.to_numeric(df['start'])
        df = df.sort_values(by='start', ascending=True).reset_index(drop=True)
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_numeric(df['timestamp'])
        df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
    
    print("✅ Data sorted chronologically.")

    # 5. Column Mapping & Optimization
    # This aligns CSV headers with what strategy.py and backtest.py expect
    column_mapping = {
        'timestamp': 'start', 'time': 'start',
        'price_low': 'low', 'price_high': 'high',
        'price_open': 'open', 'price_close': 'close',
        'base_volume': 'volume'
    }
    df = df.rename(columns=column_mapping)
    
    # Required columns for SMC logic
    required_cols = ['start', 'low', 'high', 'open', 'close']
    
    # Ensure all required columns exist
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"❌ Error: Missing columns in CSV: {missing}")
        return

    # Convert DataFrame to a list of dictionaries for high-speed looping
    candle_list = df[required_cols].to_dict('records')

    # 6. Run the Universal Backtest
    print(f"🚀 Starting simulation on {len(candle_list)} candles for {pair}...")
    
    trades, final_report_name = run_backtest(
        candle_list, 
        product_id=pair, 
        initial_balance=1000, 
        risk_percent=1.0
    )

    print("-" * 40)
    print(f"✅ Backtest complete for {pair}!")
    print(f"📄 Full trade log saved to: {final_report_name}")
    print(f"💡 Run 'python performance_summary.py --file {final_report_name}' for results.")
    print("-" * 40)

if __name__ == "__main__":
    main()