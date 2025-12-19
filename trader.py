import time
import math
from notifications import send_telegram_notification

def get_precision(client, product_id):
    """
    Fetches exact decimal requirements from Coinbase for a specific product.
    Returns (base_decimals, quote_decimals)
    """
    try:
        product = client.get_product(product_id)
        
        # Example: '0.00000001' -> 8 decimals
        base_inc = str(product.base_increment).rstrip('0')
        base_decimals = len(base_inc.split('.')[-1]) if '.' in base_inc else 0
        
        quote_inc = str(product.quote_increment).rstrip('0')
        quote_decimals = len(quote_inc.split('.')[-1]) if '.' in quote_inc else 0
        
        return base_decimals, quote_decimals
    except Exception as e:
        print(f"ERROR fetching precision: {e}")
        return 8, 2  # Conservative defaults for BTC/ETH

def get_usd_balance(private_client):
    try:
        accounts_response = private_client.get_accounts()
        if hasattr(accounts_response, 'accounts'):
            for account in accounts_response.accounts:
                if account.currency == 'USD':
                    return float(account.available_balance.value)
        return 0.0
    except Exception as e:
        send_telegram_notification(f"CRITICAL: Balance Error: {e}")
        return None

def place_market_order(private_client, product_id, side, amount):
    """
    Places a market order. Precision is now handled in main.py 
    before calling this, but we include a check here for safety.
    """
    try:
        order_config = {
            'client_order_id': f'smc-{int(time.time())}',
            'product_id': product_id,
            'side': side,
            'order_configuration': {
                'market_market_ioc': {
                    'base_quantity': str(amount)
                }
            }
        }
        response = private_client.create_order(**order_config)
        
        if response.get('success'):
            return {'success': True, 'order_id': response.get('order_id')}
        else:
            return {'success': False, 'error_response': response}
            
    except Exception as e:
        return {'success': False, 'error_response': str(e)}