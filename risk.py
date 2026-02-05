def calculate_take_profit(entry_price, stop_loss, side, rr_ratio=2.0):
    """Calculates Take Profit based on Risk-to-Reward ratio and trade direction."""
    risk_in_price = abs(entry_price - stop_loss)
    
    if side == 'BUY':
        take_profit = entry_price + (risk_in_price * rr_ratio)
    else:
        take_profit = entry_price - (risk_in_price * rr_ratio)
        
    return take_profit

def calculate_position_size(balance, risk_percent, entry_price, structural_sl, side):
    """Calculates position size with a Minimum Risk Distance check (0.1%)."""
    risk_amount = balance * (risk_percent / 100)
    
    # 1. Calculate the final SL with buffer (0.01%)
    buffer = entry_price * 0.0001 
    if side == 'BUY':
        stop_loss_final = structural_sl - buffer
        if stop_loss_final >= entry_price:
            print(f"⚠️ Invalid BUY Setup: SL ({stop_loss_final}) above Entry")
            return 0, stop_loss_final
    else:
        stop_loss_final = structural_sl + buffer
        if stop_loss_final <= entry_price:
            print(f"⚠️ Invalid SELL Setup: SL ({stop_loss_final}) below Entry")
            return 0, stop_loss_final
        
    # 2. Calculate risk distance
    final_risk_in_price = abs(entry_price - stop_loss_final)

    # --- MINIMUM DISTANCE CHECK (0.1% of price) ---
    # Prevents "0-minute" trades caused by market noise
    min_distance = entry_price * 0.001 
    if final_risk_in_price < min_distance:
        print(f"⚠️ Trade skipped: SL too tight ({final_risk_in_price:.2f} < {min_distance:.2f})")
        return 0, stop_loss_final

    position_size = risk_amount / final_risk_in_price
    return position_size, stop_loss_final