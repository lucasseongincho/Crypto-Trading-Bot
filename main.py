import pandas as pd
import argparse
from strategy import SMCStrategy  
from risk import RiskManager      

def main():
    # --- 1. RESEARCH COMMAND LINE INTERFACE ---
    parser = argparse.ArgumentParser(description="SMC Trading Bot - Research Lab (Backtesting)")
    parser.add_argument('--file', type=str, required=True, help='Path to the historical CSV candle file')
    args = parser.parse_args()

    print("="*50)
    print("🤖 SMC TRADING BOT: RESEARCH LAB MODE")
    print(f"📈 Testing Data: {args.file}")
    print("⚠️  HARD-LOCK ACTIVE: Live API connections are DISABLED.")
    print("="*50)

    try:
        df = pd.read_csv(args.file)
        if df.empty:
            print("Error: The CSV file is empty.")
            return
        
        # Standardize columns to lowercase
        df.columns = [x.lower() for x in df.columns]
        
        # --- DATE LOGIC FOR 'START' (UNIX) OR 'DATE' COLUMNS ---
        if 'start' in df.columns:
            # Convert Unix timestamp (seconds) to a date object for the log
            df['date_only'] = pd.to_datetime(df['start'], unit='s').dt.date
            print("✅ Timestamps detected in 'start' column.")
        elif 'date' in df.columns:
            df['date_only'] = pd.to_datetime(df['date']).dt.date
        elif 'time' in df.columns:
            df['date_only'] = pd.to_datetime(df['time']).dt.date
        else:
            print("❌ ERROR: No 'start', 'date', or 'time' column found.")
            return

    except FileNotFoundError:
        print(f"Error: Could not find file '{args.file}'")
        return

    # --- 3. INITIALIZE COMPONENTS ---
    strategy = SMCStrategy()
    # We keep RiskManager for the balance tracking and CSV exporting
    risk = RiskManager(initial_balance=1000.0)

    # --- 4. THE RESEARCH LOOP ---
    total_candles = len(df)
    print("\n🚀 Starting Simulation (No Circuit Breaker)...")
    
    cooldown_timer = 0  
    active_trade = None  
    
    for i in range(100, total_candles):
        
        if i % 10000 == 0:
            print(f"⏳ Scanned {i} of {total_candles} candles...")

        current_candle = df.iloc[i]
        sim_date = current_candle['date_only']

        # ==========================================
        # 🛑 STATE 1: MANAGE OPEN TRADE
        # ==========================================
        if active_trade is not None:
            trade_result = None
            
            if active_trade['type'] == 'BUY':
                if current_candle['low'] <= active_trade['stop_loss']:
                    trade_result = "LOSS"
                elif current_candle['high'] >= active_trade['take_profit']:
                    trade_result = "WIN"
                    
            elif active_trade['type'] == 'SELL':
                if current_candle['high'] >= active_trade['stop_loss']:
                    trade_result = "LOSS"
                elif current_candle['low'] <= active_trade['take_profit']:
                    trade_result = "WIN"

            if trade_result:
                risk.log_virtual_trade(
                    trade_date=sim_date,
                    signal_type=active_trade['type'],
                    entry_price=active_trade['entry_price'],
                    result=trade_result
                )
                active_trade = None  
                cooldown_timer = 12  # 1 hour cooldown
            continue 

        # ==========================================
        # 🎯 STATE 2: LOOK FOR NEW SETUP
        # ==========================================
        if cooldown_timer > 0:
            cooldown_timer -= 1
            continue  
            
        current_data = df.iloc[i-99:i+1]
        signal = strategy.check_setup(current_data)
        
        if signal:
            entry = signal['entry_price']
            sl = signal['stop_loss']
            risk_dist = abs(entry - sl)
            
            if risk_dist == 0:
                continue
                
            if signal['type'] == 'BUY':
                tp = entry + (risk_dist * risk.rr_ratio)
            else:
                tp = entry - (risk_dist * risk.rr_ratio)

            active_trade = {
                'type': signal['type'],
                'entry_price': entry,
                'stop_loss': sl,
                'take_profit': round(tp, 2)
            }

    print("\n" + "="*50)
    print("📊 SIMULATION COMPLETE")
    print(f"Final Virtual Equity: ${risk.current_balance:.2f}")
    
    risk.export_csv("trade_log.csv")
    print("="*50)

if __name__ == "__main__":
    main()