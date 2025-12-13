import csv
from datetime import datetime

def log_trade(trade_info):
    with open('trade_journal.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now(),
            trade_info['side'],
            trade_info['product'],
            trade_info['size'],
            trade_info['entry_price'],
            trade_info['stop_loss'],
            trade_info['take_profit']
        ])