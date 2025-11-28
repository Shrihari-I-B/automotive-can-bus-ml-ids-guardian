import subprocess
import time
import signal
import os
import sys
from pathlib import Path

# === PATH SETUP ===
ORCHESTRATOR_PATH = Path(__file__).resolve()
FRAMEWORK_DIR = ORCHESTRATOR_PATH.parent 
PROJECT_ROOT = FRAMEWORK_DIR.parent 

INTERFACE = "vcan0"
RAW_LOG = PROJECT_ROOT / "research_raw_huge.log"       # New log file
PARSED_CSV = PROJECT_ROOT / "research_parsed_huge.csv" # New CSV file
FEATURE_CSV = PROJECT_ROOT / "research_features_huge.csv" # New Feature file
PYTHON_EXEC = sys.executable 

# Scripts
SIM_SCRIPT = FRAMEWORK_DIR / "run_simulation_v2.py"
ATTACK_SCRIPT = FRAMEWORK_DIR / "can_ids" / "attacks" / "context_spoof.py"
PARSER_SCRIPT = PROJECT_ROOT / "parse_can_log.py"
FEATURE_SCRIPT = FRAMEWORK_DIR / "can_ids" / "processing" / "build_features.py"

# === HUGE DATASET TIMINGS (Total ~10 Minutes) ===
PHASES = {
    "baseline": 480,  # 8 Minutes of Benign Driving
    "attack": 30,     # 30 Seconds of Attack
    "cooldown": 90    # 1.5 Minutes of Cooldown
}

def start_process(command_list):
    cmd_str = " ".join([str(x) for x in command_list])
    print(f"   [+] Executing: {cmd_str}")
    script_path = Path(command_list[1])
    if not script_path.exists():
        print(f"   ❌ CRITICAL ERROR: Script not found: {script_path}")
        return None
    return subprocess.Popen(command_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_process(process):
    if process:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def main():
    print("=== HUGE DATASET GENERATOR (10 MINUTE RUN) ===")
    print(f"📂 Project Root: {PROJECT_ROOT}")
    
    if os.system(f"ip link show {INTERFACE} > /dev/null 2>&1") != 0:
        print(f"❌ Interface {INTERFACE} missing. Run ./setup_vcan.sh")
        return

    print(f"📂 Logging to {RAW_LOG.name}...")
    with open(RAW_LOG, "w") as f:
        logger = subprocess.Popen(["candump", "-t", "a", "-L", INTERFACE], stdout=f)

    print("🚗 Starting FSM Simulation...")
    sim_process = start_process([PYTHON_EXEC, str(SIM_SCRIPT), "--interface", INTERFACE])
    
    if not sim_process:
        print("❌ Simulation failed to start.")
        logger.terminate()
        return

    try:
        # Phase 1: Long Baseline
        print(f"⏳ Phase 1: Baseline Data Collection ({PHASES['baseline']}s)")
        time.sleep(PHASES['baseline'])

        # Phase 2: Context-Aware Attack
        print(f"🚨 Phase 2: Launching Context-Aware Attack ({PHASES['attack']}s)")
        attack_process = start_process([PYTHON_EXEC, str(ATTACK_SCRIPT)])
        time.sleep(PHASES['attack'])
        stop_process(attack_process)
        print("   ✅ Attack phase complete.")

        # Phase 3: Long Cooldown
        print(f"⏳ Phase 3: Cooldown ({PHASES['cooldown']}s)")
        time.sleep(PHASES['cooldown'])

    except KeyboardInterrupt:
        print("\n🛑 Aborted.")

    finally:
        print("🧹 Cleanup...")
        stop_process(sim_process)
        logger.terminate()
        
    print("\n⚙️  Starting Data Processing Pipeline...")
    
    # A. Parse Raw Log -> CSV
    if PARSER_SCRIPT.exists():
        print("   [1/2] Parsing Log...")
        # Note: Ensure parser uses the correct input/output files
        subprocess.run([PYTHON_EXEC, str(PARSER_SCRIPT), str(RAW_LOG), str(PARSED_CSV)])
    else:
        print(f"❌ Error: {PARSER_SCRIPT} not found.")
        return

    # B. Build Features
    print("   [2/2] Building Feature Matrix...")
    if FEATURE_SCRIPT.exists():
        build_cmd = [
            PYTHON_EXEC, str(FEATURE_SCRIPT),
            "--input", str(PARSED_CSV),
            "--output", str(FEATURE_CSV),
            "--window", "0.1"
        ]
        subprocess.run(build_cmd)
    else:
        print(f"❌ Error: {FEATURE_SCRIPT} not found.")
        return
    
    print("\n✅ EXPERIMENT COMPLETE.")
    print(f"   Final Dataset: {FEATURE_CSV}")

if __name__ == "__main__":
    main()
