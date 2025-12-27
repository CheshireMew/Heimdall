# Heimdall Project Documentation

## 1. 项目概述
**Heimdall** —— 北欧神话中的光之神,拥有千里眼和顺风耳,守护彩虹桥并预知未来。

本项目旨在创建一个由 AI 驱动的加密货币交易智能投顾工具。它如同 Heimdall 一般,通过读取实时的 K 线数据,利用技术指标进行深度分析,并结合 AI 大模型（如 DeepSeek）发现交易机会并提醒用户。

**核心定位**: 智能投顾/机会发现 (Signal Discovery)
**非目标**: 自动下单/高频交易 (Auto Trading)

## 2. 核心原则
- **简洁至上 (KISS)**: 保持代码简单，易于维护。
- **高内聚、低耦合**: 模块职责分明，相互独立。
- **渐进式开发**: 从核心功能开始，逐步扩展。

## 3. 系统架构与目录结构

项目位于 `e:\Work\Code\AI-Trading\AI-Guide\`，采用模块化设计。

```text
AI-Guide/
│
├── config/
│   ├── __init__.py
│   └── settings.py          # [配置层] 
│       # 作用: 集中管理 交易对(Symbols)、K线周期(Timeframe)、AI 模型参数等。
│       # 目的: 将变化与代码逻辑分离。
│
├── core/
│   ├── __init__.py
│   ├── market_provider.py   # [数据层] 
│       # 核心库: ccxt (Public API)
│       # 作用: 负责通过 CCXT 获取各大交易所(Binance/OKX)的实时 OHLCV 数据。
│       # 费用: 免费 (Public API)。
│   ├── technical_analysis.py # [计算层] 
│       # 作用: 接收 K 线数据，计算 EMA, MACD, RSI, ATR 等核心指标。
│       # 算法: 移植自 nofx-dev (Go) 的轻量级实现。
│   └── prompt_engine.py     # [逻辑层] 
│       # 作用: 将市场数据和技术指标转化为 AI 可理解的自然语言 Prompt。
│       # 参考: AI-Trading-Bot 的 promptBuilderService。
│
├── services/
│   ├── __init__.py
│   └── llm_client.py        # [服务层] 
│       # 作用: 封装 Internet 请求，与 DeepSeek API 进行交互，让 AI 识别机会。
│       # 职责: 仅负责"思考"和"建议"，不负责"操作资金"。
│
├── utils/
│   ├── __init__.py
│   └── logger.py            # [工具层] 
│       # 作用: 提供统一的日志格式，方便调试和记录运行状态。
│
├── test/
│   └── run_tests.py         # [测试] 
│       # 作用: 包含由于测试各个模块独立功能的脚本。
│
├── main.py                  # [入口] 
│       # 作用: 程序的编排者。Loop: Get Data -> Calc Indicators -> AI Analyze -> Alert User。
│
└── PROJECT_DOCUMENTATION.md # [文档] 
        # 作用: 本文件。
```

## 4. 技术选型
- **语言**: Python
- **数据源**: `ccxt` (开源免费的加密货币交易库，使用 Public API)
- **AI 模型**: DeepSeek (OpenAI Compatible API)
- **数据处理**: 纯 Python 实现 (参考 Go 版本的轻量级无依赖实现)

## 5. 开发路线图
- [x] **Phase 1: 基础建设**
    - [x] 建立项目文档与架构规划
    - [ ] 初始化目录结构与基础模块 (config, utils)
- [ ] **Phase 2: 核心功能**
    - [ ] 实现 `market_provider` (CCXT 集成)
    - [ ] 实现 `technical_analysis` (指标计算)
- [ ] **Phase 3: AI 集成**
    - [ ] 实现 `llm_client` (DeepSeek 接入)
    - [ ] 实现 `prompt_engine` (提示词工程)
- [ ] **Phase 4: 整合与交付**
    - [ ] 编写 `main.py` (主循环与提醒)
    - [ ] 完整联调测试

## 6. 更新日志
- **2025-12-27**: 
  - 初始化项目文档,定义架构与目录树
  - 项目正式命名为 **Heimdall** (海姆达尔) —— 寓意全天候守护、洞察市场机会的智能投顾
  - 完成 Phase 4 核心交付物：
    - ✅ 创建 `requirements.txt` - Python 依赖管理
    - ✅ 创建 `.env.example` - 环境变量配置模板
    - ✅ 创建 `README.md` - 完整项目文档（安装、配置、使用指南）
    - ✅ 增强 `config/settings.py` - 支持 python-dotenv 环境变量加载
    - ✅ 创建 `test/test_e2e.py` - 端到端测试
  - 测试验证通过：
    - ✅ `test_market_provider.py` - 成功获取 Binance BTC/USDT 数据
    - ✅ `test_e2e.py` - 完整流程测试通过（数据→指标→Prompt→AI）
