import csv
from datetime import datetime
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
from journal import log_trade 

def simulate_trade_outcome(signal, entry_price, sl, tp2, candles, start_index):
    """
    Simulates a trade with a 50/50 scale-out at TP1 and a breakeven stop.
    Returns: (total_pnl_units, bars_held, avg_exit_price)
    """
    risk_amount = abs(entry_price - sl)
    # TP1 is a 1:1 Risk/Reward move
    tp1 = entry_price + (risk_amount if signal == 'BUY' else -risk_amount)
    
    current_sl = sl
    tp1_hit = False
    pnl_accumulated = 0
    final_exit_price = entry_price # Default to entry

    for j in range(start_index, len(candles)):
        low_p = float(candles[j]['low'])
        high_p = float(candles[j]['high'])
        bars_held = j - (start_index - 1)

        if not tp1_hit:
            # Check Stop Loss
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                final_exit_price = current_sl
                return (current_sl - entry_price if signal == 'BUY' else entry_price - current_sl), bars_held, final_exit_price

            # Check TP1 (Scale out 50%)
            if (signal == 'BUY' and high_p >= tp1) or (signal == 'SELL' and low_p <= tp1):
                tp1_hit = True
                # Profit from first 50%
                pnl_accumulated += 0.5 * (tp1 - entry_price if signal == 'BUY' else entry_price - tp1)
                current_sl = entry_price # Move remaining 50% to Breakeven
        else:
            # Check TP2 (Exit remaining 50%)
            if (signal == 'BUY' and high_p >= tp2) or (signal == 'SELL' and low_p <= tp2):
                pnl_accumulated += 0.5 * (tp2 - entry_price if signal == 'BUY' else entry_price - tp2)
                # Average Exit = (50% at TP1 + 50% at TP2)
                avg_exit = (tp1 + tp2) / 2
                return pnl_accumulated, bars_held, avg_exit

            # Check Breakeven Stop
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                # Remaining 50% closed at entry (0 profit)
                # Average Exit = (50% at TP1 + 50% at Entry)
                avg_exit = (tp1 + entry_price) / 2
                return pnl_accumulated, bars_held, avg_exit
                
    return pnl_accumulated, (len(candles) - start_index), entry_price

def run_backtest(candles, product_id, initial_balance=1000, risk_percent=1.0):
    balance = initial_balance
    trades = []
    
    asset_name = product_id.split('-')[0] 
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    report_filename = f"trade_journal_{asset_name}_{timestamp}.csv"

    i = 50 
    while i < len(candles) - 1:
        signal, structural_price, _ = generate_trade_signal(candles, i)
        entry_price = float(candles[i]['close'])

        if signal in ['BUY', 'SELL'] and structural_price:
            # 1. Calculate Targets
            pos_size, sl_price = calculate_position_size(
                balance, risk_percent, entry_price, float(structural_price), signal
            )
            tp2_price = calculate_take_profit(entry_price, sl_price, signal, 2.0)
            tp1_price = calculate_take_profit(entry_price, sl_price, signal, 1.0) # For logging

            # 2. Simulate
            res_pnl_unit, duration, avg_exit = simulate_trade_outcome(
                signal, entry_price, sl_price, tp2_price, candles, i + 1
            )
        
            actual_pnl = pos_size * res_pnl_unit
            balance += actual_pnl
            exit_idx = min(i + max(1, duration), len(candles) - 1)
        
            # 3. Log with NEW target columns
            log_trade({
                'entry_unix': candles[i]['start'],
                'exit_unix': candles[exit_idx]['start'],
                'pair': product_id,
                'side': signal,
                'entry_price': entry_price,
                'exit_price': avg_exit,      # Uses the calculated average
                'tp1_price': tp1_price,      # New
                'tp2_price': tp2_price,      # New
                'sl_price': sl_price,        # New
                'pnl': round(actual_pnl, 2)
            }, filename=report_filename)
            
            trades.append({'Signal': signal, 'PnL': actual_pnl, 'Balance': balance})
            i += (duration + 1)
        else:
            i += 1

    return trades, report_filename