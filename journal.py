import csv
import os
from datetime import datetime

FILENAME = 'trade_journal.csv'

def log_trade(trade_info):
    """Records the initial entry of a trade."""
    file_exists = os.path.isfile(FILENAME)
    
    with open(FILENAME, 'a', newline='') as f:
        writer = csv.writer(f)
        # Add headers if it's a brand new file
        if not file_exists:
            writer.writerow(['Timestamp', 'Side', 'Product', 'Size', 'Entry', 'SL', 'TP2', 'Exit_Price', 'Profit_USD'])
            
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            trade_info['side'],
            trade_info['product'],
            trade_info['size'],
            trade_info['entry_price'],
            trade_info['stop_loss'],
            trade_info['take_profit'],
            "OPEN", # Exit Price placeholder
            "0.00"  # Profit placeholder
        ])

def update_journal_exit(exit_price, profit_usd):
    """Updates the last row in the journal with the final results."""
    rows = []
    if not os.path.isfile(FILENAME): return

    with open(FILENAME, 'r') as f:
        rows = list(csv.reader(f))

    if len(rows) > 1:
        # Update the last row's Exit Price and Profit columns
        rows[-1][7] = f"{exit_price:.2f}"
        rows[-1][8] = f"{profit_usd:.2f}"

    with open(FILENAME, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)