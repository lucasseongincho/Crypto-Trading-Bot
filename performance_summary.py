import pandas as pd
import numpy as np
import os
import glob
import argparse

def get_latest_journal(coin_name=None):
    """
    Finds the newest file. 
    If coin_name is provided, filters for that specific coin (e.g., BTC).
    """
    if coin_name:
        # Look for files like trade_journal_BTC_*.csv
        pattern = f"trade_journal_{coin_name.upper()}_*.csv"
    else:
        # Look for any timestamped journal
        pattern = "trade_journal_*.csv"
        
    files = glob.glob(pattern)
    
    if not files:
        # Fallback to the default live journal if no timestamped files exist
        return "trade_journal.csv"
        
    # Return the most recently created file
    return max(files, key=os.path.getctime)

def calculate_performance(coin_name=None):
    # Automatically grab the relevant file
    journal_file = get_latest_journal(coin_name)
    
    if not os.path.exists(journal_file):
        print(f"❌ Error: {journal_file} not found.")
        return

    try:
        # Load the journal
        df = pd.read_csv(journal_file)
        
        if df.empty:
            print(f"⚠️ Warning: {journal_file} is empty. No trades to analyze.")
            return
            
        # Ensure P/L_USD is numeric and handle potential string issues
        df['P/L_USD'] = pd.to_numeric(df['P/L_USD'], errors='coerce').fillna(0)
        
        # 1. Basic Metrics
        total_trades = len(df)
        winning_trades = df[df['P/L_USD'] > 0]
        losing_trades = df[df['P/L_USD'] < 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = df['P/L_USD'].sum()
        
        # 2. Advanced Metrics
        avg_win = winning_trades['P/L_USD'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['P/L_USD'].mean() if not losing_trades.empty else 0
        
        gross_profit = winning_trades['P/L_USD'].sum()
        gross_loss = abs(losing_trades['P/L_USD'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        # 3. Drawdown Calculation (Assuming $1000 starting capital)
        initial_balance = 1000
        df['Equity'] = initial_balance + df['P/L_USD'].cumsum()
        peak = df['Equity'].cummax()
        drawdown = (df['Equity'] - peak) / peak
        max_drawdown = drawdown.min() * 100

        # --- Print the Report ---
        print("\n" + "="*45)
        print(f"        📊 STRATEGY PERFORMANCE REPORT")
        print(f"   File: {journal_file}")
        print("="*45)
        print(f"Total Trades:         {total_trades}")
        print(f"Win Rate:             {win_rate:.2f}%")
        print(f"Total Profit/Loss:    ${total_pnl:.2f}")
        print(f"Profit Factor:        {profit_factor:.2f}")
        print("-" * 45)
        print(f"Average Win:          ${avg_win:.2f}")
        print(f"Average Loss:         ${avg_loss:.2f}")
        print(f"Largest Win:          ${df['P/L_USD'].max() if total_trades > 0 else 0:.2f}")
        print(f"Largest Loss:         ${df['P/L_USD'].min() if total_trades > 0 else 0:.2f}")
        print("-" * 45)
        print(f"Maximum Drawdown:     {max_drawdown:.2f}%")
        print(f"Final Equity:         ${df['Equity'].iloc[-1] if total_trades > 0 else initial_balance:.2f}")
        print("="*45)

    except PermissionError:
        print(f"❌ Error: Could not read {journal_file}. Close it in Excel first!")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Setup CLI for coin filtering
    parser = argparse.ArgumentParser(description="Analyze Strategy Performance")
    parser.add_argument("--coin", type=str, help="Specific coin to analyze (e.g., BTC, ETH, XRP)")
    args = parser.parse_args()

    calculate_performance(args.coin)