# Heimdall 🛡️

> **海姆达尔** —— 北欧神话中的光之神，拥有千里眼和顺风耳，守护彩虹桥并预知未来。

**Heimdall** 是一个基于 AI 的加密货币交易智能投顾工具。它如同神话中的守护者一般，全天候监控市场，通过技术分析和 AI 深度学习发现潜在的交易机会，并及时提醒你。

## ✨ 核心特性

- 🔍 **智能发现** - 通过可配置的大模型分析市场趋势和技术指标
- 📊 **多维度分析** - 支持 EMA、MACD、RSI、ATR 等核心技术指标
- 🌐 **多交易所支持** - 基于 [CCXT](https://github.com/ccxt/ccxt)，支持 Binance、OKX、Bybit 等主流交易所
- 🎯 **非自动交易** - 专注于"机会发现"和"投资建议"，不涉及自动下单
- 🧩 **模块化设计** - 高内聚、低耦合，易于扩展和维护
- 📊 **回测与模拟盘** - 支持策略回测、因子研究和纸面运行

## 🚫 非目标

- ❌ 不是自动交易机器人（No Auto Trading）
- ❌ 不是高频交易系统（No HFT）
- ❌ 不保证盈利（DYOR - Do Your Own Research）

## 启动

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

cd frontend
npm run dev

构建前端后，后端会直接托管 `frontend/dist`，生产环境只保留这一套入口。

## 📦 安装

### 1. 环境要求

- Python 3.12.x
- pip
- Node.js / npm
- 项目依赖边界固定为 `freqtrade==2026.3` + `TA-Lib==0.6.8`。

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd Heimdall
```

### 3. 安装依赖

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\venv\Scripts\python.exe -m pip install -r requirements.txt

cd frontend
npm ci
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写你的模型服务 API Key
# DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

> **获取 DeepSeek API Key**: 访问 [DeepSeek Platform](https://platform.deepseek.com/api_keys) 注册并创建 API Key

### 5. 初始化数据库

```bash
python scripts/prepare_db.py
```

数据库结构由 Alembic 管理。`DATABASE_URL` 是唯一数据库入口；服务器部署请配置 PostgreSQL 连接串，例如 `postgresql://user:password@host:5432/heimdall`。发现未配置数据库或未迁移结构会直接报错，避免运行时继续写入错误数据库或错误表结构。

## 🚀 快速开始

### 测试数据获取

```bash
python test/test_market_data_service.py
```

验证是否能成功从交易所获取 K 线数据。

### 测试技术指标计算

```bash
python test/test_technical_analysis.py
```

验证 EMA、MACD、RSI、ATR 等指标计算是否正确。

### 启动 Web Dashboard 📊

Heimdall 提供了一个现代化的 Web 界面，基于 **FastAPI** 构建，用于实时市场监控和策略回测。

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问: [http://localhost:8000](http://localhost:8000)

**API文档**（自动生成）:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

包含功能：

- **实时分析**: 查看实时价格、指标 (EMA/RSI/MACD) 和 AI 建议
- **币种对比**: 专业K线对比工具，支持多周期切换和三图联动
- **DCA模拟器**: 定投回测分析工具
- **回测中心**: 可视化运行历史回测，无需写代码
- **策略编辑器**: 使用统一策略 contract 编辑指标、规则、风控和交易计划
- **因子研究**: 构建、回测和运行因子组合
- **配置管理**: 界面化查看系统参数

## ⚙️ 配置说明

### 修改监控的交易对

编辑 `config/settings.py`：

```python
SYMBOLS = [
    'BTC/USDT',
    'ETH/USDT',
    'SOL/USDT',
    'DOGE/USDT',  # 添加更多交易对
]
```

### 修改 K 线周期

```python
TIMEFRAME = '1h'  # 可选: '1m', '5m', '15m', '1h', '4h', '1d'
```

### 修改技术指标参数

```python
EMA_PERIOD = 20      # EMA 周期
RSI_PERIOD = 14      # RSI 周期
MACD_FAST = 12       # MACD 快线
MACD_SLOW = 26       # MACD 慢线
MACD_SIGNAL = 9      # MACD 信号线
```

### 切换交易所

```python
EXCHANGE_ID = 'binance'  # 可选: 'okx', 'bybit', 'gate' 等 CCXT 支持的交易所
```

## 📂 项目结构

```
Heimdall/
├── app/                     # FastAPI 后端应用
│   ├── main.py              # FastAPI 入口
│   ├── routers/             # HTTP 路由入口
│   ├── services/            # 应用服务层
│   ├── domain/              # 纯业务规则与指标计算
│   ├── infra/               # 数据库、缓存、外部服务
│   └── schemas/             # 请求/响应 contract，前端类型从这里生成
├── config/
│   └── settings.py          # 全局配置
├── frontend/                # Vue + Vite 前端工程
│   ├── src/                 # 前端源码
│   │   ├── views/           # 页面层
│   │   ├── modules/         # 功能模块层
│   │   ├── api/             # API 访问层
│   │   └── components/      # 复用组件
│   └── dist/                # 构建产物（由后端托管）
├── utils/
│   └── logger.py            # 日志工具
├── test/                    # 测试套件
│   └── ...
├── requirements.txt         # Python 依赖
├── alembic/                 # 数据库迁移
└── .env.example             # 环境变量模板
```

## 🧪 测试

### 单元测试

```bash
pytest
```

### 前端契约与构建

```bash
cd frontend
npm run sync:contracts
npm run typecheck
npm run build
```

`frontend/src/types/backtest.ts`、`factor.ts`、`market.ts`、`tools.ts`、`config.ts` 都由后端 Pydantic schema 生成，不要手写修改。

## 🔧 高级功能

- [x] 历史数据回测 (Backtest)
- [x] Web Dashboard 可视化界面
- [x] 策略编辑器
- [x] 因子研究
- [x] 纸面运行
- [x] 后台任务运行时
- [ ] 多渠道通知（邮件 / Telegram / 企业微信）

## ❓ FAQ

### 1. 如何配置模型 API Key？

默认可以使用 DeepSeek，也可以在设置页切换到其他预设或自定义模型服务。API Key 可以写入 `.env`，也可以在界面配置。

### 2. 支持哪些交易所？

理论上支持所有 [CCXT](https://github.com/ccxt/ccxt) 支持的交易所（200+ 个），常用的有：

- Binance
- OKX
- Bybit
- Gate.io
- Coinbase
- Kraken

### 3. 可以添加自定义技术指标吗？

可以！在 [app/domain/market/technical_analysis.py](E:/Work/Code/Heimdall/app/domain/market/technical_analysis.py) 中添加新的静态方法即可，参考现有的 `calculate_ema` 等实现。

### 4. AI 分析准确吗？

AI 仅提供参考建议，不保证准确性。**加密货币投资有风险，请谨慎决策，自行承担风险。**

### 5. 程序会自动下单吗？

**不会**。Heimdall 的定位是"智能投顾"，只负责发现机会和提供建议，不涉及资金操作。

### 6. 如何让程序持续运行？

可以使用以下方式：

- **Linux/macOS**: `crontab` 定时任务
- **Windows**: 任务计划程序
- **应用后台运行时**: 启动后恢复模拟盘和行情快照任务
- **Docker**: 容器化部署（规划中）

## ⚖️ 免责声明

本项目仅供学习和研究使用。加密货币市场波动剧烈，投资有风险。使用本工具产生的任何投资决策及其后果，由用户自行承担。开发者不对任何资金损失负责。

**请务必理性投资，切勿盲目跟单。**

## 📄 许可

MIT License

---

**Built with ❤️ by Heimdall Team**
