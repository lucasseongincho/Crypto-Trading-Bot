import pandas as pd

class RiskManager:
    def __init__(self, initial_balance=1000.0, risk_per_trade=0.02, rr_ratio=1.5):
        """
        Initializes the Accountant.
        :param initial_balance: Starting USD for virtual tracking.
        :param risk_per_trade: Percentage of balance to risk (0.02 = 2%).
        :param rr_ratio: Reward-to-Risk ratio (1.5 means target is 1.5x the risk).
        """
        self.current_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.rr_ratio = rr_ratio
        self.trade_history = []

    def calculate_size(self, entry_price, stop_loss_price):
        """
        Calculates the exact position size based on the distance to Stop Loss.
        Includes a Safety Cap to prevent exceeding account balance.
        """
        risk_amount_usd = self.current_balance * self.risk_per_trade
        price_risk_per_unit = abs(entry_price - stop_loss_price)
        
        # Prevent division by zero if entry == SL
        if price_risk_per_unit == 0:
            return 0
            
        position_size = risk_amount_usd / price_risk_per_unit
        
        # 🛡️ SAFETY CAP: Prevent Infinite Leverage
        # You cannot buy more crypto than your total cash allows (1x leverage)
        max_affordable_size = self.current_balance / entry_price
        
        if position_size > max_affordable_size:
            position_size = max_affordable_size
            
        return round(position_size, 6)

    def log_virtual_trade(self, signal, result="PENDING"):
        """
        Used by main.py to record the outcome of a backtest trade.
        """
        risk_amount = self.current_balance * self.risk_per_trade
        
        if result == "WIN":
            profit = risk_amount * self.rr_ratio
            self.current_balance += profit
        elif result == "LOSS":
            self.current_balance -= risk_amount

        self.trade_history.append({
            'type': signal['type'],
            'entry': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'result': result,
            'balance': round(self.current_balance, 2)
        })

    def update_balance(self, live_balance):
        """
        Updates the current balance using real data from Coinbase API.
        """
        self.current_balance = float(live_balance)

    def export_csv(self, filename="trade_log.csv"):
        """
        Exports the virtual trade history to a CSV file for Excel analysis.
        """
        if self.trade_history:
            df = pd.DataFrame(self.trade_history)
            df.to_csv(filename, index=False)
            print(f"📁 Trade log successfully saved to {filename}")