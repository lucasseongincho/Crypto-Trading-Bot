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
PAPER_MODE = True 
PRODUCT_ID = "ETH-USD"
BALANCE = 1000.0 if PAPER_MODE else 0.0 
RISK_PCT = 1.0  
LOOKBACK_WINDOW = 100 

# Initialize Coinbase Client
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

# --- 3. CHATTY TRADE MANAGEMENT ---
def manage_trade(entry, tp1, tp2, sl, qty, side):
    """Resilient trade monitoring with mini-heartbeats."""
    entry, tp1, tp2, sl, qty = map(float, [entry, tp1, tp2, sl, qty])
    tp1_hit = False
    
    status_msg = f"🛰️ Trade Active: {side} {qty:.4f} ETH | Entry: {entry} | SL: {sl} | TP2: {tp2}"
    print(status_msg)
    send_telegram(status_msg)
    
    while True:
        try:
            # Fetch price with timeout handling
            ticker = client.get_public_product(product_id=PRODUCT_ID)
            price = float(ticker['price'])
            
            ts = datetime.now().strftime('%H:%M:%S')
            target_status = "🎯 Aiming for TP2" if tp1_hit else "🎯 Aiming for TP1"
            print(f"   [{ts}] {side} Price: {price} | {target_status}")

            # --- SELL (SHORT) LOGIC ---
            if side == 'SELL':
                if not tp1_hit:
                    if price <= tp1:
                        print(f"💰 SELL TP1 Hit! Moving SL to Breakeven ({entry})")
                        tp1_hit = True
                        send_telegram("💰 TP1 Hit! Risk removed.")
                    elif price >= sl:
                        print(f"🛑 SELL SL Hit at {price}. Trade Over.")
                        break
                else:
                    if price <= tp2:
                        print(f"🏁 SELL TP2 Hit! Profit Secured.")
                        send_telegram("🏁 TP2 Hit! Trade Closed with Full Profit.")
                        break
                    elif price >= entry:
                        print(f"🛑 SELL Breakeven SL Hit at {price}. Trade Over.")
                        break

            # --- BUY (LONG) LOGIC ---
            elif side == 'BUY':
                if not tp1_hit:
                    if price >= tp1:
                        print(f"💰 BUY TP1 Hit! Moving SL to Breakeven ({entry})")
                        tp1_hit = True
                        send_telegram("💰 TP1 Hit! Risk removed.")
                    elif price <= sl:
                        print(f"🛑 BUY SL Hit at {price}. Trade Over.")
                        break
                else:
                    if price >= tp2:
                        print(f"🏁 BUY TP2 Hit! Profit Secured.")
                        send_telegram("🏁 TP2 Hit! Trade Closed with Full Profit.")
                        break
                    elif price <= entry:
                        print(f"🛑 BUY Breakeven SL Hit at {price}. Trade Over.")
                        break
                        
            time.sleep(30) # Efficient check interval

        except Exception as e:
            print(f"⚠️ Connection lost during trade management: {e}. Retrying in 10s...")
            time.sleep(10)
            continue # Force retry

# --- 4. MAIN BOT LOOP ---
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
            # Timing sync
            current_time = time.time()
            seconds_into_candle = int(current_time) % 300
            if seconds_into_candle > 10:
                wait_time = 300 - seconds_into_candle + 1
                print(f"⏳ Waiting {wait_time}s for next candle close...")
                time.sleep(wait_time)

            # Fetch candles
            end_ts = int(time.time())
            start_ts = end_ts - (300 * 300)
            candles_response = client.get_public_candles(
                product_id=PRODUCT_ID, 
                granularity="FIVE_MINUTE",  # Use the string label, not a number
                start=str(start_ts), 
                end=str(end_ts)
            )
            candles = candles_response['candles']

            if len(candles) < LOOKBACK_WINDOW:
                time.sleep(60); continue

            # Signal Heartbeat
            signal, structural_price, counts = generate_trade_signal(candles, len(candles) - 1)
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] 🛰️ HEARTBEAT | Trend: {counts['trend']} | Bullish: {counts['bull']}/3 | Bearish: {counts['bear']}/3")

            # EXECUTION
            if signal in ['BUY', 'SELL'] and structural_price:
                ticker = client.get_public_product(product_id=PRODUCT_ID)
                entry_price = float(ticker['price'])
                sl_target = float(structural_price)

                pos_size_usd, sl_price = calculate_position_size(BALANCE, RISK_PCT, entry_price, sl_target, signal)
                tp2 = calculate_take_profit(entry_price, sl_price, signal, 2.0)
                tp1 = calculate_take_profit(entry_price, sl_price, signal, 1.0) # 1:1 TP1

                if pos_size_usd > 0:
                    print(f"🎯 {signal} Signal Found! Entry: {entry_price}")
                    qty = pos_size_usd / entry_price
                    
                    if PAPER_MODE:
                        journal.log_trade({
                            'entry_unix': entry_unix_time, # You may need to capture this when trade opens
                            'exit_unix': time.time(),
                            'pair': PRODUCT_ID,
                            'side': side,
                            'entry_price': entry,
                            'exit_price': final_exit_price,
                            'tp1_price': tp1,       # <--- ADD THIS
                            'tp2_price': tp2,       # <--- ADD THIS
                            'sl_price': sl,         # <--- ADD THIS
                            'pnl': actual_pnl_usd
                        })
                        manage_trade(entry_price, tp1, tp2, sl_price, qty, signal)
                    else:
                        order = trader.place_market_order_buy(client, PRODUCT_ID, pos_size_usd)
                        if order:
                            qty = float(order['base_size'])
                            trader.place_initial_stop_loss(client, PRODUCT_ID, qty, sl_price)
                            manage_trade(entry_price, tp1, tp2, sl_price, qty, signal)
                            BALANCE = get_coinbase_balance(client)

            time.sleep(15)

        except Exception as e:
            print(f"❌ Critical Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()