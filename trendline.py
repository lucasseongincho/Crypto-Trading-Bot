def detect_trend(lows, highs):
    """
    Determines the current trend based on swing points.
    Returns: 'UPTREND', 'DOWNTREND', or 'RANGING'
    """
    # We need at least 2 highs and 2 lows to determine a trend
    if len(lows) < 2 or len(highs) < 2:
        return "RANGING"

    # Get the last two swing points
    hh = highs[-1]['price'] > highs[-2]['price']  # Higher High
    hl = lows[-1]['price'] > lows[-2]['price']    # Higher Low
    
    lh = highs[-1]['price'] < highs[-2]['price']  # Lower High
    ll = lows[-1]['price'] < lows[-2]['price']    # Lower Low

    if hh and hl:
        return "UPTREND"
    elif lh and ll:
        return "DOWNTREND"
    else:
        return "RANGING"