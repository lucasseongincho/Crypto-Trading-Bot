import csv
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit

def simulate_trade_result(signal, entry_price, sl, tp, next_candle):
    """Simulates if SL or TP was hit first in the next candle."""
    open_p, high_p, low_p, close_p = next_candle[1], next_candle[2], next_candle[3], next_candle[4]

    if signal == 'BUY':
        # Check if SL was hit (low price is at or below SL)
        sl_hit = low_p <= sl
        # Check if TP was hit (high price is at or above TP)
        tp_hit = high_p >= tp
        
        if sl_hit and tp_hit:
            # Ambiguous: Check order based on open. Assume SL hit first for conservative testing.
            if open_p < sl: # Gap below SL
                 return sl
            elif open_p > tp: # Gap above TP
                 return tp
            return sl 
            
        elif sl_hit:
            return sl
        elif tp_hit:
            return tp
        else:
            # Neither hit, close at market
            return close_p 
            
    elif signal == 'SELL':
        # Check if SL was hit (high price is at or above SL)
        sl_hit = high_p >= sl
        # Check if TP was hit (low price is at or below TP)
        tp_hit = low_p <= tp
        
        if sl_hit and tp_hit:
            # Ambiguous: Assume SL hit first for conservative testing.
            if open_p > sl:
                 return sl
            elif open_p < tp:
                 return tp
            return sl
            
        elif sl_hit:
            return sl
        elif tp_hit:
            return tp
        else:
            # Neither hit, close at market
            return close_p
            
    return entry_price # Should not happen

def backtest(candles, initial_balance=1000, risk_percent=1, rr_ratio=2.0):
    balance = initial_balance
    trades = []
    
    # Start after enough candles for indicators (e.g., 20) and ensure next candle exists (len - 1)
    for i in range(20, len(candles) - 1): 
        current_candles = candles[:i+1]
        next_candle = candles[i+1]

        signal, structural_price = generate_trade_signal(current_candles)
        entry_price = current_candles[-1][4]  # close price

        if signal in ['BUY', 'SELL'] and structural_price:
            # Calculate Risk parameters
            position_size, stop_loss = calculate_position_size(
                balance, risk_percent, entry_price, structural_price
            )
            take_profit = calculate_take_profit(entry_price, structural_price, rr_ratio)
            
            # --- Simulate Trade Result ---
            exit_price = simulate_trade_result(signal, entry_price, stop_loss, take_profit, next_candle)
            
            pnl = 0
            if signal == 'BUY':
                pnl = position_size * (exit_price - entry_price)
            elif signal == 'SELL':
                pnl = position_size * (entry_price - exit_price)
            
            balance += pnl
            
            trades.append({
                'signal': signal, 'entry': entry_price, 'stop_loss': stop_loss, 
                'take_profit': take_profit, 'pnl': pnl, 'exit_price': exit_price
            })

    # Save results and print summary (omitted for brevity, similar to original)
    print(f"Backtest complete: Final Balance: {balance}, Total PnL: {balance - initial_balance}")
    return trades