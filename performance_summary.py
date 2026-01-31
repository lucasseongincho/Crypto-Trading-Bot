import pandas as pd
import argparse
import os
import glob

def calculate_performance(filename):
    if not os.path.exists(filename):
        print(f"❌ Error: File {filename} not found.")
        return

    # Load the journal
    df = pd.read_csv(filename)
    
    if df.empty:
        print("⚠️ Journal is empty. No trades to analyze.")
        return

    # --- COLUMN MAPPING ---
    # Using explicit names to ensure compatibility with your 11-column journal
    pnl_col = 'P/L_USD'
    
    total_trades = len(df)
    winning_trades = df[df[pnl_col] > 0]
    losing_trades = df[df[pnl_col] < 0]
    
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    total_pnl = df[pnl_col].sum()
    
    # Profit Factor calculation
    gross_profit = winning_trades[pnl_col].sum()
    gross_loss = abs(losing_trades[pnl_col].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

    # Equity Curve & Drawdown
    df['Cumulative_PnL'] = df[pnl_col].cumsum()
    df['Equity_Curve'] = 1000 + df['Cumulative_PnL'] 
    df['Peak'] = df['Equity_Curve'].cummax()
    df['Drawdown'] = (df['Equity_Curve'] - df['Peak']) / df['Peak'] * 100
    max_drawdown = df['Drawdown'].min()

    print("\n" + "="*45)
    print("         📊 STRATEGY PERFORMANCE REPORT")
    print(f"    File: {filename}")
    print("="*45)
    print(f"Total Trades:         {total_trades}")
    print(f"Win Rate:             {win_rate:.2f}%")
    print(f"Total Profit/Loss:    ${total_pnl:.2f}")
    print(f"Profit Factor:        {profit_factor:.2f}")
    print("-" * 45)
    print(f"Average Win:          ${winning_trades[pnl_col].mean() if not winning_trades.empty else 0:.2f}")
    print(f"Average Loss:         ${losing_trades[pnl_col].mean() if not losing_trades.empty else 0:.2f}")
    print(f"Maximum Drawdown:     {max_drawdown:.2f}%")
    print(f"Final Equity:         ${df['Equity_Curve'].iloc[-1]:.2f}")
    print("="*45 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze SMC Bot Performance")
    parser.add_argument("--file", help="Path to a specific trade journal CSV")
    parser.add_argument("--coin", help="Coin ticker to find the latest journal (e.g., ETH)")
    args = parser.parse_args()
    
    if args.file:
        calculate_performance(args.file)
    elif args.coin:
        # Search for files matching 'trade_journal_COIN_*.csv'
        search_pattern = f"trade_journal_{args.coin.upper()}_*.csv"
        files = glob.glob(search_pattern)
        
        if files:
            # Sort by creation time to get the newest file
            latest_file = max(files, key=os.path.getctime)
            print(f"📂 Found latest journal: {latest_file}")
            calculate_performance(latest_file)
        else:
            print(f"❌ No journal files found for {args.coin.upper()} in this directory.")
    else:
        print("Usage:")
        print("  python performance_summary.py --file trade_journal_ETH_2026.csv")
        print("  python performance_summary.py --coin ETH")