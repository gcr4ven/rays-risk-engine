import os
import psycopg2
from dotenv import load_dotenv

# Load your .env variables
load_dotenv()

# Connect to Postgres
conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    port=os.getenv("PGPORT"),
    dbname=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
)

cur = conn.cursor()

# 1️⃣ List all tables in public schema
print("=== ALL TABLES IN DATABASE ===")
cur.execute("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
""")
tables = cur.fetchall()
for table in tables:
    print("-", table[0])

# 2️⃣ Show columns of key tables
key_tables = ["positions_monthly", "fund_nav"]

for table_name in key_tables:
    print(f"\n=== COLUMNS IN {table_name.upper()} ===")
    cur.execute(f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = '{table_name}';
    """)
    columns = cur.fetchall()
    for col in columns:
        print(col[0], "-", col[1])

# 3️⃣ Preview first 5 rows of positions_monthly
print("\n=== SAMPLE DATA FROM positions_monthly ===")
cur.execute("SELECT * FROM positions_monthly LIMIT 5;")
rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()
print("\n✅ Database inspection complete.")