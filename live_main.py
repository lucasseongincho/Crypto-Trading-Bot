import os
import sys
import time
import requests
import pandas as pd
import uuid
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# DIRECT IMPORTS
from auth import client # Uses your cdp_api_key.json hub
from strategy import SMCStrategy
from risk import RiskManager

# --- 1. SETUP & ENV ---
base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- 2. CONFIGURATION ---
PAPER_MODE = True  # 📝 Set to True for simulated trading!
PAPER_BALANCE = 20000.0  # 💰 Your starting simulated balance
PRODUCT_ID = "BTC-USD"

# GLOBAL STATE
IS_IN_POSITION = False 
balance = 0.0  # Will be set to either live balance or paper balance

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

def update_bot_status(is_active, side=None, entry=None, qty=None, tp=None, sl=None):
    """Bridge to the Streamlit Dashboard. Saves active trade status to a JSON file."""
    status_file = base_dir / "bot_status.json"
    status_data = {
        "is_in_position": is_active,
        "side": side,
        "entry_price": entry,
        "qty": qty,
        "take_profit": tp,
        "stop_loss": sl,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(status_file, "w") as f:
            json.dump(status_data, f)
    except Exception as e:
        print(f"⚠️ Could not write to bot_status.json: {e}")


# --- 4. TRADE MANAGEMENT SENTRY ---
def manage_trade(entry_price, stop_loss, qty, side, risk_manager):
    """
    Monitors an open position. Executes a market sell when SL or TP is hit.
    In PAPER_MODE, it bypasses Coinbase and simulates the PnL return.
    """
    global IS_IN_POSITION
    global balance
    
    risk_per_coin = abs(entry_price - stop_loss)
    
    if side.upper() in ['BUY', 'LONG']:
        take_profit = entry_price + (risk_per_coin * 1.5)
    else:
        take_profit = entry_price - (risk_per_coin * 1.5)

    print(f"👀 SENTRY ACTIVE | Entry: ${entry_price:.2f} | Target: ${take_profit:.2f} | Stop: ${stop_loss:.2f}")
    send_telegram(f"👀 Trade Sentry Active!\nWatching {qty:.5f} BTC.\n🎯 Target: ${take_profit:.2f}\n🛡️ Stop: ${stop_loss:.2f}")

    # 🌉 Bridge: Tell the dashboard we are in a trade!
    update_bot_status(True, side.upper(), entry_price, qty, take_profit, stop_loss)

    while True:
        try:
            # 1. Fetch the exact live price from Coinbase
            product = client.get_product(PRODUCT_ID)
            if isinstance(product, dict):
                current_price = float(product['price'])
            else:
                current_price = float(product.price)

            reason = None
            
            # 2. Check targets (Direction-Aware Logic!)
            if side.upper() in ['BUY', 'LONG']:
                if current_price >= take_profit:
                    reason = "🎯 TAKE PROFIT"
                elif current_price <= stop_loss:
                    reason = "🛑 STOP LOSS"
            else: # SELL / SHORT Logic
                if current_price <= take_profit:
                    reason = "🎯 TAKE PROFIT"
                elif current_price >= stop_loss:
                    reason = "🛑 STOP LOSS"

            # 3. If a target is hit, break the loop and execute the sell!
            if reason:
                print(f"🚨 {reason} TRIGGERED at ${current_price:.2f}! Executing Sell...")
                break

            time.sleep(5)

        except Exception as e:
            print(f"⚠️ Sentry Price Fetch Error: {e}")
            time.sleep(5)

    # --- EXECUTE THE EXIT ---
    try:
        formatted_qty = f"{qty:.5f}"
        
        if PAPER_MODE:
            print(f"📝 PAPER MODE: Simulating market exit for {formatted_qty} BTC...")
        else:
            # LIVE TRADING: Actually close the position
            order_id = str(uuid.uuid4())
            if side.upper() in ['BUY', 'LONG']:
                response = client.market_order_sell(client_order_id=order_id, product_id=PRODUCT_ID, base_size=formatted_qty)
            else:
                # Close a short by buying back
                response = client.market_order_buy(client_order_id=order_id, product_id=PRODUCT_ID, base_size=formatted_qty)

        # 🧮 Calculate Profit/Loss CORRECTLY based on direction
        if side.upper() in ['BUY', 'LONG']:
            pnl = (current_price - entry_price) * qty
        else:
            pnl = (entry_price - current_price) * qty # Short math!
        
        if PAPER_MODE:
            balance += pnl
            risk_manager.current_balance = balance
            print(f"📝 PAPER BALANCE UPDATED: ${balance:.2f}")

        print(f"✅ TRADE CLOSED. Result: {reason} | Approx PnL: ${pnl:.2f}")
        send_telegram(f"✅ TRADE CLOSED ({reason})\nExit Price: ${current_price:.2f}\nApprox PnL: ${pnl:.2f}\nNew Balance: ${balance:.2f}")

        # --- THE ACCOUNTANT: Log to CSV for Streamlit ---
        try:
            trade_record = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Pair": PRODUCT_ID,
                "Side": side.upper(),
                "Entry": round(entry_price, 2),
                "Exit": round(current_price, 2),
                "Result": "WIN" if pnl > 0 else "LOSS",
                "PnL": round(pnl, 2),
                "Balance": round(balance, 2)
            }
            
            df_trade = pd.DataFrame([trade_record])
            csv_file = base_dir / "trade_journal.csv"
            
            if os.path.isfile(csv_file):
                df_trade.to_csv(csv_file, mode='a', header=False, index=False)
            else:
                df_trade.to_csv(csv_file, mode='w', header=True, index=False)
                
            print("💾 Trade securely logged to trade_journal.csv!")
            
        except Exception as e:
            print(f"⚠️ Could not write to journal: {e}")

    except Exception as e:
        error_msg = f"❌ EXIT EXECUTION FAILED: {e}"
        print(error_msg)
        send_telegram(error_msg)
        
    finally:
        IS_IN_POSITION = False
        # 🌉 Bridge: Tell the dashboard we are no longer in a trade
        update_bot_status(False)


