from datetime import datetime
from ob_fvg import detect_order_blocks, detect_fvg
from trendline import detect_trend
from fakeout import detect_fakeout
from structure import detect_swings 

def generate_trade_signal(candles_5m, candles_htf):
    # --- STEP 1: HTF Bias ---
    current_htf_close = float(candles_htf[0]['close'])
    prev_htf_close = float(candles_htf[1]['close'])
    htf_bias = "BULLISH" if current_htf_close > prev_htf_close else "BEARISH"

    # --- STEP 2: 5m Analysis ---
    visible_5m = candles_5m[:100] 
    ob_list = detect_order_blocks(visible_5m)
    fvg_list = detect_fvg(visible_5m) # MANDATORY FOR ENTRY
    swings = detect_swings(visible_5m)
    trend_5m = detect_trend([s for s in swings if s['type']=='low'], [s for s in swings if s['type']=='high'])
    fakeout = detect_fakeout(visible_5m, swings)

    bullish_signals = 0
    bearish_signals = 0
    structural_price = None
    fvg_present = False

    # Bullish Logic
    if ob_list and ob_list[-1]['type']=='bullish': 
        bullish_signals += 1
        structural_price = ob_list[-1]['low']
    if fvg_list and fvg_list[-1]['type']=='bullish': 
        bullish_signals += 1
        fvg_present = True # Found institutional energy
    if trend_5m == 'UPTREND': bullish_signals += 1
    if fakeout == 'BULL_FAKEOUT': bullish_signals += 1

    # Bearish Logic
    if ob_list and ob_list[-1]['type']=='bearish': 
        bearish_signals += 1
        structural_price = ob_list[-1]['high']
    if fvg_list and fvg_list[-1]['type']=='bearish': 
        bearish_signals += 1
        fvg_present = True # Found institutional energy
    if trend_5m == 'DOWNTREND': bearish_signals += 1
    if fakeout == 'BEAR_FAKEOUT': bearish_signals += 1

    # --- STEP 3: Sniper Filter ---
    final_signal = 'HOLD'
    
    # REQUIRE: 3 signals AND HTF Alignment AND FVG Presence
    if bullish_signals >= 3 and htf_bias == 'BULLISH' and fvg_present:
        final_signal = 'BUY'
    elif bearish_signals >= 3 and htf_bias == 'BEARISH' and fvg_present:
        final_signal = 'SELL'
    elif bullish_signals >= 3 or bearish_signals >= 3:
        reason = "HTF Mismatch" if htf_bias not in final_signal else "No FVG (No Energy)"
        print(f"🚫 {datetime.now().strftime('%H:%M:%S')} Blocked: {reason}")

    counts = {'bull': bullish_signals, 'bear': bearish_signals, 'bias': htf_bias}
    return final_signal, structural_price, counts