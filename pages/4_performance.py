"""
Page 4 — Performance Summary
Stats: Win Rate, Profit Factor, Max Drawdown, Equity Curve, Monthly P&L.
Includes Estimated Short-Term Capital Gains Tax.
"""
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="Performance", page_icon="📊", layout="wide")

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
.tax-disclaimer { font-size: 0.8rem; color: #8888aa; font-style: italic; margin-top: -10px; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

JOURNAL_PATH = Path(__file__).parent.parent / "trade_journal.csv"

# 🏦 TAX CONFIGURATION (Change this to match your actual income bracket!)
ESTIMATED_TAX_RATE = 0.24  # 24% Short-Term Capital Gains

st.markdown("# 📊 Performance Summary")
st.caption("Aggregated stats from your `trade_journal.csv`.")
st.divider()

# ── Load & validate ──────────────────────────
if not JOURNAL_PATH.exists():
    st.info("No `trade_journal.csv` found yet. Complete some trades first.")
    st.stop()

df = pd.read_csv(JOURNAL_PATH)

if df.empty or "PnL" not in df.columns:
    st.info("Journal exists but contains no trade data yet.")
    st.stop()

# ── Core stats ───────────────────────────────
pnl_col        = "PnL"
total          = len(df)
wins           = df[df[pnl_col] > 0]
losses         = df[df[pnl_col] < 0]

win_rate       = len(wins) / total * 100 if total > 0 else 0
total_pnl      = df[pnl_col].sum()

gross_profit   = wins[pnl_col].sum()
gross_loss     = abs(losses[pnl_col].sum())
profit_factor  = gross_profit / gross_loss if gross_loss != 0 else float("inf")

# 🏛️ Tax Math
estimated_tax  = total_pnl * ESTIMATED_TAX_RATE if total_pnl > 0 else 0
net_after_tax  = total_pnl - estimated_tax

# Equity curve & drawdown based on the REAL balance column
df["Cumulative_PnL"] = df[pnl_col].cumsum()
df["Equity"]        = df["Balance"]
df["Peak"]          = df["Equity"].cummax()
df["Drawdown_pct"]  = (df["Equity"] - df["Peak"]) / df["Peak"] * 100
max_drawdown        = df["Drawdown_pct"].min()
final_equity        = df["Equity"].iloc[-1]

avg_win  = wins[pnl_col].mean()   if not wins.empty   else 0
avg_loss = losses[pnl_col].mean() if not losses.empty else 0

# ── KPI cards (Row 1: Trading Stats) ─────────────────
st.markdown("### 🎯 Trading Edge")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Trades",   total)
k2.metric("Win Rate",       f"{win_rate:.1f}%")
k3.metric("Profit Factor",  f"{profit_factor:.2f}" if profit_factor != float("inf") else "∞")
k4.metric("Max Drawdown",   f"{max_drawdown:.2f}%")

# ── KPI cards (Row 2: Money & Taxes) ─────────────────
st.markdown("### 💰 Financials & Taxes")
st.markdown(f"<div class='tax-disclaimer'>*Estimated Tax assumes a {ESTIMATED_TAX_RATE*100:.0f}% short-term capital gains bracket. Consult a CPA for actual filing.</div>", unsafe_allow_html=True)
k5, k6, k7, k8 = st.columns(4)
k5.metric("Gross Profit (Pre-Tax)", f"${total_pnl:+.2f}")
k6.metric("🏛️ Est. Tax Owed", f"-${estimated_tax:.2f}")
k7.metric("💵 Net (Take-Home)", f"${net_after_tax:+.2f}")
k8.metric("Final Equity",   f"${final_equity:,.2f}")

st.divider()

# ── Equity curve with drawdown shading ────────
st.markdown("### 📈 Equity Curve")

fig_eq = go.Figure()
fig_eq.add_trace(go.Scatter(
    x=df.index, y=df["Equity"],
    mode="lines", name="Equity",
    line=dict(color="#6c63ff", width=2.5),
    fill="tozeroy", fillcolor="rgba(108,99,255,0.07)",
))

# Shade drawdown periods
in_dd    = False
dd_start = None
for idx, row in df.iterrows():
    if row["Drawdown_pct"] < 0 and not in_dd:
        in_dd    = True
        dd_start = idx
    elif row["Drawdown_pct"] >= 0 and in_dd:
        fig_eq.add_vrect(
            x0=dd_start, x1=idx,
            fillcolor="rgba(231,76,60,0.10)", line_width=0,
        )
        in_dd = False

if in_dd:
    fig_eq.add_vrect(
        x0=dd_start, x1=df.index[-1],
        fillcolor="rgba(231,76,60,0.10)", line_width=0,
    )

start_eq = df["Balance"].iloc[0] - df["PnL"].iloc[0]
fig_eq.add_hline(y=start_eq, line_dash="dash", line_color="#555580",
                 annotation_text=f"Starting Equity (${start_eq:,.0f})")

fig_eq.update_layout(
    paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
    font=dict(color="#c0c0e0", family="Inter"),
    xaxis=dict(title="Trade #", gridcolor="#1e1e38"),
    yaxis=dict(title="Equity (USD)", gridcolor="#1e1e38"),
    margin=dict(l=10, r=10, t=30, b=30), height=360,
    legend=dict(bgcolor="#161628", bordercolor="#2a2a4a"),
)
st.plotly_chart(fig_eq, use_container_width=True)

# ── Monthly P&L bar chart ─────────────────────
if "Date" in df.columns:
    st.markdown("### 📅 Monthly P&L")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    monthly = df.groupby(df["Date"].dt.to_period("M"))[pnl_col].sum().reset_index()
    monthly["Date"] = monthly["Date"].astype(str)
    
    m_colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in monthly[pnl_col]]
    
    fig_m = go.Figure(go.Bar(
        x=monthly["Date"], y=monthly[pnl_col],
        marker_color=m_colors, name="Monthly P/L",
    ))
    fig_m.update_layout(
        paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
        font=dict(color="#c0c0e0", family="Inter"),
        xaxis=dict(title="Month", gridcolor="#1e1e38"),
        yaxis=dict(title="P/L (USD)", gridcolor="#1e1e38"),
        margin=dict(l=10, r=10, t=30, b=30), height=300,
    )
    st.plotly_chart(fig_m, use_container_width=True)

