import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    port=os.getenv("PGPORT"),
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
)

cur = conn.cursor()

# Create positions_monthly
cur.execute("""
CREATE TABLE IF NOT EXISTS positions_monthly (
    id SERIAL PRIMARY KEY,
    fund_id INT NOT NULL,
    ticker TEXT NOT NULL,
    security_name TEXT,
    security_type TEXT,
    strategy_raw TEXT,
    position DECIMAL(20,4),
    realized_fx DECIMAL(20,4),
    unrealized_fx DECIMAL(20,4),
    realized_price DECIMAL(20,4),
    unrealized_price DECIMAL(20,4),
    carry DECIMAL(20,4),
    monthly_pnl DECIMAL(20,4),
    month_end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_positions_monthly_date ON positions_monthly(month_end_date);
""")

# Create fund_nav
cur.execute("""
CREATE TABLE IF NOT EXISTS fund_nav (
    id SERIAL PRIMARY KEY,
    fund_id INT NOT NULL,
    month_end_date DATE NOT NULL,
    nav DECIMAL(20,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_id, month_end_date)
);
CREATE INDEX IF NOT EXISTS idx_fund_nav_date ON fund_nav(month_end_date);
""")

conn.commit()
cur.close()
conn.close()
print("✅ Tables created successfully.")