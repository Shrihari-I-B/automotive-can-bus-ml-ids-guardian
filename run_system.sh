#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping processes..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT

# Check if vcan0 exists
if ! ip link show vcan0 > /dev/null 2>&1; then
    echo "⚠️  vcan0 interface not found. Please run:"
    echo "   sudo modprobe vcan"
    echo "   sudo ip link add dev vcan0 type vcan"
    echo "   sudo ip link set up vcan0"
    exit 1
fi

# Start Backend
echo "🚀 Starting Backend (FastAPI)..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "🚀 Starting Frontend (Vite)..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi
npm run dev -- --host &
FRONTEND_PID=$!

echo "✅ System Running!"
echo "   Backend: http://localhost:8000/docs"
echo "   Frontend: http://localhost:5173"
echo "   Press Ctrl+C to stop."

wait
