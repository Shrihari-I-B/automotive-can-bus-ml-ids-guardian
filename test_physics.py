import can
import time
import sys

def main():
    print("🕵️  PHYSICS DIAGNOSTIC TOOL")
    print("    Listening to vcan0 for correlation between RPM (0x123) and Gear (0x310)...")
    print("    [Press Ctrl+C to Stop]")
    print("-" * 60)

    try:
        bus = can.ThreadSafeBus(channel='vcan0', interface='socketcan')
    except OSError:
        print("❌ Error: vcan0 not found.")
        return

    last_rpm = 0
    last_gear = -1
    
    # Stats tracking
    valid_shifts = 0
    invalid_shifts = 0

    try:
        while True:
            msg = bus.recv(timeout=1.0)
            if not msg: continue

            # Decode RPM (ID 0x123)
            if msg.arbitration_id == 0x123:
                rpm_raw = int.from_bytes(msg.data, byteorder='big')
                last_rpm = int(rpm_raw * 0.25)

            # Decode Gear (ID 0x310)
            elif msg.arbitration_id == 0x310:
                current_gear = int(msg.data[0])

                # DETECT SHIFT EVENT
                if last_gear != -1 and current_gear != last_gear:
                    print(f"⚙️  SHIFT DETECTED: Gear {last_gear} -> {current_gear}")
                    print(f"   Current RPM: {last_rpm}")
                    
                    # LOGIC CHECK: Did the physics behave correctly?
                    
                    # CASE 1: Upshift (1->2, 2->3)
                    if current_gear > last_gear:
                        # In our FSM, we shift at > 3500 RPM. 
                        # The RPM *immediately* drops by 1000.
                        # So if we see a shift, the RPM should be either High (3500+) 
                        # OR already dropped (2500+).
                        # If it's < 2000, something is wrong (Random shifting).
                        if last_rpm > 2000: 
                            print("   ✅ PASS: Shifted in valid power band.")
                            valid_shifts += 1
                        else:
                            print(f"   ❌ FAIL: Shifted too early ({last_rpm} RPM). Engine lugging!")
                            invalid_shifts += 1
                    
                    # CASE 2: Downshift (3->2, 2->1)
                    elif current_gear < last_gear:
                        # In our FSM, we shift down at < 1200 RPM.
                        # The RPM spikes +800.
                        # So we expect RPM to be around 2000 after the shift.
                        # If it's > 4000, that's weird.
                        if last_rpm < 3500:
                            print("   ✅ PASS: Downshifted correctly.")
                            valid_shifts += 1
                        else:
                            print(f"   ❌ FAIL: Money Shift! Downshifted at high RPM ({last_rpm}).")
                            invalid_shifts += 1

                    print("-" * 40)
                
                last_gear = current_gear

    except KeyboardInterrupt:
        print("\n🛑 Test Stopped.")
        print(f"SUMMARY: {valid_shifts} Valid Shifts, {invalid_shifts} Invalid/Suspicious Shifts.")
        bus.shutdown()

if __name__ == "__main__":
    main()
