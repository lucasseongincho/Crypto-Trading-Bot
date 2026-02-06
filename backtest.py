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
    # TP1 remains a 1:1 Risk/Reward move to lock in some profit
    tp1 = entry_price + (risk_amount if signal == 'BUY' else -risk_amount)
    
    current_sl = sl
    tp1_hit = False
    pnl_accumulated = 0
    final_exit_price = entry_price 

    for j in range(start_index, len(candles)):
        low_p = float(candles[j]['low'])
        high_p = float(candles[j]['high'])
        bars_held = j - (start_index - 1)

        if not tp1_hit:
            # 1. Check Stop Loss
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                final_exit_price = current_sl
                return (current_sl - entry_price if signal == 'BUY' else entry_price - current_sl), bars_held, final_exit_price

            # 2. Check TP1 (Scale out 50%)
            if (signal == 'BUY' and high_p >= tp1) or (signal == 'SELL' and low_p <= tp1):
                tp1_hit = True
                pnl_accumulated += 0.5 * (tp1 - entry_price if signal == 'BUY' else entry_price - tp1)
                current_sl = entry_price # MOVE TO BREAKEVEN
        else:
            # 3. Check TP2 (Exit remaining 50% at 1:3 RR)
            if (signal == 'BUY' and high_p >= tp2) or (signal == 'SELL' and low_p <= tp2):
                pnl_accumulated += 0.5 * (tp2 - entry_price if signal == 'BUY' else entry_price - tp2)
                avg_exit = (tp1 + tp2) / 2
                return pnl_accumulated, bars_held, avg_exit

            # 4. Check Breakeven Stop
            if (signal == 'BUY' and low_p <= current_sl) or (signal == 'SELL' and high_p >= current_sl):
                avg_exit = (tp1 + entry_price) / 2
                return pnl_accumulated, bars_held, avg_exit
                
    return pnl_accumulated, (len(candles) - start_index), entry_price

def run_backtest(candles, product_id, initial_balance=1000, risk_percent=1.0):
    balance = initial_balance
    trades = []
    
    asset_name = product_id.split('-')[0] 
    # Added seconds (%S) to ensure a fresh file every time you run
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    report_filename = f"trade_journal_{asset_name}_{timestamp}.csv"

    # Start after lookback period
    i = 150 
    
    while i < len(candles) - 1:
        # 1. Prepare Data Windows
        candles_5m = candles[i-100:i+1]
        candles_htf = candles[i-48:i+1] # 4-Hour Trend Window
        
        # 2. Get Signal (Respects HTF Filter and FVG Mandatory Check)
        signal, structural_price, counts = generate_trade_signal(candles_5m, candles_htf)
        
        # --- THE FIX: Strictly check for active signals only ---
        if signal in ['BUY', 'SELL'] and structural_price:
            entry_price = float(candles[i]['close'])

            # 3. Risk Assessment
            pos_size, sl_price = calculate_position_size(
                balance, risk_percent, entry_price, float(structural_price), signal
            )
            
            # Skip if Risk logic rejects (e.g., SL too tight)
            if pos_size <= 0:
                i += 1
                continue

            # 4. Targets (SNIPER 1:3 RR)
            tp1_price = calculate_take_profit(entry_price, sl_price, signal, 1.0)
            tp2_price = calculate_take_profit(entry_price, sl_price, signal, 3.0) 

            # 5. Simulation
            res_pnl_unit, duration, avg_exit = simulate_trade_outcome(
                signal, entry_price, sl_price, tp2_price, candles, i + 1
            )
        
            actual_pnl = pos_size * res_pnl_unit
            balance += actual_pnl
            exit_idx = min(i + max(1, duration), len(candles) - 1)
        
            # 6. Logging
            log_trade({
                'entry_unix': candles[i]['start'],
                'exit_unix': candles[exit_idx]['start'],
                'pair': product_id,
                'side': signal,
                'entry_price': entry_price,
                'exit_price': avg_exit,
                'tp1_price': tp1_price,
                'tp2_price': tp2_price,
                'sl_price': sl_price,
                'pnl': round(actual_pnl, 2)
            }, filename=report_filename)
            
            trades.append({'Signal': signal, 'PnL': actual_pnl, 'Balance': balance})
            
            # Jump forward past the trade duration
            i += (duration + 1)
        else:
            # No signal or blocked signal
            i += 1

    return trades, report_filename