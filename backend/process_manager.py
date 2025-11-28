import subprocess
import threading
import time
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Optional

# Define paths to scripts based on exploration
BASE_DIR = Path(__file__).resolve().parent.parent
SIM_SCRIPT = BASE_DIR / "run_simulation_v2.py"
IDS_SCRIPT = BASE_DIR / "main_live_ids.py"
ATTACK_DIR = BASE_DIR / "can_ids" / "attacks"

class ProcessManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance.processes = {}
            cls._instance.logs = []
            cls._instance.lock = threading.Lock()
        return cls._instance

    def _log_reader(self, name: str, process: subprocess.Popen):
        """Reads stdout from a process and appends to logs."""
        for line in iter(process.stdout.readline, b''):
            decoded_line = line.decode('utf-8', errors='replace').strip()
            if decoded_line:
                with self.lock:
                    log_entry = f"[{name}] {decoded_line}"
                    self.logs.append(log_entry)
                    # Keep log size manageable
                    if len(self.logs) > 1000:
                        self.logs.pop(0)
                print(log_entry) # Also print to backend console

    def start_process(self, name: str, command: list):
        with self.lock:
            if name in self.processes and self.processes[name].poll() is None:
                return False, "Process already running"

            try:
                # Use unbuffered output for Python scripts
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                env["WEB_UI"] = "1"
                
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, # Merge stderr into stdout
                    env=env,
                    cwd=str(BASE_DIR) # Run from root
                )
                self.processes[name] = process
                
                # Start log reader thread
                t = threading.Thread(target=self._log_reader, args=(name, process), daemon=True)
                t.start()
                
                return True, "Started successfully"
            except Exception as e:
                return False, str(e)

    def stop_process(self, name: str):
        with self.lock:
            process = self.processes.get(name)
            if not process:
                return False, "Process not running"
            
            if process.poll() is not None:
                del self.processes[name]
                return True, "Process already stopped"

            try:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                del self.processes[name]
                return True, "Stopped successfully"
            except Exception as e:
                return False, str(e)

    def get_status(self) -> Dict[str, bool]:
        with self.lock:
            status = {}
            for name, process in self.processes.items():
                status[name] = process.poll() is None
            return status

    def get_logs(self):
        with self.lock:
            return list(self.logs)

    def clear_logs(self):
        with self.lock:
            self.logs = []

process_manager = ProcessManager()
