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
PRODUCT_ID = "BTC-USD"  # Updated to BTC based on your backtest
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
    
    status_msg = f"🛰️ Trade Active: {side} {qty:.4f} {PRODUCT_ID} | Entry: {entry} | SL: {sl}"
    print(status_msg)
    send_telegram(status_msg)
    
    while True:
        try:
            ticker = client.get_public_product(product_id=PRODUCT_ID)
            price = float(ticker['price'])
            
            # --- Trailing/Exit Logic ---
            if side == 'SELL':
                if not tp1_hit:
                    if price <= tp1: 
                        tp1_hit = True
                        send_telegram("💰 TP1 Hit! Stop Loss moved to Breakeven.")
                    elif price >= sl: final_exit_price = sl; break
                else:
                    if price <= tp2: final_exit_price = tp2; break
                    elif price >= entry: final_exit_price = entry; break # Breakeven exit

            elif side == 'BUY':
                if not tp1_hit:
                    if price >= tp1: 
                        tp1_hit = True
                        send_telegram("💰 TP1 Hit! Stop Loss moved to Breakeven.")
                    elif price <= sl: final_exit_price = sl; break
                else:
                    if price >= tp2: final_exit_price = tp2; break
                    elif price <= entry: final_exit_price = entry; break # Breakeven exit
            
            time.sleep(20) # Check price every 20 seconds
        except Exception as e:
            print(f"⚠️ Monitor Error: {e}")
            time.sleep(10); continue

    # Log to journal and RELEASE LOCK
    actual_pnl_usd = (abs(entry - final_exit_price) * qty) * (1 if (final_exit_price > entry and side == 'BUY') or (final_exit_price < entry and side == 'SELL') else -1)
    journal.log_trade({
        'entry_unix': entry_unix, 'exit_unix': time.time(), 'pair': PRODUCT_ID, 'side': side,
        'entry_price': entry, 'exit_price': final_exit_price, 'tp1_price': tp1, 'tp2_price': tp2,
        'sl_price': sl, 'pnl': actual_pnl_usd
    })
    
    is_in_position = False # LOCK OFF
    print(f"✅ Trade Closed at {final_exit_price}. PnL: ${actual_pnl_usd:.2f}")
    print("🔓 Bot is now free to look for new trades.")

# --- 4. MAIN BOT LOOP ---
def run_bot():
    print(f"🚀 SMC Bot Initializing with 4H Trend Filter...")
    print("-" * 30 + f"\n✅ Bot Online!\n💵 Balance: ${BALANCE:.2f}\n📍 Pair: {PRODUCT_ID}\n" + "-" * 30)

    while True:
        try:
            # 1. CHECK LOCK
            if is_in_position:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💤 Trade in progress... skipping scan.")
                time.sleep(60); continue

            # 2. SYNC TO 5-MINUTE CANDLE
            seconds_into_candle = int(time.time()) % 300
            if seconds_into_candle > 15:
                wait_time = 300 - seconds_into_candle + 2
                print(f"⏳ Syncing... Waiting {wait_time}s for next candle close.")
                time.sleep(wait_time)

            # 3. FETCH DATA (5M and 4H)
            now = int(time.time())
            
            # 5-Minute Candles
            resp_5m = client.get_public_candles(PRODUCT_ID, str(now - 300 * 110), str(now), "FIVE_MINUTE")
            candles_5m = resp_5m['candles']

            # 4-Hour (SIX_HOUR in Coinbase API is the standard for 4H/6H HTF)
            resp_htf = client.get_public_candles(PRODUCT_ID, str(now - 21600 * 50), str(now), "SIX_HOUR")
            candles_htf = resp_htf['candles']

            if not candles_5m or not candles_htf:
                print("⚠️ API returned empty data. Retrying..."); time.sleep(10); continue

            # 4. RUN STRATEGY
            signal, structural_p, counts = generate_trade_signal(candles_5m, candles_htf)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛰️ HEARTBEAT | Bias: {counts['bias']} | Bullish: {counts['bull']}/3 | Bearish: {counts['bear']}/3")

            # 5. EXECUTION
            if signal in ['BUY', 'SELL'] and structural_p:
                ticker = client.get_public_product(product_id=PRODUCT_ID)
                entry_p = float(ticker['price'])
                
                # Position Sizing
                pos_usd, sl_p = calculate_position_size(BALANCE, RISK_PCT, entry_p, float(structural_p), signal)
                
                if pos_usd > 0:
                    tp1_p = calculate_take_profit(entry_p, sl_p, signal, 1.0) # 1:1 RR
                    tp2_p = calculate_take_profit(entry_p, sl_p, signal, 2.0) # 1:2 RR
                    
                    manage_trade(entry_p, tp1_p, tp2_p, sl_p, pos_usd/entry_p, signal, time.time())

            time.sleep(15)
        except Exception as e:
            print(f"❌ Critical Error: {e}"); time.sleep(60)

if __name__ == "__main__":
    run_bot()