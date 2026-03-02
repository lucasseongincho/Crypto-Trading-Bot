import os
import sys
import time
import requests
import pandas as pd
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# DIRECT IMPORTS
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
PAPER_MODE = False  # 🚨 Set to False to execute real trades
PRODUCT_ID = "BTC-USD"
IS_IN_POSITION = False 

# 📈 DYNAMIC KILL SWITCH VARIABLES
MAX_DRAWDOWN_PERCENT = 0.20  # Reduced to 20% for tighter live safety
HEARTBEAT_INTERVAL = 3600  
last_heartbeat_time = 0

# --- 3. HELPER FUNCTIONS ---

def get_live_balance():
    """Fetches the actual USD balance from Coinbase API."""
    try:
        accounts = client.get_accounts()
        for acc in accounts['accounts']:
            if acc['currency'] == 'USD':
                return float(acc['available_balance']['value'])
    except Exception as e:
        print(f"❌ Balance Fetch Error: {e}")
    return None

def send_telegram(message):
    prefix = "🚨 [LIVE SNIPER] " if not PAPER_MODE else "📝 [PAPER SNIPER] "
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": prefix + message}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def parse_candles(response):
    raw_list = response['candles'] if isinstance(response, dict) else (response.candles if hasattr(response, 'candles') else response)
    clean_data = []
    for c in raw_list:
        if isinstance(c, dict): clean_data.append(c)
        elif hasattr(c, 'to_dict'): clean_data.append(c.to_dict())
        elif hasattr(c, '__dict__'): clean_data.append(vars(c))
            
    df = pd.DataFrame(clean_data)
    if not df.empty:
        df.columns = [str(x).lower() for x in df.columns]
        if 'start' in df.columns:
            df['start'] = df['start'].astype(int)
            df = df.sort_values('start', ascending=True).reset_index(drop=True)
    return df

# --- 4. MAIN EXECUTION LOOP ---

def run_bot():
    global last_heartbeat_time
    print(f"--- SNIPER BOT LIVE ---")
    
    # 💰 INITIALIZE DYNAMIC BALANCE
    live_bal = get_live_balance()
    if live_bal is None or live_bal == 0:
        print("❌ Could not verify balance. Check API keys.")
        sys.exit()

    balance = live_bal
    high_water_mark = balance
    total_trades = 0

    # 🧠 INITIALIZE CLASSES WITH LIVE DATA
    strategy = SMCStrategy()
    risk = RiskManager(initial_balance=balance)
    
    send_telegram(f"🚀 Sniper Bot is ONLINE.\nMode: {'PAPER' if PAPER_MODE else 'LIVE'}\nSync Balance: ${balance:.2f}")
    
    while True:
        try:
            # 🔄 Refresh balance from Coinbase to keep math perfect
            current_bal = get_live_balance()
            if current_bal:
                balance = current_bal
                risk.current_balance = balance # Keep risk manager in sync
            
            # 📈 Update Peak Balance (High Water Mark)
            if balance > high_water_mark:
                high_water_mark = balance
                
            dynamic_kill_limit = high_water_mark * (1.0 - MAX_DRAWDOWN_PERCENT)

            # 🛑 The Dynamic Kill Switch
            if balance <= dynamic_kill_limit:
                msg = f"🚨 FATAL: Drawdown Limit. Balance: ${balance:.2f}. Shutting down."
                send_telegram(msg)
                sys.exit()

            # 💓 Heartbeat
            current_time = time.time()
            if current_time - last_heartbeat_time >= HEARTBEAT_INTERVAL:
                status_msg = (
                    f"💓 Heartbeat Status\n"
                    f"💰 Balance: ${balance:.2f}\n"
                    f"🛑 Kill Limit: ${dynamic_kill_limit:.2f}\n"
                    f"🔎 Scanning: {PRODUCT_ID}"
                )
                send_telegram(status_msg)
                last_heartbeat_time = current_time

            # ⏳ Sync to 5-minute candle closes
            wait = 300 - (int(time.time()) % 300) + 2
            print(f"⌛ Syncing... scanning in {wait}s")
            time.sleep(wait)

            now = int(time.time())
            resp_5m = client.get_public_candles(PRODUCT_ID, str(now - 300*150), str(now), "FIVE_MINUTE")
            resp_htf = client.get_public_candles(PRODUCT_ID, str(now - 21600*50), str(now), "SIX_HOUR")
            
            df_5m = parse_candles(resp_5m)
            df_htf = parse_candles(resp_htf)

            if not df_5m.empty:
                signal_data = strategy.check_setup(df_5m, df_htf)
                
                if signal_data:
                    side = signal_data['type']
                    entry = signal_data['entry_price']
                    sl = signal_data['stop_loss']
                    
                    # 🧮 Position sizing now uses real $200 math
                    qty = risk.calculate_size(entry, sl)
                    
                    if qty > 0:
                        # 1. Format quantity to 5 decimals to prevent Coinbase "Tick Size" errors
                        formatted_qty = f"{qty:.5f}"
                        print(f"🚀 ATTEMPTING TO EXECUTE {side} ORDER FOR {formatted_qty} {PRODUCT_ID}...")
                        
                        try:
                            # 2. Generate a unique Order ID (Required by Coinbase)
                            order_id = str(uuid.uuid4())
                            
                            # 3. Execute the Market Order based on trade direction
                            if side.upper() in ['BUY', 'LONG']:
                                response = client.market_order_buy(
                                    client_order_id=order_id,
                                    product_id=PRODUCT_ID,
                                    base_size=formatted_qty
                                )
                            elif side.upper() in ['SELL', 'SHORT']:
                                response = client.market_order_sell(
                                    client_order_id=order_id,
                                    product_id=PRODUCT_ID,
                                    base_size=formatted_qty
                                )
                            else:
                                print(f"⚠️ Unknown trade side: {side}")
                                continue

                            # 4. Success! Log it and alert Telegram
                            print(f"✅ TRADE EXECUTED SUCCESSFULLY! Coinbase Response: {response}")
                            send_telegram(f"✅ LIVE TRADE EXECUTED!\nDirection: {side}\nSize: {formatted_qty} BTC\nTarget Entry: ${entry:.2f}")
                            
                            # 5. Tell the bot we are now in a trade
                            IS_IN_POSITION = True
                            
                        except Exception as e:
                            # 🚨 If Coinbase rejects it, this will scream EXACTLY why
                            error_msg = f"❌ TRADE FAILED TO EXECUTE: {e}"
                            print(error_msg)
                            send_telegram(error_msg)

        except Exception as e:
            print(f"Main Loop Error: {e}"); time.sleep(30)

if __name__ == "__main__":
    run_bot()