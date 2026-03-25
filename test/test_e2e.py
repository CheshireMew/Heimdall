"""
端到端测试 - 验证完整的 Heimdall 分析流程
包括：数据获取 → 指标计算 → Prompt 构建 → (可选) AI 分析
"""
import asyncio

from app.services.market.market_data_service import MarketDataService
from app.domain.market.prompt_engine import PromptEngine
from app.domain.market.technical_analysis import TechnicalAnalysis
from app.infra.llm_client import LLMClient
from config import settings
from utils.logger import logger


def test_data_pipeline():
    """测试数据处理管道"""
    print("\n" + "="*60)
    print("端到端测试: Heimdall 完整分析流程")
    print("="*60)
    
    # 1. 初始化 MarketDataService
    print("\n[1/5] 初始化 MarketDataService...")
    try:
        provider = MarketDataService()
        print(f"[OK] MarketDataService 初始化成功 (交易所: {settings.EXCHANGE_ID})")
    except Exception as e:
        print(f"[ERROR] MarketDataService 初始化失败: {e}")
        raise AssertionError(f"MarketDataService 初始化失败: {e}") from e
    
    # 2. 获取 K 线数据
    print("\n[2/5] 获取市场数据...")
    test_symbol = settings.SYMBOLS[0]  # 默认测试第一个交易对
    try:
        kline_data = provider.get_kline_data(test_symbol, limit=50)
        if not kline_data or len(kline_data) < 20:
            raise AssertionError("获取数据失败或数据不足 (需要至少 20 条)")
        print(f"[OK] 成功获取 {test_symbol} K线数据: {len(kline_data)} 条")
        print(f"   最新价格: {kline_data[-1][4]}")
    except Exception as e:
        raise AssertionError(f"数据获取异常: {e}") from e
    
    # 3. 计算技术指标
    print("\n[3/5] 计算技术指标...")
    try:
        closes = [x[4] for x in kline_data]
        highs = [x[2] for x in kline_data]
        lows = [x[3] for x in kline_data]
        
        indicators = {}
        indicators['ema'] = TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD)
        indicators['rsi'] = TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD)
        indicators['macd'] = TechnicalAnalysis.calculate_macd(
            closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
        )
        indicators['atr'] = TechnicalAnalysis.calculate_atr(highs, lows, closes, 14)
        
        # 验证指标有效性
        if indicators['ema'] is None or indicators['rsi'] is None:
            raise AssertionError("指标计算失败 (EMA 或 RSI 为 None)")
            
        print(f"[OK] 技术指标计算完成:")
        print(f"   EMA({settings.EMA_PERIOD}): {indicators['ema']:.2f}")
        print(f"   RSI({settings.RSI_PERIOD}): {indicators['rsi']:.2f}")
        if indicators['macd'] and indicators['macd'][0]:
            dif, dea, hist = indicators['macd']
            print(f"   MACD: DIF={dif:.2f}, DEA={dea:.2f}, HIST={hist:.2f}")
        if indicators['atr']:
            print(f"   ATR: {indicators['atr']:.2f}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise AssertionError(f"指标计算异常: {e}") from e
    
    # 4. 构建 Prompt
    print("\n[4/5] 构建 AI Prompt...")
    try:
        prompt = PromptEngine.build_analysis_prompt(test_symbol, kline_data, indicators)
        if not prompt or len(prompt) < 50:
            raise AssertionError("Prompt 构建失败 (内容过短)")
        print(f"[OK] Prompt 构建成功 (长度: {len(prompt)} 字符)")
        print(f"   前 150 字符预览: {prompt[:150]}...")
    except Exception as e:
        raise AssertionError(f"Prompt 构建异常: {e}") from e
    
    # 5. AI 分析 (可选，取决于是否配置了 API Key)
    print("\n[5/5] 调用 AI 分析 (可选)...")
    try:
        llm_client = LLMClient()
        
        # 检查是否配置了有效的 API Key
        if not settings.DEEPSEEK_API_KEY or len(settings.DEEPSEEK_API_KEY) < 10:
            print("[WARN]  未配置有效的 DEEPSEEK_API_KEY，跳过 AI 分析测试")
            print("   提示: 在 .env 文件中配置 API Key 以启用 AI 分析")
        else:
            print("   正在调用 DeepSeek API (可能需要几秒钟)...")
            result = asyncio.run(llm_client.analyze(prompt))
            
            if result:
                print(f"[OK] AI 分析成功:")
                print(f"   信号: {result.get('signal', 'N/A')}")
                print(f"   置信度: {result.get('confidence', 0)}%")
                print(f"   理由: {result.get('reasoning', 'N/A')[:100]}...")
            else:
                print("[WARN]  AI 未返回有效结果 (可能是 API 调用失败)")
                
    except Exception as e:
        print(f"[WARN]  AI 分析异常: {e}")
        # AI 分析失败不影响整体测试通过
    
    # 6. 测试总结
    print("\n" + "="*60)
    print("[OK] 端到端测试通过")
    print("="*60)
    print("\n核心功能验证:")
    print("  [OK] 数据获取模块")
    print("  [OK] 技术分析模块")
    print("  [OK] Prompt 构建模块")
    print("  [OK] LLM 客户端模块 (可选)")
    print("\n🎉 Heimdall 已准备就绪!")


if __name__ == "__main__":
    test_data_pipeline()
