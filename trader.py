# trader.py
from client import auth_client
import uuid # Needed to generate a unique client_order_id

def execute_order(side, product, size):
    # The new SDK requires a unique client_order_id for every new order
    client_order_id = str(uuid.uuid4())
    size_str = f"{size:.8f}" # Ensure size is a precise string

    if side.lower() == 'buy':
        # Market order to spend 'quote_size' (e.g., USD)
        order = auth_client.market_order_buy(
            client_order_id=client_order_id,
            product_id=product,
            quote_size=size_str # We use quote_size since we calculated size based on USD risk
        )
    elif side.lower() == 'sell':
        # Market order to sell 'base_size' (e.g., BTC)
        order = auth_client.market_order_sell(
            client_order_id=client_order_id,
            product_id=product,
            base_size=size_str
        )
    else:
        # Handle case where side is neither buy nor sell
        raise ValueError("Invalid side: must be 'buy' or 'sell'")
        
    # The response structure is also different. Check for 'success'
    if order.get('success'):
        return order['success_response']
    else:
        # Handle error case
        raise Exception(f"Order failed: {order.get('error_response')}")