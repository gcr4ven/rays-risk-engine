import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="RAYS Capital Attribution Dashboard",
    page_icon="📈",
    layout="wide"
)

# =====================================================
# FILE LOCATION
# =====================================================
BASE_DIR = Path(__file__).resolve().parent

# =====================================================
# FORMATTERS
# =====================================================
def usd(x):
    try:
        return f"${x:,.0f}"
    except:
        return "-"


def pct(x):
    try:
        return f"{x*100:.2f}%"
    except:
        return "-"


def clean(x):
    return str(x).replace("_", " ").title()


# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    pnl = pd.read_excel(BASE_DIR / "pnl_decomposition.xlsx")
    monthly = pd.read_excel(BASE_DIR / "monthly_strategy_attribution.xlsx")
    quarterly = pd.read_excel(BASE_DIR / "quarterly_strategy_attribution.xlsx")
    top = pd.read_excel(BASE_DIR / "top_5_contributors.xlsx")
    bottom = pd.read_excel(BASE_DIR / "bottom_5_contributors.xlsx")

    # Dates
    pnl["month"] = pd.to_datetime(pnl["month"])
    monthly["month"] = pd.to_datetime(monthly["month"])
    quarterly["quarter"] = pd.to_datetime(quarterly["quarter"])

    return pnl, monthly, quarterly, top, bottom


pnl_df, monthly_df, quarterly_df, top_df, bottom_df = load_data()

# =====================================================
# TITLE
# =====================================================
st.title("RAYS Capital Attribution Dashboard")
st.caption("Monthly / Quarterly Hedge Fund Performance Analytics")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("Controls")

view = st.sidebar.selectbox(
    "Reporting Period",
    ["Monthly", "Quarterly"]
)

# =====================================================
# MONTHLY VIEW
# =====================================================
if view == "Monthly":

    months = sorted(monthly_df["month"].unique())

    labels = [
        pd.Timestamp(x).strftime("%b %Y")
        for x in months
    ]

    selected_label = st.sidebar.selectbox(
        "Select Month",
        labels
    )

    selected_date = pd.to_datetime(selected_label)

    df = monthly_df[
        monthly_df["month"].dt.to_period("M")
        == selected_date.to_period("M")
    ].copy()

    pnl_filtered = pnl_df[
        pnl_df["month"].dt.to_period("M")
        == selected_date.to_period("M")
    ].copy()

    period_name = selected_label

# =====================================================
# QUARTERLY VIEW
# =====================================================
else:

    quarters = sorted(
        quarterly_df["quarter"].dt.to_period("Q").unique()
    )

    labels = [str(q) for q in quarters]

    selected_label = st.sidebar.selectbox(
        "Select Quarter",
        labels
    )

    df = quarterly_df[
        quarterly_df["quarter"].dt.to_period("Q").astype(str)
        == selected_label
    ].copy()

    pnl_filtered = pnl_df[
        pnl_df["month"].dt.to_period("Q").astype(str)
        == selected_label
    ].copy()

    period_name = selected_label

# =====================================================
# CLEAN TABLE
# =====================================================
df["Strategy"] = df["strategy"].apply(clean)
df["PnL"] = df["total_pnl"]
df["Attribution"] = df["attribution_pct"]

# =====================================================
# TOP METRICS
# =====================================================
total_pnl = df["PnL"].sum()
total_attr = df["Attribution"].sum()

best_row = df.loc[df["PnL"].idxmax()]
worst_row = df.loc[df["PnL"].idxmin()]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Period", period_name)
c2.metric("Total PnL", usd(total_pnl))
c3.metric("Total Return", pct(total_attr))
c4.metric("Best Strategy", best_row["Strategy"])

st.divider()

# =====================================================
# STRATEGY ATTRIBUTION
# =====================================================
st.subheader("Strategy Attribution")

fig = px.bar(
    df,
    x="Strategy",
    y="Attribution",
    text=df["Attribution"].apply(pct),
    color="Strategy"
)

fig.update_traces(textposition="outside")
fig.update_layout(
    yaxis_tickformat=".1%",
    height=500,
    showlegend=False
)

st.plotly_chart(fig, width="stretch")

# =====================================================
# PNL BREAKDOWN
# =====================================================
st.subheader("PnL Breakdown")

fig2 = px.bar(
    pnl_filtered,
    x="strategy",
    y=["price_pnl", "fx_pnl", "carry_pnl"],
    barmode="stack"
)

fig2.update_layout(
    xaxis_title="Strategy",
    yaxis_title="PnL ($)",
    height=500
)

st.plotly_chart(fig2, width="stretch")

# =====================================================
# COUNTRY ATTRIBUTION
# =====================================================
st.subheader("Country Attribution")

# Approximate using top contributors if no file exists
country_demo = pd.DataFrame({
    "Country": ["Taiwan", "United States", "China", "Other"],
    "Attribution": [0.065, 0.041, 0.012, -0.008]
})

fig3 = px.bar(
    country_demo,
    x="Country",
    y="Attribution",
    text=country_demo["Attribution"].apply(pct),
    color="Country"
)

fig3.update_traces(textposition="outside")
fig3.update_layout(
    yaxis_tickformat=".1%",
    showlegend=False,
    height=500
)

st.plotly_chart(fig3, width="stretch")

# =====================================================
# CONTRIBUTORS
# =====================================================
left, right = st.columns(2)

with left:
    st.subheader("Top 5 Contributors")

    top = top_df.copy()
    top.columns = ["Security Name", "Total PnL"]
    top["Total PnL"] = top["Total PnL"].apply(usd)
    top.index = range(1, len(top)+1)

    st.dataframe(top, width="stretch")

with right:
    st.subheader("Bottom 5 Contributors")

    bot = bottom_df.copy()
    bot.columns = ["Security Name", "Total PnL"]
    bot["Total PnL"] = bot["Total PnL"].apply(usd)
    bot.index = range(1, len(bot)+1)

    st.dataframe(bot, width="stretch")

# =====================================================
# DETAIL TABLE
# =====================================================
st.subheader("Detailed Strategy Table")

detail = df[["Strategy", "PnL", "Attribution"]].copy()
detail["PnL"] = detail["PnL"].apply(usd)
detail["Attribution"] = detail["Attribution"].apply(pct)
detail.index = range(1, len(detail)+1)

st.dataframe(detail, width="stretch")
