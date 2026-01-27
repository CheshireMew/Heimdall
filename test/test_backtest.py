"""
回测模块测试
验证历史数据获取和回测逻辑
"""
import sys
import os
from datetime import datetime, timedelta

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backtester import Backtester
from models.database import init_db, get_session
from models.schema import BacktestRun  # 更新导入路径


def test_historical_data():
    """测试历史数据获取"""
    print("\n" + "="*60)
    print("测试 1: 历史数据获取")
    print("="*60)
    
    backtester = Backtester(use_ai=False)
    
    # 获取最近 3 天的数据
    end = datetime.now()
    start = end - timedelta(days=3)
    
    print(f"时间范围: {start} - {end}")
    
    data = backtester.fetch_historical_data('BTC/USDT', start, end, '1h')
    
    if data and len(data) > 0:
        print(f"成功获取 {len(data)} 条历史数据")
        print(f"   第一条: {datetime.fromtimestamp(data[0][0]/1000)} - 价格: {data[0][4]}")
        print(f"   最后一条: {datetime.fromtimestamp(data[-1][0]/1000)} - 价格: {data[-1][4]}")
        return True
    else:
        print("历史数据获取失败")
        return False


def test_backtest_run():
    """测试回测执行"""
    print("\n" + "="*60)
    print("测试 2: 回测执行")
    print("="*60)
    
    # 初始化数据库
    init_db()
    
    backtester = Backtester(use_ai=False)
    
    # 回测最近 2 天
    end = datetime.now()
    start = end - timedelta(days=2)
    
    print(f"开始回测: BTC/USDT ({start} - {end})")
    
    try:
        backtest_id = backtester.run_backtest('BTC/USDT', start, end, '1h')
        
        if backtest_id:
            print(f"回测完成! ID: {backtest_id}")
            
            # 获取结果
            result = backtester.get_backtest_result(backtest_id)
            
            if result:
                print(f"\n回测结果:")
                print(f"  交易对: {result['symbol']}")
                print(f"  K线总数: {result['total_candles']}")
                print(f"  信号总数: {result['total_signals']}")
                print(f"  BUY 信号: {result['buy_signals']}")
                print(f"  SELL 信号: {result['sell_signals']}")
                print(f"  HOLD 信号: {result['hold_signals']}")
                print(f"  状态: {result['status']}")
                
                # 显示前 3 个信号
                if result['signals']:
                    print(f"\n前 3 个信号:")
                    for i, sig in enumerate(result['signals'][:3]):
                        print(f"  [{i+1}] {sig['timestamp']} - {sig['signal']} @ {sig['price']} (置信度: {sig['confidence']}%)")
                
                return True
            else:
                print("获取回测结果失败")
                return False
        else:
            print("回测执行失败 (backtest_id is None)")
            return False
    except Exception as e:
        print(f"回测执行抛出异常: {repr(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """测试数据库查询"""
    print("\n" + "="*60)
    print("测试 3: 数据库查询")
    print("="*60)
    
    session = get_session()
    
    try:
        # 查询所有回测记录
        backtest_runs = session.query(BacktestRun).all()
        
        print(f"数据库中共有 {len(backtest_runs)} 条回测记录")
        
        for run in backtest_runs[-3:]:  # 显示最近 3 条
            print(f"  ID: {run.id}, {run.symbol}, {run.status}, 信号数: {run.total_signals}")
        
        if backtest_runs:
            print("数据库查询正常")
            return True
        else:
            print("数据库为空（这是正常的，如果这是首次运行）")
            return True
            
    except Exception as e:
        print(f"数据库查询失败: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("\nHeimdall 回测模块测试")
    print("="*60)
    
    results = []
    
    # 测试 1: 历史数据
    results.append(("历史数据获取", test_historical_data()))
    
    # 测试 2: 回测执行
    results.append(("回测执行", test_backtest_run()))
    
    # 测试 3: 数据库
    results.append(("数据库查询", test_database()))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, success in results:
        status = "通过" if success else "失败"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n所有测试通过!")
    else:
        print("\n部分测试失败")
    
    sys.exit(0 if all_passed else 1)
