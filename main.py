import os
import time
import requests
from dotenv import load_dotenv
from coinbase.rest import RESTClient
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
import trader

# 1. Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 2. Configuration
KEY_FILE_PATH = "cdp_api_key.json" 
PRODUCT_ID = "ETH-USD"
BALANCE = 18.0  
RISK_PCT = 2.0  

# 3. Initialize Coinbase Client
client = RESTClient(key_file=KEY_FILE_PATH)

def send_telegram(message):
    """Sends a notification with explicit error reporting to find issues."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("!!! Telegram Error: Token or Chat ID missing from .env !!!")
        return
    
    # Ensure CHAT_ID is a clean string without quotes or spaces
    clean_chat_id = str(CHAT_ID).replace('"', '').replace("'", "").strip()
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    try:
        response = requests.post(
            url, 
            json={"chat_id": clean_chat_id, "text": message}, 
            timeout=10
        )
        # If Telegram rejects it, we now see exactly WHY in the terminal
        if response.status_code != 200:
            print(f"!!! Telegram API Rejected (Code {response.status_code}): {response.text} !!!")
        else:
            print(f"Telegram Notification Sent: {message[:20]}...")
    except Exception as e:
        print(f"!!! Connection Error to Telegram: {e} !!!")

def get_coinbase_balance(client):
    """Corrected function for official Coinbase SDK object structure."""
    try:
        # Fetch accounts
        accounts_response = client.get_accounts()
        
        # The SDK returns an object with an 'accounts' list
        for account in accounts_response.accounts:
            # Direct attribute access (dot notation)
            if account.currency == 'USD':
                # available_balance is also an object with a 'value' attribute
                balance_value = account.available_balance['value'] 
                return float(balance_value)
                
        print("!!! USD Account not found !!!")
        return 0.0
    except Exception as e:
        # If dot notation fails for nested fields, fallback to dict conversion
        try:
            for account in accounts_response.accounts:
                acc_dict = account.to_dict()
                if acc_dict['currency'] == 'USD':
                    return float(acc_dict['available_balance']['value'])
        except:
            print(f"!!! Balance Error: {e} !!!")
        return 0.0

def run_bot():
    print(f"SMC Bot Active. Connecting to Coinbase...")
    
    # Verify balance before starting
    live_balance = get_coinbase_balance(client)
    
    # Create a nice status update
    status_msg = (
        f"✅ Bot Connection Verified!\n"
        f"💵 Live Balance Found: ${live_balance:.2f}\n"
        f"📍 Monitoring: {PRODUCT_ID}"
    )
    
    print("-" * 30)
    print(status_msg)
    print("-" * 30)
    
    # Send to Telegram so you can see it on your phone
    send_telegram(status_msg)

    # Use the live balance for risk calculations
    global BALANCE
    BALANCE = live_balance
    
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
                
                print(f"Signal Detected! Entry: {entry_price}, TP1: {tp1}, SL: {sl_price}")
                
                # EXECUTE ENTRY
                buy_order = trader.place_market_order_buy(client, PRODUCT_ID, pos_size_usd)
                if buy_order:
                    qty = float(buy_order['base_size'])
                    send_telegram(f"🚀 BUY {PRODUCT_ID} executed!\nQty: {qty}\nEntry: {entry_price}\nSL: {sl_price}")
                    
                    # PLACE INITIAL PROTECTION
                    trader.place_initial_stop_loss(client, PRODUCT_ID, qty, sl_price)
                    
                    # START MANAGEMENT LOOP
                    manage_trade(entry_price, tp1, tp2, sl_price, qty)
                    
        except Exception as e:
            print(f"Loop Error: {e}")
        
        # Check for signal every 60 seconds
        time.sleep(60) 

def manage_trade(entry_price, tp1, tp2, sl, qty):
    tp1_hit = False
    current_qty = qty
    
    while True:
        ticker = client.get_public_product(product_id=PRODUCT_ID)
        price = float(ticker['price'])
        
        if not tp1_hit:
            if price >= tp1:
                print("TP1 Hit! Selling 50% and moving SL to Breakeven.")
                client.market_order_sell(product_id=PRODUCT_ID, base_size=str(current_qty/2))
                current_qty /= 2
                trader.move_to_breakeven(client, PRODUCT_ID, current_qty, entry_price)
                tp1_hit = True
                send_telegram(f"✅ TP1 HIT! Locked in profit. SL moved to Breakeven (${entry_price})")
        else:
            if price >= tp2:
                print("TP2 Hit! Closing remaining position.")
                client.market_order_sell(product_id=PRODUCT_ID, base_size=str(current_qty))
                send_telegram(f"💰 TP2 HIT! Trade closed with full profit.")
                break
        
        # Check if price hit SL or BE
        if price <= (entry_price if tp1_hit else sl):
            print("Trade closed by Stop Loss/Breakeven.")
            send_telegram(f"📉 Trade Closed: Hit {'Breakeven' if tp1_hit else 'Stop Loss'}")
            break
            
        time.sleep(20)

if __name__ == "__main__":
    run_bot()