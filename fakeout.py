def detect_fakeout(candles, swings):
    if len(swings) < 2:
        return None
    last = swings[-1]
    prev = swings[-2]
    
    # Bullish fakeout: sweep prev low, then current candle closes above the swept level
    if last['type'] == 'low' and last['price'] < prev['price'] and candles[last['index']]['close'] > prev['price']:
        return 'BULL_FAKEOUT'
    # Bearish fakeout: sweep prev high, then current candle closes below the swept level
    elif last['type'] == 'high' and last['price'] > prev['price'] and candles[last['index']]['close'] < prev['price']:
        return 'BEAR_FAKEOUT'
    return None