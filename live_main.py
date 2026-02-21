import os
import sys
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# DIRECT IMPORTS FROM YOUR FILES
from auth import client # Uses your cdp_api_key.json hub
from strategy import SMCStrategy
from risk import RiskManager
import journal 

# --- 1. SETUP & ENV ---
base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- 2. CONFIGURATION ---
PAPER_MODE = True  # Set to False to execute real trades
PRODUCT_ID = "BTC-USD"
BALANCE = 20000.0   # Default starting balance for Paper Mode
TOTAL_TRADES = 0   
IS_IN_POSITION = False 

# 📈 DYNAMIC KILL SWITCH VARIABLES
HIGH_WATER_MARK = BALANCE
MAX_DRAWDOWN_PERCENT = 0.30  # 30% acceptable drop from the peak

HEARTBEAT_INTERVAL = 3600  
last_heartbeat_time = 0

# 🧠 INITIALIZE THE CLASSES
strategy = SMCStrategy()
risk = RiskManager(initial_balance=BALANCE)

# --- 3. HELPER FUNCTIONS ---

def send_telegram(message):
    prefix = "🚨 [LIVE SNIPER] " if not PAPER_MODE else "📝 [PAPER SNIPER] "
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": prefix + message}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# 🛡️ Safely parse the Coinbase SDK response
def parse_candles(response):
    """
    Converts Coinbase objects/dicts into a clean Pandas DataFrame.
    Prevents the 'int object' error and ensures chronological order.
    """
    raw_list = response['candles'] if isinstance(response, dict) else (response.candles if hasattr(response, 'candles') else response)
    
    clean_data = []
    for c in raw_list:
        if isinstance(c, dict):
            clean_data.append(c)
        elif hasattr(c, 'to_dict'):
            clean_data.append(c.to_dict())
        elif hasattr(c, '__dict__'):
            clean_data.append(vars(c))
            
    df = pd.DataFrame(clean_data)
    
    if not df.empty:
        df.columns = [str(x).lower() for x in df.columns]
        # ⚠️ CRITICAL FIX: Sort oldest to newest for SMC to read left-to-right!
        if 'start' in df.columns:
            df['start'] = df['start'].astype(int)
            df = df.sort_values('start', ascending=True).reset_index(drop=True)
            
    return df

def manage_trade(entry, sl, tp_final, qty, side, entry_unix):
    global IS_IN_POSITION, BALANCE, TOTAL_TRADES
    IS_IN_POSITION = True
    
    risk_dist = abs(entry - sl)
    tp_safety = entry + risk_dist if side == 'BUY' else entry - risk_dist
    
    is_breakeven = False
    final_exit_price = entry
    
    msg = f"🟢 Trade Opened: {side} {qty:.5f}\nEntry: {entry}\nSL: {sl}\nTarget (1.5R): {tp_final}"
    send_telegram(msg)
    print("\n" + msg)

    while True:
        try:
            ticker = client.get_public_product(product_id=PRODUCT_ID)
            price = float(ticker['price'])

            # 1. Check Stop Loss
            if (side == 'BUY' and price <= sl) or (side == 'SELL' and price >= sl):
                final_exit_price = sl
                break
            
            # 2. Check Take Profit
            if (side == 'BUY' and price >= tp_final) or (side == 'SELL' and price <= tp_final):
                final_exit_price = tp_final
                break

            # 3. Check Safety Target (Move to Breakeven)
            if not is_breakeven:
                if (side == 'BUY' and price >= tp_safety) or (side == 'SELL' and price <= tp_safety):
                    sl = entry 
                    is_breakeven = True
                    alert = f"🛡️ Safety reached! Stop Loss moved to Breakeven ({entry})"
                    send_telegram(alert)
                    print(alert)

            time.sleep(5) 
        except Exception as e:
            print(f"Monitor Error: {e}"); time.sleep(5)

    # Calculate PnL and Update Balance
    direction_mult = 1 if side == 'BUY' else -1
    pnl = (final_exit_price - entry) * qty * direction_mult
    
    BALANCE += pnl
    risk.current_balance = BALANCE # Keep Risk Manager in sync
    TOTAL_TRADES += 1
    
    # Log to CSV Journal
    try:
        journal.log_trade({
            'entry_unix': entry_unix, 'exit_unix': time.time(), 'pair': PRODUCT_ID, 'side': side,
            'entry_price': entry, 'exit_price': final_exit_price, 'tp1_price': tp_safety, 'tp2_price': tp_final,
            'sl_price': sl, 'pnl': round(pnl, 2),
            'balance': round(BALANCE, 2) 
        })
    except Exception as e:
        print(f"Journal Error: {e}")
    
    close_msg = f"🏁 Trade Closed at {final_exit_price}\nPnL: ${round(pnl, 2)}\nNew Balance: ${round(BALANCE, 2)}"
    send_telegram(close_msg)
    print("\n" + close_msg)
    IS_IN_POSITION = False

