from ob_fvg import detect_order_blocks, detect_fvg
from trendline import detect_trend
from fakeout import detect_fakeout
from structure import detect_swings 

def generate_trade_signal(candles, current_idx):
    # Standard lookback window to keep logic consistent and fast
    window_size = 100
    start_lookback = max(0, current_idx - window_size)
    visible_candles = candles[start_lookback : current_idx + 1] 

    # Detect market structure elements
    swings = detect_swings(visible_candles)
    ob_list = detect_order_blocks(visible_candles)
    fvg_list = detect_fvg(visible_candles)
    
    swing_lows = [s for s in swings if s['type']=='low']
    swing_highs = [s for s in swings if s['type']=='high']
    
    # Analyze trend and fakeouts
    trend = detect_trend(swing_lows, swing_highs)
    fakeout = detect_fakeout(visible_candles, swings)

    structural_price = None
    bullish_signals = 0
    bearish_signals = 0

    # --- Bullish Confirmation Logic ---
    if ob_list and ob_list[-1]['type']=='bullish': 
        bullish_signals += 1
        structural_price = ob_list[-1]['low']
        
    if fvg_list and fvg_list[-1]['type']=='bullish': bullish_signals += 1
    if trend == 'UPTREND': bullish_signals += 1
    if fakeout == 'BULL_FAKEOUT': bullish_signals += 1

    # --- Bearish Confirmation Logic ---
    if ob_list and ob_list[-1]['type']=='bearish': 
        bearish_signals += 1
        structural_price = ob_list[-1]['high']
        
    if fvg_list and fvg_list[-1]['type']=='bearish': bearish_signals += 1
    if trend == 'DOWNTREND': bearish_signals += 1
    if fakeout == 'BEAR_FAKEOUT': bearish_signals += 1

    # New: Dictionary for the Heartbeat display in main.py
    counts = {
        'bull': bullish_signals,
        'bear': bearish_signals,
        'trend': trend,
        'fake': fakeout
    }

    # Logic: Return Signal, SL Price, and the Confirmation Counts
    if bullish_signals >= 3:
        return 'BUY', structural_price, counts
    elif bearish_signals >= 3:
        return 'SELL', structural_price, counts
        
    return 'HOLD', None, counts