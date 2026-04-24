import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="RAYS Capital Risk Dashboard",
    page_icon="📈",
    layout="wide"
)

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent


def fmt_dollar(x):
    try:
        return f"${x:,.0f}"
    except:
        return "-"


def fmt_pct(x):
    try:
        return f"{x*100:.2f}%"
    except:
        return "-"


def clean_name(txt):
    txt = str(txt).replace("_", " ").title()
    return txt


# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
@st.cache_data
def load_data():
    pnl = pd.read_excel(BASE_DIR / "pnl_decomposition.xlsx")
    monthly = pd.read_excel(BASE_DIR / "monthly_strategy_attribution.xlsx")
    quarterly = pd.read_excel(BASE_DIR / "quarterly_strategy_attribution.xlsx")
    top = pd.read_excel(BASE_DIR / "top_5_contributors.xlsx")
    bottom = pd.read_excel(BASE_DIR / "bottom_5_contributors.xlsx")

    pnl["month"] = pd.to_datetime(pnl["month"])
    monthly["month"] = pd.to_datetime(monthly["month"])
    quarterly["quarter"] = pd.to_datetime(quarterly["quarter"])

    return pnl, monthly, quarterly, top, bottom


pnl_df, monthly_df, quarterly_df, top_df, bottom_df = load_data()

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.title("RAYS Capital Risk Dashboard")
st.caption("Institutional Hedge Fund Analytics")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.header("Filters")

view = st.sidebar.selectbox(
    "View",
    ["Monthly", "Quarterly"]
)

# ---------------------------------------------------
# MONTHLY VIEW
# ---------------------------------------------------
if view == "Monthly":

    periods = sorted(monthly_df["month"].dt.strftime("%b %Y").unique())
    selected = st.sidebar.selectbox("Select Month", periods)

    selected_date = pd.to_datetime(selected)

    df = monthly_df[
        monthly_df["month"].dt.to_period("M")
        == selected_date.to_period("M")
    ].copy()

    pnl_filtered = pnl_df[
        pnl_df["month"].dt.to_period("M")
        == selected_date.to_period("M")
    ].copy()

    period_label = selected

# ---------------------------------------------------
# QUARTERLY VIEW
# ---------------------------------------------------
else:

    periods = sorted(quarterly_df["quarter"].dt.strftime("Q%q %Y").unique())
    selected = st.sidebar.selectbox("Select Quarter", periods)

    quarter_map = {
        "Q1 2021": "2021Q1",
        "Q2 2021": "2021Q2",
        "Q3 2021": "2021Q3",
        "Q4 2021": "2021Q4"
    }

    q_period = quarter_map[selected]

    df = quarterly_df[
        quarterly_df["quarter"].dt.to_period("Q").astype(str) == q_period
    ].copy()

    pnl_filtered = pnl_df[
        pnl_df["month"].dt.to_period("Q").astype(str) == q_period
    ].copy()

    period_label = selected

# ---------------------------------------------------
# CLEAN DISPLAY DATA
# ---------------------------------------------------
df["Strategy"] = df["strategy"].apply(clean_name)
df["PnL"] = df["total_pnl"]
df["Attribution"] = df["attribution_pct"]

# ---------------------------------------------------
# TOP METRICS
# ---------------------------------------------------
total_pnl = df["PnL"].sum()
best = df.loc[df["PnL"].idxmax()] if len(df) > 0 else None
worst = df.loc[df["PnL"].idxmin()] if len(df) > 0 else None

col1, col2, col3, col4 = st.columns(4)

col1.metric("Period", period_label)
col2.metric("Total PnL", fmt_dollar(total_pnl))

if best is not None:
    col3.metric(
        "Best Strategy",
        best["Strategy"],
        fmt_dollar(best["PnL"])
    )

if worst is not None:
    col4.metric(
        "Worst Strategy",
        worst["Strategy"],
        fmt_dollar(worst["PnL"])
    )

st.divider()

# ---------------------------------------------------
# STRATEGY BAR CHART
# ---------------------------------------------------
st.subheader("Strategy Attribution")

fig = px.bar(
    df,
    x="Strategy",
    y="PnL",
    text=df["Attribution"].apply(fmt_pct),
)

fig.update_traces(textposition="outside")
fig.update_layout(height=500)

st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------
# PNL BREAKDOWN
# ---------------------------------------------------
st.subheader("PnL Decomposition")

fig2 = px.bar(
    pnl_filtered,
    x="strategy",
    y=["price_pnl", "fx_pnl", "carry_pnl"],
    barmode="stack"
)

fig2.update_layout(
    xaxis_title="Strategy",
    yaxis_title="PnL",
    legend_title="Component",
    height=500
)

st.plotly_chart(fig2, width="stretch")

# ---------------------------------------------------
# TOP / BOTTOM CONTRIBUTORS
# ---------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Top 5 Contributors")

    top_show = top_df.copy()
    top_show.index = range(1, len(top_show) + 1)
    top_show.columns = ["Security Name", "Total PnL"]

    top_show["Total PnL"] = top_show["Total PnL"].apply(fmt_dollar)

    st.dataframe(top_show, width="stretch")

with right:
    st.subheader("Bottom 5 Contributors")

    bot_show = bottom_df.copy()
    bot_show.index = range(1, len(bot_show) + 1)
    bot_show.columns = ["Security Name", "Total PnL"]

    bot_show["Total PnL"] = bot_show["Total PnL"].apply(fmt_dollar)

    st.dataframe(bot_show, width="stretch")

# ---------------------------------------------------
# DETAIL TABLE
# ---------------------------------------------------
st.subheader("Detailed Attribution Table")

table = df[["Strategy", "PnL", "Attribution"]].copy()
table.index = range(1, len(table) + 1)
table["PnL"] = table["PnL"].apply(fmt_dollar)
table["Attribution"] = table["Attribution"].apply(fmt_pct)

st.dataframe(table, width="stretch")
