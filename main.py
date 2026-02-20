import pandas as pd
import argparse
from strategy import SMCStrategy  
from risk import RiskManager      

def main():
    # --- 1. RESEARCH COMMAND LINE INTERFACE ---
    parser = argparse.ArgumentParser(description="SMC Trading Bot - Research Lab (Backtesting)")
    parser.add_argument('--file', type=str, required=True, help='Path to the historical CSV candle file')
    args = parser.parse_args()

    IS_RESEARCH_MODE = True
    
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
        # Ensure column headers are lowercase to prevent errors
        df.columns = [x.lower() for x in df.columns]
    except FileNotFoundError:
        print(f"Error: Could not find file '{args.file}'")
        return

    # --- 3. INITIALIZE COMPONENTS ---
    strategy = SMCStrategy()
    risk = RiskManager(initial_balance=1000.0)

    # --- 4. THE RESEARCH LOOP (Realistic Forward-Walking) ---
    total_candles = len(df)
    print("\n🚀 Starting Simulation (Realistic Forward-Walking)...")
    print("🔇 Trade prints are muted. Waiting for final results...\n")
    
    cooldown_timer = 0  
    active_trade = None  # Tracks our open position in time
    
    for i in range(100, total_candles):
        
        # ⏱️ PROGRESS TRACKER
        if i % 10000 == 0:
            print(f"⏳ Scanned {i} of {total_candles} candles...")

        current_candle = df.iloc[i]

        # ==========================================
        # 🛑 STATE 1: MANAGE OPEN TRADE
        # ==========================================
        if active_trade is not None:
            trade_result = None
            
            # Did the market hit our Stop Loss or Take Profit this candle?
            if active_trade['type'] == 'BUY':
                # Check Stop Loss first (conservative backtesting)
                if current_candle['low'] <= active_trade['stop_loss']:
                    trade_result = "LOSS"
                elif current_candle['high'] >= active_trade['take_profit']:
                    trade_result = "WIN"
                    
            elif active_trade['type'] == 'SELL':
                if current_candle['high'] >= active_trade['stop_loss']:
                    trade_result = "LOSS"
                elif current_candle['low'] <= active_trade['take_profit']:
                    trade_result = "WIN"

            # If a target was hit, close the trade and log it!
            if trade_result:
                risk.log_virtual_trade(active_trade['signal_data'], result=trade_result)
                active_trade = None  # Clear the position
                cooldown_timer = 12  # Wait 1 hour before looking for next setup
                
            continue # Skip looking for new setups while we are busy managing this trade

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
            
            # Safety check: if Entry and SL are the exact same, skip it
            if risk_dist == 0:
                continue
                
            # Calculate exact Take Profit based on the 1.5 Risk/Reward ratio
            if signal['type'] == 'BUY':
                tp = entry + (risk_dist * risk.rr_ratio)
            else:
                tp = entry - (risk_dist * risk.rr_ratio)

            # Lock the engine into this trade!
            active_trade = {
                'type': signal['type'],
                'entry_price': entry,
                'stop_loss': sl,
                'take_profit': round(tp, 2),
                'signal_data': signal # Store original signal to pass to the logger later
            }

    print("\n" + "="*50)
    print("📊 SIMULATION COMPLETE")
    print(f"Final Virtual Equity: ${risk.current_balance:.2f}")
    
    # 📁 EXPORT THE CSV
    risk.export_csv()
    print("="*50)

if __name__ == "__main__":
    main()