import pandas as pd
import numpy as np
import os

def calculate_performance(journal_file="trade_journal.csv"):
    if not os.path.exists(journal_file):
        print(f"❌ Error: {journal_file} not found. Run a backtest first!")
        return

    try:
        # Load the journal
        df = pd.read_csv(journal_file)
        
        # Ensure P/L_USD is numeric
        df['P/L_USD'] = pd.to_numeric(df['P/L_USD'])
        
        # 1. Basic Metrics
        total_trades = len(df)
        winning_trades = df[df['P/L_USD'] > 0]
        losing_trades = df[df['P/L_USD'] < 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = df['P/L_USD'].sum()
        
        # 2. Advanced Metrics
        avg_win = winning_trades['P/L_USD'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['P/L_USD'].mean() if not losing_trades.empty else 0
        profit_factor = abs(winning_trades['P/L_USD'].sum() / losing_trades['P/L_USD'].sum()) if not losing_trades.empty else float('inf')
        
        # 3. Drawdown Calculation
        initial_balance = 1000
        df['Equity'] = initial_balance + df['P/L_USD'].cumsum()
        peak = df['Equity'].cummax()
        drawdown = (df['Equity'] - peak) / peak
        max_drawdown = drawdown.min() * 100

        # Print the Report
        print("\n" + "="*45)
        print(f"       📊 STRATEGY PERFORMANCE REPORT")
        print("="*45)
        print(f"Total Trades:         {total_trades}")
        print(f"Win Rate:             {win_rate:.2f}%")
        print(f"Total Profit/Loss:    ${total_pnl:.2f}")
        print(f"Profit Factor:        {profit_factor:.2f}")
        print("-" * 45)
        print(f"Average Win:          ${avg_win:.2f}")
        print(f"Average Loss:         ${avg_loss:.2f}")
        print(f"Largest Win:          ${df['P/L_USD'].max():.2f}")
        print(f"Largest Loss:         ${df['P/L_USD'].min():.2f}")
        print("-" * 45)
        print(f"Maximum Drawdown:     {max_drawdown:.2f}%")
        print(f"Final Equity:         ${df['Equity'].iloc[-1]:.2f}")
        print("="*45)

    except PermissionError:
        print("❌ Error: Could not read CSV. Please close 'trade_journal.csv' in Excel and try again!")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    calculate_performance()