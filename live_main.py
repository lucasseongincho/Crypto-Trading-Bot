import os
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# DIRECT IMPORTS FROM YOUR FILES
from auth import client # Uses your cdp_api_key.json hub
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
import journal 

# --- 1. SETUP & ENV ---
base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- 2. CONFIGURATION ---
PAPER_MODE = True  # Set to False to execute real trades on Coinbase
PRODUCT_ID = "BTC-USD"
BALANCE = 1000.0   # Default starting balance for Paper Mode
TOTAL_TRADES = 0   # Counter for Heartbeat
IS_IN_POSITION = False 

# Heartbeat Settings
HEARTBEAT_INTERVAL = 3600  # 1hour (3600 sec)
last_heartbeat_time = 0

# --- 3. HELPER FUNCTIONS ---

def send_telegram(message):
    """Uses your .env keys to send real-time alerts."""
    prefix = "🚨 [LIVE SNIPER] " if not PAPER_MODE else "📝 [PAPER SNIPER] "
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": prefix + message}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_atr(candles, period=14):
    """Calculates ATR to satisfy the requirement in your risk.py."""
    if len(candles) < period + 1: return 0
    trs = []
    for i in range(1, period + 1):
        h = float(candles[-i]['high'])
        l = float(candles[-i]['low'])
        pc = float(candles[-i-1]['close'])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    return sum(trs) / len(trs)

def manage_trade(entry, sl, tp_final, qty, side, entry_unix):
    """
    Hybrid Management:
    1. Monitors for 1:1 RR to move SL to Breakeven.
    2. Closes at 1.5R.
    """
    global IS_IN_POSITION, BALANCE, TOTAL_TRADES
    IS_IN_POSITION = True
    
    risk_dist = abs(entry - sl)
    tp_safety = entry + risk_dist if side == 'BUY' else entry - risk_dist
    
    is_breakeven = False
    final_exit_price = entry
    
    msg = f"🟢 Trade Opened: {side} {qty:.5f}\nEntry: {entry}\nSL: {sl}\nTarget (1.5R): {tp_final}"
    send_telegram(msg)

    while True:
        try:
            ticker = client.get_public_product(product_id=PRODUCT_ID)
            price = float(ticker['price'])

            # 1. CHECK STOP LOSS
            if (side == 'BUY' and price <= sl) or (side == 'SELL' and price >= sl):
                final_exit_price = sl
                break
            
            # 2. CHECK TAKE PROFIT (1.5R)
            if (side == 'BUY' and price >= tp_final) or (side == 'SELL' and price <= tp_final):
                final_exit_price = tp_final
                break

            # 3. CHECK BREAKEVEN TRIGGER (1:1R)
            if not is_breakeven:
                if (side == 'BUY' and price >= tp_safety) or (side == 'SELL' and price <= tp_safety):
                    sl = entry 
                    is_breakeven = True
                    send_telegram(f"🛡️ Safety reached! Stop Loss moved to Breakeven ({entry})")

            time.sleep(5) 
        except Exception as e:
            print(f"Monitor Error: {e}"); time.sleep(5)

    # EXIT LOGIC & STATS UPDATE
    pnl = (abs(entry - final_exit_price) * qty) * (1 if (final_exit_price > entry and side == 'BUY') or (final_exit_price < entry and side == 'SELL') else -1)
    
    BALANCE += pnl
    TOTAL_TRADES += 1
    
    journal.log_trade({
        'entry_unix': entry_unix, 'exit_unix': time.time(), 'pair': PRODUCT_ID, 'side': side,
        'entry_price': entry, 'exit_price': final_exit_price, 'tp1_price': tp_safety, 'tp2_price': tp_final,
        'sl_price': sl, 'pnl': round(pnl, 2)
    })
    
    send_telegram(f"🏁 Trade Closed at {final_exit_price}\nPnL: ${round(pnl, 2)}\nNew Balance: ${round(BALANCE, 2)}")
    IS_IN_POSITION = False

# --- 4. MAIN EXECUTION LOOP ---

def run_bot():
    global last_heartbeat_time
    print(f"--- SNIPER BOT LIVE (1.11 PF LOGIC) ---")
    
    # POWER ON NOTIFICATION
    send_telegram(f"🚀 Sniper Bot is ONLINE.\nMode: {'PAPER' if PAPER_MODE else 'LIVE'}\nStarting Balance: ${BALANCE}")
    
    while True:
        try:
            # HEARTBEAT LOGIC
            current_time = time.time()
            if current_time - last_heartbeat_time >= HEARTBEAT_INTERVAL:
                status_msg = (
                    f"💓 Heartbeat Status\n"
                    f"💰 Balance: ${round(BALANCE, 2)}\n"
                    f"📊 Total Trades: {TOTAL_TRADES}\n"
                    f"🔎 Scanning: {PRODUCT_ID}"
                )
                send_telegram(status_msg)
                last_heartbeat_time = current_time

            if IS_IN_POSITION:
                time.sleep(60); continue

            # Sync to the 5m candle close
            wait = 300 - (int(time.time()) % 300) + 2
            print(f"⌛ Syncing... scanning in {wait}s")
            time.sleep(wait)

            # Fetch Data
            now = int(time.time())
            c_5m = client.get_public_candles(PRODUCT_ID, str(now - 300*150), str(now), "FIVE_MINUTE")['candles']
            c_htf = client.get_public_candles(PRODUCT_ID, str(now - 21600*50), str(now), "SIX_HOUR")['candles']

            # Run strategy logic
            signal, structural_p, counts = generate_trade_signal(c_5m, c_htf)
            
            if signal in ['BUY', 'SELL'] and structural_p:
                ticker = client.get_public_product(product_id=PRODUCT_ID)
                price = float(ticker['price'])
                atr = get_atr(c_5m)
                
                pos_usd, sl_price = calculate_position_size(BALANCE, 1.0, price, float(structural_p), signal, atr)
                
                if pos_usd > 0:
                    tp_price = calculate_take_profit(price, sl_price, signal, 1.5)
                    manage_trade(price, sl_price, tp_price, pos_usd/price, signal, time.time())

        except Exception as e:
            print(f"Main Loop Error: {e}"); time.sleep(30)

if __name__ == "__main__":
    run_bot()