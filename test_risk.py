import unittest
from risk import RiskManager

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        # Initialize a fresh RiskManager before each test
        self.risk = RiskManager(initial_balance=1000.0)

    def test_calculate_size(self):
        # 1% of 1000 = $10 risk. 
        # Entry 50000, SL 49000 -> $1000 risk per coin.
        # Size should be 10 / 1000 = 0.01
        size = self.risk.calculate_size(entry_price=50000, stop_loss=49000)
        self.assertEqual(size, 0.01)

    def test_log_virtual_trade_win(self):
        # Win should add 1.5% ($15) to balance
        self.risk.log_virtual_trade("2026-02-01", "BUY", 50000, "WIN")
        self.assertEqual(self.risk.current_balance, 1015.0)
        self.assertEqual(self.risk.trade_history[0]['pnl'], 15.0)

    def test_log_virtual_trade_loss(self):
        # Loss should deduct 1% ($10) from balance
        self.risk.log_virtual_trade("2026-02-01", "SELL", 50000, "LOSS")
        self.assertEqual(self.risk.current_balance, 990.0)
        self.assertEqual(self.risk.trade_history[0]['pnl'], -10.0)

if __name__ == '__main__':
    unittest.main()