import csv
import pandas as pd
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit

def simulate_trade_outcome(signal, entry_price, sl, tp, candles, start_index):
    """
    Walks through future candles to see if TP or SL is hit first.
    Returns: (exit_price, bars_held)
    """
    for j in range(start_index, len(candles)):
        # Candle format: [timestamp, low, high, open, close]
        low_p = float(candles[j][1])
        high_p = float(candles[j][2])
        close_p = float(candles[j][4])
        
        if signal == 'BUY':
            if low_p <= sl: return sl, (j - start_index)
            if high_p >= tp: return tp, (j - start_index)
        elif signal == 'SELL':
            if high_p >= sl: return sl, (j - start_index)
            if low_p <= tp: return tp, (j - start_index)
            
    # If end of data reached before exit, close at last known price
    return float(candles[-1][4]), (len(candles) - start_index)

def run_backtest(candles, initial_balance=1000, risk_percent=1.0):
    balance = initial_balance
    trades = []

    print(f"Starting Backtest with ${initial_balance}...")

    # Loop through historical data
    for i in range(50, len(candles) - 1):
        # Current slice of history
        history = candles[:i+1]
        
        # Check strategy logic
        signal, structural_price = generate_trade_signal(history)
        entry_price = float(history[-1][4])

        if signal in ['BUY', 'SELL'] and structural_price:
            # Calculate Risk Math
            pos_size, sl_price = calculate_position_size(balance, risk_percent, entry_price, structural_price)
            tp_price = calculate_take_profit(entry_price, sl_price, 2.0)

            # Simulate the "Hold" period
            exit_price, duration = simulate_trade_outcome(signal, entry_price, sl_price, tp_price, candles, i + 1)
            
            # Calculate PnL
            if signal == 'BUY':
                pnl = pos_size * (exit_price - entry_price)
            else:
                pnl = pos_size * (entry_price - exit_price)
            
            balance += pnl
            trades.append({
                'Signal': signal,
                'Entry': entry_price,
                'Exit': exit_price,
                'PnL': pnl,
                'Balance': balance,
                'Duration_Bars': duration
            })
            
            # Fast-forward time to skip candles where we were already in a trade
            i += duration 

    # --- Performance Summary ---
    if trades:
        wins = [t for t in trades if t['PnL'] > 0]
        win_rate = (len(wins) / len(trades)) * 100
        print(f"\nBACKTEST SUMMARY")
        print(f"----------------")
        print(f"Total Trades: {len(trades)}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Final Balance: ${balance:.2f}")
        print(f"Total Return: {((balance/initial_balance)-1)*100:.2f}%")
    else:
        print("No trades were triggered.")

    return trades