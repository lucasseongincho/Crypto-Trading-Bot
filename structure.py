import pandas as pd

def detect_swings(candles, left_bars=3, right_bars=3):
    """
    Detects Swing Highs and Swing Lows.
    Works with both Lists (Live) and DataFrames (Backtest).
    """
    # 🛡️ THE UNIVERSAL TRANSLATOR
    df = pd.DataFrame(candles) if isinstance(candles, list) else candles
    df.columns = [x.lower() for x in df.columns]
    
    swings = []
    
    # We need enough candles to check left and right
    if len(df) < left_bars + right_bars + 1:
        return swings

    for i in range(left_bars, len(df) - right_bars):
        curr = df.iloc[i]
        
        # Check for Swing High
        is_high = True
        for j in range(1, left_bars + 1):
            if float(df.iloc[i-j]['high']) >= float(curr['high']):
                is_high = False; break
        for j in range(1, right_bars + 1):
            if float(df.iloc[i+j]['high']) >= float(curr['high']):
                is_high = False; break
        
        if is_high:
            swings.append({'type': 'high', 'price': float(curr['high']), 'index': i})

        # Check for Swing Low
        is_low = True
        for j in range(1, left_bars + 1):
            if float(df.iloc[i-j]['low']) <= float(curr['low']):
                is_low = False; break
        for j in range(1, right_bars + 1):
            if float(df.iloc[i+j]['low']) <= float(curr['low']):
                is_low = False; break
                
        if is_low:
            swings.append({'type': 'low', 'price': float(curr['low']), 'index': i})

    return swings