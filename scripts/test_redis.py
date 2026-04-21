import time

from app.infra.cache import build_cache_service
from app.runtime_graph import build_app_runtime_services


def test_redis_connection():
    cache_service = build_cache_service()
    cache_service.connect()
    print("测试 Redis 连接...")
    if cache_service.client:
        print("[OK] Redis 连接成功！")

        print("测试写入...")
        cache_service.set("test_key", "hello_redis", ttl=10)

        print("测试读取...")
        val = cache_service.get("test_key")
        print(f"   Value: {val}")
        
        if val == "hello_redis":
            print("[OK] 读写测试通过！")
        else:
            print("[ERROR] 读写测试失败")
    else:
        print("[ERROR] Redis 连接失败 (client is None)")

def test_market_cache():
    print("\n[DATA] 测试 K线数据缓存...")
    provider = build_app_runtime_services().market.market_data_service
    if provider is None:
        raise RuntimeError("MarketDataService 未初始化")
    symbol = 'BTC/USDT'
    
    start_time = time.time()
    print("   第1次请求 (应走交易所)...")
    data1 = provider.get_kline_data(symbol, limit=5)
    t1 = time.time() - start_time
    print(f"   耗时: {t1:.4f}s")
    
    if not data1:
        print("[ERROR] 获取数据失败，无法继续测试缓存")
        return

    start_time = time.time()
    print("   第2次请求 (应走 Redis)...")
    data2 = provider.get_kline_data(symbol, limit=5)
    t2 = time.time() - start_time
    print(f"   耗时: {t2:.4f}s")
    
    if t2 < t1 and t2 < 0.1:
        print("[OK] 缓存生效！速度显著提升。")
    else:
        print("[WARN] 缓存似乎未生效，或网络极快。")
        
    # 验证数据一致性
    if data1 == data2:
         print("[OK] 数据一致性验证通过。")
    else:
         print("[ERROR] 数据不一致！")

if __name__ == "__main__":
    test_redis_connection()
    test_market_cache()
