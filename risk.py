import pandas as pd

class RiskManager:
    def __init__(self, initial_balance=1000.0):
        self.current_balance = initial_balance
        self.trade_history = []
        self.rr_ratio = 1.5  # Risk-to-Reward Ratio

    def log_virtual_trade(self, trade_date, signal_type, entry_price, result):
        """
        Calculates PnL and updates history using the Live-compatible format.
        """
        # Risk 1% of current balance per trade
        risk_amount = self.current_balance * 0.01
        
        if result == "WIN":
            pnl = risk_amount * self.rr_ratio
        else:
            pnl = -risk_amount
        
        self.current_balance += pnl
        
        # Standardized keys: date, type, entry, result, pnl, balance
        self.trade_history.append({
            'date': trade_date,
            'type': signal_type,
            'entry': entry_price,
            'result': result,
            'pnl': round(pnl, 2),
            'balance': round(self.current_balance, 2)
        })

    def export_csv(self, filename="trade_log.csv"):
        """Exports the full history to a CSV file."""
        if not self.trade_history:
            print("⚠️ No trades to export.")
            return

        df = pd.DataFrame(self.trade_history)
        df.to_csv(filename, index=False)
        print(f"✅ Trade log successfully exported to {filename}")