import os
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from coinbase.rest import RESTClient
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
import trader
import journal 

# --- 1. SETUP & ENV ---
base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- 2. CONFIGURATION ---
PAPER_MODE = True  # Set to False for real trading
PRODUCT_ID = "ETH-USD"
BALANCE = 1000.0 if PAPER_MODE else 0.0 
RISK_PCT = 1.0  
LOOKBACK_WINDOW = 100 

# Initialize Coinbase Client (CDP API)
KEY_FILE_PATH = base_dir / "cdp_api_key.json"
client = RESTClient(key_file=str(KEY_FILE_PATH))

def send_telegram(message):
    prefix = "[PAPER] " if PAPER_MODE else "[LIVE] "
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": prefix + message}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_coinbase_balance(client):
    if PAPER_MODE: return BALANCE
    try:
        accounts = client.get_accounts()
        for acc in accounts.accounts:
            if acc.currency == 'USD':
                return float(acc.available_balance['value'])
        return 0.0
    except Exception as e:
        print(f"Balance Fetch Error: {e}")
        return 0.0

def run_bot():
    global BALANCE
    mode_text = "VIRTUAL (Paper)" if PAPER_MODE else "REAL MONEY"
    print(f"🚀 SMC Bot Initializing in {mode_text} mode...")
    
    if not PAPER_MODE:
        BALANCE = get_coinbase_balance(client)
    
    status_init = f"✅ Bot Online!\n💵 Balance: ${BALANCE:.2f}\n📍 Pair: {PRODUCT_ID}"
    print("-" * 30 + "\n" + status_init + "\n" + "-" * 30)
    send_telegram(status_init)

    while True:
        try:
            # --- 1. TIMING SYNC ---
            current_time = time.time()
            seconds_into_candle = int(current_time) % 300
            
            if seconds_into_candle > 10:
                wait_time = 300 - seconds_into_candle + 1
                print(f"⏳ Waiting {wait_time}s for next candle close...")
                time.sleep(wait_time)

            # --- 2. FETCH DATA ---
            end_ts = int(time.time())
            start_ts = end_ts - (300 * 300)
            
            candles_response = client.get_public_candles(
                product_id=PRODUCT_ID, 
                granularity="FIVE_MINUTE", 
                start=str(start_ts), 
                end=str(end_ts)
            )
            candles = candles_response['candles']

            if len(candles) < LOOKBACK_WINDOW:
                print(f"⚠️ Data warm-up: {len(candles)}/{LOOKBACK_WINDOW}")
                time.sleep(60)
                continue

            # --- 3. GENERATE SIGNAL & HEARTBEAT ---
            signal, structural_price, counts = generate_trade_signal(candles, len(candles) - 1)
            
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] 🛰️ HEARTBEAT")
            print(f"   ├─ Trend: {counts['trend']} | Fakeout: {counts['fake']}")
            print(f"   ├─ Bullish: {counts['bull']}/3")
            print(f"   └─ Bearish: {counts['bear']}/3")

            # --- 4. EXECUTION LOGIC ---
            if signal in ['BUY', 'SELL'] and structural_price:
                ticker = client.get_public_product(product_id=PRODUCT_ID)
                entry_price = float(ticker['price'])
                
                # FIX: Explicitly convert structural_price to float to avoid math errors
                sl_target = float(structural_price)
                
                # Position sizing and targets
                pos_size_usd, sl_price = calculate_position_size(BALANCE, RISK_PCT, entry_price, sl_target)
                tp2 = calculate_take_profit(entry_price, sl_price, 2.0)
                tp1 = entry_price + abs(entry_price - sl_price)

                print(f"🎯 {signal} Signal Found! Entry: {entry_price} | SL: {sl_price} | TP2: {tp2}")
                
                if PAPER_MODE:
                    qty = pos_size_usd / entry_price
                    send_telegram(f"📝 PAPER ORDER: {signal} {qty:.4f} ETH at {entry_price}")
                    journal.log_trade({
                        'side': signal, 'pair': PRODUCT_ID, 'entry_price': entry_price, 
                        'exit_price': 0, 'pnl': 0, 'entry_unix': time.time()
                    })
                    manage_trade(entry_price, tp1, tp2, sl_price, qty)
                else:
                    order = trader.place_market_order_buy(client, PRODUCT_ID, pos_size_usd)
                    if order:
                        qty = float(order['base_size'])
                        journal.log_trade({
                            'side': signal, 'pair': PRODUCT_ID, 'entry_price': entry_price, 
                            'entry_unix': time.time()
                        })
                        trader.place_initial_stop_loss(client, PRODUCT_ID, qty, sl_price)
                        manage_trade(entry_price, tp1, tp2, sl_price, qty)
                        BALANCE = get_coinbase_balance(client)

            # --- 5. COOL DOWN ---
            time.sleep(15)

        except Exception as e:
            print(f"❌ Critical Error: {e}")
            # If a connection reset happens, wait a bit longer before retry
            time.sleep(60)

def manage_trade(entry, tp1, tp2, sl, qty):
    # Ensure all inputs are treated as floats
    entry, tp1, tp2, sl, qty = map(float, [entry, tp1, tp2, sl, qty])
    tp1_hit = False
    print(f"🛰️ Monitoring Open Trade...")
    
    while True:
        try:
            ticker = client.get_public_product(product_id=PRODUCT_ID)
            price = float(ticker['price'])
            
            # Logic for BUY trades
            if entry < tp2: 
                if not tp1_hit:
                    if price >= tp1:
                        print(f"💰 TP1 Hit! Moving SL to Breakeven.")
                        tp1_hit = True
                    elif price <= sl:
                        print(f"🛑 SL Hit.")
                        break
                else:
                    if price >= tp2 or price <= entry:
                        print(f"🏁 Trade Closed.")
                        break
            # Logic for SELL trades
            else: 
                if not tp1_hit:
                    if price <= tp1:
                        print(f"💰 TP1 Hit! Moving SL to Breakeven.")
                        tp1_hit = True
                    elif price >= sl:
                        print(f"🛑 SL Hit.")
                        break
                else:
                    if price <= tp2 or price >= entry:
                        print(f"🏁 Trade Closed.")
                        break
                        
            time.sleep(20)
        except Exception as e:
            print(f"Trade Mgmt Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()