"""
Check market indicators data in database
"""
from sqlalchemy import create_engine, text

from config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Check Meta
    result = conn.execute(text('SELECT * FROM market_indicator_meta'))
    print('=== Market Indicator Meta ===')
    for row in result:
        print(f'{row[0]:20} | {row[1]:30} | {row[2]:12}')

    # Check Data
    result2 = conn.execute(text('SELECT indicator_id, timestamp, value FROM market_indicator_data ORDER BY timestamp DESC LIMIT 10'))
    print('\n=== Market Indicator Data (Recent 10) ===')
    for row in result2:
        print(f'{row[0]:20} | {str(row[1]):19} | {row[2]:12.2f}')
