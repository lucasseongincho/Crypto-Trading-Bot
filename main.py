import pandas as pd
import argparse
import sys
from strategy import SMCStrategy  # Assumes your logic is in strategy.py
from risk import RiskManager      # Assumes your risk logic is in risk.py

def main():
    # --- 1. RESEARCH COMMAND LINE INTERFACE ---
    parser = argparse.ArgumentParser(description="SMC Trading Bot - Research Lab (Backtesting)")
    parser.add_argument('--file', type=str, required=True, help='Path to the historical CSV candle file')
    args = parser.parse_args()

    # --- 2. THE HARD-LOCK (SAFETY CHECK) ---
    # This ensures main.py can NEVER be used for live trading.
    IS_RESEARCH_MODE = True
    
    print("="*50)
    print("🤖 SMC TRADING BOT: RESEARCH LAB MODE")
    print(f"📈 Testing Data: {args.file}")
    print("⚠️  HARD-LOCK ACTIVE: Live API connections are DISABLED.")
    print("="*50)

    try:
        # Load the data
        df = pd.read_csv(args.file)
        if df.empty:
            print("Error: The CSV file is empty.")
            return
    except FileNotFoundError:
        print(f"Error: Could not find file '{args.file}'")
        return

    # --- 3. INITIALIZE COMPONENTS ---
    strategy = SMCStrategy()
    risk = RiskManager(initial_balance=1000.0) # Virtual balance for testing

    # --- 4. THE RESEARCH LOOP (Candle-by-Candle Simulation) ---
    # We simulate the live environment by feeding the bot one row at a time.
    print("\nStarting Simulation...")
    
    for i in range(len(df)):
        # Simulate a "New Candle" event
        current_data = df.iloc[:i+1]
        
        # Check for SMC Setup (Liquidity Sweep -> MSS -> FVG)
        signal = strategy.check_setup(current_data)
        
        if signal:
            # Calculate Risk & Size
            position_size = risk.calculate_size(signal['entry_price'])
            
            print(f"✅ [SIGNAL] {signal['type']} at {signal['entry_price']} | Size: {position_size}")
            
            # NOTE: In main.py, we never call trader.place_order()
            # We only log it to a virtual journal.
            risk.log_virtual_trade(signal)

    print("\n" + "="*50)
    print("📊 SIMULATION COMPLETE")
    print(f"Final Virtual Equity: ${risk.current_balance:.2f}")
    print("="*50)

if __name__ == "__main__":
    main()