from ob_fvg import detect_order_blocks, detect_fvg
from trendline import detect_trend
from fakeout import detect_fakeout
from structure import detect_swings # Corrected import from structure.py

def generate_trade_signal(candles):
    swings = detect_swings(candles)
    ob_list = detect_order_blocks(candles)
    fvg_list = detect_fvg(candles)
    
    swing_lows = [s for s in swings if s['type']=='low']
    swing_highs = [s for s in swings if s['type']=='high']
    trend = detect_trend(swing_lows, swing_highs)
    fakeout = detect_fakeout(candles, swings)

    # Variables to store the structural level for SL
    structural_price = None

    # --- 3-Signal Confirmation Logic ---
    bullish_signals = 0
    bearish_signals = 0

    if ob_list and ob_list[-1]['type']=='bullish': 
        bullish_signals += 1
        structural_price = ob_list[-1]['low'] # Use OB low for SL
        
    if fvg_list and fvg_list[-1]['type']=='bullish': bullish_signals += 1
    if trend=='UPTREND': bullish_signals +=1
    if fakeout=='BULL_FAKEOUT': bullish_signals +=1

    if ob_list and ob_list[-1]['type']=='bearish': 
        bearish_signals += 1
        structural_price = ob_list[-1]['high'] # Use OB high for SL
        
    if fvg_list and fvg_list[-1]['type']=='bearish': bearish_signals += 1
    if trend=='DOWNTREND': bearish_signals +=1
    if fakeout=='BEAR_FAKEOUT': bearish_signals +=1

    if bullish_signals >= 3:
        return 'BUY', structural_price
    elif bearish_signals >= 3:
        return 'SELL', structural_price
        
    return 'HOLD', None