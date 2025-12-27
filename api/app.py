"""
Heimdall Flask API 服务
提供 RESTful API 接口，支持 Web Dashboard
"""
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.market_provider import MarketProvider
from core.technical_analysis import TechnicalAnalysis
from core.prompt_engine import PromptEngine
from core.backtester import Backtester
from services.llm_client import LLMClient
from models.database import init_db, get_session, BacktestRun
from config import settings
from utils.logger import logger

# 创建 Flask 应用
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

# 启用 CORS（允许跨域请求）
CORS(app)

# 初始化数据库
init_db()

# 全局实例
market_provider = MarketProvider()
llm_client = LLMClient()


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def api_status():
    """
    GET /api/status
    获取系统状态
    """
    try:
        return jsonify({
            'status': 'ok',
            'exchange': settings.EXCHANGE_ID,
            'symbols': settings.SYMBOLS,
            'timeframe': settings.TIMEFRAME,
            'ai_enabled': bool(settings.DEEPSEEK_API_KEY and len(settings.DEEPSEEK_API_KEY) > 10)
        })
    except Exception as e:
        logger.error(f"API /status 错误: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/realtime/<symbol>', methods=['GET'])
def api_realtime(symbol):
    """
    GET /api/realtime/:symbol
    获取实时分析
    """
    try:
        logger.info(f"实时分析请求: {symbol}")
        
        # 获取 K 线数据
        kline_data = market_provider.get_kline_data(symbol, settings.TIMEFRAME, settings.LIMIT)
        
        if not kline_data:
            return jsonify({'error': '获取数据失败'}), 500
        
        # 计算技术指标
        closes = [x[4] for x in kline_data]
        highs = [x[2] for x in kline_data]
        lows = [x[3] for x in kline_data]
        
        indicators = {
            'ema': TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD),
            'rsi': TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD),
            'macd': TechnicalAnalysis.calculate_macd(
                closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
            ),
            'atr': TechnicalAnalysis.calculate_atr(highs, lows, closes, 14)
        }
        
        # 构建 Prompt 并调用 AI（可选）
        ai_analysis = None
        if settings.DEEPSEEK_API_KEY and len(settings.DEEPSEEK_API_KEY) > 10:
            try:
                prompt = PromptEngine.build_analysis_prompt(symbol, kline_data, indicators)
                ai_analysis = llm_client.analyze(prompt)
            except Exception as e:
                logger.warning(f"AI 分析失败: {e}")
        
        # 返回结果
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': closes[-1],
            'indicators': {
                'ema': indicators['ema'],
                'rsi': indicators['rsi'],
                'macd': {
                    'dif': indicators['macd'][0] if indicators['macd'][0] else None,
                    'dea': indicators['macd'][1] if indicators['macd'][1] else None,
                    'histogram': indicators['macd'][2] if indicators['macd'][2] else None
                } if indicators['macd'] else None,
                'atr': indicators['atr']
            },
            'ai_analysis': ai_analysis,
            'kline_data': kline_data[-50:]  # 返回最近 50 根 K 线用于图表
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API /realtime 错误: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/start', methods=['POST'])
def api_backtest_start():
    """
    POST /api/backtest/start
    启动回测
    
    Request Body:
    {
        "symbol": "BTC/USDT",
        "days": 7,  // 回测最近 N 天
        "use_ai": false
    }
    """
    try:
        data = request.get_json()
        
        symbol = data.get('symbol', 'BTC/USDT')
        days = data.get('days', 7)
        use_ai = data.get('use_ai', False)
        
        logger.info(f"启动回测: {symbol}, 最近 {days} 天, AI={use_ai}")
        
        # 计算时间范围
        end = datetime.now()
        start = end - timedelta(days=days)
        
        # 创建回测实例
        backtester = Backtester(use_ai=use_ai)
        
        # 执行回测
        backtest_id = backtester.run_backtest(symbol, start, end, settings.TIMEFRAME)
        
        if backtest_id:
            return jsonify({
                'success': True,
                'backtest_id': backtest_id,
                'message': '回测已完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': '回测执行失败'
            }), 500
            
    except Exception as e:
        logger.error(f"API /backtest/start 错误: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/<int:backtest_id>', methods=['GET'])
def api_backtest_get(backtest_id):
    """
    GET /api/backtest/:id
    获取回测结果
    """
    try:
        backtester = Backtester(use_ai=False)
        result = backtester.get_backtest_result(backtest_id)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': '回测记录不存在'}), 404
            
    except Exception as e:
        logger.error(f"API /backtest/{backtest_id} 错误: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/list', methods=['GET'])
def api_backtest_list():
    """
    GET /api/backtest/list
    获取所有回测记录列表
    """
    try:
        session = get_session()
        backtest_runs = session.query(BacktestRun).order_by(BacktestRun.created_at.desc()).all()
        
        results = [
            {
                'id': run.id,
                'symbol': run.symbol,
                'timeframe': run.timeframe,
                'start_date': run.start_date.isoformat(),
                'end_date': run.end_date.isoformat(),
                'created_at': run.created_at.isoformat(),
                'status': run.status,
                'total_signals': run.total_signals,
                'buy_signals': run.buy_signals,
                'sell_signals': run.sell_signals
            }
            for run in backtest_runs
        ]
        
        session.close()
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"API /backtest/list 错误: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET', 'PUT'])
def api_config():
    """
    GET/PUT /api/config
    获取或更新配置
    """
    if request.method == 'GET':
        try:
            return jsonify({
                'exchange': settings.EXCHANGE_ID,
                'symbols': settings.SYMBOLS,
                'timeframe': settings.TIMEFRAME,
                'indicators': {
                    'ema_period': settings.EMA_PERIOD,
                    'rsi_period': settings.RSI_PERIOD,
                    'macd_fast': settings.MACD_FAST,
                    'macd_slow': settings.MACD_SLOW,
                    'macd_signal': settings.MACD_SIGNAL
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'PUT':
        # TODO: 实现配置更新（需要持久化到文件）
        return jsonify({'error': '配置更新功能暂未实现'}), 501


if __name__ == '__main__':
    logger.info("启动 Heimdall API 服务...")
    logger.info("访问地址: http://localhost:5000")
    
    # 开发模式运行
    app.run(host='0.0.0.0', port=5000, debug=True)
