import pandas as pd

def detect_fakeout(candles, swings):
    """
    Detects liquidity sweeps / fakeouts.
    Works with both Lists (Live) and DataFrames (Backtest).
    """
    # 🛡️ THE UNIVERSAL TRANSLATOR
    df = pd.DataFrame(candles) if isinstance(candles, list) else candles
    df.columns = [x.lower() for x in df.columns]
    
    if len(df) < 3 or not swings:
        return None
        
    curr_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]
    
    # Bullish Fakeout: Swept a recent low, but closed back above it
    recent_lows = [s for s in swings if s['type'] == 'low']
    if recent_lows:
        last_low = recent_lows[-1]['price']
        if float(prev_candle['low']) < last_low and float(curr_candle['close']) > last_low:
            return 'BULL_FAKEOUT'
            
    # Bearish Fakeout: Swept a recent high, but closed back below it
    recent_highs = [s for s in swings if s['type'] == 'high']
    if recent_highs:
        last_high = recent_highs[-1]['price']
        if float(prev_candle['high']) > last_high and float(curr_candle['close']) < last_high:
            return 'BEAR_FAKEOUT'

    return None