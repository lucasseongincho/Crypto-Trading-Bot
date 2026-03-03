"""
Page 5 — Settings & Notifications
Displays masked credentials, risk parameters, and lets you send a test Telegram message.
"""
import sys
import json
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
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
.info-box {
    background: #161628;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.info-box h4 { color: #a0a0d0 !important; margin-top: 0; margin-bottom: 12px; }
.info-row { display:flex; justify-content:space-between; margin-bottom:8px; }
.info-label { color: #6666aa; font-size:0.85rem; }
.info-value { color: #c0c0e0; font-size:0.85rem; font-family:monospace; }
.info-value.masked { color:#555577; letter-spacing:2px; }
</style>
""", unsafe_allow_html=True)
BASE_DIR  = Path(__file__).parent.parent
KEY_PATH  = BASE_DIR / "cdp_api_key.json"
ENV_PATH  = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)
st.markdown("# ⚙️ Settings & Notifications")
st.caption("Read-only view of your credentials and risk parameters. No secrets are ever written or displayed in full.")
st.divider()
# ──────────────────────────────────────────────
# Coinbase API Key info
# ──────────────────────────────────────────────
st.markdown("### 🔑 Coinbase API Credentials")
col_a, col_b = st.columns(2)
with col_a:
    if KEY_PATH.exists():
        try:
            with open(KEY_PATH) as f:
                key_data = json.load(f)
            api_name = key_data.get("name", "N/A")
            has_secret = bool(key_data.get("privateKey", ""))
            st.markdown(f"""
<div class='info-box'>
  <h4>cdp_api_key.json</h4>
  <div class='info-row'>
    <span class='info-label'>Key Name</span>
    <span class='info-value'>{api_name}</span>
  </div>
  <div class='info-row'>
    <span class='info-label'>Private Key</span>
    <span class='info-value masked'>{'●●●●●●●●●●●●' if has_secret else '❌ Missing'}</span>
  </div>
  <div class='info-row'>
    <span class='info-label'>Status</span>
    <span class='info-value'>{'✅ Loaded' if api_name else '⚠️ Incomplete'}</span>
  </div>
</div>
""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not parse `cdp_api_key.json`: {e}")
    else:
        st.warning("⚠️ `cdp_api_key.json` not found.")
# ──────────────────────────────────────────────
# Telegram credentials
# ──────────────────────────────────────────────
with col_b:
    tg_token  = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat   = os.getenv("TELEGRAM_CHAT_ID",   "")
    token_display = f"…{tg_token[-6:]}" if len(tg_token) > 6 else ("❌ Missing" if not tg_token else tg_token)
    chat_display  = tg_chat if tg_chat else "❌ Missing"
    st.markdown(f"""
<div class='info-box'>
  <h4>Telegram (.env)</h4>
  <div class='info-row'>
    <span class='info-label'>Bot Token</span>
    <span class='info-value masked'>{token_display}</span>
  </div>
  <div class='info-row'>
    <span class='info-label'>Chat ID</span>
    <span class='info-value'>{chat_display}</span>
  </div>
  <div class='info-row'>
    <span class='info-label'>Status</span>
    <span class='info-value'>{'✅ Configured' if tg_token and tg_chat else '⚠️ Incomplete'}</span>
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()
# ──────────────────────────────────────────────
# Risk parameters (read from RiskManager defaults)
# ──────────────────────────────────────────────
st.markdown("### 🛡️ Risk Parameters")
try:
    from risk import RiskManager
    rm = RiskManager()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk per Trade",        "1.0% of balance")
    c2.metric("Risk-Reward Ratio",     f"{rm.rr_ratio} R")
    c3.metric("Min SL Distance",       f"${rm.min_sl_distance}")
    c4.metric("Max Drawdown (live)",   "20%  (kill switch)")
except Exception as e:
    st.warning(f"Could not load RiskManager: {e}")
st.divider()
# ──────────────────────────────────────────────
# Strategy signal thresholds
# ──────────────────────────────────────────────
st.markdown("### 🧠 Strategy Parameters")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Min Signals Required", "3 of 4")
c2.metric("Lookback (LTF)",       "100 candles")
c3.metric("LTF Timeframe",        "5-Minute")
c4.metric("HTF Timeframe",        "6-Hour")
st.divider()
# ──────────────────────────────────────────────
# Send test Telegram notification
# ──────────────────────────────────────────────
st.markdown("### 📨 Send Test Telegram Notification")
if not tg_token or not tg_chat:
    st.warning("⚠️ Cannot send — Telegram credentials are missing or incomplete in `.env`.")
else:
    test_msg = st.text_input(
        "Message",
        value="✅ [Dashboard] Test notification from SMC Crypto Bot Dashboard.",
        max_chars=200,
    )
    if st.button("📤 Send Test Message"):
        try:
            from notifications import send_telegram_notification
            send_telegram_notification(test_msg)
            st.success("✅ Message sent! Check your Telegram bot.")
        except Exception as e:
            st.error(f"❌ Failed to send: {e}")
st.divider()
# ──────────────────────────────────────────────
# File health check
# ──────────────────────────────────────────────
st.markdown("### 📂 File Health Check")
files = {
    "cdp_api_key.json":      BASE_DIR / "cdp_api_key.json",
    ".env":                  BASE_DIR / ".env",
    "trade_journal.csv":     BASE_DIR / "trade_journal.csv",
    "BTC-USD_candles.csv":   BASE_DIR / "BTC-USD_candles.csv",
    "auth.py":               BASE_DIR / "auth.py",
    "strategy.py":           BASE_DIR / "strategy.py",
    "risk.py":               BASE_DIR / "risk.py",
    "notifications.py":      BASE_DIR / "notifications.py",
}
rows = []
for name, path in files.items():
    exists  = path.exists()
    size    = f"{path.stat().st_size:,} bytes" if exists else "—"
    status  = "✅ OK" if exists else "❌ Missing"
    rows.append({"File": name, "Status": status, "Size": size})
import pandas as pd
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
