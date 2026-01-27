import sys
import os
from pathlib import Path
import time

# 添加项目根目录
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

try:
    from services.redis_service import redis_service
    from core.market_provider import MarketProvider
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_redis_connection():
    print("🔌 测试 Redis 连接...")
    if redis_service.client:
        print("✅ Redis 连接成功！")
        
        print("💾 测试写入...")
        redis_service.set("test_key", "hello_redis", ttl=10)
        
        print("📖 测试读取...")
        val = redis_service.get("test_key")
        print(f"   Value: {val}")
        
        if val == "hello_redis":
            print("✅ 读写测试通过！")
        else:
            print("❌ 读写测试失败")
    else:
        print("❌ Redis 连接失败 (client is None)")

def test_market_cache():
    print("\n📊 测试 K线数据缓存...")
    provider = MarketProvider()
    symbol = 'BTC/USDT'
    
    start_time = time.time()
    print("   第1次请求 (应走交易所)...")
    data1 = provider.get_kline_data(symbol, limit=5)
    t1 = time.time() - start_time
    print(f"   耗时: {t1:.4f}s")
    
    if not data1:
        print("❌ 获取数据失败，无法继续测试缓存")
        return

    start_time = time.time()
    print("   第2次请求 (应走 Redis)...")
    data2 = provider.get_kline_data(symbol, limit=5)
    t2 = time.time() - start_time
    print(f"   耗时: {t2:.4f}s")
    
    if t2 < t1 and t2 < 0.1:
        print("✅ 缓存生效！速度显著提升。")
    else:
        print("⚠️ 缓存似乎未生效，或网络极快。")
        
    # 验证数据一致性
    if data1 == data2:
         print("✅ 数据一致性验证通过。")
    else:
         print("❌ 数据不一致！")

if __name__ == "__main__":
    test_redis_connection()
    test_market_cache()
