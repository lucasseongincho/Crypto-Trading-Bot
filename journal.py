import csv
import os
from datetime import datetime

JOURNAL_FILE = "trade_journal.csv"

def log_trade(trade_data):
    """
    Logs trade details with human-readable dates and advanced metrics.
    trade_data should be a dictionary.
    """
    file_exists = os.path.isfile(JOURNAL_FILE)
    
    # Format Unix to Readable
    entry_time = datetime.fromtimestamp(trade_data['entry_unix']).strftime('%Y-%m-%d %H:%M:%S')
    exit_time = datetime.fromtimestamp(trade_data['exit_unix']).strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate Holding Time (Minutes)
    holding_mins = round((trade_data['exit_unix'] - trade_data['entry_unix']) / 60, 2)

    fieldnames = [
        'Entry_Date', 'Exit_Date', 'Holding_Mins', 'Pair', 'Side', 
        'Entry_Price', 'Exit_Price', 'P/L_USD', 'MAE_USD', 'MFE_USD', 'Drawdown_Pct'
    ]

    with open(JOURNAL_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'Entry_Date': entry_time,
            'Exit_Date': exit_time,
            'Holding_Mins': holding_mins,
            'Pair': trade_data['pair'],
            'Side': trade_data['side'],
            'Entry_Price': trade_data['entry_price'],
            'Exit_Price': trade_data['exit_price'],
            'P/L_USD': trade_data['pnl'],
            'MAE_USD': trade_data.get('mae', 0), # Max loss during trade
            'MFE_USD': trade_data.get('mfe', 0), # Max profit during trade
            'Drawdown_Pct': trade_data.get('drawdown', 0)
        })

print("Journal system updated with Readable Dates and Metrics.")