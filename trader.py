import numpy as np
import time 
from notifications import send_telegram_notification

# --- Trading Indicator Logic ---

def calculate_sma(data, window):
    """Calculates the Simple Moving Average (SMA)."""
    return np.mean(data[-window:])

def check_for_signal(closes, short_period, long_period):
    """
    Checks for a Simple Moving Average (SMA) crossover signal.
    Returns 'BUY', 'SELL', or 'HOLD'.
    """
    short_sma = calculate_sma(closes, short_period)
    long_sma = calculate_sma(closes, long_period)

    prev_short_sma = calculate_sma(closes[:-1], short_period)
    prev_long_sma = calculate_sma(closes[:-1], long_period)

    if short_sma > long_sma and prev_short_sma <= prev_long_sma:
        return 'BUY'
    elif short_sma < long_sma and prev_short_sma >= prev_long_sma:
        return 'SELL'
    else:
        return 'HOLD'

# --- Advanced Trade SDK Functions ---

def get_usd_balance(private_client):
    """
    Fetches the available USD balance from the Coinbase account using the
    CORRECT object structure for the Advanced Trade SDK.
    """
    try:
        accounts_response = private_client.get_accounts()
        if hasattr(accounts_response, 'accounts') and accounts_response.accounts:
            for account in accounts_response.accounts:
                
                if account.currency == 'USD':
                    balance_value = account.available_balance.value
                    balance = float(balance_value)
                    
                    print(f"DEBUG: Found USD Account. Available Balance: ${balance:.2f}")
                    
                    return balance

        # If accounts list is empty or USD not found
        print("DEBUG: USD account not found, or accounts list is empty.")
        return 0.0

    except Exception as e:
        print(f"ERROR fetching USD balance: {e}")
        send_telegram_notification(f"‼️ Account Read Error: {e}") 
        return None

def calculate_position_size(usd_balance, last_close_price, risk_percentage):
    """
    Calculates the quantity of the product to buy based on available USD balance.
    """
    try:
        investment_amount = usd_balance * risk_percentage
        
        if investment_amount < 10:  
            print("Calculated investment amount is less than $10 minimum.")
            return 0.0

        quantity = investment_amount / last_close_price
        
        return round(quantity, 4)

    except Exception as e:
        print(f"Error calculating position size: {e}")
        return 0.0

def place_market_order(private_client, product_id, side, amount):
    """
    Places a market order using the Advanced Trade SDK structure.
    """
    try:
        order_config = {
            'client_order_id': f'smc-bot-{int(time.time())}', 
            'product_id': product_id,
            'side': side,
            'order_configuration': {
                'market_market_ioc': {
                    'base_quantity': str(amount) 
                }
            }
        }

        response = private_client.create_order(**order_config)
        
        if 'success' in response and response['success']:
            return {'success': True, 'order_id': response.get('order_id')}
        else:
            return {'success': False, 'error_response': response}

    except Exception as e:
        print(f"Order placement failed: {e}")
        send_telegram_notification(f"‼️ Order Placement Error: {e}")
        return {'success': False, 'error_response': {'error': str(e)}}