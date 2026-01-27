"""
数据迁移脚本：SQLite -> PostgreSQL
"""
import sqlite3
import json
from datetime import datetime
import sys
from pathlib import Path

# 添加根目录
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from app.database import SessionLocal, engine
from app.models import schema
from sqlalchemy import text

SQLITE_DB = 'data/heimdall.db'

def migrate_klines(sqlite_cursor, pg_session):
    print("⏳ 正在迁移 klines 表...")
    sqlite_cursor.execute("SELECT symbol, timeframe, timestamp, open, high, low, close, volume FROM klines")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print("  - 无数据，跳过")
        return
        
    print(f"  - 发现 {len(rows)} 条K线数据，准备批量插入...")
    
    # 使用 PostgreSQL 的高效插入方法
    # TRUNCATE 表（可选，防止重复）
    pg_session.execute(text("TRUNCATE TABLE klines"))
    
    # 批量构建对象
    # 注意：ORM 批量插入较慢，这里使用 core insert
    try:
        data = [
            {
                "symbol": r[0], "timeframe": r[1], "timestamp": r[2],
                "open": r[3], "high": r[4], "low": r[5], "close": r[6], "volume": r[7]
            }
            for r in rows
        ]
        
        # 分批插入，每批 5000 条
        batch_size = 5000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            pg_session.bulk_insert_mappings(schema.Kline, batch)
            print(f"    - 已插入 {i + len(batch)} / {len(data)}")
            
        pg_session.commit()
        print("✅ klines 表迁移完成！")
        
    except Exception as e:
        pg_session.rollback()
        print(f"❌ klines 迁移失败: {e}")

def migrate_backtests(sqlite_cursor, pg_session):
    print("\n⏳ 正在迁移回测数据...")
    
    # 1. 迁移 backtest_runs
    sqlite_cursor.execute("SELECT id, symbol, timeframe, start_date, end_date, created_at, status, total_candles, total_signals, buy_signals, sell_signals, hold_signals, metadata FROM backtest_runs")
    runs = sqlite_cursor.fetchall()
    
    id_map = {} # 旧ID -> 新ID (如果自增ID变化)
    
    for r in runs:
        # SQLite 时间字符串转换为 datetime 对象
        # 格式通常是 '2023-01-01 00:00:00.000000' 或 '2023-01-01 00:00:00'
        def parse_time(t):
            if not t: return None
            if isinstance(t, str):
                try:
                    return datetime.fromisoformat(t)
                except:
                    # 尝试常见格式
                    try:
                        return datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
                    except:
                        try:
                            return datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
                        except:
                            return None
            return t

        run = schema.BacktestRun(
            # id=r[0], # 不指定ID，让Postgres自增
            symbol=r[1],
            timeframe=r[2],
            start_date=parse_time(r[3]),
            end_date=parse_time(r[4]),
            created_at=parse_time(r[5]),
            status=r[6],
            total_candles=r[7],
            total_signals=r[8],
            buy_signals=r[9],
            sell_signals=r[10],
            hold_signals=r[11],
            metadata_info=json.loads(r[12]) if r[12] else None
        )
        pg_session.add(run)
        pg_session.flush() # 获取新ID
        id_map[r[0]] = run.id
        
    print(f"  - 已迁移 {len(runs)} 条 backtest_runs")
    
    # 2. 迁移 backtest_signals
    # 由于外键依赖，我们需要更新 backtest_id
    sqlite_cursor.execute("SELECT backtest_id, timestamp, price, signal, confidence, indicators, reasoning FROM backtest_signals")
    signals = sqlite_cursor.fetchall()
    
    batch_signals = []
    skipped = 0
    for s in signals:
        old_bid = s[0]
        if old_bid not in id_map:
            skipped += 1
            continue
            
        def parse_time(t):
            if isinstance(t, str):
                try:
                    return datetime.fromisoformat(t)
                except:
                   try: 
                       return datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
                   except:
                       return datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
            return t
            
        batch_signals.append({
            "backtest_id": id_map[old_bid],
            "timestamp": parse_time(s[1]),
            "price": s[2],
            "signal": s[3],
            "confidence": s[4],
            "indicators": json.loads(s[5]) if s[5] else None,
            "reasoning": s[6]
        })
    
    if batch_signals:
         # 分批插入
        batch_size = 2000
        for i in range(0, len(batch_signals), batch_size):
            batch = batch_signals[i:i+batch_size]
            pg_session.bulk_insert_mappings(schema.BacktestSignal, batch)
            
    print(f"  - 已迁移 {len(batch_signals)} 条 backtest_signals (跳过 {skipped} 条无效外键)")
    
    pg_session.commit()
    print("✅ 回测数据迁移完成！")

def main():
    if not Path(SQLITE_DB).exists():
        print(f"❌ SQLite数据库未找到: {SQLITE_DB}")
        return

    print(f"🔌 连接SQLite: {SQLITE_DB} ...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()
    
    print("🔌 连接PostgreSQL...")
    pg_session = SessionLocal()
    
    try:
        migrate_klines(sqlite_cursor, pg_session)
        migrate_backtests(sqlite_cursor, pg_session)
        print("\n🎉🎉🎉 全部迁移成功！")
    except Exception as e:
        pg_session.rollback()
        print(f"\n❌ 迁移过程中发生错误: {e}")
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    main()
