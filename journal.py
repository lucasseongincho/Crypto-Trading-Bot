import csv
import os
from datetime import datetime

def log_trade(trade_data, filename="trade_journal.csv"):
    """
    Appends a new trade record to the CSV journal. 
    Includes TP1, TP2, SL prices, and the running Balance.
    """
    
    # 1. Format the Date and Time from Unix timestamps
    try:
        entry_date = datetime.fromtimestamp(trade_data['entry_unix']).strftime('%Y/%m/%d %H:%M')
        exit_date = datetime.fromtimestamp(trade_data['exit_unix']).strftime('%Y/%m/%d %H:%M')
        # Calculate duration in minutes
        duration_mins = int((trade_data['exit_unix'] - trade_data['entry_unix']) / 60)
    except Exception:
        entry_date = "N/A"
        exit_date = "N/A"
        duration_mins = 0

    # 2. Define the Columns (The Row)
    # We round to 2 decimals for clean data
    row = [
        entry_date,                             # Column 1: Entry Time
        exit_date,                              # Column 2: Exit Time
        duration_mins,                          # Column 3: Hold Time (Min)
        trade_data.get('pair', 'N/A'),          # Column 4: Ticker
        trade_data.get('side', 'N/A'),          # Column 5: BUY/SELL
        round(trade_data['entry_price'], 2),    # Column 6: Entry Price
        round(trade_data['exit_price'], 2),     # Column 7: Final Exit Price
        round(trade_data['tp1_price'], 2),      # Column 8: TP1 Target
        round(trade_data['tp2_price'], 2),      # Column 9: TP2 Target
        round(trade_data['sl_price'], 2),       # Column 10: Initial Stop Loss
        round(trade_data['pnl'], 2),            # Column 11: Total P/L USD
        round(trade_data.get('balance', 0), 2)  # Column 12: Account Balance
    ]

    # 3. Check if file exists to determine if we need a header
    file_exists = os.path.isfile(filename)

    # 4. Write to CSV
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # If the file is new, add the header first
        if not file_exists:
            writer.writerow([
                'Entry_Date', 'Exit_Date', 'Holding_M', 'Pair', 'Side', 
                'Entry_Price', 'Exit_Price', 'TP1_Price', 'TP2_Price', 'SL_Price', 'P/L_USD', 'Balance'
            ])
            
        writer.writerow(row)