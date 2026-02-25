import pandas as pd

class RiskManager:
    def __init__(self, initial_balance=1000.0):
        self.current_balance = initial_balance
        self.trade_history = []
        self.rr_ratio = 1.5  # Risk-to-Reward Ratio
        self.min_sl_distance = 50.0  # 🛡️ MINIMUM SAFE SPREAD (in dollars)

    def calculate_size(self, entry_price, stop_loss):
        """
        Calculates position size based on risking 1% of the current balance.
        Includes safety checks for micro-spreads and Spot account limits.
        """
        risk_amount = self.current_balance * 0.01
        risk_per_coin = abs(entry_price - stop_loss)
        
        # 🛡️ SAFETY 1: Reject the trade if the SL is too close to the Entry
        if risk_per_coin < self.min_sl_distance:
            print(f"⚠️ Trade Rejected: Stop Loss distance (${risk_per_coin:.2f}) is below the ${self.min_sl_distance} minimum safe threshold.")
            return 0
            
        if risk_per_coin == 0:
            return 0
            
        # Calculate ideal quantity based on risk
        ideal_qty = risk_amount / risk_per_coin
        
        # 🛡️ SAFETY 2: Spot Trading Purchasing Power Cap
        # We use 0.98 to leave a 2% buffer for Coinbase trading fees
        max_affordable_qty = (self.current_balance * 0.98) / entry_price
        
        if ideal_qty > max_affordable_qty:
            print(f"⚠️ Spot Cap Active: Ideal size {ideal_qty:.4f} BTC costs too much. Capping at {max_affordable_qty:.4f} BTC.")
            return max_affordable_qty
            
        return ideal_qty

    def log_virtual_trade(self, trade_date, signal_type, entry_price, result):
        """
        Logs virtual trades for the offline main.py backtester.
        """
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
        """
        Exports offline backtest results to a CSV.
        """
        if not self.trade_history:
            print("⚠️ No trades to export.")
            return

        df = pd.DataFrame(self.trade_history)
        df.to_csv(filename, index=False)
        print(f"✅ Trade log successfully exported to {filename}")