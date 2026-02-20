import csv
import os
from datetime import datetime
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
from journal import log_trade 

def simulate_trade_outcome(signal, entry_price, sl, tp2, candles, start_index):
    """
    1:2 Hybrid Simulation:
    - Moves SL to Breakeven at 1:1 (TP1)
    - NO scale-out (keeps 100% position)
    - Final exit at 1:2 (TP2) or SL/Breakeven.
    Returns: (total_pnl_units, bars_held, avg_exit_price)
    """
    risk_amount = abs(entry_price - sl)
    # TP1 is the 1:1 'Safety' trigger
    tp1 = entry_price + (risk_amount if signal == 'BUY' else -risk_amount)
    
    current_sl = sl
    tp1_hit = False
    final_exit_price = entry_price 

    for j in range(start_index, len(candles)):
        low_p = float(candles[j]['low'])
        high_p = float(candles[j]['high'])
        bars_held = j - (start_index - 1)

        if not tp1_hit:
            # 1. Check Initial Stop Loss
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                final_exit_price = current_sl
                # Full Loss (-1R)
                return (current_sl - entry_price if signal == 'BUY' else entry_price - current_sl), bars_held, final_exit_price

            # 2. Check 1:1 Safety Trigger (Move to Breakeven)
            if (signal == 'BUY' and high_p >= tp1) or (signal == 'SELL' and low_p <= tp1):
                tp1_hit = True
                current_sl = entry_price # MOVE TO BREAKEVEN
        else:
            # 3. Check Final TP2 (1:2 Reward)
            if (signal == 'BUY' and high_p >= tp2) or (signal == 'SELL' and low_p <= tp2):
                final_exit_price = tp2
                # Full 1:2 Profit (+2R)
                return (tp2 - entry_price if signal == 'BUY' else entry_price - tp2), bars_held, final_exit_price

            # 4. Check Breakeven Stop
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                final_exit_price = current_sl
                # Breakeven Result (0 PnL)
                return 0, bars_held, final_exit_price
                
    return 0, (len(candles) - start_index), entry_price

def calculate_atr(candles, current_idx, period=14):
    """Calculates the True Range average for volatility-based buffering."""
    trs = []
    for j in range(current_idx - period, current_idx):
        if j <= 0: continue
        h = float(candles[j]['high'])
        l = float(candles[j]['low'])
        pc = float(candles[j-1]['close'])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    return sum(trs) / len(trs) if trs else 0

def run_backtest(candles, product_id, initial_balance=1000, risk_percent=1.0):
    balance = initial_balance
    trades = []
    
    asset_name = product_id.split('-')[0] 
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    report_filename = f"trade_journal_{asset_name}_{timestamp}.csv"

    # Start after trend/indicator lookback
    i = 150 
    
    while i < len(candles) - 1:
        candles_5m = candles[i-100:i+1]
        candles_htf = candles[i-48:i+1]
        
        signal, structural_price, _ = generate_trade_signal(candles_5m, candles_htf)
        
        if signal in ['BUY', 'SELL'] and structural_price:
            entry_price = float(candles[i]['close'])
            atr_now = calculate_atr(candles, i, period=14)

            # --- Uses the 1.5x ATR buffer inside risk.py ---
            pos_size, sl_price = calculate_position_size(
                balance, risk_percent, entry_price, float(structural_price), signal, atr_now
            )
            
            if pos_size <= 0:
                i += 1
                continue

            # --- Target set to 1:2 RR ---
            tp2_price = calculate_take_profit(entry_price, sl_price, signal, 1.5) 

            res_pnl_unit, duration, avg_exit = simulate_trade_outcome(
                signal, entry_price, sl_price, tp2_price, candles, i + 1
            )
        
            actual_pnl = pos_size * res_pnl_unit
            balance += actual_pnl
            exit_idx = min(i + max(1, duration), len(candles) - 1)
        
            log_trade({
                'entry_unix': candles[i]['start'],
                'exit_unix': candles[exit_idx]['start'],
                'pair': product_id,
                'side': signal,
                'entry_price': entry_price,
                'exit_price': avg_exit,
                'tp1_price': entry_price + abs(entry_price - sl_price), # Visual 1:1 ref
                'tp2_price': tp2_price,
                'sl_price': sl_price,
                'pnl': round(actual_pnl, 2)
            }, filename=report_filename)
            
            trades.append({'Signal': signal, 'PnL': actual_pnl, 'Balance': balance})
            i += (duration + 1)
        else:
            i += 1

    return trades, report_filename