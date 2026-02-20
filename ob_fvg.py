import pandas as pd

def detect_order_blocks(candles):
    """
    Detects standard SMC Order Blocks.
    Works with both Lists (Live) and DataFrames (Backtest).
    """
    # 🛡️ THE UNIVERSAL TRANSLATOR
    df = pd.DataFrame(candles) if isinstance(candles, list) else candles
    
    # Ensure column names are lowercase so 'Close' or 'close' both work
    df.columns = [x.lower() for x in df.columns]
    
    ob_list = []
    
    # Need at least 2 candles to compare
    if len(df) < 2:
        return ob_list

    # Loop using .iloc for DataFrame safety
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        # Bullish OB: A down-close candle followed by a strong up-close candle
        if float(prev['close']) < float(prev['open']) and float(curr['close']) > float(curr['open']):
            if float(curr['close']) > float(prev['high']): # Engulfing / Strong push
                ob_list.append({
                    'type': 'bullish',
                    'high': float(prev['high']),
                    'low': float(prev['low']),
                    'index': i
                })
                
        # Bearish OB: An up-close candle followed by a strong down-close candle
        elif float(prev['close']) > float(prev['open']) and float(curr['close']) < float(curr['open']):
            if float(curr['close']) < float(prev['low']):
                ob_list.append({
                    'type': 'bearish',
                    'high': float(prev['high']),
                    'low': float(prev['low']),
                    'index': i
                })

    return ob_list

def detect_fvg(candles):
    """
    Detects Fair Value Gaps (3-candle patterns).
    """
    # 🛡️ THE UNIVERSAL TRANSLATOR
    df = pd.DataFrame(candles) if isinstance(candles, list) else candles
    df.columns = [x.lower() for x in df.columns]
    
    fvg_list = []
    
    # Need at least 3 candles to find a gap
    if len(df) < 3:
        return fvg_list

    for i in range(2, len(df)):
        candle_1 = df.iloc[i-2]
        # candle_2 is the large impulse candle in the middle
        candle_3 = df.iloc[i]
        
        # Bullish FVG: Gap between C1 High and C3 Low
        if float(candle_3['low']) > float(candle_1['high']):
            fvg_list.append({
                'type': 'bullish',
                'top': float(candle_3['low']),
                'bottom': float(candle_1['high']),
                'index': i
            })
            
        # Bearish FVG: Gap between C1 Low and C3 High
        elif float(candle_3['high']) < float(candle_1['low']):
            fvg_list.append({
                'type': 'bearish',
                'top': float(candle_1['low']),
                'bottom': float(candle_3['high']),
                'index': i
            })

    return fvg_list