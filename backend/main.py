from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from backend.routers import control
from backend.process_manager import process_manager
from backend.can_listener import can_listener
from backend.log_parser import log_parser

app = FastAPI(title="CAN IDS Dashboard API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(control.router, prefix="/api")

# Start CAN Listener on startup
@app.on_event("startup")
async def startup_event():
    can_listener.start()

@app.on_event("shutdown")
async def shutdown_event():
    can_listener.stop()
    # Stop all processes
    process_manager.stop_process("Simulator")
    process_manager.stop_process("IDS")
    process_manager.stop_process("Attacker")

# WebSocket for Dashboard Data (CAN + Alerts)
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. Get CAN Data
            can_data = can_listener.latest_data
            
            # 2. Get Logs & Parse Alerts
            logs = process_manager.get_logs()
            alerts = log_parser.parse_alerts(logs)
            vehicle_state = log_parser.parse_vehicle_state(logs)
            
            # 3. Get System Status
            status = process_manager.get_status()
            
            # 4. Check for DoS Attack
            is_dos_active = log_parser.check_dos_status(logs)

            # Send combined update
            payload = {
                "can": can_data if not is_dos_active else {"RPM": 0, "Speed": 0, "Gear": 0}, # Block data if DoS
                "vehicle_state": vehicle_state if not is_dos_active else "Connection Lost",
                "alerts": alerts[-10:], # Send last 10 alerts
                "status": status,
                "logs": logs[-50:], # Send last 50 logs for live view
                "dos_active": is_dos_active # Flag for Frontend
            }
            
            await websocket.send_json(payload)
            await asyncio.sleep(0.1) # 10Hz update rate
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
