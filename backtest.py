import csv
from datetime import datetime
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
from journal import log_trade 

def simulate_trade_outcome(signal, entry_price, sl, tp2, candles, start_index):
    risk_amount = abs(entry_price - sl)
    tp1 = entry_price + (risk_amount if signal == 'BUY' else -risk_amount)
    
    current_sl = sl
    tp1_hit = False
    pnl_accumulated = 0

    # Start looking at candles from the NEXT index forward
    for j in range(start_index, len(candles)):
        low_p = float(candles[j]['low'])
        high_p = float(candles[j]['high'])
        
        # Current duration in bars
        bars_held = j - (start_index - 1)

        if not tp1_hit:
            # Check Stop Loss
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                return (current_sl - entry_price if signal == 'BUY' else entry_price - current_sl), bars_held

            # Check TP1 (Bank 50%, move SL to Breakeven)
            if (signal == 'BUY' and high_p >= tp1) or (signal == 'SELL' and low_p <= tp1):
                tp1_hit = True
                pnl_accumulated += 0.5 * (tp1 - entry_price if signal == 'BUY' else entry_price - tp1)
                current_sl = entry_price 
        else:
            # Check TP2 (Exit remaining 50%)
            if (signal == 'BUY' and high_p >= tp2) or (signal == 'SELL' and low_p <= tp2):
                pnl_accumulated += 0.5 * (tp2 - entry_price if signal == 'BUY' else entry_price - tp2)
                return pnl_accumulated, bars_held

            # Check Breakeven Stop
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                return pnl_accumulated, bars_held
                
    return pnl_accumulated, (len(candles) - start_index)

def run_backtest(candles, product_id, initial_balance=1000, risk_percent=1.0):
    balance = initial_balance
    trades = []
    
    # Extract the base asset (e.g., "SOL" from "SOL-USD")
    asset_name = product_id.split('-')[0] 

    # --- Generate Universal Filename ---
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    report_filename = f"trade_journal_{asset_name}_{timestamp}.csv"

    i = 50 
    while i < len(candles) - 1:
        signal, structural_price, _ = generate_trade_signal(candles, i)
        entry_price = float(candles[i]['close'])

        if signal in ['BUY', 'SELL'] and structural_price:
            pos_size, sl_price = calculate_position_size(balance, risk_percent, entry_price, structural_price)
            tp2_price = calculate_take_profit(entry_price, sl_price, 2.0)

            # (Assume simulate_trade_outcome is defined below)
            res_pnl_unit, duration = simulate_trade_outcome(signal, entry_price, sl_price, tp2_price, candles, i + 1)
        
            actual_pnl = pos_size * res_pnl_unit
            balance += actual_pnl
            exit_idx = min(i + max(1, duration), len(candles) - 1)
        
            log_trade({
                'entry_unix': candles[i]['start'],
                'exit_unix': candles[exit_idx]['start'],
                'pair': product_id,
                'side': signal,
                'entry_price': entry_price,
                'exit_price': float(candles[exit_idx]['close']),
                'pnl': round(actual_pnl, 2)
            }, filename=report_filename)
            
            trades.append({'Signal': signal, 'PnL': actual_pnl, 'Balance': balance})
            i += (duration + 1)
        else:
            i += 1

    return trades, report_filename