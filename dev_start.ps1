# Heimdall 开发环境一键启动脚本 (PowerShell)
# 自动启动后端 (FastAPI) 和前端 (Vue 3) 开发服务器

Write-Host "🛡️ Heimdall 开发环境启动中..." -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# 检查是否存在虚拟环境
$venvPath = Join-Path $scriptPath "venv\Scripts\Activate.ps1"
$activateCommand = if (Test-Path $venvPath) {
    "& '$venvPath'; python -m uvicorn app.main:app --reload --port 5001"
}
else {
    "python -m uvicorn app.main:app --reload --port 5001"
}

# 1. 启动后端 (FastAPI - Port 5001)
Write-Host "🚀 启动后端服务 (FastAPI)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", $activateCommand

# 等待后端启动
Start-Sleep -Seconds 3

# 2. 启动前端 (Vue 3 + Vite - Port 5173)
Write-Host "🎨 启动前端服务 (Vite)..." -ForegroundColor Green
Set-Location frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

# 返回根目录
Set-Location $scriptPath

Write-Host ""
Write-Host "✅ 服务启动完成!" -ForegroundColor Cyan
Write-Host "📊 后端 API: http://localhost:5001" -ForegroundColor Yellow
Write-Host "🌐 前端页面: http://localhost:5173" -ForegroundColor Yellow
Write-Host "📖 API 文档: http://localhost:5001/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 提示: 关闭各个窗口即可停止服务" -ForegroundColor Gray
