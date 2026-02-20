def calculate_take_profit(entry_price, stop_loss, side, rr_ratio=3.0):
    """Calculates Take Profit with the Sniper 1:3 Risk-to-Reward ratio."""
    risk_in_price = abs(entry_price - stop_loss)
    
    if side == 'BUY':
        take_profit = entry_price + (risk_in_price * rr_ratio)
    else:
        take_profit = entry_price - (risk_in_price * rr_ratio)
        
    return take_profit

def calculate_position_size(balance, risk_percent, entry_price, structural_sl, side, atr_value):
    """
    Calculates size using an ATR-based buffer.
    atr_value should be the 14-period ATR of the current candle.
    """
    risk_amount = balance * (risk_percent / 100)
    
    # We use 0.5x ATR as the buffer. 
    # This covers the 'noise' of the current market volatility.
    buffer = atr_value * 1.5
    
    if side == 'BUY':
        stop_loss_final = structural_sl - buffer
        if stop_loss_final >= entry_price: return 0, stop_loss_final
    else:
        stop_loss_final = structural_sl + buffer
        if stop_loss_final <= entry_price: return 0, stop_loss_final
        
    final_risk_in_price = abs(entry_price - stop_loss_final)

    # Minimum Distance Check (0.1%)
    min_distance = entry_price * 0.001 
    if final_risk_in_price < min_distance:
        return 0, stop_loss_final

    position_size = risk_amount / final_risk_in_price
    return position_size, stop_loss_final