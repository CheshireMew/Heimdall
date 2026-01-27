
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
from core.market_provider import MarketProvider
from utils.logger import logger
from utils.time_manager import TimeManager
from config import settings

class DCACalculator:
    """
    定投 (Dollar Cost Averaging) 收益计算器
    模拟每天固定时间投入固定金额
    """
    
    def __init__(self):
        self.market_provider = MarketProvider()
        
    def calculate_dca(
        self, 
        symbol: str, 
        start_date_str: str, 
        end_date_str: str,
        daily_investment: float,
        target_time_str: str = "23:00",
        timezone: str = "Asia/Shanghai",
        strategy: str = "standard",
        strategy_params: Optional[Dict] = None
    ) -> Dict:
        """
        计算定投收益
        
        Args:
            symbol: 交易对 (e.g., 'BTC/USDT')
            start_date_str: 开始日期 (YYYY-MM-DD)
            end_date_str: 结束日期 (YYYY-MM-DD) or None (now)
            daily_investment: 每日定投金额 (USDT)
            target_time_str: 定投时间 (HH:MM), 用户本地时间
            timezone: 用户时区 (e.g., 'Asia/Shanghai')
            
        Returns:
            Dict: 模拟结果
        """
        try:
            # 0. 准备时区管理
            # 用户输入的 start_date_str 是本地日期的零点
            # 我们需要确定每一天的“定投时刻”在 UTC 是几点
            
            # 解析本地定投时间
            target_h, target_m = map(int, target_time_str.split(':'))
            
            # Use TimeManager to get current time logic
            now_local = TimeManager.get_now(timezone)
            
            # 1. 解析开始日期 (本地时间 00:00)
            start_dt_local = datetime.strptime(start_date_str, "%Y-%m-%d")
            # 构造第一笔定投的本地时间: start_date + target_time
            first_invest_local = start_dt_local.replace(hour=target_h, minute=target_m, second=0)
            
            # 转换 UTC，用于计算相对于 UTC 0点 的小时偏移，或者后续直接比较 timestamp
            # 但我们的 klines 数据是 UTC timestamp.
            # 最简单的方法：遍历每一天，构造当天的 Local Invest Time -> 转 UTC -> 找对应 K 线
            
            # 2. 解析结束日期
            if not end_date_str:
                end_dt_local = now_local.replace(tzinfo=None) # naive for comparison logic below if needed, or stick to aware
            else:
                end_dt_local = datetime.strptime(end_date_str, "%Y-%m-%d")
                if end_dt_local.date() == now_local.date():
                    end_dt_local = now_local.replace(tzinfo=None)
                else:
                    end_dt_local = end_dt_local.replace(hour=23, minute=59, second=59)
            
            logger.info(f"计算定投: {symbol}, 日投 {daily_investment}, {start_dt_local} - {end_dt_local} (Local), 时区 {timezone}")
            
            # 3. 确定数据获取范围 (UTC)
            # 为了确保覆盖 local start/end，我们多取前后 1 天 buffer + 200天指标 buffer
            buffer_days = 200
            fetch_start_date = start_dt_local - timedelta(days=buffer_days + 1)
            fetch_end_date = end_dt_local + timedelta(days=1)
            
            # 转换为 UTC 进行 fetch (MarketProvider 期望 naive UTC or aware UTC? explicitly passing aware is safer if provider handles it)
            # MarketProvider `fetch_ohlcv_range` expects datetime objects. 
            # Ideally we pass UTC datetimes.
            fetch_start_utc = TimeManager.convert_to_utc(fetch_start_date, timezone)
            fetch_end_utc = TimeManager.convert_to_utc(fetch_end_date, timezone)
            
            logger.info(f"下载数据 (UTC): {fetch_start_utc} - {fetch_end_utc}")
            klines = self.market_provider.fetch_ohlcv_range(symbol, '1h', fetch_start_utc, fetch_end_utc)
            
            if not klines:
                return {'error': '该时间段无数据'}
                
            # 2. DataFrame 处理
            all_df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            all_df['datetime'] = pd.to_datetime(all_df['timestamp'], unit='ms', utc=True)
            
            # Convert to user timezone for filtering
            # map to local
            tz_obj = TimeManager.get_timezone(timezone)
            all_df['local_dt'] = all_df['datetime'].dt.tz_convert(tz_obj)
            
            # --- 策略指标计算 (在完整数据上计算) ---
            # Resample to daily for consistent Indicator Calculation
            # Indicators are usually calculated on Daily Close
            # We can use the Local Daily Close or UTC Daily Close?
            # Standard crypto indicators are often UTC based, but let's stick to UTC for indicators to be consistent with standard charts.
            # So daily_df comes from 'datetime' (UTC)
            
            daily_df = all_df.set_index('datetime').resample('D').agg({'close': 'last'}).dropna()

            # 1. EMA20
            daily_df['ema20'] = daily_df['close'].ewm(span=20, adjust=False).mean()
            
            # 2. RSI 14
            delta = daily_df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            daily_df['rsi'] = 100 - (100 / (1 + rs))

            # 3. AHR999 (MA200 & Exp Price)
            daily_df['ma200'] = daily_df['close'].rolling(window=200).mean()
            
            genesis_date = datetime(2009, 1, 3)
            # Ensure age_days is calculated correctly for each row
            daily_df['age_days'] = (daily_df.index.tz_localize(None) - genesis_date).days
            
            # AHR999 Calculation
            import numpy as np
            daily_df = daily_df[daily_df['age_days'] > 0] 
            log_age = np.log10(daily_df['age_days'])
            daily_df['exp_price'] = 10 ** (5.84 * log_age - 17.01)
            daily_df['ahr999'] = (daily_df['close'] / daily_df['ma200']) * (daily_df['close'] / daily_df['exp_price'])

            # --- Merge Indicators back to 1h DataFrame ---
            # Join on UTC Date String
            daily_df['date_str'] = daily_df.index.strftime('%Y-%m-%d')
            all_df['date_str'] = all_df['datetime'].dt.strftime('%Y-%m-%d')
            
            all_df = pd.merge(all_df, daily_df[['date_str', 'ema20', 'rsi', 'ahr999']], on='date_str', how='left')

            # --- Slicing: Cut off the buffer period ---
            # Filter by Local Time Start Date
            # start_dt_local is aware (if we made it so) or naive.
            # Local Comparison:
            df = all_df[all_df['local_dt'] >= start_dt_local.replace(tzinfo=tz_obj)].copy()
            
            # 3. 筛选每日定投时刻 (Local Hour == Target Hour)
            # Use 'local_dt' to check hour
            target_klines = df[df['local_dt'].dt.hour == target_h].copy()
            
            # Since data is 1h, it matches the hour. 
            # If target_m != 0, we just pick the hour candle (approximation)? 
            # Or assume 1h candles mean XX:00. Yes.

            
            # --- 策略逻辑准备 ---
            # df['ema20'] = 0.0 # This line is no longer needed as indicators are pre-calculated
            # The following blocks are now redundant as calculations are done upfront
            # if strategy == 'ema_deviation':
            #      # 计算 EMA20 (基于 'close')
            #      # 注意：这里需要在原始 1h 数据上计算，还是在日线上计算？
            #      # 通常 EMA20 指的是日线 EMA20。
            #      # 我们先将数据重采样为日线来计算 EMA，然后 merge 回去，或者简单点，直接在 1h 数据上算长周期的 EMA (20*24=480) 近似？
            #      # 准确做法：重采样到日线 -> 计算 EMA20 -> 每日定投点取当日 EMA。
                 
            #      # Resample to daily to calculate proper Daily EMA20
            #      daily_df = df.set_index('datetime').resample('D').agg({'close': 'last'}).dropna()
            #      daily_df['ema20'] = daily_df['close'].ewm(span=20, adjust=False).mean()
                 
            #      # 将 ema20 映射回 target_klines (通过日期)
            #      target_klines['date_str'] = target_klines['datetime'].dt.strftime('%Y-%m-%d')
            #      daily_df['date_str'] = daily_df.index.strftime('%Y-%m-%d')
                 
            #      # Merge ema20
            #      target_klines = pd.merge(target_klines, daily_df[['date_str', 'ema20']], on='date_str', how='left')
            
            # 4. 模拟循环 (使用 enumerate 获得正确的相对天数)
            total_invested = 0.0
            total_coins = 0.0
            history = []
            
            # 策略参数
            ema_multiplier = strategy_params.get('multiplier', 3.0) if strategy_params else 3.0
            
            # 预加载数据 for Advanced Strategies
            sentiment_map = {}
            if strategy == 'fear_greed':
                from services.sentiment_service import sentiment_service
                sentiment_map = sentiment_service.get_sentiment_history(start_dt_local, end_dt_local)
            
            # RSI Dynamic Prep - REMOVED, now calculated upfront
            # if strategy == 'rsi_dynamic':
            #      # Calculate RSI 14 on daily data matches standard
            #      daily_df = df.set_index('datetime').resample('D').agg({'close': 'last'}).dropna()
            #      # Simple RSI calculation using pandas
            #      delta = daily_df['close'].diff()
            #      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            #      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            #      rs = gain / loss
            #      daily_df['rsi'] = 100 - (100 / (1 + rs))
                 
            #      target_klines['date_str'] = target_klines['datetime'].dt.strftime('%Y-%m-%d')
            #      daily_df['date_str'] = daily_df.index.strftime('%Y-%m-%d')
            #      target_klines = pd.merge(target_klines, daily_df[['date_str', 'rsi']], on='date_str', how='left')

            # AHR999 Prep (BTC Only roughly) - REMOVED, now calculated upfront
            # if strategy == 'ahr999':
            #      daily_df = df.set_index('datetime').resample('D').agg({'close': 'last'}).dropna()
            #      # AHR999 = (Price / 200 Day MA) * (Price / Exp Growth Valuation)
            #      # 简化版: 既然没有全量历史数据算准确的 200日均线 (如果查询范围不够长)，
            #      # 这里做一个近似：假设用户查询的时间段够长，或者简单使用 200日均线
            #      # Exp Growth: 10^ (5.84 * log(Age_Days) - 17.01) (常见拟合公式，Age=Days since 2009-01-03)
                 
            #      daily_df['ma200'] = daily_df['close'].rolling(window=200).mean()
                 
            #      genesis_date = datetime(2009, 1, 3)
            #      daily_df['age_days'] = (daily_df.index - genesis_date).days
                 
            #      import numpy as np
            #      # 拟合价格 (Log-Log Regression)
            #      # Coin value days: 5.84 * log(days) - 17.01 (This is a common fitting, adjust if needed)
            #      # Price = 10 ^ (2.68 * log10(age) - 1.18) ? There are many versions.
            #      # Let's use a standard AHR999 implementation reference:
            #      # AHR999 = (Price / 200MA) * (Price / (10^(5.84 * log10(age) - 17.01)))
                 
            #      log_age = np.log10(daily_df['age_days'])
            #      daily_df['exp_price'] = 10 ** (5.84 * log_age - 17.01)
                 
            #      daily_df['ahr999'] = (daily_df['close'] / daily_df['ma200']) * (daily_df['close'] / daily_df['exp_price'])
                 
            #      target_klines['date_str'] = target_klines['datetime'].dt.strftime('%Y-%m-%d')
            #      daily_df['date_str'] = daily_df.index.strftime('%Y-%m-%d')
            #      target_klines = pd.merge(target_klines, daily_df[['date_str', 'ahr999']], on='date_str', how='left')

            # Main Loop - use day_count for proper Value Averaging index
            for day_count, (index, row) in enumerate(target_klines.iterrows()):
                price = row['close']
                
                # --- 动态金额计算 ---
                current_investment = daily_investment
                multiplier = 1.0
                
                if strategy == 'ema_deviation':
                    ema_val = row['ema20']
                    if pd.notna(ema_val) and ema_val > 0:
                        factor = (ema_val - price) / ema_val
                        multiplier = 1 + (ema_multiplier * factor)
                
                elif strategy == 'rsi_dynamic':
                    rsi = row.get('rsi')
                    if pd.notna(rsi):
                        # Formula: 1 + Strength * (50 - RSI) / 50
                        # RSI < 50 => Multiplier > 1
                        multiplier = 1 + ema_multiplier * (50 - rsi) / 50
                
                elif strategy == 'ahr999':
                    ahr = row.get('ahr999')
                    if pd.notna(ahr) and ahr > 0:
                         # Formula: 1 / (AHR ^ Strength) ?? Or specific thresholds?
                         # User asked for "continuous", so let's use inverse.
                         # AHR=0.45 -> High invest. AHR=1.2 -> Low invest.
                         # Let's try: Multiplier = Base / (AHR)
                         # With strength: Multiplier = 1 / (AHR ^ (Strength/3)) ? 
                         # Let's stick to simplest inverse prop: Multiplier = 1 / AHR
                         # Applying user strength param as power:
                         # If strength=1, 1/AHR. If strength=0.5, 1/sqrt(AHR).
                         # Default strength 3 might be too aggressive for power. 
                         # Let's use: Multiplier = 1 + Strength * (0.8 - AHR) ? (0.8 is pivot)
                         # Let's use the Geometric Mean logic implied by AHR:
                         # AHR < 0.45抄底. Pivot at ~1.0? 
                         # Let's use: Multiplier = 1 / (AHR ** (ema_multiplier * 0.5))
                         multiplier = 1 / (ahr ** (ema_multiplier * 0.3))

                elif strategy == 'fear_greed':
                    date_str = row['datetime'].strftime('%Y-%m-%d')
                    fng_val = sentiment_map.get(date_str)
                    if fng_val is not None:
                        # Index 0-100. Lower is Fear (Buy).
                        # Formula: 1 + Strength * (50 - Index) / 50
                        multiplier = 1 + ema_multiplier * (50 - fng_val) / 50
                
                # --- Apply Multiplier or Value Averaging Logic ---
                
                if strategy == 'value_averaging':
                    # 固定市值法逻辑: 目标是每天增加 daily_investment 的市值
                    # Target Value for Today = (Index + 1) * Daily_Increment
                    # Current Value = Total Coins * Current Price
                    # Action = Target - Current
                    
                    target_total_value = (day_count + 1) * daily_investment
                    current_holdings_value = total_coins * price
                    
                    # 需要投入的资金 (如果是负数，表示需要卖出)
                    current_investment = target_total_value - current_holdings_value
                    
                    # 限制: 不能卖出超过持有的币
                    if current_investment < 0:
                        amount_to_sell = abs(current_investment)
                        # 最多卖出所有持仓的价值
                        max_sell_value = current_holdings_value
                        if amount_to_sell > max_sell_value:
                            current_investment = -max_sell_value
                    
                    # 限制: 最大单次买入上限 (防止深熊无底洞)
                    # 传统 VA 策略通常设置上限，例如每日定投额的 5-10 倍
                    # 这里设置为 10 倍，既保留激进补仓特性，又避免天价账单
                    elif current_investment > 0:
                         max_buy_cap = daily_investment * 10
                         if current_investment > max_buy_cap:
                             logger.info(f"触发熔断: 理论需投 {current_investment}, 限制为 {max_buy_cap}")
                             current_investment = max_buy_cap
                            
                else:
                    # 其他定投策略 (Multiplier based)
                    if strategy != 'standard':
                        current_investment = daily_investment * multiplier

                    # 安全边界 (仅针对定投类策略，VA策略自带逻辑)
                    # 下限: 0
                    if current_investment < 0:
                        current_investment = 0
                    # 上限: 5倍
                    max_cap = daily_investment * 5
                    if current_investment > max_cap:
                        current_investment = max_cap

                # Execute Buy/Sell
                # current_investment > 0 : Buy
                # current_investment < 0 : Sell
                
                coins_change = current_investment / price
                
                total_invested += current_investment # Cash flow adjustment
                total_coins += coins_change
                
                # Precision fix
                if total_coins < 1e-8: 
                    total_coins = 0.0
                
                current_value = total_coins * price
                if total_invested > 0:
                    roi_percent = ((current_value - total_invested) / total_invested) * 100
                else:
                    roi_percent = 0.0 # Avoid ZeroDivisionError when principal is withdrawn
                avg_cost = total_invested / total_coins if total_coins > 0 else 0
                
                history.append({
                    'date': row['datetime'].strftime('%Y-%m-%d'),
                    'price': price,
                    'invested': round(total_invested, 2),
                    'value': round(current_value, 2),
                    'coins': round(total_coins, 6),
                    'roi': round(roi_percent, 2),
                    'avg_cost': round(avg_cost, 2)
                })
                
            if not history:
                return {'error': '无符合时间的数据点 (可能数据太短)'}
                
            # 5. Mark-to-Market: 使用当前实时价格计算最终价值
            # 即使最后一次定投是在昨天，除此之外持有的资产价值也应该按当前价格计算
            try:
                # 获取最新 1m 价格作为当前价格
                latest_kline = self.market_provider.get_kline_data(symbol, '1m', limit=1)
                if latest_kline:
                    current_price = latest_kline[-1][4] # close price
                else:
                    current_price = history[-1]['price']
            except Exception as e:
                logger.warning(f"无法获取实时价格，降级使用最后一次定投价格: {e}")
                current_price = history[-1]['price']

            final_value = total_coins * current_price
            profit_loss = final_value - total_invested
            roi_percent = (profit_loss / total_invested) * 100 if total_invested > 0 else 0

            return {
                'symbol': symbol,
                'start_date': start_date_str,
                'end_date': end_dt_local.strftime('%Y-%m-%d'),
                'target_time': target_time_str,
                'total_days': len(history),
                'total_invested': round(total_invested, 2),
                'final_value': round(final_value, 2),
                'total_coins': round(total_coins, 6),
                'roi': round(roi_percent, 2),
                'average_cost': round(history[-1]['avg_cost'], 2),
                'profit_loss': round(profit_loss, 2),
                'current_price': current_price,
                'history': history,
            }
            
        except Exception as e:
            logger.error(f"DCA Error: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

if __name__ == '__main__':
    # Test
    calc = DCACalculator()
    end = datetime.now()
    start = end - timedelta(days=365) # 1 year
    res = calc.calculate_dca('BTC/USDT', start, end, 100)
    if 'error' not in res:
        print(f"Invested: {res['total_invested']}, Value: {res['final_value']}, ROI: {res['roi_percent']}%")
    else:
        print(res['error'])
