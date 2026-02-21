import pandas as pd

class RiskManager:
    def __init__(self, initial_balance=1000.0):
        self.current_balance = initial_balance
        self.trade_history = []
        self.rr_ratio = 1.5  # Risk-to-Reward Ratio

    def calculate_size(self, entry_price, stop_loss):
        """
        Calculates position size based on risking 1% of the current balance.
        """
        risk_amount = self.current_balance * 0.01
        risk_per_coin = abs(entry_price - stop_loss)
        
        if risk_per_coin == 0:
            return 0
            
        # Return quantity of coin to buy/sell
        qty = risk_amount / risk_per_coin
        return qty

    def log_virtual_trade(self, trade_date, signal_type, entry_price, result):
        # ... (keep your existing log_virtual_trade code here)
        risk_amount = self.current_balance * 0.01
        
        if result == "WIN":
            pnl = risk_amount * self.rr_ratio
        else:
            pnl = -risk_amount
        
        self.current_balance += pnl
        
        self.trade_history.append({
            'date': trade_date,
            'type': signal_type,
            'entry': entry_price,
            'result': result,
            'pnl': round(pnl, 2),
            'balance': round(self.current_balance, 2)
        })

    def export_csv(self, filename="trade_log.csv"):
        # ... (keep your existing export_csv code here)
        if not self.trade_history:
            print("⚠️ No trades to export.")
            return

        df = pd.DataFrame(self.trade_history)
        df.to_csv(filename, index=False)
        print(f"✅ Trade log successfully exported to {filename}")