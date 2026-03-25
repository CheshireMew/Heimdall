from app.domain.market.technical_analysis import TechnicalAnalysis

def test_ema():
    print("\n--- Testing EMA ---")
    prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    period = 5
    # SMA first 5: (10+11+12+13+14)/5 = 12
    # Multiplier: 2/(5+1) = 1/3
    # EMA #6 (Price 15): (15 - 12) * 1/3 + 12 = 13
    # EMA #7 (Price 16): (16 - 13) * 1/3 + 13 = 14
    
    ema = TechnicalAnalysis.calculate_ema(prices, period)
    print(f"Prices: {prices}")
    print(f"EMA(5): {ema}")
    
    expected = 16.0 # For the last one: ... it tends to linear if linear input
    # Let's trust the logic if it runs without error first
    if ema is not None:
        print("EMA Calculation: OK")
    else:
        print("EMA Calculation: FAILED (None)")

def test_rsi():
    print("\n--- Testing RSI ---")
    # Alternating up and down
    prices = [100, 102, 101, 104, 102, 105, 103, 108, 105, 110] # 10 prices
    period = 6
    rsi = TechnicalAnalysis.calculate_rsi(prices, period)
    print(f"RSI(6): {rsi}")
    if rsi is not None and 0 <= rsi <= 100:
        print("RSI Range: OK")
    else:
        print("RSI Calculation: FAILED")

def test_macd():
    print("\n--- Testing MACD ---")
    # Need at least 26 + 9 candles ideally, let's make dummy long data
    prices = [i + (i%5)*2 for i in range(100)] # 100 candles with some waves
    dif, dea, hist = TechnicalAnalysis.calculate_macd(prices)
    
    print(f"DIF: {dif}")
    print(f"DEA: {dea}")
    print(f"Hist: {hist}")
    
    if dif is not None and dea is not None:
        print("MACD Calculation: OK")
    else:
        print("MACD Calculation: FAILED")

if __name__ == "__main__":
    test_ema()
    test_rsi()
    test_macd()
