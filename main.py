import time
from config import settings
from core.market_provider import MarketProvider
from core.technical_analysis import TechnicalAnalysis
from core.prompt_engine import PromptEngine
from services.llm_client import LLMClient
from utils.logger import logger

def process_symbol(symbol, provider, llm_client):
    """
    处理单个交易对的完整流程
    """
    logger.info(f"=== 开始分析 {symbol} ===")
    
    # 1. 获取数据
    kline_data = provider.get_kline_data(symbol)
    if not kline_data:
        logger.error(f"{symbol} 数据获取失败，跳过")
        return

    # 2. 计算指标
    # kline format: [time, open, high, low, close, volume]
    closes = [x[4] for x in kline_data]
    highs = [x[2] for x in kline_data]
    lows = [x[3] for x in kline_data]
    
    indicators = {}
    
    # EMA
    indicators['ema'] = TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD)
    
    # RSI
    indicators['rsi'] = TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD)
    
    # MACD
    indicators['macd'] = TechnicalAnalysis.calculate_macd(
        closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
    )
    
    # ATR
    indicators['atr'] = TechnicalAnalysis.calculate_atr(
        highs, lows, closes, 14
    )
    
    logger.info(f"{symbol} 指标计算完成: RSI={indicators['rsi']:.2f}")

    # 3. 构建 Prompt
    prompt = PromptEngine.build_analysis_prompt(symbol, kline_data, indicators)
    
    # 4. 调用 AI
    # 如果没有配置 Key，这里会返回 None，我们在 LLMClient 里处理了警告
    analysis_result = llm_client.analyze(prompt)
    
    # 5. 输出结果 / 提醒
    if analysis_result:
        signal = analysis_result.get('signal', 'UNKNOWN')
        confidence = analysis_result.get('confidence', 0)
        
        logger.info(f"AI 分析结果 [{symbol}]:")
        logger.info(f"Signal: {signal} (Confidence: {confidence}%)")
        logger.info(f"Reasoning: {analysis_result.get('reasoning')}")
        
        # 简单的阈值提醒
        if signal in ['BUY', 'SELL'] and confidence >= 70:
            logger.info(f"🔔 !!! 发现高置信度机会: {symbol} {signal} !!!")
            # 这里可以扩展发送邮件、Telegram等
    else:
        logger.info(f"{symbol} AI 分析未能返回有限结果 (可能是 Key 未配置)")

def main():
    logger.info("启动 AI-Guide 智能分析助手...")
    logger.info(f"配置: 交易所={settings.EXCHANGE_ID}, 周期={settings.TIMEFRAME}")
    
    provider = None
    try:
        provider = MarketProvider()
        llm_client = LLMClient()
        
        for symbol in settings.SYMBOLS:
            process_symbol(symbol, provider, llm_client)
            time.sleep(1) # 避免速率限制
            
    except Exception as e:
        logger.error(f"主程序发成错误: {e}")
    finally:
        if provider:
            provider.close()
        logger.info("分析任务结束")

if __name__ == "__main__":
    main()
