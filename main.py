import time
import datetime as dt 
from datetime import timezone
from auth import private_client
from client import public_client
from trader import get_usd_balance, place_market_order
from strategy import generate_trade_signal
from risk import calculate_position_size, calculate_take_profit
from notifications import send_telegram_notification

# --- Configuration ---
PRODUCT = 'ETH-USD'  
TRADING_INTERVAL_SECONDS = 60
RISK_PERCENTAGE = 0.05  
RR_RATIO = 2.0         

def get_precision_details(product_id):
    """Fetches base_increment to prevent 'Invalid Quantity' errors."""
    try:
        product = public_client.get_product(product_id=product_id)
        increment = str(product.base_increment).rstrip('0')
        return len(increment.split('.')[-1]) if '.' in increment else 0
    except Exception:
        return 4 

def run_strategy():
    print(f"\n--- {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    try:
        end_time = dt.datetime.now(timezone.utc) 
        start_time = end_time - dt.timedelta(hours=6)
        
        raw_response = public_client.get_candles(
            product_id=PRODUCT, 
            start=str(int(start_time.timestamp())),
            end=str(int(end_time.timestamp())),
            granularity='FIVE_MINUTE'
        )
        candles = raw_response.candles if hasattr(raw_response, 'candles') else []
        candles.reverse() 
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    if len(candles) < 20: 
        print("Insufficient candle data.")
        return

    # Using SMC Strategy
    signal, structural_sl = generate_trade_signal(candles)
    print(f"Strategy Scan: {signal}")

    if signal in ['BUY', 'SELL']:
        balance = get_usd_balance(private_client)
        if not balance or balance < 10:
            print("Insufficient funds.")
            return

        entry_price = float(candles[-1].close)
        pos_size, final_sl = calculate_position_size(balance, RISK_PERCENTAGE, entry_price, structural_sl)
        tp_price = calculate_take_profit(entry_price, final_sl, RR_RATIO)

        precision = get_precision_details(PRODUCT)
        final_qty = round(pos_size, precision)

        if final_qty > 0:
            print(f"Executing {signal} for {final_qty} {PRODUCT}...")
            order = place_market_order(private_client, PRODUCT, signal, final_qty)
            
            if order.get('success'):
                msg = (f"ALERT: {signal} EXECUTED\n"
                       f"Price: {entry_price}\n"
                       f"SL: {final_sl:.2f} | TP: {tp_price:.2f}\n"
                       f"Size: {final_qty}")
                send_telegram_notification(msg)
            else:
                send_telegram_notification(f"ERROR: Order Failed: {order.get('error_response')}")

if __name__ == '__main__':
    send_telegram_notification(f"SMC Bot Started: {PRODUCT}")
    precision_limit = get_precision_details(PRODUCT)
    print(f"Bot Active. Precision for {PRODUCT} set to {precision_limit} decimals.")
    
    while True:
        run_strategy()
        time.sleep(TRADING_INTERVAL_SECONDS)