"""
Page 1 — Live Monitor
Fetches live BTC-USD data from Coinbase, runs the SMC strategy,
and renders a candlestick chart with OB/FVG overlays.
"""
import sys, time, json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Allow importing from the parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from ob_fvg import detect_order_blocks, detect_fvg
from structure import detect_swings
from trendline import detect_trend
from fakeout import detect_fakeout
from strategy import SMCStrategy
from risk import RiskManager

st.set_page_config(page_title="Live Monitor", page_icon="📡", layout="wide")

# ── Shared CSS (imported via st.markdown so it applies on this page too) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0f0f1a 0%,#1a1a2e 100%); }
[data-testid="stSidebar"] * { color: #e0e0f0 !important; }
[data-testid="stAppViewContainer"] { background: #0d0d1a; }
[data-testid="stMetric"] { background:#161628; border:1px solid #2a2a4a; border-radius:12px; padding:16px 20px; }
[data-testid="stMetricLabel"] { color:#8888aa !important; font-size:0.78rem; }
[data-testid="stMetricValue"] { color:#e0e0ff !important; font-size:1.6rem; font-weight:700; }
h1,h2,h3 { color:#c0c0ff !important; }
hr { border-color:#2a2a4a; }
.stButton > button { background:linear-gradient(135deg,#6c63ff,#4a90e2); color:white; border:none; border-radius:8px; padding:0.45rem 1.2rem; font-weight:600; }
.badge { display:inline-block; padding:4px 14px; border-radius:20px; font-size:0.85rem; font-weight:600; }
.badge-bull  { background:#0d2e1a; color:#39d37a; border:1px solid #39d37a44; }
.badge-bear  { background:#2e0d0d; color:#ff5c5c; border:1px solid #ff5c5c44; }
.badge-range { background:#1a1a30; color:#9090d0; border:1px solid #9090d044; }
.badge-buy   { background:#0a2e18; color:#2ecc71; border:1px solid #2ecc7144; }
.badge-sell  { background:#2e0a0a; color:#e74c3c; border:1px solid #e74c3c44; }
.badge-none  { background:#1a1a2e; color:#7070a0; border:1px solid #7070a044; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent
PRODUCT_ID  = "BTC-USD"
CANDLE_GRAN = "FIVE_MINUTE"
HTF_GRAN    = "SIX_HOUR"

def get_coinbase_client():
    try:
        from auth import client
        return client
    except Exception as e:
        return None

def get_bot_status():
    """Reads the JSON bridge file from the live bot."""
    status_file = BASE_DIR / "bot_status.json"
    if status_file.exists():
        try:
            with open(status_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"is_in_position": False}

@st.cache_data(ttl=30, show_spinner=False)
def fetch_live_balance(dummy_ts):
    client = get_coinbase_client()
    if client is None:
        return None
    try:
        accounts = client.get_accounts()
        for acc in accounts["accounts"]:
            if acc["currency"] == "USD":
                return float(acc["available_balance"]["value"])
    except Exception:
        return None

@st.cache_data(ttl=30, show_spinner=False)
def fetch_candles(dummy_ts):
    client = get_coinbase_client()
    if client is None:
        return pd.DataFrame(), pd.DataFrame()
    try:
        now = int(time.time())
        resp_5m  = client.get_public_candles(PRODUCT_ID, str(now - 300*150),    str(now), CANDLE_GRAN)
        resp_htf = client.get_public_candles(PRODUCT_ID, str(now - 21600*50),   str(now), HTF_GRAN)
        
        def parse(resp):
            raw = resp["candles"] if isinstance(resp, dict) else resp.candles
            rows = []
            for c in raw:
                rows.append(c if isinstance(c, dict) else (c.to_dict() if hasattr(c, "to_dict") else vars(c)))
            df = pd.DataFrame(rows)
            if not df.empty:
                df.columns = [x.lower() for x in df.columns]
                if "start" in df.columns:
                    df["start"] = df["start"].astype(int)
                    df = df.sort_values("start").reset_index(drop=True)
                for col in ["open", "high", "low", "close", "volume"]:
                    if col in df.columns:
                        df[col] = df[col].astype(float)
                if "start" in df.columns:
                    # Convert UNIX to UTC, then translate to New York time
                    df["datetime"] = pd.to_datetime(df["start"], unit="s").dt.tz_localize("UTC").dt.tz_convert("America/New_York")
            return df
            
        return parse(resp_5m), parse(resp_htf)
    except Exception as e:
        st.error(f"Coinbase API error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ──────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────
st.markdown("# 📡 Live Monitor")
st.caption("Auto-refreshes every 30 s via Coinbase Advanced Trade API (read-only).")

refresh_col, _ = st.columns([1, 5])
with refresh_col:
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()

st.divider()

# 🌉 THE BRIDGE: Check bot status and display banner
bot_status = get_bot_status()

if bot_status.get("is_in_position"):
    st.success(f"🤖 **BOT ACTIVE TRADE:** {bot_status.get('side')} {bot_status.get('qty')} BTC @ **${bot_status.get('entry_price'):,.2f}**  |  🎯 TP: **${bot_status.get('take_profit'):,.2f}**  |  🛡️ SL: **${bot_status.get('stop_loss'):,.2f}**")
else:
    st.info("🤖 **BOT STATUS:** Scanning for setups... (No active trade)")


# Use current minute as cache buster so auto-cache TTL applies
ts_bucket = int(time.time() // 30)

with st.spinner("Fetching live data…"):
    df_5m, df_htf = fetch_candles(ts_bucket)
    live_balance  = fetch_live_balance(ts_bucket)

# ── KPI Row ──────────────────────────────────
if df_5m.empty:
    st.warning("⚠️ Could not fetch candle data. Check your API keys and internet connection.")
else:
    current_price = df_5m.iloc[-1]["close"]
    prev_price    = df_5m.iloc[-2]["close"] if len(df_5m) > 1 else current_price
    price_delta   = current_price - prev_price
    
    # Run strategy
    strategy = SMCStrategy()
    signal   = strategy.check_setup(df_5m, df_htf if not df_htf.empty else None)
    
    # Risk / kill switch
    if live_balance:
        risk      = RiskManager(initial_balance=live_balance)
        kill_lim  = live_balance * 0.80  # 20% drawdown threshold
    else:
        kill_lim  = None
        
    # Indicator data
    visible  = df_5m.tail(100).copy()
    ob_list  = detect_order_blocks(visible)
    fvg_list = detect_fvg(visible)
    swings   = detect_swings(visible)
    lows     = [s for s in swings if s["type"] == "low"]
    highs    = [s for s in swings if s["type"] == "high"]
    trend    = detect_trend(lows, highs)
    fakeout  = detect_fakeout(visible, swings)
    
    # HTF bias
    if not df_htf.empty and len(df_htf) >= 2:
        htf_bias = "BULLISH" if df_htf.iloc[-1]["close"] > df_htf.iloc[-2]["close"] else "BEARISH"
    else:
        htf_bias = "N/A"
        
    # ── 5 KPI cards ──
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("BTC Price (USD)",  f"${current_price:,.2f}", f"{price_delta:+.2f}")
    k2.metric("Live USD Balance", f"${live_balance:,.2f}"  if live_balance else "N/A")
    k3.metric("Kill-Switch Limit", f"${kill_lim:,.2f}"    if kill_lim  else "N/A")
    k4.metric("HTF Bias",          htf_bias)
    k5.metric("Last Refresh",      datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    # ── Signal + Trend badges ──
    badge_col1, badge_col2, badge_col3 = st.columns(3)
    with badge_col1:
        if signal:
            sig_type  = signal["type"]
            cls       = "badge-buy" if sig_type == "BUY" else "badge-sell"
            emo       = "🟢" if sig_type == "BUY" else "🔴"
            st.markdown(f"**Scanner Setup:** <span class='badge {cls}'>{emo} {sig_type} @ ${signal['entry_price']:,.2f} | SL ${signal['stop_loss']:,.2f}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge badge-none'>⚪ No Scanner Setup</span>", unsafe_allow_html=True)
    with badge_col2:
        t_cls = {"UPTREND": "badge-bull", "DOWNTREND": "badge-bear", "RANGING": "badge-range"}.get(trend, "badge-range")
        t_emo = {"UPTREND": "📈", "DOWNTREND": "📉", "RANGING": "↔️"}.get(trend, "")
        st.markdown(f"**5m Trend:** <span class='badge {t_cls}'>{t_emo} {trend}</span>", unsafe_allow_html=True)
    with badge_col3:
        if fakeout:
            fk_cls = "badge-bull" if "BULL" in fakeout else "badge-bear"
            st.markdown(f"**Fakeout:** <span class='badge {fk_cls}'>⚡ {fakeout}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge badge-none'>— No Fakeout</span>", unsafe_allow_html=True)
            
    st.divider()
    
    # ── Candlestick chart ──
    st.markdown("### BTC-USD — 5 Minute Candles (Last 100)")
    plot_df = df_5m.tail(150).copy()
    fig = go.Figure()
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=plot_df["datetime"],
        open=plot_df["open"], high=plot_df["high"],
        low=plot_df["low"],   close=plot_df["close"],
        name="BTC-USD",
        increasing_line_color="#2ecc71",
        decreasing_line_color="#e74c3c",
        increasing_fillcolor="#1a4a2e",
        decreasing_fillcolor="#4a1a1a",
    ))
    
    # Volume bars (secondary y-axis)
    if "volume" in plot_df.columns:
        fig.add_trace(go.Bar(
            x=plot_df["datetime"], y=plot_df["volume"],
            name="Volume", marker_color="#3a3a6a",
            opacity=0.4, yaxis="y2"
        ))
        
    # Order Block rectangles
    for ob in ob_list[-5:]:
        x0 = plot_df.iloc[max(0, ob["index"] - 2)]["datetime"]
        x1 = plot_df.iloc[-1]["datetime"]
        color = "rgba(46,204,113,0.15)" if ob["type"] == "bullish" else "rgba(231,76,60,0.15)"
        line_color = "#2ecc71" if ob["type"] == "bullish" else "#e74c3c"
        fig.add_shape(type="rect", xref="x", yref="y",
                      x0=x0, x1=x1, y0=ob["low"], y1=ob["high"],
                      fillcolor=color, line=dict(color=line_color, width=1, dash="dot"))
        fig.add_annotation(x=x1, y=(ob["high"] + ob["low"]) / 2, xref="x", yref="y",
                           text=f"OB {'▲' if ob['type']=='bullish' else '▼'}",
                           font=dict(color=line_color, size=10), showarrow=False,
                           xanchor="right")
                           
    # FVG rectangles
    for fvg in fvg_list[-5:]:
        if fvg["index"] < len(plot_df):
            x0 = plot_df.iloc[max(0, fvg["index"] - 2)]["datetime"]
            x1 = plot_df.iloc[-1]["datetime"]
            color = "rgba(108,99,255,0.12)" if fvg["type"] == "bullish" else "rgba(255,165,0,0.12)"
            lc    = "#6c63ff" if fvg["type"] == "bullish" else "#ffa500"
            fig.add_shape(type="rect", xref="x", yref="y",
                          x0=x0, x1=x1, y0=fvg["bottom"], y1=fvg["top"],
                          fillcolor=color, line=dict(color=lc, width=1, dash="dot"))
            fig.add_annotation(x=x1, y=(fvg["top"] + fvg["bottom"]) / 2, xref="x", yref="y",
                               text=f"FVG {'▲' if fvg['type']=='bullish' else '▼'}",
                               font=dict(color=lc, size=10), showarrow=False,
                               xanchor="right")
                               
    # 🌉 CHART BRIDGE: Active Trade Lines vs Scanner Signals
    if bot_status.get("is_in_position"):
        # Draw the real, active trade the bot is managing
        ep = bot_status.get("entry_price")
        sl = bot_status.get("stop_loss")
        tp = bot_status.get("take_profit")
        side = bot_status.get("side")
        
        # Color based on trade direction
        entry_color = "#2ecc71" if side in ["BUY", "LONG"] else "#e74c3c"
        
        fig.add_hline(y=ep, line_color=entry_color, line_dash="solid", line_width=2,
                      annotation_text=f"ACTIVE {side} ENTRY", annotation_font_color=entry_color)
        fig.add_hline(y=tp, line_color="#3498db", line_dash="dashdot", line_width=1.5,
                      annotation_text="TAKE PROFIT", annotation_font_color="#3498db")
        fig.add_hline(y=sl, line_color="#ff9900", line_dash="dot", line_width=1.5,
                      annotation_text="STOP LOSS", annotation_font_color="#ff9900")
                      
    elif signal:
        # If not in a trade, show what the scanner is currently seeing
        ep = signal["entry_price"]
        sl = signal["stop_loss"]
        sig_color = "#2ecc71" if signal["type"] == "BUY" else "#e74c3c"
        fig.add_hline(y=ep, line_color=sig_color, line_dash="dash", line_width=1.5,
                      annotation_text=f"Setup: {signal['type']} Entry", annotation_font_color=sig_color)
        fig.add_hline(y=sl, line_color="#ff9900", line_dash="dot", line_width=1,
                      annotation_text="Setup: Stop Loss", annotation_font_color="#ff9900")
                      
    fig.update_layout(
        paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
        font=dict(color="#c0c0e0", family="Inter"),
        xaxis=dict(gridcolor="#1e1e38", showgrid=True, rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor="#1e1e38", showgrid=True, side="right"),
        yaxis2=dict(overlaying="y", side="left", showgrid=False, showticklabels=False,
                    range=[0, plot_df["volume"].max() * 6] if "volume" in plot_df.columns else [0, 1]),
        legend=dict(bgcolor="#161628", bordercolor="#2a2a4a"),
        margin=dict(l=10, r=60, t=30, b=10),
        height=520,
    )
    fig.update_xaxes(showspikes=True, spikecolor="#6c63ff", spikethickness=1)
    fig.update_yaxes(showspikes=True, spikecolor="#6c63ff", spikethickness=1)
    st.plotly_chart(fig, use_container_width=True)
    
    # ── Swing points table ──
    with st.expander("🔎 Detected Swing Points (last 10)"):
        if swings:
            sw_df = pd.DataFrame(swings).tail(10)
            st.dataframe(sw_df, use_container_width=True, hide_index=True)
        else:
            st.info("No swing points detected.")