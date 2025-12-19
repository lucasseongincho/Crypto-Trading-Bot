import csv
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit

def simulate_trade_outcome(signal, entry_price, sl, tp, candles, start_index):
    """
    Walks through future candles to see if TP or SL is hit first.
    Returns: (exit_price, bars_held)
    """
    for j in range(start_index, len(candles)):
        # Using dictionary keys to match live bot data format
        low_p = float(candles[j]['low'])
        high_p = float(candles[j]['high'])
        close_p = float(candles[j]['close'])
        
        if signal == 'BUY':
            # Priority check: If both hit in one candle, assume SL hit first (conservative)
            if low_p <= sl: 
                return sl, (j - start_index)
            if high_p >= tp: 
                return tp, (j - start_index)
        elif signal == 'SELL':
            if high_p >= sl: 
                return sl, (j - start_index)
            if low_p <= tp: 
                return tp, (j - start_index)
            
    # If the backtest ends before hitting SL or TP, close at the final candle's price
    return float(candles[-1]['close']), (len(candles) - start_index)

def run_backtest(candles, initial_balance=1000, risk_percent=1.0):
    balance = initial_balance
    trades = []

    print(f"Starting Backtest with ${initial_balance}...")

    # We skip the first 50 candles to allow indicators/swings to populate
    i = 50
    while i < len(candles) - 1:
        # Current slice of history for analysis
        history = candles[:i+1]
        
        # 1. Check strategy logic
        signal, structural_price = generate_trade_signal(history)
        entry_price = float(history[i]['close'])

        if signal in ['BUY', 'SELL'] and structural_price:
            # 2. Calculate Risk Math (Matches risk.py)
            pos_size, sl_price = calculate_position_size(
                balance, risk_percent, entry_price, structural_price
            )
            
            # Using 2.0 RR Ratio as defined in your setup
            tp_price = calculate_take_profit(entry_price, sl_price, 2.0)

            # 3. Simulate the "Hold" period
            exit_price, duration = simulate_trade_outcome(
                signal, entry_price, sl_price, tp_price, candles, i + 1
            )
            
            # 4. Calculate PnL
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
                'Duration': duration
            })
            
            # Skip the bars we were already "holding" the trade
            i += (duration + 1)
        else:
            i += 1

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
        print("\nNo trades were triggered during this period.")

    return trades