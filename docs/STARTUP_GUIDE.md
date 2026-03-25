# Heimdall 启动指南

## 🚀 快速启动（推荐）

使用启动脚本同时启动前后端：

### Windows
```bash
scripts\start.bat
```

### Linux/Mac
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

---

## 📋 手动启动（分步骤）

### Step 1: 启动后端 (FastAPI)

**新建终端 1:**
```bash
cd E:\Work\Code\Heimdall

# 激活虚拟环境（如果有）
# venv\Scripts\activate

# 启动后端
python -m uvicorn app.main:app --reload --port 5001
```

**后端地址:**
- API: http://localhost:5001
- API文档: http://localhost:5001/docs
- 健康检查: http://localhost:5001/health

---

### Step 2: 启动前端 (Vue + Vite)

**新建终端 2:**
```bash
cd E:\Work\Code\Heimdall\frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

**前端地址:**
- 应用: http://localhost:5173

---

## 🔧 配置说明

### 端口配置

| 服务 | 端口 | 配置文件 |
|------|------|----------|
| 后端 FastAPI | 5001 | `app/main.py` |
| 前端 Vite | 5173 | `frontend/vite.config.js` |

### API 代理

前端通过 Vite 代理转发 API 请求：
```javascript
// frontend/vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5001',  // 后端地址
      changeOrigin: true
    }
  }
}
```

---

## ✅ 验证启动

### 1. 后端验证
```bash
# 测试健康检查
curl http://localhost:5001/health

# 预期输出
{"status":"healthy","version":"2.0.0"}

# 测试指标API
curl http://localhost:5001/api/v1/indicators?days=30
```

### 2. 前端验证
打开浏览器访问: http://localhost:5173

应该看到：
- ✅ Heimdall 侧边栏
- ✅ Dashboard 页面
- ✅ 市场指标卡片
- ✅ K线图表

---

## 🐛 常见问题

### Q1: 端口被占用
```bash
# Windows 查看端口占用
netstat -ano | findstr :5001
netstat -ano | findstr :5173

# 杀死进程
taskkill /PID <进程ID> /F
```

### Q2: 前端无法连接后端
**检查清单:**
- [ ] 后端是否运行在 5001 端口？
- [ ] 防火墙是否阻止？
- [ ] CORS 配置是否正确？

**解决方案:**
```bash
# 检查后端日志
# 应该看到: INFO:     Uvicorn running on http://0.0.0.0:5001
```

### Q3: npm install 失败
```bash
# 清除缓存
npm cache clean --force

# 使用淘宝镜像
npm install --registry=https://registry.npmmirror.com
```

### Q4: 前端报错 "Cannot connect to API"
**检查:**
1. 后端是否启动：访问 http://localhost:5001/health
2. 查看浏览器控制台的网络请求
3. 确认 vite.config.js 中的代理配置

---

## 📊 启动流程图

```
用户
  │
  ├─> 启动后端 (python -m uvicorn app.main:app --reload --port 5001)
  │    └─> FastAPI 监听 localhost:5001
  │         ├─> 初始化数据库
  │         ├─> 启动定时任务 (Cron)
  │         └─> 加载路由 (/api/v1/*)
  │
  └─> 启动前端 (npm run dev)
       └─> Vite 监听 localhost:5173
            ├─> 加载 Vue 组件
            ├─> 配置 API 代理 (/api -> :5001)
            └─> 热重载开发
```

---

## 🎯 生产环境部署

### 构建前端
```bash
cd frontend
npm run build
# 生成 dist/ 目录
```

### 前端构建产物
构建完成后，后端会自动服务 `frontend/dist`，不需要再额外挂旧静态目录。

### 使用 Nginx 反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📝 启动检查清单

启动前确认：
- [ ] PostgreSQL 数据库运行中
- [ ] Redis 服务运行中（如果使用）
- [ ] .env 文件配置正确
- [ ] Python 依赖已安装 (requirements.txt)
- [ ] Node.js 依赖已安装 (npm install)
- [ ] 端口 5001 和 5173 未被占用

启动后验证：
- [ ] 后端健康检查通过
- [ ] 前端页面可访问
- [ ] API 请求正常
- [ ] 数据库连接正常
- [ ] 定时任务运行正常

---

## 🚀 现在就开始

**方式 1: 一键启动（推荐）**
```bash
scripts\start.bat
```

**方式 2: 手动启动**
```bash
# 终端1 - 后端
python -m uvicorn app.main:app --reload --port 5001

# 终端2 - 前端
cd frontend && npm run dev
```

**然后访问:**
http://localhost:5173

祝你使用愉快！🎉
