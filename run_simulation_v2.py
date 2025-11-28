import can
import time
import sys
import os
import threading
import argparse
from can_ids.simulation.vehicle_fsm import VehicleFSM
from can_ids.simulation.virtual_ecu import VirtualECU

# Global Dashboard State
dashboard_view = {
    "RPM": 0, 
    "Gear": 0, 
    "Brake": 0,
    "Last_RPM_Time": 0,
    "Last_Gear_Time": 0,
    "Msg_Count": 0  # Track volume for DoS detection visual
}

def dashboard_listener(interface):
    """
    Listens to vcan0 and updates the dashboard view.
    Also counts total messages to show 'Bus Load'.
    """
    try:
        bus = can.ThreadSafeBus(channel=interface, interface='socketcan')
        while True:
            msg = bus.recv(timeout=0.01)
            if not msg: continue
            
            # Increment global counter for every single message (even 0x000)
            dashboard_view["Msg_Count"] += 1
            
            current_time = time.time()
            
            if msg.arbitration_id == 0x123:
                raw = int.from_bytes(msg.data, byteorder='big')
                dashboard_view["RPM"] = int(raw * 0.25)
                dashboard_view["Last_RPM_Time"] = current_time
            elif msg.arbitration_id == 0x310:
                dashboard_view["Gear"] = int(msg.data[0])
                dashboard_view["Last_Gear_Time"] = current_time
            elif msg.arbitration_id == 0x240:
                dashboard_view["Brake"] = 1 if msg.data[0] == 1 else 0
                
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="vcan0")
    args = parser.parse_args()

    print(f"🚗 Starting Research-Grade Simulator on {args.interface}...")
    
    vehicle = VehicleFSM()
    
    try:
        bus_send = can.ThreadSafeBus(channel=args.interface, interface='socketcan')
    except OSError:
        print(f"❌ Error: Could not bind to {args.interface}.")
        sys.exit(1)
    
    ecus = [
        VirtualECU(bus_send, "Engine", vehicle, 'RPM', 0.02),
        VirtualECU(bus_send, "Trans", vehicle, 'GEAR', 0.1),
        VirtualECU(bus_send, "ABS", vehicle, 'ABS', 0.05),
        VirtualECU(bus_send, "Body", vehicle, 'BODY', 1.0)
    ]
    for ecu in ecus: ecu.start()

    t_dash = threading.Thread(target=dashboard_listener, args=(args.interface,), daemon=True)
    t_dash.start()

    print("✅ Simulation Running. Press Ctrl+C to stop.")

    # Rate Calculation Variables
    last_calc_time = time.time()
    last_msg_count = 0

    try:
        while True:
            # A. Feedback Loop
            vehicle.set_observed_gear(dashboard_view['Gear'])
            vehicle.update()
            
            # B. Calculate Bus Load (Messages per Second)
            curr_time = time.time()
            if curr_time - last_calc_time >= 1.0:
                rate = dashboard_view["Msg_Count"] - last_msg_count
                last_msg_count = dashboard_view["Msg_Count"]
                last_calc_time = curr_time
                
                # Store rate for display (hacky but works for print loop)
                dashboard_view["Rate"] = rate

            # C. Visualize
            state_name = vehicle.get_state_data()['state']
            brake_status = "ON " if dashboard_view['Brake'] == 1 else "OFF"
            
            # Get Rate safely
            rate = dashboard_view.get("Rate", 0)
            
            # Visual Warning if Rate is high (Flood Attack)
            rate_str = f"{rate} msg/s"
            if rate > 1000:
                rate_str = f"🔥 {rate} msg/s (FLOOD!)"

            # Check for Signal Loss
            time_since_gear = time.time() - dashboard_view["Last_Gear_Time"]
            gear_display = dashboard_view['Gear']
            if time_since_gear > 1.0: gear_str = "???"
            else: gear_str = f"{gear_display}"

            # Check if running in Web UI mode
            if os.environ.get("WEB_UI"):
                # JSON-like or simple format for easy parsing
                print(f"STATE:{state_name}|RPM:{dashboard_view['RPM']}|GEAR:{gear_str}|RATE:{rate}")
                sys.stdout.flush()
            else:
                sys.stdout.write(
                    f"\r[{state_name:16s}] RPM: {dashboard_view['RPM']:4d} | Gear: {gear_str:<3} | {rate_str:<20}   "
                )
                sys.stdout.flush()
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        for ecu in ecus: ecu.stop()
        bus_send.shutdown()

if __name__ == "__main__":
    main()
