import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from coinbase.rest import RESTClient
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
import trader
import journal  # <--- IMPORT YOUR JOURNAL HERE

# --- 1. ROBUST ENV LOADING ---
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- 2. CONFIGURATION ---
KEY_FILE_PATH = base_dir / "cdp_api_key.json" 
PRODUCT_ID = "ETH-USD"
BALANCE = 18.2  
RISK_PCT = 2.0  

# Initialize Coinbase Client
client = RESTClient(key_file=str(KEY_FILE_PATH))

def send_telegram(message):
    """Sends a notification with detailed error reporting."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print(f"!!! Telegram Connection Failed: {e} !!!")

def get_coinbase_balance(client):
    """Fetches the actual USD balance from your live Coinbase account."""
    try:
        accounts_response = client.get_accounts()
        for account in accounts_response.accounts:
            if account.currency == 'USD':
                return float(account.available_balance['value'])
        return 0.0
    except Exception as e:
        print(f"!!! Balance Fetch Error: {e} !!!")
        return 0.0

def run_bot():
    print(f"SMC Bot Active. Connecting to Coinbase...")
    
    # Verify balance and update global config
    global BALANCE
    BALANCE = get_coinbase_balance(client)
    
    status_msg = (
        f"✅ Bot Connection Verified!\n"
        f"💵 Live Balance: ${BALANCE:.2f}\n"
        f"📍 Monitoring: {PRODUCT_ID}"
    )
    print("-" * 30 + "\n" + status_msg + "\n" + "-" * 30)
    send_telegram(status_msg)

    while True:
        try:
            # Get latest 5-minute candles
            candles_data = client.get_public_candles(product_id=PRODUCT_ID, start="", end="", granularity="FIVE_MINUTE")
            
            # Check for Trade Signal
            signal, structural_price = generate_trade_signal(candles_data['candles'])
            
            if signal == 'BUY':
                ticker = client.get_public_product(product_id=PRODUCT_ID)
                entry_price = float(ticker['price'])
                
                # Calculate Risk and Targets
                pos_size_usd, sl_price = calculate_position_size(BALANCE, RISK_PCT, entry_price, structural_price)
                tp1 = entry_price + (entry_price - sl_price)
                tp2 = calculate_take_profit(entry_price, sl_price, 2.0)
                
                print(f"Signal Detected! Entry: {entry_price}")
                
                # EXECUTE ENTRY
                buy_order = trader.place_market_order_buy(client, PRODUCT_ID, pos_size_usd)
                if buy_order:
                    qty = float(buy_order['base_size'])
                    
                    # --- NEW: LOG TO JOURNAL ---
                    trade_info = {
                        'side': 'BUY',
                        'product': PRODUCT_ID,
                        'size': qty,
                        'entry_price': entry_price,
                        'stop_loss': sl_price,
                        'take_profit': tp2
                    }
                    journal.log_trade(trade_info)
                    # ---------------------------

                    send_telegram(f"🚀 BUY {PRODUCT_ID} Executed & Logged!\nQty: {qty}\nEntry: {entry_price}")
                    
                    # PLACE PROTECTION & MANAGE
                    trader.place_initial_stop_loss(client, PRODUCT_ID, qty, sl_price)
                    manage_trade(entry_price, tp1, tp2, sl_price, qty)
                    
        except Exception as e:
            print(f"Loop Error: {e}")
        
        time.sleep(60)

def manage_trade(entry_price, tp1, tp2, sl, qty):
    tp1_hit = False
    total_profit_usd = 0.0
    
    while True:
        ticker = client.get_public_product(product_id=PRODUCT_ID)
        price = float(ticker['price'])
        
        if not tp1_hit:
            if price >= tp1:
                # Part 1: Sell half and calculate profit
                sell_qty = qty / 2
                profit_tp1 = (price - entry_price) * sell_qty
                total_profit_usd += profit_tp1
                
                client.market_order_sell(product_id=PRODUCT_ID, base_size=str(sell_qty))
                trader.move_to_breakeven(client, PRODUCT_ID, sell_qty, entry_price)
                tp1_hit = True
                
        else:
            # Check for Final Exit (TP2 or Breakeven)
            if price >= tp2 or price <= entry_price:
                final_profit = (price - entry_price) * (qty / 2)
                total_profit_usd += final_profit
                
                # Update Journal with final numbers
                journal.update_journal_exit(price, total_profit_usd)
                
                client.market_order_sell(product_id=PRODUCT_ID, base_size=str(qty/2))
                send_telegram(f"Trade Over! Total P/L: ${total_profit_usd:.2f}")
                break
        
        # Check for Initial Stop Loss (If TP1 never hit)
        if not tp1_hit and price <= sl:
            loss = (price - entry_price) * qty
            journal.update_journal_exit(price, loss)
            break

        time.sleep(20)

if __name__ == "__main__":
    run_bot()