def calculate_take_profit(entry_price, stop_loss, side, rr_ratio=3.0):
    """Calculates Take Profit with an increased 1:3 Risk-to-Reward ratio."""
    risk_in_price = abs(entry_price - stop_loss)
    
    if side == 'BUY':
        # Long: TP is ABOVE entry
        take_profit = entry_price + (risk_in_price * rr_ratio)
    else:
        # Short: TP is BELOW entry
        take_profit = entry_price - (risk_in_price * rr_ratio)
        
    return take_profit

def calculate_position_size(balance, risk_percent, entry_price, structural_sl, side):
    """Calculates size with strict minimum distance and sanity checks."""
    risk_amount = balance * (risk_percent / 100)
    buffer = entry_price * 0.0001 
    
    if side == 'BUY':
        stop_loss_final = structural_sl - buffer
        if stop_loss_final >= entry_price: return 0, stop_loss_final
    else:
        stop_loss_final = structural_sl + buffer
        if stop_loss_final <= entry_price: return 0, stop_loss_final
        
    final_risk_in_price = abs(entry_price - stop_loss_final)

    # Maintain the 0.1% Minimum Distance to avoid market noise
    min_distance = entry_price * 0.001 
    if final_risk_in_price < min_distance:
        return 0, stop_loss_final

    position_size = risk_amount / final_risk_in_price
    return position_size, stop_loss_final