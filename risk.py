def calculate_take_profit(entry_price, structural_sl, rr_ratio=2.0):
    """Calculates Take Profit based on Risk-to-Reward ratio."""
    risk_in_price = abs(entry_price - structural_sl)
    
    if entry_price > structural_sl:  # Bullish Trade (SL below entry)
        take_profit = entry_price + (risk_in_price * rr_ratio)
    else:  # Bearish Trade (SL above entry)
        take_profit = entry_price - (risk_in_price * rr_ratio)
        
    return take_profit

def calculate_position_size(balance, risk_percent, entry_price, structural_sl):
    """Calculates position size based on dollar risk and structural stop loss."""
    risk_amount = balance * risk_percent / 100
    
    # The actual price difference that represents 1R of risk
    risk_in_price = abs(entry_price - structural_sl) 
    
    # Add a small buffer to the SL for execution tolerance (e.g., 0.01%)
    buffer = entry_price * 0.0001 
    if entry_price > structural_sl:
        stop_loss_final = structural_sl - buffer # Long: SL below OB low
    else:
        stop_loss_final = structural_sl + buffer # Short: SL above OB high
        
    # Recalculate risk using the buffered SL
    final_risk_in_price = abs(entry_price - stop_loss_final)

    # Avoid division by zero or overly tight risk
    if final_risk_in_price < 0.0001: 
        return 0, stop_loss_final

    # Position size = Dollar Risk / Final Risk in Price
    position_size = risk_amount / final_risk_in_price
    
    return position_size, stop_loss_final