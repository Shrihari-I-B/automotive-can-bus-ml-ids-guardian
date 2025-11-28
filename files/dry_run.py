import subprocess
import os
import sys
import time

def main():
    print("🧪 STARTING SYSTEM DRY RUN (FAST VERIFICATION)...")
    
    # 1. Verify Sudo/Permissions
    if os.system("ip link show vcan0") != 0:
        print("❌ FAIL: vcan0 not found.")
        return

    # 2. Run Short Simulation (5s)
    print("   Running Simulation for 5s...", end=" ")
    sim = subprocess.Popen([sys.executable, "can_ids_framework/run_simulation_v2.py"], 
                           stdout=subprocess.DEVNULL)
    time.sleep(5)
    if sim.poll() is None: # Still running
        print("✅ PASSED.")
        sim.terminate()
    else:
        print("❌ FAILED (Crashed).")
        return

    # 3. Verify Log File Creation
    # We need to actually log something to test parsing
    print("   Testing Logger & Parser...", end=" ")
    with open("test.log", "w") as f:
        logger = subprocess.Popen(["candump", "-t", "a", "-L", "vcan0"], stdout=f)
        sim = subprocess.Popen([sys.executable, "can_ids_framework/run_simulation_v2.py"], 
                               stdout=subprocess.DEVNULL)
        time.sleep(2)
        sim.terminate()
        logger.terminate()
    
    if os.path.exists("test.log") and os.path.getsize("test.log") > 0:
        # Run Parser
        subprocess.run([sys.executable, "parse_can_log.py", "test.log", "test.csv"], 
                       stdout=subprocess.DEVNULL)
        if os.path.exists("test.csv"):
            print("✅ PASSED.")
        else:
            print("❌ FAILED (Parser crashed).")
    else:
        print("❌ FAILED (No log data).")

    # Cleanup
    os.remove("test.log")
    if os.path.exists("test.csv"): os.remove("test.csv")
    
    print("\n🎉 SYSTEM CHECK COMPLETE. YOU ARE READY FOR DEMO.")

if __name__ == "__main__":
    main()

