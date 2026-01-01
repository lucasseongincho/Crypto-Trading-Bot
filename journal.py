import csv
import os
from datetime import datetime

# Default file for the Live/Paper bot
DEFAULT_JOURNAL = "trade_journal.csv"

def log_trade(trade_data, filename=DEFAULT_JOURNAL):
    """
    Logs trade details with human-readable dates.
    filename: defaults to trade_journal.csv unless specified by backtest.
    """
    file_exists = os.path.isfile(filename)
    
    # Handle Date Formatting
    # If it's a backtest, we have Unix. If it's Live, we might have a string or now()
    if 'entry_unix' in trade_data:
        entry_time = datetime.fromtimestamp(trade_data['entry_unix']).strftime('%Y-%m-%d %H:%M:%S')
    else:
        entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Calculate Holding Time (Only if exit_unix exists, like in backtests)
    holding_mins = 0
    exit_time = "OPEN"
    if 'exit_unix' in trade_data:
        exit_time = datetime.fromtimestamp(trade_data['exit_unix']).strftime('%Y-%m-%d %H:%M:%S')
        holding_mins = round((trade_data['exit_unix'] - trade_data['entry_unix']) / 60, 2)

    fieldnames = [
        'Entry_Date', 'Exit_Date', 'Holding_Mins', 'Pair', 'Side', 
        'Entry_Price', 'Exit_Price', 'P/L_USD'
    ]

    with open(filename, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'Entry_Date': entry_time,
            'Exit_Date': exit_time,
            'Holding_Mins': holding_mins,
            'Pair': trade_data.get('pair', trade_data.get('product', 'ETH-USD')),
            'Side': trade_data['side'],
            'Entry_Price': trade_data['entry_price'],
            'Exit_Price': trade_data.get('exit_price', 0),
            'P/L_USD': trade_data.get('pnl', 0)
        })

def update_journal_exit(exit_price, pnl, filename=DEFAULT_JOURNAL):
    """Used by main.py to update the last trade with final exit data."""
    # Note: This updates the DEFAULT file for live sessions
    pass