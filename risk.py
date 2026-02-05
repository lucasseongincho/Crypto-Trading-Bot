def calculate_take_profit(entry_price, stop_loss, side, rr_ratio=2.0):
    """Calculates Take Profit based on Risk-to-Reward ratio and trade direction."""
    risk_in_price = abs(entry_price - stop_loss)
    
    if side == 'BUY':
        # Long: TP is ABOVE entry
        take_profit = entry_price + (risk_in_price * rr_ratio)
    else:
        # Short: TP is BELOW entry
        take_profit = entry_price - (risk_in_price * rr_ratio)
        
    return take_profit

def calculate_position_size(balance, risk_percent, entry_price, structural_sl, side):
    """Calculates position size and buffered SL based on trade direction."""
    risk_amount = balance * (risk_percent / 100)
    
    # Buffer for execution tolerance (0.01%)
    buffer = entry_price * 0.0001 
    
    if side == 'BUY':
        # SL must be BELOW entry. If structural_sl is above entry, this is an invalid setup.
        stop_loss_final = structural_sl - buffer
        if stop_loss_final >= entry_price:
            print(f"⚠️ Invalid BUY Setup: SL ({stop_loss_final}) is above Entry ({entry_price})")
            return 0, stop_loss_final
    else:
        # SL must be ABOVE entry.
        stop_loss_final = structural_sl + buffer
        if stop_loss_final <= entry_price:
            print(f"⚠️ Invalid SELL Setup: SL ({stop_loss_final}) is below Entry ({entry_price})")
            return 0, stop_loss_final
        
    final_risk_in_price = abs(entry_price - stop_loss_final)

    # Prevent division by zero or extremely tiny positions
    if final_risk_in_price < 0.0001: 
        return 0, stop_loss_final

    position_size = risk_amount / final_risk_in_price
    
    return position_size, stop_loss_final