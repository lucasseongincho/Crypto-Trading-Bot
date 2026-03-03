"""
Crypto Bot Dashboard — Home Page
Run with: streamlit run dashboard.py
"""
import streamlit as st
from pathlib import Path
# ──────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Crypto Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ──────────────────────────────────────────────
# Global CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
/* ── Dark sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
}
[data-testid="stSidebar"] * {
    color: #e0e0f0 !important;
}
/* ── Main background ── */
[data-testid="stAppViewContainer"] {
    background: #0d0d1a;
}
/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #161628;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricLabel"] { color: #8888aa !important; font-size: 0.78rem; }
[data-testid="stMetricValue"] { color: #e0e0ff !important; font-size: 1.6rem; font-weight: 700; }
[data-testid="stMetricDelta"] { font-size: 0.8rem; }
/* ── Headings ── */
h1, h2, h3 { color: #c0c0ff !important; }
/* ── Divider ── */
hr { border-color: #2a2a4a; }
/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #6c63ff, #4a90e2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.45rem 1.2rem;
    font-weight: 600;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; }
/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border: 1px solid #2a2a4a;
    border-radius: 10px;
}
/* ── Nav cards on home ── */
.nav-card {
    background: linear-gradient(135deg, #161628, #1e1e38);
    border: 1px solid #2e2e50;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s, transform 0.15s;
}
.nav-card:hover { border-color: #6c63ff; transform: translateY(-2px); }
.nav-card h3 { color: #a0a0ff !important; margin-top: 0; }
.nav-card p  { color: #8080aa; margin: 0; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)
# ──────────────────────────────────────────────
# Sidebar branding
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Crypto Bot")
    st.markdown("**SMC Sniper v1** — BTC-USD")
    st.divider()
    st.caption("Use the pages above to navigate.")
    st.divider()
    st.caption("⚠️ Dashboard is **read-only**. The live bot runs separately in its own terminal.")
# ──────────────────────────────────────────────
# Home content
# ──────────────────────────────────────────────
st.markdown("# 📈 SMC Crypto Bot Dashboard")
st.markdown("Welcome! Use the **sidebar** to navigate between pages.")
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
<div class="nav-card">
  <h3>📡 Live Monitor</h3>
  <p>Real-time balance, BTC-USD candlestick chart with Order Block & FVG overlays, current signal, and kill-switch status.</p>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class="nav-card">
  <h3>🔬 Backtester</h3>
  <p>Run a historical SMC simulation on any candle CSV. See an equity curve and full trade log.</p>
</div>
""", unsafe_allow_html=True)
with col2:
    st.markdown("""
<div class="nav-card">
  <h3>📓 Trade Journal</h3>
  <p>Browse, filter, and export every trade logged to <code>trade_journal.csv</code>.</p>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class="nav-card">
  <h3>📊 Performance</h3>
  <p>Win rate, profit factor, max drawdown, equity curve, and monthly P&L breakdown.</p>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<div class="nav-card" style="max-width:100%;">
  <h3>⚙️ Settings</h3>
  <p>View masked API credentials, current risk parameters, and send a test Telegram notification.</p>
</div>
""", unsafe_allow_html=True)
# ──────────────────────────────────────────────
# Quick status check
# ──────────────────────────────────────────────
st.divider()
st.markdown("### 🔍 Quick Status")
base = Path(__file__).parent
journal_path = base / "trade_journal.csv"
candles_path = base / "BTC-USD_candles.csv"
key_path     = base / "cdp_api_key.json"
env_path     = base / ".env"
c1, c2, c3, c4 = st.columns(4)
c1.metric("API Key File",    "✅ Found" if key_path.exists()     else "❌ Missing")
c2.metric(".env File",       "✅ Found" if env_path.exists()     else "❌ Missing")
c3.metric("Trade Journal",   "✅ Found" if journal_path.exists() else "⚠️ Empty")
c4.metric("Candle CSV",      "✅ Found" if candles_path.exists() else "⚠️ None")