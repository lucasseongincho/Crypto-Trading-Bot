import pandas as pd
from datetime import datetime
from ob_fvg import detect_order_blocks, detect_fvg
from trendline import detect_trend
from fakeout import detect_fakeout
from structure import detect_swings 

class SMCStrategy:
    def __init__(self):
        self.name = "SMC Sniper v1"

    def check_setup(self, candles_input, candles_htf=None):
        """
        Main brain logic. Works for both Live (List) and Research (DataFrame).
        """
        # 🛡️ UNIVERSAL DATA CONVERTER
        # Converts List of Dicts to DataFrame ONLY if needed
        df = pd.DataFrame(candles_input) if isinstance(candles_input, list) else candles_input
        
        # Ensure column names are lowercase to avoid errors
        df.columns = [x.lower() for x in df.columns]

        # --- STEP 1: HTF Bias (Higher Time Frame) ---
        if candles_htf is None:
            # SIMULATION MODE: Compare current price to the price 8 hours ago
            current_close = float(df.iloc[-1]['close'])
            past_close = float(df.iloc[0]['close'])
            htf_bias = "BULLISH" if current_close > past_close else "BEARISH"
        else:
            # LIVE MODE: Use actual Coinbase HTF data
            htf_df = pd.DataFrame(candles_htf) if isinstance(candles_htf, list) else candles_htf
            htf_df.columns = [x.lower() for x in htf_df.columns]
            
            current_htf_close = float(htf_df.iloc[-1]['close'])
            prev_htf_close = float(htf_df.iloc[-2]['close'])
            htf_bias = "BULLISH" if current_htf_close > prev_htf_close else "BEARISH"

        # --- STEP 2: 5m Analysis ---
        # Get the last 100 candles for analysis
        visible_5m = df.tail(100).copy()
        
        # Call your external detection modules
        ob_list = detect_order_blocks(visible_5m)
        fvg_list = detect_fvg(visible_5m)
        swings = detect_swings(visible_5m)
        
        # Trend and Fakeout detection
        lows = [s for s in swings if s['type']=='low']
        highs = [s for s in swings if s['type']=='high']
        trend_5m = detect_trend(lows, highs)
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
            fvg_present = True 
        if trend_5m == 'UPTREND': bullish_signals += 1
        if fakeout == 'BULL_FAKEOUT': bullish_signals += 1

        # Bearish Logic
        if ob_list and ob_list[-1]['type']=='bearish': 
            bearish_signals += 1
            structural_price = ob_list[-1]['high']
        if fvg_list and fvg_list[-1]['type']=='bearish': 
            bearish_signals += 1
            fvg_present = True 
        if trend_5m == 'DOWNTREND': bearish_signals += 1
        if fakeout == 'BEAR_FAKEOUT': bearish_signals += 1

        # --- STEP 3: Final Signal Generation ---
        current_price = float(visible_5m.iloc[-1]['close'])
        
        if bullish_signals >= 3 and htf_bias == 'BULLISH' and fvg_present:
            # For a BUY, Stop Loss MUST be lower than current price
            safe_sl = structural_price if (structural_price and structural_price < current_price) else current_price * 0.99
            return {
                'type': 'BUY', 
                'entry_price': current_price, 
                'stop_loss': round(safe_sl, 2)
            }
        
        if bearish_signals >= 3 and htf_bias == 'BEARISH' and fvg_present:
            # For a SELL, Stop Loss MUST be higher than current price
            safe_sl = structural_price if (structural_price and structural_price > current_price) else current_price * 1.01
            return {
                'type': 'SELL', 
                'entry_price': current_price, 
                'stop_loss': round(safe_sl, 2)
            }

        return None # No clear setup found