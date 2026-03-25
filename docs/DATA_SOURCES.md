# 数据源解决方案汇总

## 🎯 推荐方案对比

| 数据源 | 成本 | 限流 | 稳定性 | 数据质量 | 推荐度 |
|--------|------|------|--------|----------|--------|
| **FRED API** | 🟢 免费 | 🟢 无限制 | 🟢 极高 | 🟢 官方数据 | ⭐⭐⭐⭐⭐ |
| Alpha Vantage | 🟢 免费 | 🟡 5次/分钟 | 🟢 高 | 🟢 可靠 | ⭐⭐⭐⭐ |
| YFinance | 🟢 免费 | 🔴 严格限流 | 🟡 中等 | 🟡 一般 | ⭐⭐⭐ |
| Binance PAXG | 🟢 免费 | 🟢 宽松 | 🟢 高 | 🟢 实时 | ⭐⭐⭐⭐ |

---

## 📝 快速设置指南

### 1️⃣ FRED API（最推荐，30秒搞定）

**获取 API Key：**
1. 访问：https://fred.stlouisfed.org/
2. 点击右上角 "My Account" → "API Keys"
3. 点击 "Request API Key"
4. 填写简单信息（邮箱、用途）
5. 立即获得 API Key

**配置：**
```bash
# .env 文件添加
FRED_API_KEY=your_fred_api_key_here
```

**可用数据：**
- ✅ US10Y (10年期美债) - Series: DGS10
- ✅ FEDFUNDS (联邦基金利率) - Series: DFF
- ✅ M2 (货币供应量) - Series: M2SL
- ✅ CPI (通胀指数) - Series: CPIAUCSL
- ✅ 高收益债利差 - Series: BAMLH0A0HYM2
- ✅ 10000+ 其他经济指标

**优势：**
- 🚀 无限请求，无需延迟
- 📊 美联储官方数据，最权威
- 🔄 自动更新，每日维护
- 📖 文档完善：https://fred.stlouisfed.org/docs/api/

---

### 2️⃣ Alpha Vantage（备用方案）

**获取 API Key：**
1. 访问：https://www.alphavantage.co/support/#api-key
2. 填写邮箱，点击 "GET FREE API KEY"
3. 立即收到 API Key

**配置：**
```bash
# .env 文件添加
ALPHA_VANTAGE_API_KEY=your_av_api_key_here
```

**限制：**
- 免费层：5次请求/分钟，500次/天
- 付费层：$50/月 = 无限制

**可用数据：**
- ✅ 美股指数（NASDAQ, S&P500）
- ✅ 外汇汇率
- ✅ 数字货币价格
- ✅ 技术指标

---

### 3️⃣ YFinance 优化（无需注册）

**已优化项：**
- ✅ 添加 User-Agent 伪装
- ✅ 使用 Session 复用连接
- ✅ 串行请求 + 2秒延迟
- ✅ 自动降级重试

**适用场景：**
- 仅作为最后降级方案
- 偶尔获取数据OK，频繁使用会被封

---

### 4️⃣ Binance PAXG（黄金价格）

**无需配置！**
- ✅ 使用现有 ccxt 库
- ✅ PAXG = 实物黄金锚定币
- ✅ 1 PAXG = 1 盎司黄金
- ✅ 实时价格，无延迟

---

## 🔧 实施步骤

### Step 1: 申请 FRED API Key
```bash
# 1. 访问 https://fred.stlouisfed.org/
# 2. 注册账号并申请 API Key
# 3. 添加到 .env 文件
echo "FRED_API_KEY=abcdef123456" >> .env
```

### Step 2: 更新 Cron Job
```bash
# 编辑 app/services/market_cron.py
# 将 MacroProvider 替换为 MacroProviderV2
```

### Step 3: 测试数据获取
```bash
cd E:\Work\Code\Heimdall
python app/services/indicators/macro_provider_v2.py
```

### Step 4: 运行完整 Cron Job
```bash
python app/services/market_cron.py
```

---

## 📊 数据源映射表

| 指标 | FRED Series ID | YF Ticker | Binance Symbol |
|------|---------------|-----------|----------------|
| 10年期美债 | DGS10 | ^TNX | - |
| 纳斯达克 | - | ^IXIC | - |
| 黄金价格 | - | GC=F | PAXG/USDT |
| 联邦基金利率 | DFF | - | - |
| M2货币供应 | M2SL | - | - |
| 高收益债利差 | BAMLH0A0HYM2 | - | - |

---

## 🧪 测试脚本

运行测试：
```bash
# 测试 FRED API
python -c "
from app.services.indicators.macro_provider_v2 import MacroProviderV2
import asyncio
async def test():
    p = MacroProviderV2()
    data = await p.fetch_data()
    print(f'Fetched {len(data)} indicators')
    for d in data:
        print(f'  {d[\"indicator_id\"]}: {d[\"value\"]}')
asyncio.run(test())
"

# 测试 Binance Gold
python app/services/indicators/crypto_gold_provider.py
```

---

## ✅ 最终推荐

**生产环境配置：**
1. **主要数据源：FRED API**（美债、利率、货币供应）
2. **备用数据源：Binance**（黄金通过PAXG）
3. **降级方案：YFinance**（纳斯达克等指数）

**预期效果：**
- 🚀 0限流问题
- 📊 数据更权威
- 💰 完全免费
- ⚡ 实时更新
