from datetime import datetime
from ob_fvg import detect_order_blocks, detect_fvg
from trendline import detect_trend
from fakeout import detect_fakeout
from structure import detect_swings

def generate_trade_signal(candles_5m, candles_htf):
    # --- STEP 1: Determine Higher Timeframe (HTF) Bias ---
    # Coinbase returns candles [newest ... oldest]
    # We compare the latest closed 4h/6h candle to the one before it
    current_htf_close = float(candles_htf[0]['close'])
    prev_htf_close = float(candles_htf[1]['close'])
    
    htf_bias = "BULLISH" if current_htf_close > prev_htf_close else "BEARISH"

    # --- STEP 2: Analyze 5-Minute Setup ---
    # We use a 100-candle window for the 5m analysis
    window_size = 100
    visible_5m = candles_5m[:window_size] 

    swings = detect_swings(visible_5m)
    ob_list = detect_order_blocks(visible_5m)
    fvg_list = detect_fvg(visible_5m)
    
    swing_lows = [s for s in swings if s['type']=='low']
    swing_highs = [s for s in swings if s['type']=='high']
    
    trend_5m = detect_trend(swing_lows, swing_highs)
    fakeout = detect_fakeout(visible_5m, swings)

    bullish_signals = 0
    bearish_signals = 0
    structural_price = None

    # Bullish Logic
    if ob_list and ob_list[-1]['type']=='bullish': 
        bullish_signals += 1
        structural_price = ob_list[-1]['low'] # SL below OB
    if fvg_list and fvg_list[-1]['type']=='bullish': bullish_signals += 1
    if trend_5m == 'UPTREND': bullish_signals += 1
    if fakeout == 'BULL_FAKEOUT': bullish_signals += 1

    # Bearish Logic
    if ob_list and ob_list[-1]['type']=='bearish': 
        bearish_signals += 1
        structural_price = ob_list[-1]['high'] # SL above OB
    if fvg_list and fvg_list[-1]['type']=='bearish': bearish_signals += 1
    if trend_5m == 'DOWNTREND': bearish_signals += 1
    if fakeout == 'BEAR_FAKEOUT': bearish_signals += 1

    # --- STEP 3: Apply the HTF Filter ---
    final_signal = 'HOLD'
    
    if bullish_signals >= 3 and htf_bias == 'BULLISH':
        final_signal = 'BUY'
    elif bearish_signals >= 3 and htf_bias == 'BEARISH':
        final_signal = 'SELL'
    elif bullish_signals >= 3 or bearish_signals >= 3:
        # Log that a setup was found but blocked by the big trend
        print(f"🚫 {datetime.now().strftime('%H:%M:%S')} Signal Blocked: 5m is {final_signal} but HTF Bias is {htf_bias}")

    counts = {
        'bull': bullish_signals,
        'bear': bearish_signals,
        'bias': htf_bias,
        'trend': trend_5m
    }

    return final_signal, structural_price, counts