# --- 5. MAIN EXECUTION LOOP ---

def run_bot():
    global last_heartbeat_time
    global balance
    print(f"--- SNIPER BOT LIVE ---")
    
    # 💰 INITIALIZE BALANCE (LIVE OR PAPER)
    if PAPER_MODE:
        balance = PAPER_BALANCE
        print(f"📝 PAPER TRADING ACTIVE. Starting with simulated ${balance:.2f}")
    else:
        live_bal = get_live_balance()
        if live_bal is None or live_bal == 0:
            print("❌ Could not verify live balance. Check API keys.")
            sys.exit()
        balance = live_bal

    high_water_mark = balance

    # 🧠 INITIALIZE CLASSES
    strategy = SMCStrategy()
    risk = RiskManager(initial_balance=balance)
    
    send_telegram(f"🚀 Sniper Bot is ONLINE.\nMode: {'PAPER' if PAPER_MODE else 'LIVE'}\nSync Balance: ${balance:.2f}")
    
    # Reset Dashboard JSON status on startup
    update_bot_status(False)

    while True:
        try:
            # 🔄 Refresh balance
            if not PAPER_MODE:
                current_bal = get_live_balance()
                if current_bal:
                    balance = current_bal
                    risk.current_balance = balance 
            else:
                risk.current_balance = balance # Keep paper risk synced

            # 📈 Update Peak Balance (High Water Mark)
            if balance > high_water_mark:
                high_water_mark = balance
                
            dynamic_kill_limit = high_water_mark * (1.0 - MAX_DRAWDOWN_PERCENT)

            if balance <= dynamic_kill_limit:
                msg = f"🚨 FATAL: Drawdown Limit. Balance: ${balance:.2f}. Shutting down."
                send_telegram(msg)
                sys.exit()

            current_time = time.time()
            if current_time - last_heartbeat_time >= HEARTBEAT_INTERVAL:
                status_msg = (f"💓 Heartbeat Status\n💰 Balance: ${balance:.2f}\n🛑 Kill Limit: ${dynamic_kill_limit:.2f}\n🔎 Scanning: {PRODUCT_ID}")
                send_telegram(status_msg)
                last_heartbeat_time = current_time

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
                    
                    qty = risk.calculate_size(entry, sl)
                    
                    if qty > 0:
                        formatted_qty = f"{qty:.5f}"
                        print(f"🚀 ATTEMPTING TO EXECUTE {side} ORDER FOR {formatted_qty} {PRODUCT_ID}...")
                        
                        try:
                            if PAPER_MODE:
                                print(f"📝 PAPER MODE: Simulating {side} execution...")
                                response = {'status': 'SIMULATED_SUCCESS', 'size': formatted_qty}
                            else:
                                # LIVE TRADING: Actually buy on Coinbase
                                order_id = str(uuid.uuid4())
                                if side.upper() in ['BUY', 'LONG']:
                                    response = client.market_order_buy(client_order_id=order_id, product_id=PRODUCT_ID, base_size=formatted_qty)
                                elif side.upper() in ['SELL', 'SHORT']:
                                    response = client.market_order_sell(client_order_id=order_id, product_id=PRODUCT_ID, base_size=formatted_qty)

                            print(f"✅ TRADE EXECUTED SUCCESSFULLY! Response: {response}")
                            send_telegram(f"✅ TRADE EXECUTED!\nDirection: {side}\nSize: {formatted_qty} BTC\nTarget Entry: ${entry:.2f}")
                            
                            IS_IN_POSITION = True
                            
                            # --- LAUNCH THE SENTRY ---
                            # Pass risk manager so sentry can update paper balance PnL
                            manage_trade(entry, sl, qty, side, risk)
                            
                        except Exception as e:
                            error_msg = f"❌ TRADE FAILED TO EXECUTE: {e}"
                            print(error_msg)
                            send_telegram(error_msg)

        except Exception as e:
            print(f"Main Loop Error: {e}"); time.sleep(30)

if __name__ == "__main__":
    run_bot()