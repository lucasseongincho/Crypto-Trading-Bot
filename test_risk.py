from risk import calculate_position_size, calculate_take_profit

def run_unit_test():
    # --- TEST DATA ---
    balance = 1000.0
    risk_pct = 1.0
    entry_price = 3000.0
    
    print("🧪 STARTING RISK LOGIC UNIT TEST\n" + "="*40)

    # --- TEST 1: BUY (LONG) ---
    # In a BUY, SL must be BELOW entry
    bullish_sl_target = 2950.0 
    
    pos_size_buy, sl_buy = calculate_position_size(balance, risk_pct, entry_price, bullish_sl_target, 'BUY')
    tp2_buy = calculate_take_profit(entry_price, sl_buy, 'BUY', 2.0)

    print(f"🔹 [BUY TEST]")
    print(f"   Entry: {entry_price}")
    print(f"   Final SL: {sl_buy:.2f} (Should be < {entry_price})")
    print(f"   Final TP2: {tp2_buy:.2f} (Should be > {entry_price})")
    
    # Validation Logic
    if sl_buy < entry_price and tp2_buy > entry_price:
        print("   ✅ BUY MATH PASSED")
    else:
        print("   ❌ BUY MATH FAILED")

    print("-" * 40)

    # --- TEST 2: SELL (SHORT) ---
    # In a SELL, SL must be ABOVE entry
    bearish_sl_target = 3050.0 
    
    pos_size_sell, sl_sell = calculate_position_size(balance, risk_pct, entry_price, bearish_sl_target, 'SELL')
    tp2_sell = calculate_take_profit(entry_price, sl_sell, 'SELL', 2.0)

    print(f"🔸 [SELL TEST]")
    print(f"   Entry: {entry_price}")
    print(f"   Final SL: {sl_sell:.2f} (Should be > {entry_price})")
    print(f"   Final TP2: {tp2_sell:.2f} (Should be < {entry_price})")
    
    # Validation Logic
    if sl_sell > entry_price and tp2_sell < entry_price:
        print("   ✅ SELL MATH PASSED")
    else:
        print("   ❌ SELL MATH FAILED")

    print("="*40)

if __name__ == "__main__":
    run_unit_test()