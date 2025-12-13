import time
from client import public_client
from strategy import generate_trade_signal
from trader import execute_order
from risk import calculate_position_size, calculate_take_profit
from journal import log_trade
from notifications import send_telegram_message

PRODUCT = 'BTC-USD'
RISK_PERCENT = 1  # Risk 1% per trade
RR_RATIO = 2.0  # Risk 1% to gain 2% (1:2 R:R)

while True:
    # Format: [ time, low, high, open, close, volume ]
    # We convert to a list of dicts for easier access in indicator files
    raw_candles = public_client.get_product_historic_rates(PRODUCT, granularity=300)  # 5-min candles
    candles = [{'low': c[1], 'high': c[2], 'open': c[3], 'close': c[4]} for c in raw_candles]

    # signal now returns the side and the price for structural SL
    signal, structural_price = generate_trade_signal(candles)

    # Only proceed if we have a valid signal AND the structural price for SL
    if signal in ['BUY', 'SELL'] and structural_price is not None:
        
        # NOTE: Need to handle error if USD account is not found
        try:
            account_balance = float(auth_client.get_account('USD')['balance'])
        except Exception:
            send_telegram_message("**ERROR**: Could not fetch USD account balance.")
            time.sleep(60)
            continue
            
        entry_price = candles[-1]['close'] 
        
        # Calculate Risk parameters using the new structural logic
        position_size, stop_loss = calculate_position_size(
            account_balance, RISK_PERCENT, entry_price, structural_price
        )
        take_profit = calculate_take_profit(entry_price, structural_price, RR_RATIO)
        
        if position_size > 0:
            trade_info = {
                'side': signal,
                'product': PRODUCT,
                'size': position_size,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }

            try:
                # Execute Trade
                execute_order(signal.lower(), PRODUCT, position_size)
                log_trade(trade_info)
                
                # Send Notification
                msg = (f"✅ **{signal} Order Executed!**\n"
                       f"Product: `{PRODUCT}`\n"
                       f"Entry: `${entry_price:.2f}`\n"
                       f"Size: `{position_size:.4f}`\n"
                       f"SL: `${stop_loss:.2f}`\n"
                       f"TP (1:{RR_RATIO}): `${take_profit:.2f}`")
                send_telegram_message(msg)

            except Exception as e:
                send_telegram_message(f"**Trade Execution Failed!** Error: {e}")
                
    time.sleep(60)  # check every minute