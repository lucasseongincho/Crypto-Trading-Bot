import os
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from coinbase.rest import RESTClient
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
import journal 

# --- 1. SETUP & ENV ---
base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- 2. CONFIGURATION ---
PAPER_MODE = True  
PRODUCT_ID = "ETH-USD"
BALANCE = 1000.0 if PAPER_MODE else 0.0 
RISK_PCT = 1.0  
LOOKBACK_WINDOW = 100 

# SAFETY LOCK: Ensures only one trade is managed at a time
is_in_position = False 

# Initialize Coinbase Client
KEY_FILE_PATH = base_dir / "cdp_api_key.json"
client = RESTClient(key_file=str(KEY_FILE_PATH))

# --- 3. HELPER FUNCTIONS ---
def send_telegram(message):
    prefix = "[PAPER] " if PAPER_MODE else "[LIVE] "
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": prefix + message}, timeout=10)
    except Exception: pass

def manage_trade(entry, tp1, tp2, sl, qty, side, entry_unix):
    """Monitors trade and releases the position lock when finished."""
    global is_in_position
    is_in_position = True # LOCK ON
    
    entry, tp1, tp2, sl, qty = map(float, [entry, tp1, tp2, sl, qty])
    tp1_hit = False
    final_exit_price = entry
    
    status_msg = f"🛰️ Trade Active: {side} {qty:.4f} ETH | Entry: {entry} | SL: {sl}"
    print(status_msg)
    send_telegram(status_msg)
    
    while True:
        try:
            ticker = client.get_public_product(product_id=PRODUCT_ID)
            price = float(ticker['price'])
            
            # --- Trailing/Exit Logic ---
            if side == 'SELL':
                if not tp1_hit:
                    if price <= tp1: tp1_hit = True; send_telegram("💰 TP1 Hit! Risk removed.")
                    elif price >= sl: final_exit_price = sl; break
                else:
                    if price <= tp2: final_exit_price = (tp1 + tp2) / 2; break
                    elif price >= entry: final_exit_price = (tp1 + entry) / 2; break
            elif side == 'BUY':
                if not tp1_hit:
                    if price >= tp1: tp1_hit = True; send_telegram("💰 TP1 Hit! Risk removed.")
                    elif price <= sl: final_exit_price = sl; break
                else:
                    if price >= tp2: final_exit_price = (tp1 + tp2) / 2; break
                    elif price <= entry: final_exit_price = (tp1 + entry) / 2; break
            time.sleep(30)
        except Exception: time.sleep(10); continue

    # Log to journal and RELEASE LOCK
    actual_pnl_usd = (abs(entry - final_exit_price) * qty) * (1 if (final_exit_price > entry and side == 'BUY') or (final_exit_price < entry and side == 'SELL') else -1)
    journal.log_trade({
        'entry_unix': entry_unix, 'exit_unix': time.time(), 'pair': PRODUCT_ID, 'side': side,
        'entry_price': entry, 'exit_price': final_exit_price, 'tp1_price': tp1, 'tp2_price': tp2,
        'sl_price': sl, 'pnl': actual_pnl_usd
    })
    
    is_in_position = False # LOCK OFF
    print("🔓 Bot is now free to look for new trades.")

# --- 4. MAIN BOT LOOP ---
def run_bot():
    print(f"🚀 SMC Bot Initializing in {'VIRTUAL' if PAPER_MODE else 'REAL MONEY'} mode...")
    print("-" * 30 + f"\n✅ Bot Online!\n💵 Balance: ${BALANCE:.2f}\n📍 Pair: {PRODUCT_ID}\n" + "-" * 30)

    while True:
        try:
            # CHECK LOCK FIRST
            if is_in_position:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💤 Trade in progress... skipping scan.")
                time.sleep(60); continue

            # Timing Sync
            seconds_into_candle = int(time.time()) % 300
            if seconds_into_candle > 10:
                wait_time = 300 - seconds_into_candle + 1
                print(f"⏳ Waiting {wait_time}s for next candle close...")
                time.sleep(wait_time)

            # Fetch Data
            end_ts = int(time.time())
            start_ts = end_ts - (300 * 110) # 10 extra candles for buffer
            response = client.get_public_candles(product_id=PRODUCT_ID, granularity="FIVE_MINUTE", start=str(start_ts), end=str(end_ts))
            candles = response['candles']

            if not candles or len(candles) < LOOKBACK_WINDOW:
                print("⚠️ Data Warning: Insufficient candles. Retrying..."); time.sleep(10); continue

            # Strategy Signal
            signal, structural_p, counts = generate_trade_signal(candles, len(candles) - 1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛰️ HEARTBEAT | Trend: {counts['trend']} | Bullish: {counts['bull']}/3 | Bearish: {counts['bear']}/3")

            if signal in ['BUY', 'SELL'] and structural_p:
                ticker = client.get_public_product(product_id=PRODUCT_ID)
                entry_p = float(ticker['price'])
                
                # Risk Calc
                pos_usd, sl_p = calculate_position_size(BALANCE, RISK_PCT, entry_p, float(structural_p), signal)
                if pos_usd > 0:
                    tp1_p = calculate_take_profit(entry_p, sl_p, signal, 1.0)
                    tp2_p = calculate_take_profit(entry_p, sl_p, signal, 2.0)
                    manage_trade(entry_p, tp1_p, tp2_p, sl_p, pos_usd/entry_p, signal, time.time())

            time.sleep(15)
        except Exception as e:
            print(f"❌ Critical Error: {e}"); time.sleep(60)

if __name__ == "__main__":
    run_bot()