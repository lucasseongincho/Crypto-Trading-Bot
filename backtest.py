import csv
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit

def simulate_trade_outcome(signal, entry_price, sl, tp2, candles, start_index):
    """
    Simulates a 2-stage exit:
    1. TP1 (at 1:1 RR) -> Close 50% and move SL to Breakeven.
    2. TP2 (at 2:1 RR) -> Close remaining 50%.
    """
    # TP1 is set at 1:1 Risk-to-Reward
    risk_amount = abs(entry_price - sl)
    tp1 = entry_price + risk_amount if signal == 'BUY' else entry_price - risk_amount
    
    current_sl = sl
    tp1_hit = False
    pnl_accumulated = 0
    bars_held = 0

    for j in range(start_index, len(candles)):
        low_p = float(candles[j]['low'])
        high_p = float(candles[j]['high'])
        bars_held = j - start_index

        if not tp1_hit:
            # Check for Initial Stop Loss (Full Position Loss)
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                return (current_sl - entry_price if signal == 'BUY' else entry_price - current_sl), bars_held

            # Check for TP1
            if (signal == 'BUY' and high_p >= tp1) or (signal == 'SELL' and low_p <= tp1):
                tp1_hit = True
                # Bank 50% profit
                pnl_accumulated += 0.5 * (tp1 - entry_price if signal == 'BUY' else entry_price - tp1)
                # MOVE SL TO BREAKEVEN
                current_sl = entry_price 
        else:
            # Check for TP2 (The original 2:1 target)
            if (signal == 'BUY' and high_p >= tp2) or (signal == 'SELL' and low_p <= tp2):
                pnl_accumulated += 0.5 * (tp2 - entry_price if signal == 'BUY' else entry_price - tp2)
                return pnl_accumulated, bars_held

            # Check for Breakeven SL (Remaining 50% hits entry price)
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                return pnl_accumulated, bars_held
                
    return pnl_accumulated, bars_held

def run_backtest(candles, initial_balance=1000, risk_percent=1.0):
    balance = initial_balance
    trades = []
    print(f"Starting Backtest on {len(candles)} candles...")

    i = 50
    while i < len(candles) - 1:
        history = candles[:i+1]
        signal, structural_price = generate_trade_signal(history)
        entry_price = float(history[i]['close'])

        if signal in ['BUY', 'SELL'] and structural_price:
            pos_size, sl_price = calculate_position_size(balance, risk_percent, entry_price, structural_price)
            tp2_price = calculate_take_profit(entry_price, sl_price, 2.0)

            total_pnl_per_unit, duration = simulate_trade_outcome(signal, entry_price, sl_price, tp2_price, candles, i + 1)
            
            actual_pnl = pos_size * total_pnl_per_unit
            balance += actual_pnl
            
            # Status check for logging
            status = "TP1 Hit & BE" if (0 < actual_pnl < (pos_size * (tp2_price - entry_price))) else "Full Win/Loss"
            
            trades.append({'Signal': signal, 'PnL': actual_pnl, 'Balance': balance, 'Status': status})
            i += (duration + 1)
        else:
            i += 1

    # --- FINAL SUMMARY BLOCK ---
    if trades:
        wins = [t for t in trades if t['PnL'] > 0]
        win_rate = (len(wins) / len(trades)) * 100
        print("\n" + "="*40)
        print(f"   BACKTEST RESULTS (LINK-USD)")
        print("="*40)
        print(f"Total Trades:    {len(trades)}")
        print(f"Win Rate:        {win_rate:.2f}%")
        print(f"Final Balance:   ${balance:.2f}")
        print(f"Total Return:    {((balance/initial_balance)-1)*100:.2f}%")
        print("="*40)
    else:
        print("\n[!] No trades found. Check your strategy.py settings.")

    return trades