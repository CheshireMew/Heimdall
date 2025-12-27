"""
端到端测试 - 验证完整的 Heimdall 分析流程
包括：数据获取 → 指标计算 → Prompt 构建 → (可选) AI 分析
"""
import sys
import os

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.market_provider import MarketProvider
from core.technical_analysis import TechnicalAnalysis
from core.prompt_engine import PromptEngine
from services.llm_client import LLMClient
from config import settings
from utils.logger import logger


def test_data_pipeline():
    """测试数据处理管道"""
    print("\n" + "="*60)
    print("端到端测试: Heimdall 完整分析流程")
    print("="*60)
    
    # 1. 初始化 MarketProvider
    print("\n[1/5] 初始化 MarketProvider...")
    try:
        provider = MarketProvider()
        print(f"✅ MarketProvider 初始化成功 (交易所: {settings.EXCHANGE_ID})")
    except Exception as e:
        print(f"❌ MarketProvider 初始化失败: {e}")
        return False
    
    # 2. 获取 K 线数据
    print("\n[2/5] 获取市场数据...")
    test_symbol = settings.SYMBOLS[0]  # 默认测试第一个交易对
    try:
        kline_data = provider.get_kline_data(test_symbol, limit=50)
        if not kline_data or len(kline_data) < 20:
            print(f"❌ 获取数据失败或数据不足 (需要至少 20 条)")
            return False
        print(f"✅ 成功获取 {test_symbol} K线数据: {len(kline_data)} 条")
        print(f"   最新价格: {kline_data[-1][4]}")
    except Exception as e:
        print(f"❌ 数据获取异常: {e}")
        return False
    
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
            print(f"❌ 指标计算失败 (EMA 或 RSI 为 None)")
            return False
            
        print(f"✅ 技术指标计算完成:")
        print(f"   EMA({settings.EMA_PERIOD}): {indicators['ema']:.2f}")
        print(f"   RSI({settings.RSI_PERIOD}): {indicators['rsi']:.2f}")
        if indicators['macd'] and indicators['macd'][0]:
            dif, dea, hist = indicators['macd']
            print(f"   MACD: DIF={dif:.2f}, DEA={dea:.2f}, HIST={hist:.2f}")
        if indicators['atr']:
            print(f"   ATR: {indicators['atr']:.2f}")
            
    except Exception as e:
        print(f"❌ 指标计算异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 构建 Prompt
    print("\n[4/5] 构建 AI Prompt...")
    try:
        prompt = PromptEngine.build_analysis_prompt(test_symbol, kline_data, indicators)
        if not prompt or len(prompt) < 50:
            print(f"❌ Prompt 构建失败 (内容过短)")
            return False
        print(f"✅ Prompt 构建成功 (长度: {len(prompt)} 字符)")
        print(f"   前 150 字符预览: {prompt[:150]}...")
    except Exception as e:
        print(f"❌ Prompt 构建异常: {e}")
        return False
    
    # 5. AI 分析 (可选，取决于是否配置了 API Key)
    print("\n[5/5] 调用 AI 分析 (可选)...")
    try:
        llm_client = LLMClient()
        
        # 检查是否配置了有效的 API Key
        if not settings.DEEPSEEK_API_KEY or len(settings.DEEPSEEK_API_KEY) < 10:
            print("⚠️  未配置有效的 DEEPSEEK_API_KEY，跳过 AI 分析测试")
            print("   提示: 在 .env 文件中配置 API Key 以启用 AI 分析")
        else:
            print("   正在调用 DeepSeek API (可能需要几秒钟)...")
            result = llm_client.analyze(prompt)
            
            if result:
                print(f"✅ AI 分析成功:")
                print(f"   信号: {result.get('signal', 'N/A')}")
                print(f"   置信度: {result.get('confidence', 0)}%")
                print(f"   理由: {result.get('reasoning', 'N/A')[:100]}...")
            else:
                print("⚠️  AI 未返回有效结果 (可能是 API 调用失败)")
                
    except Exception as e:
        print(f"⚠️  AI 分析异常: {e}")
        # AI 分析失败不影响整体测试通过
    
    # 6. 测试总结
    print("\n" + "="*60)
    print("✅ 端到端测试通过")
    print("="*60)
    print("\n核心功能验证:")
    print("  ✓ 数据获取模块")
    print("  ✓ 技术分析模块")
    print("  ✓ Prompt 构建模块")
    print("  ✓ LLM 客户端模块 (可选)")
    print("\n🎉 Heimdall 已准备就绪!")
    
    return True


if __name__ == "__main__":
    success = test_data_pipeline()
    sys.exit(0 if success else 1)
