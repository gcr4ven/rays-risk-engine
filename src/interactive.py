import streamlit as st
import pandas as pd

st.set_page_config(page_title="RAYS Attribution Dashboard", layout="wide")

# ----------------------------
# LOAD DATA
# ----------------------------
@st.cache_data
def load_data():
    pnl = pd.read_excel("pnl_decomposition.xlsx")
    monthly = pd.read_excel("monthly_strategy_attribution.xlsx")
    quarterly = pd.read_excel("quarterly_strategy_attribution.xlsx")
    top = pd.read_excel("top_5_contributors.xlsx")

    return pnl, monthly, quarterly, top


pnl_df, monthly_df, quarterly_df, top_df = load_data()

# ----------------------------
# NORMALIZE TIME COLUMNS
# ----------------------------
pnl_df["month"] = pd.to_datetime(pnl_df["month"], errors="coerce")
pnl_df["quarter"] = pnl_df["month"].dt.to_period("Q")
pnl_df["month_period"] = pnl_df["month"].dt.to_period("M")

monthly_df["month"] = pd.to_datetime(monthly_df["month"], errors="coerce")
monthly_df["month_period"] = monthly_df["month"].dt.to_period("M")

quarterly_df["quarter"] = quarterly_df["quarter"].astype(str)

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("Controls")

view_type = st.sidebar.selectbox("View", ["Monthly", "Quarterly"])

st.title("📊 RAYS Capital Attribution Dashboard")
st.caption("Internal Prototype – Strategy & PnL Attribution Engine")

# ----------------------------
# MONTHLY VIEW
# ----------------------------
if view_type == "Monthly":

    periods = sorted(pnl_df["month_period"].dropna().unique())
    selected_period = st.sidebar.selectbox("Month", periods)

    pnl_filtered = pnl_df[pnl_df["month_period"] == selected_period]
    df = monthly_df[monthly_df["month_period"] == selected_period]

# ----------------------------
# QUARTERLY VIEW (FIXED)
# ----------------------------
else:

    periods = sorted(pnl_df["quarter"].dropna().unique())
    selected_period = st.sidebar.selectbox("Quarter", periods)

    pnl_filtered = pnl_df[pnl_df["quarter"] == selected_period]

    # 🔥 FIX: normalize quarterly_df properly
    quarterly_df["quarter"] = pd.to_datetime(
        quarterly_df["quarter"],
        errors="coerce"
    ).dt.to_period("Q")

    df = quarterly_df[quarterly_df["quarter"] == selected_period]
# ----------------------------
# SAFETY CHECK (IMPORTANT)
# ----------------------------
if df.empty:
    st.warning("No data available for this period. Check data alignment or mapping.")
    st.stop()

# ----------------------------
# KPI CALCULATION (SAFE)
# ----------------------------
total = df["total_pnl"].sum()
long = df[df["strategy"] == "LONG"]["total_pnl"].sum()
short = df[df["strategy"] == "SHORT"]["total_pnl"].sum()
box = df[df["strategy"] == "BOX"]["total_pnl"].sum()

# ----------------------------
# KPI DISPLAY
# ----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total PnL", f"${total:,.0f}")
col2.metric("Long PnL", f"${long:,.0f}")
col3.metric("Short PnL", f"${short:,.0f}")
col4.metric("Box PnL", f"${box:,.0f}")

st.divider()

# ----------------------------
# STRATEGY ATTRIBUTION TABLE
# ----------------------------
st.subheader("Strategy Attribution")

st.dataframe(
    df[["strategy", "total_pnl", "attribution_pct"]]
    .sort_values("total_pnl", ascending=False),
    use_container_width=True
)

st.divider()

# ----------------------------
# PNL DECOMPOSITION
# ----------------------------
st.subheader("PnL Decomposition")

st.dataframe(pnl_filtered, use_container_width=True)

st.divider()

# ----------------------------
# TOP CONTRIBUTORS
# ----------------------------
st.subheader("Top Contributors")

st.dataframe(df, width="stretch")

st.divider()

# ----------------------------
# KEY INSIGHTS (SAFE)
# ----------------------------
st.subheader("Key Insight")

if df["total_pnl"].notna().any():

    best_strategy = df.loc[df["total_pnl"].idxmax(), "strategy"]
    worst_strategy = df.loc[df["total_pnl"].idxmin(), "strategy"]

    st.write(f"""
    - Best performing strategy: **{best_strategy}**
    - Weakest performing strategy: **{worst_strategy}**
    """)

else:
    st.write("No valid PnL data for insight generation.")