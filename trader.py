def get_usd_balance(private_client):
    try:
        accounts_response = private_client.get_accounts()
        if hasattr(accounts_response, 'accounts') and accounts_response.accounts:
            for account in accounts_response.accounts:
                if account.currency == 'USD':
                    balance = float(account.available_balance.value)
                    print(f"DEBUG: USD Available Balance: {balance:.2f}")
                    return balance
        return 0.0
    except Exception as e:
        print(f"ERROR fetching USD balance: {e}")
        send_telegram_notification(f"CRITICAL: Account Read Error: {e}") 
        return None

def place_market_order(private_client, product_id, side, amount):
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
        return {'success': True} if response.get('success') else {'success': False, 'error_response': response}
    except Exception as e:
        send_telegram_notification(f"CRITICAL: Order Placement Error: {e}")
        return {'success': False, 'error_response': str(e)}