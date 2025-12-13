def detect_trend(swing_lows, swing_highs):
    if len(swing_lows) < 2 or len(swing_highs) < 2:
        return 'SIDEWAYS'
        
    # Higher Highs (HH) and Higher Lows (HL)
    if swing_lows[-1]['price'] > swing_lows[-2]['price'] and swing_highs[-1]['price'] > swing_highs[-2]['price']:
        return 'UPTREND'
    # Lower Highs (LH) and Lower Lows (LL)
    elif swing_lows[-1]['price'] < swing_lows[-2]['price'] and swing_highs[-1]['price'] < swing_highs[-2]['price']:
        return 'DOWNTREND'
    return 'SIDEWAYS'