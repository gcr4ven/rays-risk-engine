import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    port=os.getenv("PGPORT"),
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD")
)

cur = conn.cursor()

data_folder = "../risk_engine_raw_data"
files = [f for f in os.listdir(data_folder) if f.startswith("MTD")]

print("Files found:", files)

for file in files:
    path = os.path.join(data_folder, file)
    print("Loading:", file)

    df = pd.read_excel(path)

    for _, row in df.iterrows():

        # 🔹 Clean NaNs
        row = row.replace({pd.NA: None, float("nan"): None})

        # 🔹 Skip useless rows (VERY IMPORTANT)
        if row.get("Security Name") is None:
            continue

        if row.get("MTD P/L (Fund Ccy)") is None:
            continue

        # 🔹 Handle date
        date_value = row.get("Date")
        if pd.isna(date_value) or date_value is None:
            continue  # skip rows without valid date

        # 🔹 Ticker fallback
        ticker = row.get("RAYS Identifiers") or row.get("Underlying") or "UNKNOWN"

        try:
            cur.execute("""
            INSERT INTO positions_monthly (
                fund_id,
                ticker,
                security_name,
                security_type,
                strategy_raw,
                position,
                realized_fx,
                unrealized_fx,
                realized_price,
                unrealized_price,
                carry,
                monthly_pnl,
                month_end_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                1,
                ticker,
                row.get("Security Name"),
                row.get("Security Type Name"),
                row.get("Strategy Name"),
                row.get("Position"),
                row.get("Fund MTD Realized FX G/L"),
                row.get("Fund MTD Unrealized FX G/L"),
                row.get("Fund MTD Realized Price G/L"),
                row.get("Fund MTD Unrealized Price G/L"),
                row.get("Fund MTD Carry"),
                row.get("MTD P/L (Fund Ccy)"),
                date_value
            ))

        except Exception as e:
            print("Skipping bad row:", e)
            conn.rollback()   
            continue

# Commit everything at the end
conn.commit()

cur.close()
conn.close()

print("✅ Data loaded successfully")