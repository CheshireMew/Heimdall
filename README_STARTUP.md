# 🚀 Heimdall 快速启动指南

## ⚡ 一键启动（最简单）

### Windows
```bash
cd E:\Work\Code\Heimdall
scripts\start.bat
```

这个脚本会：
1. 启动后端 (FastAPI) - http://localhost:5001
2. 启动前端 (Vue) - http://localhost:5173
3. 自动打开浏览器

### 停止服务
```bash
scripts\stop.bat
```

---

## 📝 手动启动（如果脚本不工作）

### 终端 1 - 启动后端

```bash
cd E:\Work\Code\Heimdall
python -m uvicorn app.main:app --reload --port 5001
```

**预期输出：**
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5001
```

**验证后端：**
- 打开浏览器访问: http://localhost:5001/docs
- 应该看到 FastAPI 自动生成的 API 文档

---

### 终端 2 - 启动前端

**新开一个终端：**
```bash
cd E:\Work\Code\Heimdall\frontend
npm run dev
```

**预期输出：**
```
VITE v7.2.4  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**验证前端：**
- 自动打开浏览器或手动访问: http://localhost:5173
- 应该看到 Heimdall 界面

---

## 🎯 验证市场指标系统

启动成功后，访问 http://localhost:5173

### Dashboard 页面应该显示：

#### 1. **市场指标区域** (顶部)
```
🌐 Macro & On-chain Indicators

┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│  US10Y         │ │  FEAR_GREED    │ │  STABLECOIN    │ │  HASHRATE      │
│  4.04%         │ │  11 (Extreme   │ │  3089亿 USD    │ │  xxxxx EH/s    │
│  [趋势图]      │ │   Fear)        │ │  [趋势图]      │ │  [趋势图]      │
└────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
```

#### 2. **K线图表区域** (底部)
- BTC/USDT 实时图表
- 时间周期切换 (5m, 15m, 1h, 4h, 1d, 1w, 1M)
- 无限滚动加载历史数据

---

## 🔍 故障排查

### 问题1: 端口被占用

**症状：**
```
Error: listen EADDRINUSE: address already in use :::5001
```

**解决：**
```bash
# Windows
netstat -ano | findstr :5001
taskkill /PID <进程ID> /F

netstat -ano | findstr :5173
taskkill /PID <进程ID> /F
```

---

### 问题2: 数据库连接失败

**症状：**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决：**
```bash
# 检查 PostgreSQL 是否运行
# Windows: 服务管理器中查看 postgresql 服务

# 验证连接
psql -h localhost -U postgres -d heimdall
```

---

### 问题3: 前端 API 请求 404

**症状：**
浏览器控制台显示:
```
GET http://localhost:5173/api/v1/indicators 404 (Not Found)
```

**原因：** 后端未启动或端口不对

**解决：**
1. 确认后端运行在 5001 端口
2. 访问 http://localhost:5001/health 验证
3. 查看后端终端的日志

---

### 问题4: 指标数据为空

**症状：**
Dashboard 显示 "Waiting for background cron job..."

**原因：** 数据库中还没有数据

**解决：**
```bash
# 手动运行一次数据采集
python -m app.services.market_cron

# 验证数据
python -m scripts.check_indicators
```

---

## 📊 端口说明

| 服务 | 端口 | 用途 | 访问地址 |
|------|------|------|----------|
| 后端 FastAPI | 5001 | API 服务 | http://localhost:5001 |
| 前端 Vite | 5173 | Web 界面 | http://localhost:5173 |
| PostgreSQL | 5432 | 数据库 | localhost:5432 |
| Redis | 6379 | 缓存 | localhost:6379 |

---

## 🎨 界面预览

访问 http://localhost:5173 后，你应该看到：

```
┌─────────────────────────────────────────────────────────────┐
│  Heimdall                                          [🌙 Dark] │
├──────────┬──────────────────────────────────────────────────┤
│          │  🌐 Macro & On-chain Indicators                  │
│ 📊 实时  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│   分析   │  │US10Y │ │ F&G  │ │STABLE│ │ HASH │            │
│          │  │ 4.04%│ │  11  │ │3089B │ │ .... │            │
│ 🧪 回测  │  └──────┘ └──────┘ └──────┘ └──────┘            │
│   中心   │                                                  │
│          │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ ⚖️ 币种  │  BTC/USDT  [5m 15m 1h 4h 1d 1w 1M]             │
│   对比   │  ┌────────────────────────────────────────────┐ │
│          │  │                                            │ │
│ 💰 DCA   │  │        📈 K线图表                          │ │
│   模拟   │  │                                            │ │
│          │  │                                            │ │
│ 🕐 减半  │  └────────────────────────────────────────────┘ │
│   周期   │                                                  │
│          │                                                  │
│ ⚙️ 配置  │                                                  │
│   中心   │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

---

## ✅ 启动检查清单

启动前：
- [ ] PostgreSQL 运行中
- [ ] .env 配置正确（FRED_API_KEY 已设置）
- [ ] Python 依赖已安装
- [ ] Node.js 依赖已安装
- [ ] 端口 5001 和 5173 空闲

启动后：
- [ ] 后端响应 http://localhost:5001/health
- [ ] 前端页面 http://localhost:5173 可访问
- [ ] Dashboard 显示市场指标
- [ ] K线图表正常加载
- [ ] 浏览器控制台无错误

---

## 🎉 现在就开始！

**最简单的方式：**
```bash
cd E:\Work\Code\Heimdall
scripts\start.bat
```

然后等待浏览器自动打开到 http://localhost:5173

**查看你的市场指标数据！** 📊

---

需要帮助？查看：
- 详细启动文档: `docs/STARTUP_GUIDE.md`
- FRED配置成功报告: `docs/FRED_CONFIGURATION_SUCCESS.md`
