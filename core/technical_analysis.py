import math
from utils.logger import logger

class TechnicalAnalysis:
    @staticmethod
    def calculate_ema(prices, period):
        """
        计算指数移动平均线 (EMA)
        Reference: nofx-dev/market/data.go calculateEMA
        """
        if len(prices) < period:
            return None

        # 1. Calculate SMA as initial EMA
        initial_sma = sum(prices[:period]) / period
        
        # 2. Calculate multiplier
        multiplier = 2.0 / (period + 1)
        
        ema = initial_sma
        
        # 3. Calculate EMA for the rest
        for i in range(period, len(prices)):
            ema = (prices[i] - ema) * multiplier + ema
            
        return ema

    @staticmethod
    def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
        """
        计算 MACD
        Reference: nofx-dev/market/data.go calculateMACD
        Returns: (dif, dea, macd_hist)
        """
        if len(prices) < slow_period:
            return None, None, None

        # Helper to get EMA series (not just last value)
        def get_ema_series(data, period):
            if len(data) < period:
                return []
            
            ema_series = []
            # Initial SMA
            current_ema = sum(data[:period]) / period
            # We align series to end of data, so first (period-1) are None or skipped.
            # Here we just return the valid EMAs starting from index 'period-1'
            
            # Re-calculating properly to return a list aligned with `prices`
            # But to keep it simple and efficient for just the *latest* MACD:
            # We need the full series for the Signal line (DEA) calculation.
            
            multiplier = 2.0 / (period + 1)
            
            # Pre-pad with None or handle alignment. Let's return list of valid EMAs.
            valid_emas = [current_ema]
            
            for i in range(period, len(data)):
                current_ema = (data[i] - current_ema) * multiplier + current_ema
                valid_emas.append(current_ema)
                
            return valid_emas

        # 1. Get Fast and Slow EMA series
        # Note: The series lengths will differ. fast_emas will be longer than slow_emas.
        # fast_emas starts at index `fast_period-1` of prices
        # slow_emas starts at index `slow_period-1` of prices
        fast_emas_valid = get_ema_series(prices, fast_period)
        slow_emas_valid = get_ema_series(prices, slow_period)
        
        if not fast_emas_valid or not slow_emas_valid:
            return None, None, None
            
        # Align them to the end (Latest values match). 
        # The DIF is Fast - Slow. We can only calc DIF where both exist.
        # Both end at the same real-time point.
        # Slow EMA defines the start point of valid MACD.
        
        # Determine overlap length
        overlap = len(slow_emas_valid)
        
        # Fast EMAs relevant slice (last `overlap` items)
        fast_emas_aligned = fast_emas_valid[-overlap:]
        
        # DIF Series
        dif_series = [f - s for f, s in zip(fast_emas_aligned, slow_emas_valid)]
        
        # 2. Key: The last value is the Current DIF
        current_dif = dif_series[-1]
        
        # 3. DEA (Signal Line) is EMA of DIF
        # We need enough DIF history to calculate DEA
        if len(dif_series) < signal_period:
            return current_dif, None, None
            
        current_dea = TechnicalAnalysis.calculate_ema(dif_series, signal_period)
        
        # 4. MACD Histogram
        macd_hist = current_dif - current_dea
        
        return current_dif, current_dea, macd_hist

    @staticmethod
    def calculate_rsi(prices, period=14):
        """
        计算 RSI (Relative Strength Index)
        Reference: nofx-dev/market/data.go calculateRSI (Wilder's Smoothing)
        """
        if len(prices) <= period:
            return None

        gains = 0.0
        losses = 0.0

        # 1. Initial Avg Gain/Loss for the first period
        for i in range(1, period + 1):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains += change
            else:
                losses += abs(change)

        avg_gain = gains / period
        avg_loss = losses / period

        # 2. Wilder's Smoothing for the rest
        for i in range(period + 1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                avg_gain = (avg_gain * (period - 1) + change) / period
                avg_loss = (avg_loss * (period - 1)) / period
            else:
                avg_gain = (avg_gain * (period - 1)) / period
                avg_loss = (avg_loss * (period - 1) + abs(change)) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi

    @staticmethod
    def calculate_atr(highs, lows, closes, period=14):
        """
        计算 ATR (Average True Range)
        Reference: nofx-dev/market/data.go calculateATR
        """
        if len(closes) <= period:
            return None

        # 1. Calculate TR series
        trs = [0.0] * len(closes)
        # TR for i=0 is undefined or just H-L, but usually we ignore first or start from i=1
        
        for i in range(1, len(closes)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            trs[i] = max(tr1, max(tr2, tr3))

        # 2. Initial ATR (Simple Average of first `period` TRs, starting index 1 to period)
        # Note: nofx-dev calculates sum from i=1 to period.
        current_atr = sum(trs[1:period+1]) / period
        
        # 3. Wilder's Smoothing
        for i in range(period + 1, len(closes)):
            current_atr = (current_atr * (period - 1) + trs[i]) / period
            
        return current_atr

    @staticmethod
    def analyze_trend(price, ema20):
        """简单的趋势判断"""
        if price > ema20:
            return "Bullish (价格在 EMA20 之上)"
        else:
            return "Bearish (价格在 EMA20 之下)"
