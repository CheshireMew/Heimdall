import sqlite3
import os

db_path = 'data/heimdall.db'

if not os.path.exists(db_path):
    print(f"❌ Database file not found at {db_path}")
else:
    print(f"✅ Database file found: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        
        total_rows = 0
        for table_name in tables:
            name = table_name[0]
            # Skip internal sqlite tables
            if name.startswith('sqlite_'):
                continue
                
            cursor.execute(f"SELECT COUNT(*) FROM {name}")
            count = cursor.fetchone()[0]
            print(f"  - {name}: {count} rows")
            total_rows += count
            
        print(f"\n📈 Total rows across all tables: {total_rows}")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