# --- 4. MAIN EXECUTION LOOP ---

def run_bot():
    global last_heartbeat_time, HIGH_WATER_MARK
    print(f"--- SNIPER BOT LIVE (1.11 PF LOGIC) ---")
    
    send_telegram(f"🚀 Sniper Bot is ONLINE.\nMode: {'PAPER' if PAPER_MODE else 'LIVE'}\nStarting Balance: ${BALANCE}")
    
    while True:
        try:
            # ==========================================
            # 📈 UPDATE HIGH WATER MARK
            # ==========================================
            if BALANCE > HIGH_WATER_MARK:
                HIGH_WATER_MARK = BALANCE
                
            dynamic_kill_limit = HIGH_WATER_MARK * (1.0 - MAX_DRAWDOWN_PERCENT)

            # ==========================================
            # 🛑 THE DYNAMIC KILL SWITCH
            # ==========================================
            if BALANCE <= dynamic_kill_limit:
                msg = (f"🚨 FATAL: Balance dropped to ${round(BALANCE, 2)}.\n"
                       f"📉 This is a 30% drop from peak (${round(HIGH_WATER_MARK, 2)}).\n"
                       f"🛑 Kill Switch Activated. Bot shutting down forever.")
                print("\n" + msg)
                send_telegram(msg)
                sys.exit() 

            # ==========================================
            # 💓 HEARTBEAT & STATUS ALERTS
            # ==========================================
            current_time = time.time()
            if current_time - last_heartbeat_time >= HEARTBEAT_INTERVAL:
                status_msg = (
                    f"💓 Heartbeat Status\n"
                    f"💰 Balance: ${round(BALANCE, 2)}\n"
                    f"🏔️ Peak Balance: ${round(HIGH_WATER_MARK, 2)}\n"
                    f"🛑 Kill Limit: ${round(dynamic_kill_limit, 2)}\n"
                    f"📊 Total Trades: {TOTAL_TRADES}\n"
                    f"🔎 Scanning: {PRODUCT_ID}"
                )
                send_telegram(status_msg)
                last_heartbeat_time = current_time

            if IS_IN_POSITION:
                time.sleep(60); continue

            wait = 300 - (int(time.time()) % 300) + 2
            print(f"⌛ Syncing... scanning in {wait}s")
            time.sleep(wait)

            now = int(time.time())
            
            # 📡 Fetch Data
            resp_5m = client.get_public_candles(PRODUCT_ID, str(now - 300*150), str(now), "FIVE_MINUTE")
            resp_htf = client.get_public_candles(PRODUCT_ID, str(now - 21600*50), str(now), "SIX_HOUR")
            
            # 🛡️ Parse & Sort Data
            df_5m = parse_candles(resp_5m)
            df_htf = parse_candles(resp_htf)

            if df_5m.empty:
                print("⚠️ Received empty data from Coinbase. Retrying...")
                continue

            # 🧠 Run strategy logic
            signal_data = strategy.check_setup(df_5m, df_htf)
            
            if signal_data:
                side = signal_data['type']
                entry = signal_data['entry_price']
                sl = signal_data['stop_loss']
                
                # 🧮 Dynamic Risk Sizing
                qty = risk.calculate_size(entry, sl)
                
                if qty > 0:
                    risk_dist = abs(entry - sl)
                    tp_final = entry + (risk_dist * risk.rr_ratio) if side == 'BUY' else entry - (risk_dist * risk.rr_ratio)
                    
                    manage_trade(entry, sl, round(tp_final, 2), qty, side, time.time())

        except Exception as e:
            print(f"Main Loop Error: {e}"); time.sleep(30)

if __name__ == "__main__":
    run_bot()