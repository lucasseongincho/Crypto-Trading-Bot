import time

def place_market_order_buy(client, product_id, amount_usd):
    """Executes a market buy based on USD amount."""
    try:
        order = client.market_order_buy(product_id=product_id, quote_size=str(amount_usd))
        return order
    except Exception as e:
        print(f"Error placing buy order: {e}")
        return None

def place_initial_stop_loss(client, product_id, qty, sl_price):
    """Places a Stop-Limit Sell for the full position."""
    try:
        # Limit price usually 1% below stop price to ensure fill
        limit_price = sl_price * 0.99 
        order = client.stop_limit_order_gtc_sell(
            product_id=product_id,
            base_size=str(qty),
            limit_price=f"{limit_price:.2f}",
            stop_price=f"{sl_price:.2f}"
        )
        return order
    except Exception as e:
        print(f"Error placing stop loss: {e}")
        return None

def move_to_breakeven(client, product_id, remaining_qty, entry_price):
    """Cancels existing orders and places a new Stop at Entry."""
    try:
        # 1. Cancel existing Stop Loss
        client.cancel_orders(product_ids=[product_id])
        time.sleep(1) 
        
        # 2. Place new Stop at Entry Price
        limit_price = entry_price * 0.99
        order = client.stop_limit_order_gtc_sell(
            product_id=product_id,
            base_size=f"{remaining_qty:.4f}",
            limit_price=f"{limit_price:.2f}",
            stop_price=f"{entry_price:.2f}"
        )
        print(f"SUCCESS: Stop Loss moved to Breakeven at {entry_price}")
        return order
    except Exception as e:
        print(f"Error moving to breakeven: {e}")
        return None