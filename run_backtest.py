import pandas as pd
from backtest import run_backtest

# 1. Load the data
print("Loading historical_data.csv...")
df = pd.read_csv('historical_data.csv')

# 2. Convert Rows to Dictionaries (Matches live bot format)
# This maps the CSV columns back to the names your strategy expects
candle_list = []
for _, row in df.iterrows():
    candle_list.append({
        'start': row['timestamp'],
        'low': float(row['low']),
        'high': float(row['high']),
        'open': float(row['open']),
        'close': float(row['close']),
        'volume': float(row['volume'])
    })

# 3. Run the Backtest
print(f"Starting simulation on {len(candle_list)} candles...")
trades = run_backtest(candle_list, initial_balance=1000, risk_percent=1.0)