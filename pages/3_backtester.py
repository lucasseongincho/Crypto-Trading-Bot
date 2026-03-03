"""
Page 3 — Backtester
Run a historical SMC simulation on BTC-USD_candles.csv or an uploaded file.
"""
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from strategy import SMCStrategy
from risk import RiskManager
st.set_page_config(page_title="Backtester", page_icon="🔬", layout="wide")
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
</style>
""", unsafe_allow_html=True)
BASE_DIR          = Path(__file__).parent.parent
DEFAULT_CSV_PATH  = BASE_DIR / "BTC-USD_candles.csv"
st.markdown("# 🔬 Backtester")
st.caption("Simulate the SMC Sniper strategy on historical 5-minute candle data.")
st.divider()
# ── Sidebar config ─────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Backtest Settings")
    initial_balance = st.number_input("Starting Balance ($)", min_value=100.0, max_value=100000.0, value=1000.0, step=100.0)
    rr_ratio        = st.slider("Risk-Reward Ratio", 1.0, 5.0, 1.5, 0.1)
    risk_pct        = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.0, 0.1)
    cooldown_bars   = st.number_input("Post-Trade Cooldown (bars)", min_value=0, max_value=100, value=12)
    st.divider()
    st.markdown("### 📂 Data Source")
    source = st.radio("Source", ["Use existing BTC-USD_candles.csv", "Upload CSV"])
# ── Data loading ───────────────────────────────
df_raw = None
if source == "Use existing BTC-USD_candles.csv":
    if DEFAULT_CSV_PATH.exists():
        df_raw = pd.read_csv(DEFAULT_CSV_PATH)
        st.success(f"✅ Loaded `BTC-USD_candles.csv` — {len(df_raw):,} rows")
    else:
        st.warning("⚠️ `BTC-USD_candles.csv` not found in the project folder.")
        st.info("Use `download_data.py` first, or upload a CSV below.")
else:
    uploaded = st.file_uploader("Upload a candle CSV", type=["csv"])
    if uploaded:
        df_raw = pd.read_csv(uploaded)
        st.success(f"✅ Uploaded: {uploaded.name} — {len(df_raw):,} rows")
# ── Run backtest ───────────────────────────────
if df_raw is not None:
    df = df_raw.copy()
    df.columns = [x.lower() for x in df.columns]
    # Date column
    if "start" in df.columns:
        df["datetime"] = pd.to_datetime(df["start"].astype(int), unit="s")
        df["date_only"] = df["datetime"].dt.date
    elif "date" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"])
        df["date_only"] = df["datetime"].dt.date
    else:
        st.error("❌ CSV must have a `start` (unix) or `date` column.")
        st.stop()
    # Preview
    with st.expander("🔍 Data Preview (first 10 rows)"):
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
    st.divider()
    if st.button("▶️ Run Backtest"):
        strategy    = SMCStrategy()
        risk        = RiskManager(initial_balance=initial_balance)
        risk.rr_ratio = rr_ratio
        trades       = []
        active_trade = None
        cooldown     = 0
        total        = len(df)
        prog         = st.progress(0, text="Running simulation…")
        for i in range(100, total):
            if i % 1000 == 0:
                prog.progress(i / total, text=f"Scanning candle {i:,} / {total:,}…")
            current = df.iloc[i]
            # ── Manage open trade ──────────────────
            if active_trade is not None:
                result = None
                if active_trade["type"] == "BUY":
                    if current["low"]  <= active_trade["stop_loss"]:   result = "LOSS"
                    elif current["high"] >= active_trade["take_profit"]: result = "WIN"
                elif active_trade["type"] == "SELL":
                    if current["high"] >= active_trade["stop_loss"]:   result = "LOSS"
                    elif current["low"]  <= active_trade["take_profit"]: result = "WIN"
                if result:
                    risk_amt = risk.current_balance * (risk_pct / 100)
                    pnl      = risk_amt * risk.rr_ratio if result == "WIN" else -risk_amt
                    risk.current_balance += pnl
                    trades.append({
                        "date":       str(current["date_only"]),
                        "type":       active_trade["type"],
                        "entry":      active_trade["entry_price"],
                        "stop_loss":  active_trade["stop_loss"],
                        "take_profit": active_trade["take_profit"],
                        "result":     result,
                        "pnl":        round(pnl, 2),
                        "balance":    round(risk.current_balance, 2),
                    })
                    active_trade = None
                    cooldown     = int(cooldown_bars)
                continue
            # ── Cooldown ───────────────────────────
            if cooldown > 0:
                cooldown -= 1
                continue
            # ── Look for signal ─────────────────────
            window = df.iloc[i - 99: i + 1]
            signal = strategy.check_setup(window)
            if signal:
                entry = signal["entry_price"]
                sl    = signal["stop_loss"]
                dist  = abs(entry - sl)
                if dist == 0:
                    continue
                tp = entry + dist * rr_ratio if signal["type"] == "BUY" else entry - dist * rr_ratio
                active_trade = {
                    "type":        signal["type"],
                    "entry_price": entry,
                    "stop_loss":   sl,
                    "take_profit": round(tp, 2),
                }
        prog.progress(1.0, text="✅ Simulation complete!")
        # ── Store results in session ────────────────
        st.session_state["backtest_trades"]  = trades
        st.session_state["backtest_balance"] = risk.current_balance
    # ── Show results ───────────────────────────
    if "backtest_trades" in st.session_state and st.session_state["backtest_trades"]:
        trades_df = pd.DataFrame(st.session_state["backtest_trades"])
        final_bal = st.session_state["backtest_balance"]
        total_t   = len(trades_df)
        wins      = (trades_df["result"] == "WIN").sum()
        losses    = total_t - wins
        net_pnl   = trades_df["pnl"].sum()
        win_rate  = wins / total_t * 100 if total_t > 0 else 0
        st.divider()
        st.markdown("### 📊 Backtest Results")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Trades",    total_t)
        c2.metric("Win Rate",        f"{win_rate:.1f}%")
        c3.metric("Net P/L (USD)",   f"${net_pnl:+.2f}")
        c4.metric("Final Balance",   f"${final_bal:,.2f}")
        c5.metric("Return",          f"{((final_bal - initial_balance) / initial_balance * 100):+.1f}%")
        # Equity curve
        eq_df = trades_df.copy()
        eq_df["trade_num"] = range(1, len(eq_df) + 1)
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(
            x=eq_df["trade_num"], y=eq_df["balance"],
            mode="lines", name="Equity",
            line=dict(color="#6c63ff", width=2),
            fill="tozeroy", fillcolor="rgba(108,99,255,0.08)"
        ))
        fig_eq.add_hline(y=initial_balance, line_dash="dash",
                         line_color="#8888aa", annotation_text="Starting Balance")
        fig_eq.update_layout(
            title="Equity Curve",
            paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
            font=dict(color="#c0c0e0", family="Inter"),
            xaxis=dict(title="Trade #", gridcolor="#1e1e38"),
            yaxis=dict(title="Balance (USD)", gridcolor="#1e1e38"),
            margin=dict(l=10, r=10, t=40, b=30),
            height=380,
        )
        st.plotly_chart(fig_eq, use_container_width=True)
        # Trade log table
        st.markdown("### 📋 Trade Log")
        def color_result(val):
            return "color: #2ecc71; font-weight:600" if val == "WIN" else "color: #e74c3c; font-weight:600"
        styled = trades_df.style.applymap(color_result, subset=["result"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
        # Download
        csv_bytes = trades_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Trade Log CSV", data=csv_bytes,
                           file_name="backtest_results.csv", mime="text/csv")
    elif "backtest_trades" in st.session_state:
        st.info("No trades were generated. Try adjusting the strategy parameters or a longer date range.")