def detect_swings(candles):
    # This remains the simple N-bar swing detection
    swings = []
    for i in range(1, len(candles)-1):
        if candles[i]['low'] < candles[i-1]['low'] and candles[i]['low'] < candles[i+1]['low']:
            swings.append({'type':'low','index':i,'price':candles[i]['low']})
        elif candles[i]['high'] > candles[i-1]['high'] and candles[i]['high'] > candles[i+1]['high']:
            swings.append({'type':'high','index':i,'price':candles[i]['high']})
    return swings

def detect_bos(swings):
    if len(swings) < 2:
        return None
    if swings[-1]['type'] == 'high' and swings[-1]['price'] > swings[-2]['price']:
        return 'BOS_UP'
    elif swings[-1]['type'] == 'low' and swings[-1]['price'] < swings[-2]['price']:
        return 'BOS_DOWN'
    return None