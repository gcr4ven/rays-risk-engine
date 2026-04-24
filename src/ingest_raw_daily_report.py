import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE", "risk_engine")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD")

if not PGPASSWORD:
    raise ValueError("Missing PGPASSWORD in .env")

engine = create_engine(
    f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
)

EXCEL_PATH = r"risk_engine_raw_data\Daily_Position_Valuation_Report.xlsx"

df = pd.read_excel(EXCEL_PATH)
df.columns = [c.strip() for c in df.columns]

rename_map = {
    "Fund Name": "fund_name",
    "Date": "report_date",
    "Underlying": "underlying",
    "Security Name": "security_name",
    "Security Type Name": "security_type_name",
    "RAYS Identifiers": "rays_identifiers",
    "Position": "position",
    "Price": "price",
    "Market Value (Fund Ccy)": "market_value",
    "Security Currency": "security_currency",
    "Base -> Sec FX": "base_to_sec_fx",
    "MTD P/L (Fund Ccy)": "mtd_pl_fund_ccy",
    "YTD P/L (Fund Ccy)": "ytd_pl_fund_ccy",
    "Country": "default_country",
    "Custodian Name": "prime_broker",
}

df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

df["underlying"] = df["underlying"].astype(str).str.strip()
df["fund_name"] = df["fund_name"].astype(str).str.strip()
df["prime_broker"] = df["prime_broker"].astype(str).str.strip()

df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce").dt.date
if df["report_date"].isna().any():
    raise ValueError("Some report_date values could not be parsed")

keep_cols = [
    "fund_name", "report_date", "underlying",
    "security_name", "security_type_name", "rays_identifiers",
    "position", "price", "market_value",
    "security_currency", "base_to_sec_fx",
    "mtd_pl_fund_ccy", "ytd_pl_fund_ccy",
    "default_country", "prime_broker",
]
keep_cols = [c for c in keep_cols if c in df.columns]

df_out = df[keep_cols].dropna(subset=["fund_name", "report_date", "underlying"])
df_out.to_sql("raw_daily_position_valuation", engine, if_exists="append", index=False)

print(f"Loaded {len(df_out)} rows into raw_daily_position_valuation")
print("Funds:", sorted(df_out['fund_name'].unique()))
print("Dates:", sorted(df_out['report_date'].unique()))
