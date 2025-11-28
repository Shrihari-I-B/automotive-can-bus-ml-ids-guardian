import re
from typing import List, Dict, Optional

class LogParser:
    @staticmethod
    def parse_alerts(logs: List[str]) -> List[Dict]:
        alerts = []
        # Regex to match the alert format in main_live_ids.py
        # Web Mode: print(f"🚨 ALERT: {attack_name} | Vol: {count} | {debug_str}")
        
        pattern = re.compile(r"🚨 ALERT:\s*(.*?)\s*\|\s*Vol:\s*(\d+)\s*\|(.*)")
        
        for line in logs:
            if "🚨 ALERT" in line:
                # Remove [IDS] prefix if present
                clean_line = line.split("]", 1)[1] if "]" in line else line
                
                match = pattern.search(clean_line)
                if match:
                    attack_type = match.group(1).strip()
                    volume = match.group(2).strip()
                    debug_info = match.group(3).strip()
                    
                    alerts.append({
                        "timestamp": "Now", 
                        "type": attack_type,
                        "volume": volume,
                        "details": debug_info,
                        "raw": line
                    })
        return alerts

    @staticmethod
    def parse_vehicle_state(logs: List[str]) -> str:
        # Web Mode: print(f"STATE:{state_name}|RPM:{dashboard_view['RPM']}|GEAR:{gear_str}|RATE:{rate}")
        # We look for the LATEST state log
        for line in reversed(logs):
            if "STATE:" in line:
                try:
                    # Extract STATE:Cruising
                    parts = line.split("|")
                    for part in parts:
                        if "STATE:" in part:
                            return part.split(":")[1].strip()
                except:
                    pass
        return "Unknown"

    @staticmethod
    def check_dos_status(logs: List[str]) -> bool:
        """
        Check if a FLOODING attack is currently active.
        Logic: Look at the last 10 logs. If we see "FLOODING" and haven't seen "NORMAL" 
        since then, we assume it's active.
        """
        # We only care about recent logs to avoid getting stuck in DoS state
        recent_logs = logs[-20:] 
        
        for line in reversed(recent_logs):
            if "FLOODING" in line:
                return True
            if "NORMAL" in line:
                return False
        return False

log_parser = LogParser()
