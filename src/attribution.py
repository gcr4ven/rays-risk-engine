import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

# 🔹 Load environment variables
load_dotenv()

# 🔹 Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    port=os.getenv("PGPORT"),
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD")
)

# 🔹 TEMP NAV (replace later with real NAV table)
NAV = 100_000_000


# =========================================================
# 🔹 CHECK TABLE STRUCTURE (DEBUG)
# =========================================================
print("\nChecking table structure...")

query_check = """
SELECT * FROM positions_monthly LIMIT 5;
"""

df_check = pd.read_sql(query_check, conn)

print(df_check.head())
print("\nCOLUMNS:")
print(df_check.columns)


# =========================================================
# 🔹 TOP 5 CONTRIBUTORS
# =========================================================
query_top = """
SELECT
    security_name,
    SUM(monthly_pnl) AS total_pnl
FROM positions_monthly
GROUP BY security_name
ORDER BY total_pnl DESC
LIMIT 5;
"""

df_top = pd.read_sql(query_top, conn)

print("\nTop 5 Contributors:")
print(df_top)

df_top.to_excel("top_5_contributors.xlsx", index=False)


# =========================================================
# 🔹 BOTTOM 5 CONTRIBUTORS
# =========================================================
query_bottom = """
SELECT
    security_name,
    SUM(monthly_pnl) AS total_pnl
FROM positions_monthly
GROUP BY security_name
ORDER BY total_pnl ASC
LIMIT 5;
"""

df_bottom = pd.read_sql(query_bottom, conn)

print("\nBottom 5 Contributors:")
print(df_bottom)

df_bottom.to_excel("bottom_5_contributors.xlsx", index=False)


# =========================================================
# 🔹 STRATEGY ATTRIBUTION (TOTAL)
# =========================================================
query_strategy = """
SELECT
    strategy_raw AS strategy,
    SUM(monthly_pnl) AS total_pnl
FROM positions_monthly
GROUP BY strategy_raw
ORDER BY total_pnl DESC;
"""

df_strategy = pd.read_sql(query_strategy, conn)

# 🔹 Add attribution %
df_strategy["attribution_pct"] = df_strategy["total_pnl"] / NAV

print("\nStrategy Attribution:")
print(df_strategy)

df_strategy.to_excel("strategy_attribution.xlsx", index=False)


# =========================================================
# 🔹 MONTHLY STRATEGY ATTRIBUTION
# =========================================================
query_monthly = """
SELECT
    DATE_TRUNC('month', month_end_date) AS month,
    strategy_raw AS strategy,
    SUM(monthly_pnl) AS total_pnl
FROM positions_monthly
GROUP BY month, strategy_raw
ORDER BY month, total_pnl DESC;
"""

df_monthly = pd.read_sql(query_monthly, conn)

# 🔹 Fix timezone for Excel
df_monthly["month"] = pd.to_datetime(df_monthly["month"]).dt.tz_localize(None)

# 🔹 Add attribution %
df_monthly["attribution_pct"] = df_monthly["total_pnl"] / NAV

print("\nMonthly Strategy Attribution:")
print(df_monthly)

df_monthly.to_excel("monthly_strategy_attribution.xlsx", index=False)


# =========================================================
# 🔹 QUARTERLY STRATEGY ATTRIBUTION
# =========================================================
query_quarterly = """
SELECT
    DATE_TRUNC('quarter', month_end_date) AS quarter,
    strategy_raw AS strategy,
    SUM(monthly_pnl) AS total_pnl
FROM positions_monthly
GROUP BY quarter, strategy_raw
ORDER BY quarter, total_pnl DESC;
"""

df_quarterly = pd.read_sql(query_quarterly, conn)

# 🔹 Fix timezone for Excel
df_quarterly["quarter"] = pd.to_datetime(df_quarterly["quarter"]).dt.tz_localize(None)

# 🔹 Add attribution %
df_quarterly["attribution_pct"] = df_quarterly["total_pnl"] / NAV

print("\nQuarterly Strategy Attribution:")
print(df_quarterly)

df_quarterly.to_excel("quarterly_strategy_attribution.xlsx", index=False)


# =========================================================
# 🔹 PIVOT TABLES (CLEAN REPORT FORMAT)
# =========================================================

# Monthly pivot
pivot_monthly = df_monthly.pivot(
    index="month",
    columns="strategy",
    values="total_pnl"
).fillna(0)

pivot_monthly.to_excel("monthly_pivot.xlsx")


# Quarterly pivot
pivot_quarterly = df_quarterly.pivot(
    index="quarter",
    columns="strategy",
    values="total_pnl"
).fillna(0)

pivot_quarterly.to_excel("quarterly_pivot.xlsx")

# =========================================================
# 🔹 P&L DECOMPOSITION (PRICE / FX / CARRY)
# =========================================================

query_decomp = """
SELECT
    DATE_TRUNC('month', month_end_date) AS month,
    strategy_raw AS strategy,

    SUM(realized_price + unrealized_price) AS price_pnl,
    SUM(realized_fx + unrealized_fx) AS fx_pnl,
    SUM(carry) AS carry_pnl,

    SUM(monthly_pnl) AS total_pnl

FROM positions_monthly
GROUP BY month, strategy_raw
ORDER BY month;
"""

df_decomp = pd.read_sql(query_decomp, conn)

# 🔹 Fix timezone
df_decomp["month"] = pd.to_datetime(df_decomp["month"]).dt.tz_localize(None)

# 🔹 Attribution %
df_decomp["price_pct"] = df_decomp["price_pnl"] / NAV
df_decomp["fx_pct"] = df_decomp["fx_pnl"] / NAV
df_decomp["carry_pct"] = df_decomp["carry_pnl"] / NAV

print("\nP&L Decomposition:")
print(df_decomp)

df_decomp.to_excel("pnl_decomposition.xlsx", index=False)

# =========================================================
# 🔹 OFFICIAL RETURN RECONCILIATION LAYER
# =========================================================

print("\nRECONCILIATION REPORT")

# Example official monthly return from back office
official_return_pct = -0.0123   # -1.23%

# Pull March 2021 monthly attribution rows
march_data = df_monthly[df_monthly["month"] == "2021-03-01 08:00:00"]

# Initialize buckets
long_pct = 0
short_pct = 0
box_pct = 0
forward_pct = 0
other_pct = 0

for _, row in march_data.iterrows():
    strat = row["strategy"]
    
    if strat == "LONG":
        long_pct = row["attribution_pct"]
    elif strat == "SHORT":
        short_pct = row["attribution_pct"]
    elif strat == "BOX":
        box_pct = row["attribution_pct"]
    elif strat == "FORWARD":
        forward_pct = row["attribution_pct"]
    else:
        other_pct += row["attribution_pct"]

# Explained return
explained_return = (
    long_pct +
    short_pct +
    box_pct +
    forward_pct +
    other_pct
)

# Residual bucket
mgmt_fee_pct = official_return_pct - explained_return

# Print final report
print(f"Long: {long_pct:.2%}")
print(f"Short: {short_pct:.2%}")
print(f"Box: {box_pct:.2%}")
print(f"Forward: {forward_pct:.2%}")
print(f"Other: {other_pct:.2%}")
print(f"Mgmt Fee & Other Monthly Fees: {mgmt_fee_pct:.2%}")
print(f"Overall Official Return: {official_return_pct:.2%}")

# =========================================================
# 🔴 CLOSE CONNECTION
# =========================================================
conn.close()