# ── Pie chart ─────────────────────────────────
col_l, col_r = st.columns([1, 2])

with col_l:
    st.markdown("### 🥧 Win / Loss Split")
    fig_pie = go.Figure(go.Pie(
        labels=["Wins", "Losses"],
        values=[len(wins), len(losses)],
        marker=dict(colors=["#2ecc71", "#e74c3c"]),
        hole=0.45,
        textfont=dict(color="#e0e0ff"),
    ))
    fig_pie.update_layout(
        paper_bgcolor="#0d0d1a",
        font=dict(color="#c0c0e0", family="Inter"),
        margin=dict(l=10, r=10, t=10, b=10), height=280,
        showlegend=True,
        legend=dict(bgcolor="#161628", bordercolor="#2a2a4a"),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_r:
    st.markdown("### 📉 Drawdown Over Time")
    fig_dd = go.Figure(go.Scatter(
        x=df.index, y=df["Drawdown_pct"],
        mode="lines", fill="tozeroy",
        line=dict(color="#e74c3c", width=1.5),
        fillcolor="rgba(231,76,60,0.15)",
        name="Drawdown %",
    ))
    fig_dd.update_layout(
        paper_bgcolor="#0d0d1a", plot_bgcolor="#0d0d1a",
        font=dict(color="#c0c0e0", family="Inter"),
        xaxis=dict(title="Trade #", gridcolor="#1e1e38"),
        yaxis=dict(title="Drawdown (%)", gridcolor="#1e1e38"),
        margin=dict(l=10, r=10, t=30, b=30), height=280,
    )
    st.plotly_chart(fig_dd, use_container_width=True)