#!/bin/bash

case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        WIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -W)"
        cmd.exe //c "cd /d $WIN_ROOT && echo.|scripts\\start.bat"
        exit $?
        ;;
esac

echo "======================================================================"
echo "                    Heimdall Startup Script"
echo "======================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
API_PORT=8000
FRONTEND_PORT=4173

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

# Check if ports are in use
if lsof -Pi :"$API_PORT" -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}[WARNING]${NC} Port $API_PORT is already in use. Backend might be running."
fi

if lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}[WARNING]${NC} Port $FRONTEND_PORT is already in use. Frontend might be running."
fi

echo ""
echo "[Step 1/3] Starting Backend (FastAPI)..."
echo "Backend will run on: http://localhost:$API_PORT"
echo "API Documentation: http://localhost:$API_PORT/docs"
echo ""

# Start backend in background
cd "$PROJECT_ROOT"
HEIMDALL_API_PORT="$API_PORT" python -m uvicorn app.main:app --reload --port "$API_PORT" > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Save PIDs for cleanup
echo $BACKEND_PID > /tmp/heimdall_backend.pid

# Wait for backend to start
sleep 3

echo ""
echo "[Step 2/3] Starting Frontend (Vue + Vite)..."
echo "Frontend will run on: http://localhost:$FRONTEND_PORT"
echo ""

# Check if node_modules exists
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo -e "${YELLOW}[INFO]${NC} node_modules not found. Running npm install..."
    cd "$PROJECT_ROOT/frontend"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} npm install failed. Please check your Node.js installation."
        kill $BACKEND_PID
        exit 1
    fi
fi

# Start frontend in background
cd "$PROJECT_ROOT/frontend"
HEIMDALL_API_PORT="$API_PORT" HEIMDALL_FRONTEND_PORT="$FRONTEND_PORT" npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Save PIDs for cleanup
echo $FRONTEND_PID > /tmp/heimdall_frontend.pid

# Wait for services to initialize
echo ""
echo "[Step 3/3] Waiting for services to start..."
sleep 5

echo ""
echo "======================================================================"
echo "                        Startup Complete!"
echo "======================================================================"
echo ""
echo "Services:"
echo "  Backend:  http://localhost:$API_PORT/docs"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo ""
echo "Logs:"
echo "  Backend:  logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "To stop services, run: scripts/stop.sh"
echo "Or press Ctrl+C"
echo ""

# Open browser (macOS/Linux)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:$FRONTEND_PORT"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "http://localhost:$FRONTEND_PORT" 2>/dev/null
fi

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
