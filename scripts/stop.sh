#!/bin/bash

echo "Stopping Heimdall services..."

API_PORT=8000
FRONTEND_PORT=4173

if command -v lsof >/dev/null 2>&1; then
    lsof -Pi :"$API_PORT" -sTCP:LISTEN -t | xargs -r kill
    lsof -Pi :"$FRONTEND_PORT" -sTCP:LISTEN -t | xargs -r kill
else
    pkill -f "uvicorn app.main:app --reload --port $API_PORT" 2>/dev/null
    pkill -f "vite" 2>/dev/null
fi

echo "Services stopped."
