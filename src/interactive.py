import streamlit as st
import pandas as pd
from pathlib import Path

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="RAYS Risk Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# DATA LOADING
# =========================

@st.cache_data
def load_data():
    pnl = pd.read_excel(BASE_DIR / "src" / "pnl_decomposition.xlsx")
    monthly = pd.read_excel(BASE_DIR / "src" / "monthly_strategy_attribution.xlsx")
    quarterly = pd.read_excel(BASE_DIR / "src" / "quarterly_strategy_attribution.xlsx")
    top = pd.read_excel(BASE_DIR / "src" / "top_5_contributors.xlsx")
    bottom = pd.read_excel(BASE_DIR / "src" / "bottom_5_contributors.xlsx")

    # normalize dates
    pnl["month"] = pd.to_datetime(pnl["month"])
    monthly["month"] = pd.to_datetime(monthly["month"])
    quarterly["quarter"] = pd.to_datetime(quarterly["quarter"])

    return pnl, monthly, quarterly, top, bottom


pnl_df, monthly_df, quarterly_df, top_df, bottom_df = load_data()

# =========================
# SIDEBAR FILTERS
# =========================

st.sidebar.title("Filters")

view_type = st.sidebar.selectbox("View", ["Monthly", "Quarterly"])

if view_type == "Monthly":
    period = st.sidebar.selectbox(
        "Select Month",
        sorted(monthly_df["month"].dt.to_period("M").astype(str).unique())
    )
else:
    period = st.sidebar.selectbox(
        "Select Quarter",
        sorted(quarterly_df["quarter"].dt.to_period("Q").astype(str).unique())
    )

# =========================
# FILTER DATA
# =========================

if view_type == "Monthly":
    selected_period = pd.Period(period, freq="M")

    pnl_filtered = pnl_df[
        pnl_df["month"].dt.to_period("M") == selected_period
    ]

    strategy_filtered = monthly_df[
        monthly_df["month"].dt.to_period("M") == selected_period
    ]

else:
    selected_period = pd.Period(period, freq="Q")

    pnl_filtered = pnl_df[
        pnl_df["month"].dt.to_period("Q") == selected_period
    ]

    strategy_filtered = quarterly_df[
        quarterly_df["quarter"].dt.to_period("Q") == selected_period
    ]

# =========================
# SAFETY CHECKS
# =========================

if pnl_filtered.empty:
    st.warning("No PnL data for selected period")
    st.stop()

if strategy_filtered.empty:
    st.warning("No strategy data for selected period")
    st.stop()

# =========================
# HEADER KPIs
# =========================

st.title("RAYS Capital Risk Dashboard")

total_pnl = pnl_filtered["total_pnl"].sum()

col1, col2, col3 = st.columns(3)

col1.metric("Total PnL", f"${total_pnl:,.0f}")
col2.metric("Rows", len(pnl_filtered))
col3.metric("Period", str(selected_period))

# =========================
# STRATEGY ATTRIBUTION
# =========================

st.subheader("Strategy Attribution")

strategy_view = strategy_filtered.copy()

strategy_view["total_pnl"] = strategy_view["total_pnl"].astype(float)
strategy_view["attribution_pct"] = strategy_view["attribution_pct"].astype(float)

st.dataframe(
    strategy_view.style.format({
        "total_pnl": "${:,.0f}",
        "attribution_pct": "{:.2%}"
    }),
    use_container_width=True
)

# =========================
# TOP / BOTTOM CONTRIBUTORS
# =========================

st.subheader("Top 5 Contributors")

st.dataframe(
    top_df.head(5).style.format({
        "total_pnl": "${:,.0f}"
    }),
    use_container_width=True
)

st.subheader("Bottom 5 Contributors")

st.dataframe(
    bottom_df.head(5).style.format({
        "total_pnl": "${:,.0f}"
    }),
    use_container_width=True
)

# =========================
# KEY INSIGHTS (SAFE)
# =========================

st.subheader("Key Insights")

if not strategy_filtered.empty:
    best_strategy = strategy_filtered.loc[
        strategy_filtered["total_pnl"].idxmax(),
        "strategy"
    ]

    worst_strategy = strategy_filtered.loc[
        strategy_filtered["total_pnl"].idxmin(),
        "strategy"
    ]

    st.write(f"📈 Best Strategy: **{best_strategy}**")
    st.write(f"📉 Worst Strategy: **{worst_strategy}**")

else:
    st.write("No strategy insights available")

# =========================
# RAW PNL VIEW (DEBUG)
# =========================

with st.expander("Raw PnL Data"):
    st.dataframe(pnl_filtered, use_container_width=True)
