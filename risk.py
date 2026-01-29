def calculate_take_profit(entry_price, stop_loss, side, rr_ratio=2.0):
    """Calculates Take Profit based on Risk-to-Reward ratio and trade direction."""
    risk_in_price = abs(entry_price - stop_loss)
    
    if side == 'BUY':
        # Long: TP is above entry
        take_profit = entry_price + (risk_in_price * rr_ratio)
    else:
        # Short: TP is below entry
        take_profit = entry_price - (risk_in_price * rr_ratio)
        
    return take_profit

def calculate_position_size(balance, risk_percent, entry_price, structural_sl, side):
    """Calculates position size and buffered SL based on trade direction."""
    risk_amount = balance * (risk_percent / 100)
    
    # buffer for execution tolerance (0.01%)
    buffer = entry_price * 0.0001 
    
    if side == 'BUY':
        stop_loss_final = structural_sl - buffer # SL below entry
    else:
        stop_loss_final = structural_sl + buffer # SL above entry
        
    final_risk_in_price = abs(entry_price - stop_loss_final)

    if final_risk_in_price < 0.0001: 
        return 0, stop_loss_final

    position_size = risk_amount / final_risk_in_price
    
    return position_size, stop_loss_final