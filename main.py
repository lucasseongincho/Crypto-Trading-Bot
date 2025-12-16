import time
import datetime as dt 
from datetime import timezone
from auth import public_client, private_client
from client import public_client
from trader import calculate_position_size, check_for_signal, place_market_order, get_usd_balance
from notifications import send_telegram_notification

# --- Configuration ---
PRODUCT = 'ETH-USD'  
TRADING_INTERVAL_SECONDS = 60

# --- Trading Logic Constants ---
SHORT_PERIOD = 50 
LONG_PERIOD = 200
# The position size as a percentage of your total available USD balance
RISK_PERCENTAGE = 0.05 

def run_strategy():
    """Main loop for the trading strategy."""
    
    # --- 1. Fetch Historical Data (Candles) ---
    try:
        # Define the time window for the candles (must be UTC)
        end_time = dt.datetime.now(timezone.utc) 
        start_time = end_time - dt.timedelta(hours=24) 

        # Convert datetime objects to Unix Timestamps (seconds since epoch)
        start_unix = int(start_time.timestamp()) 
        end_unix = int(end_time.timestamp())

        # Pass the Unix timestamps as strings
        start_param = str(start_unix)
        end_param = str(end_unix)

        print(f"Fetching {PRODUCT} data...")
        raw_response = public_client.get_candles(
            product_id=PRODUCT, 
            start=start_param,
            end=end_param,
            granularity='FIVE_MINUTE'
        )
        
        raw_candles = raw_response.candles if hasattr(raw_response, 'candles') else []

    except Exception as e:
        print(f"Error fetching candles: {e}")
        send_telegram_notification(f"Data Fetch Error: {e}")
        return

    # --- 2. Data Preparation and Signal Generation ---
    if not raw_candles:
        print("No candle data received. Skipping analysis.")
        return

    # The API returns candles as a list of dictionaries, usually newest first.
    # We must reverse them and extract the closing prices for SMA calculation.
    
    # Reverse list so oldest candle is first (ascending order)
    raw_candles.reverse() 
    
    # Extract the 'close' price from the dictionary format
    closes = [float(c['close']) for c in raw_candles]

    # Safety check for sufficient data for the 200-period SMA
    if len(closes) < LONG_PERIOD:
        print(f"Insufficient data for analysis. Found {len(closes)} candles, need at least {LONG_PERIOD}.")
        return

    # Get the trade signal based on the closing prices
    signal = check_for_signal(closes, SHORT_PERIOD, LONG_PERIOD)
    
    # --- 3. Execute Trade ---
    
    if signal == 'BUY':
        print(f"Signal detected: {signal}. Checking balance and calculating position...")
        
        # Get current USD balance using the private client
        usd_balance = get_usd_balance(private_client)

        if usd_balance is not None and usd_balance > 10:  # Ensure a minimum balance
            
            # Calculate the quantity of crypto to buy
            position_size = calculate_position_size(usd_balance, closes[-1], RISK_PERCENTAGE)
            
            if position_size > 0:
                print(f"Placing BUY order for {position_size:.4f} {PRODUCT.split('-')[0]}...")
                
                # Place the market order
                order_result = place_market_order(private_client, PRODUCT, 'BUY', position_size)
                
                if order_result and 'success' in order_result and order_result['success']:
                    # Send a success notification via Telegram
                    send_telegram_notification(f"BUY Order Executed!\nProduct: {PRODUCT}\nAmount: {position_size:.4f}")
                else:
                    # Send a failure notification
                    error_message = order_result.get('error_response', {}).get('error', 'Unknown Error')
                    send_telegram_notification(f"BUY Order Failed:\n{error_message}")
            else:
                print("Calculated position size is too small or balance is insufficient.")
        else:
            print("Insufficient USD balance to place a trade.")

    elif signal == 'SELL':
        # NOTE: For this simple example, we assume we sell the whole position.
        # In a real bot, you'd calculate the crypto balance to sell.
        print("SELL signal detected. This bot only implements the BUY side for safety.")

    else:
        print(f"No trade signal ('{signal}') detected. Waiting...")


# --- Main Execution Loop ---
if __name__ == '__main__':
    print("SMC Crypto Bot V2 (Advanced Trade SDK) started.")
    print(f"Monitoring {PRODUCT} every {TRADING_INTERVAL_SECONDS} seconds...")
    send_telegram_notification(f"Bot Started: Monitoring {PRODUCT}.")
    
    while True:
        run_strategy()
        time.sleep(TRADING_INTERVAL_SECONDS)