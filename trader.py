import time
import math
from notifications import send_telegram_notification

def place_limit_order(private_client, product_id, side, amount, limit_price):
    """
    Places a Limit IOC order to protect against slippage.
    """
    try:
        # Create a unique ID for the order
        client_oid = f'smc-{int(time.time())}'
        
        # Structure for Advanced Trade V3 API
        order_config = {
            'client_order_id': client_oid,
            'product_id': product_id,
            'side': side,
            'order_configuration': {
                'limit_limit_ioc': {
                    'base_size': str(amount),
                    'limit_price': str(limit_price)
                }
            }
        }

        response = private_client.create_order(**order_config)
        
        if response.get('success'):
            return {'success': True, 'order_id': response.get('order_id')}
        else:
            return {'success': False, 'error_response': response}
            
    except Exception as e:
        print(f"Order failure: {e}")
        return {'success': False, 'error_response': str(e)}

def calculate_limit_price(current_price, side, slippage_buffer=0.001):
    """
    Adds a small buffer to the current price for Limit IOC orders.
    Default buffer is 0.1%
    """
    if side == 'BUY':
        return round(current_price * (1 + slippage_buffer), 2)
    else:
        return round(current_price * (1 - slippage_buffer), 2)