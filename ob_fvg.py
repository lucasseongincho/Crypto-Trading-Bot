def detect_order_blocks(candles):
    ob_list = []
    # Simplified detection: look for a large opposite color candle (OB) before the impulse move
    for i in range(1, len(candles)):
        prev = candles[i-1]
        curr = candles[i]
        
        # Bullish OB: prev candle is red, curr is green, curr closes above prev high
        if curr['close'] > curr['open'] and prev['close'] < prev['open'] and curr['close'] > prev['high']:
            ob_list.append({'type':'bullish','low':prev['low'],'high':prev['high']})
        # Bearish OB: prev candle is green, curr is red, curr closes below prev low
        elif curr['close'] < curr['open'] and prev['close'] > prev['open'] and curr['close'] < prev['low']:
            ob_list.append({'type':'bearish','low':prev['low'],'high':prev['high']})
    return ob_list

def detect_fvg(candles):
    fvg_list = []
    # FVG = Gap between Candle 1's high/low and Candle 3's high/low
    for i in range(2, len(candles)):
        # Bullish FVG: Low[i] > High[i-2]
        if candles[i]['low'] > candles[i-2]['high']:
            fvg_list.append({'type':'bullish','low':candles[i-2]['high'],'high':candles[i]['low']})
        # Bearish FVG: High[i] < Low[i-2]
        elif candles[i]['high'] < candles[i-2]['low']:
            fvg_list.append({'type':'bearish','low':candles[i]['high'],'high':candles[i-2]['low']})
    return fvg_list