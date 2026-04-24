import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="RAYS Risk Dashboard", layout="wide")

# -----------------------------
# SAFE HELPERS
# -----------------------------
def safe_pct(x):
    if pd.isna(x):
        return 0.0
    return x

def fmt_money(x):
    if pd.isna(x):
        return "$0"
    return f"${x:,.0f}"

def fmt_pct(x):
    if pd.isna(x):
        return "0.00%"
    return f"{x*100:.2f}%"


def safe_idxmax(df, col):
    if df is None or df.empty or col not in df.columns:
        return None
    if df[col].dropna().empty:
        return None
    return df[col].idxmax()


# -----------------------------
# LOAD DATA (replace with your real loader)
# -----------------------------
@st.cache_data
def load_data():
    # This assumes you already load from SQL or excel
    # Replace with your engine logic
    return pd.read_csv("pnl_decomposition.csv") if False else pd.DataFrame()


# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------
st.sidebar.title("RAYS Dashboard Controls")

view_mode = st.sidebar.selectbox(
    "Time Horizon",
    ["Monthly", "Quarterly", "Full", "Rolling (coming soon)"]
)

# -----------------------------
# LOAD DATA
# -----------------------------
df = load_data()

# -----------------------------
# HANDLE EMPTY DATA SAFELY
# -----------------------------
if df.empty:
    st.warning("No data loaded. Check ingestion pipeline.")
    st.stop()

# -----------------------------
# TOTAL PNL
# -----------------------------
total_pnl = df["total_pnl"].sum() if "total_pnl" in df else 0

st.title("RAYS Risk Engine Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Total PnL", fmt_money(total_pnl))
col2.metric("Rows", len(df))
col3.metric("Strategies", df["strategy"].nunique() if "strategy" in df else 0)

st.divider()

# -----------------------------
# STRATEGY ATTRIBUTION
# -----------------------------
st.subheader("Strategy Attribution")

if "strategy" in df.columns:
    strat = df.groupby("strategy")["total_pnl"].sum().reset_index()
    strat["pct"] = strat["total_pnl"] / strat["total_pnl"].sum()

    col1, col2 = st.columns(2)

    with col1:
        st.dataframe(
            strat.sort_values("total_pnl", ascending=False),
            use_container_width=True
        )

    with col2:
        st.bar_chart(strat.set_index("strategy")["total_pnl"])

# -----------------------------
# TOP / BOTTOM CONTRIBUTORS
# -----------------------------
st.subheader("Top / Bottom Contributors")

# expects: security_name + total_pnl
if "security_name" in df.columns and "total_pnl" in df.columns:

    contrib = df.groupby("security_name")["total_pnl"].sum().reset_index()

    top5 = contrib.sort_values("total_pnl", ascending=False).head(5)
    bottom5 = contrib.sort_values("total_pnl", ascending=True).head(5)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Top 5 Contributors")
        st.dataframe(top5, use_container_width=True)

    with c2:
        st.markdown("### Bottom 5 Contributors")
        st.dataframe(bottom5, use_container_width=True)

# -----------------------------
# COUNTRY ATTRIBUTION (SAFE)
# -----------------------------
st.subheader("Country Attribution")

if "country" in df.columns and "total_pnl" in df.columns:

    country = df.groupby("country")["total_pnl"].sum().reset_index()
    country["pct"] = country["total_pnl"] / country["total_pnl"].sum()

    st.dataframe(country.sort_values("total_pnl", ascending=False),
                 use_container_width=True)

# -----------------------------
# SECTOR ATTRIBUTION (SAFE)
# -----------------------------
st.subheader("Sector Attribution")

if "sector" in df.columns and "total_pnl" in df.columns:

    sector = df.groupby("sector")["total_pnl"].sum().reset_index()
    sector["pct"] = sector["total_pnl"] / sector["total_pnl"].sum()

    st.dataframe(sector.sort_values("total_pnl", ascending=False),
                 use_container_width=True)

# -----------------------------
# KEY INSIGHTS (SAFE)
# -----------------------------
st.subheader("Key Insights")

best_strategy = None
worst_strategy = None

if "strategy" in df.columns and "total_pnl" in df.columns:
    strat = df.groupby("strategy")["total_pnl"].sum()

    if not strat.empty:
        best_strategy = strat.idxmax()
        worst_strategy = strat.idxmin()

st.write("Best Strategy:", best_strategy if best_strategy else "N/A")
st.write("Worst Strategy:", worst_strategy if worst_strategy else "N/A")

# -----------------------------
# RAW TABLE (DEBUG / ALVIN BACKUP)
# -----------------------------
st.subheader("Raw Data (Debug View)")
st.dataframe(df, use_container_width=True)
