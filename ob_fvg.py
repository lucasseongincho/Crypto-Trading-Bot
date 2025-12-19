def detect_order_blocks(candles):
    ob_list = []
    # Loop to find initial OB patterns
    for i in range(1, len(candles)):
        prev = candles[i-1]
        curr = candles[i]
        
        ob = None
        # Bullish OB detection
        if curr['close'] > curr['open'] and prev['close'] < prev['open'] and curr['close'] > prev['high']:
            ob = {'type': 'bullish', 'low': prev['low'], 'high': prev['high'], 'index': i}
        # Bearish OB detection
        elif curr['close'] < curr['open'] and prev['close'] > prev['open'] and curr['close'] < prev['low']:
            ob = {'type': 'bearish', 'low': prev['low'], 'high': prev['high'], 'index': i}

        if ob:
            # --- MITIGATION CHECK ---
            # Check every candle from the OB creation until the latest candle
            is_mitigated = False
            for j in range(i + 1, len(candles)):
                # If a future candle dips into a Bullish OB or rallies into a Bearish OB
                if ob['type'] == 'bullish' and candles[j]['low'] <= ob['high']:
                    is_mitigated = True
                    break
                elif ob['type'] == 'bearish' and candles[j]['high'] >= ob['low']:
                    is_mitigated = True
                    break
            
            if not is_mitigated:
                ob_list.append(ob)
                
    return ob_list

def detect_fvg(candles):
    fvg_list = []
    for i in range(2, len(candles)):
        fvg = None
        if candles[i]['low'] > candles[i-2]['high']:
            fvg = {'type': 'bullish', 'low': candles[i-2]['high'], 'high': candles[i]['low'], 'index': i}
        elif candles[i]['high'] < candles[i-2]['low']:
            fvg = {'type': 'bearish', 'low': candles[i]['high'], 'high': candles[i-2]['low'], 'index': i}

        if fvg:
            # --- MITIGATION CHECK ---
            is_mitigated = False
            for j in range(i + 1, len(candles)):
                if fvg['type'] == 'bullish' and candles[j]['low'] <= fvg['low']:
                    is_mitigated = True
                    break
                elif fvg['type'] == 'bearish' and candles[j]['high'] >= fvg['high']:
                    is_mitigated = True
                    break
            
            if not is_mitigated:
                fvg_list.append(fvg)
    return fvg_list