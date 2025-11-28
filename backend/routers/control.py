from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..process_manager import process_manager, SIM_SCRIPT, IDS_SCRIPT, ATTACK_DIR
import sys

router = APIRouter()

class AttackRequest(BaseModel):
    type: str # "replay", "spoof", "flood"

@router.post("/start/simulator")
async def start_simulator():
    cmd = [sys.executable, str(SIM_SCRIPT), "--interface", "vcan0"]
    success, msg = process_manager.start_process("Simulator", cmd)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "started", "message": msg}

@router.post("/stop/simulator")
async def stop_simulator():
    success, msg = process_manager.stop_process("Simulator")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "stopped", "message": msg}

@router.post("/start/ids")
async def start_ids():
    cmd = [sys.executable, str(IDS_SCRIPT)]
    success, msg = process_manager.start_process("IDS", cmd)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "started", "message": msg}

@router.post("/stop/ids")
async def stop_ids():
    success, msg = process_manager.stop_process("IDS")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "stopped", "message": msg}

@router.post("/start/attack")
async def start_attack(request: AttackRequest):
    script_map = {
        "replay": "replay.py",
        "spoof": "context_spoof.py",
        "flood": "flood.py"
    }
    
    script_name = script_map.get(request.type)
    if not script_name:
        raise HTTPException(status_code=400, detail="Invalid attack type")
        
    script_path = ATTACK_DIR / script_name
    cmd = [sys.executable, str(script_path)]
    
    # Attacks might need specific args, but for now we run them as is based on exploration
    # If they need args, we can add them here.
    
    success, msg = process_manager.start_process("Attacker", cmd)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "started", "message": msg}

@router.post("/stop/attack")
async def stop_attack():
    success, msg = process_manager.stop_process("Attacker")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "stopped", "message": msg}

@router.get("/status")
async def get_status():
    return process_manager.get_status()

@router.get("/logs")
async def get_logs():
    return {"logs": process_manager.get_logs()}

@router.post("/logs/clear")
async def clear_logs():
    process_manager.clear_logs()
    return {"status": "cleared"}
