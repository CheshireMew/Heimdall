from datetime import datetime, timezone
from sqlalchemy import create_engine, text

from config import settings

DB_URL = settings.DATABASE_URL


def check_database():
    print(f"--- Checking Database: {DB_URL} ---")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT count(*) FROM klines"))
            count = result.scalar()
            print(f"[OK] Connection Successful")
            print(f"[DATA] Total Rows in 'klines' table: {count}")

            print("\n--- Data Breakdown ---")
            breakdown = conn.execute(text("""
                SELECT
                    symbol,
                    count(*) as count,
                    min(timestamp) as min_ts,
                    max(timestamp) as max_ts
                FROM klines
                GROUP BY symbol
            """))

            for row in breakdown:
                min_date = datetime.fromtimestamp(row[2]/1000, tz=timezone.utc).strftime('%Y-%m-%d') if row[2] else 'N/A'
                max_date = datetime.fromtimestamp(row[3]/1000, tz=timezone.utc).strftime('%Y-%m-%d') if row[3] else 'N/A'
                print(f"Symbol: {row[0]:<10} | Rows: {row[1]:<6} | Range: {min_date} -> {max_date}")
    except Exception as e:
        print(f"[ERROR] Connection Failed: {e}")


if __name__ == "__main__":
    check_database()
