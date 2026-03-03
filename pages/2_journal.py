"""
Page 2 — Trade Journal
Displays and filters the trade_journal.csv with stats and CSV export.
"""
import sys
import streamlit as st
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Trade Journal", page_icon="📓", layout="wide")
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
JOURNAL_PATH = Path(__file__).parent.parent / "trade_journal.csv"
st.markdown("# 📓 Trade Journal")
st.caption("Live view of `trade_journal.csv` — all executed and logged trades.")
st.divider()
# ── Load data ─────────────────────────────────
if not JOURNAL_PATH.exists():
    st.info("No `trade_journal.csv` found yet. Start the live bot or complete a backtest to populate it.")
    st.stop()
df = pd.read_csv(JOURNAL_PATH)
if df.empty:
    st.info("The trade journal exists but contains no trades yet.")
    st.stop()
# ── Parse dates ───────────────────────────────
if "Entry_Date" in df.columns:
    df["Entry_Date"] = pd.to_datetime(df["Entry_Date"], errors="coerce")
if "Exit_Date" in df.columns:
    df["Exit_Date"] = pd.to_datetime(df["Exit_Date"], errors="coerce")
# ── Sidebar filters ────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")
    if "Entry_Date" in df.columns and df["Entry_Date"].notna().any():
        min_d = df["Entry_Date"].min().date()
        max_d = df["Entry_Date"].max().date()
        date_range = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    else:
        date_range = None
    side_filter = st.multiselect("Side", options=["BUY", "SELL"], default=["BUY", "SELL"])
    result_filter = st.multiselect(
        "Result",
        options=df["P/L_USD"].apply(lambda x: "WIN" if x > 0 else "LOSS").unique().tolist(),
        default=["WIN", "LOSS"],
    ) if "P/L_USD" in df.columns else []
# ── Apply filters ──────────────────────────────
filtered = df.copy()
if date_range and len(date_range) == 2 and "Entry_Date" in filtered.columns:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[filtered["Entry_Date"].between(start, end)]
if side_filter and "Side" in filtered.columns:
    filtered = filtered[filtered["Side"].isin(side_filter)]
if result_filter and "P/L_USD" in filtered.columns:
    keep_win  = "WIN"  in result_filter
    keep_loss = "LOSS" in result_filter
    filtered = filtered[((filtered["P/L_USD"] > 0) & keep_win) | ((filtered["P/L_USD"] <= 0) & keep_loss)]
# ── KPI Row ────────────────────────────────────
total   = len(filtered)
wins    = (filtered["P/L_USD"] > 0).sum() if "P/L_USD" in filtered.columns else 0
losses  = total - wins
net_pnl = filtered["P/L_USD"].sum() if "P/L_USD" in filtered.columns else 0
win_rt  = (wins / total * 100) if total > 0 else 0
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Trades",  total)
c2.metric("Wins",          wins)
c3.metric("Losses",        losses)
c4.metric("Win Rate",      f"{win_rt:.1f}%")
c5.metric("Net P/L (USD)", f"${net_pnl:+.2f}", delta=f"{net_pnl:+.2f}")
st.divider()
# ── Styled table ───────────────────────────────
st.markdown(f"### Trades ({total} rows shown)")
if "P/L_USD" in filtered.columns:
    def color_pnl(val):
        color = "#2ecc71" if val > 0 else "#e74c3c"
        return f"color: {color}; font-weight: 600"
    styled = filtered.style.applymap(color_pnl, subset=["P/L_USD"])
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.dataframe(filtered, use_container_width=True, hide_index=True)
# ── CSV download ───────────────────────────────
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_bytes,
    file_name="trade_journal_export.csv",
    mime="text/csv",
)
# ── P/L bar chart ──────────────────────────────
if "P/L_USD" in filtered.columns and not filtered.empty:
    import plotly.graph_objects as go
    st.divider()
    st.markdown("### 📊 P/L per Trade")
    colors = ["#2ecc71" if v > 0 else "#e74c3c" for v in filtered["P/L_USD"]]
    fig = go.Figure(go.Bar(
        x=list(range(len(filtered))),
        y=filtered["P/L_USD"],
        marker_color=colors,
        name="P/L",
    ))
    fig.update_layout(
        paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
        font=dict(color="#c0c0e0", family="Inter"),
        xaxis=dict(title="Trade #", gridcolor="#1e1e38"),
        yaxis=dict(title="P/L (USD)", gridcolor="#1e1e38"),
        margin=dict(l=10, r=10, t=30, b=30),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)
