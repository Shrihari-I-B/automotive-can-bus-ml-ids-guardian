import can
import threading
import time
import asyncio
import json
from typing import List, Callable

class CANListener:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CANListener, cls).__new__(cls)
            cls._instance.running = False
            cls._instance.thread = None
            cls._instance.subscribers: List[Callable] = []
            cls._instance.latest_data = {
                "RPM": 0,
                "Gear": 0,
                "Speed": 0, # Derived or direct
                "Throttle": 0,
                "Brake": 0
            }
        return cls._instance

    def start(self, interface="vcan0"):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen, args=(interface,), daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def broadcast(self, message: dict):
        # Notify all subscribers (WebSocket handlers)
        # We need to run this in the event loop of the subscribers
        for callback in self.subscribers:
            await callback(message)

    def _listen(self, interface):
        print(f"Starting CAN listener on {interface}")
        try:
            bus = can.ThreadSafeBus(channel=interface, interface='socketcan')
        except Exception as e:
            print(f"Failed to connect to CAN bus: {e}")
            self.running = False
            return

        while self.running:
            try:
                msg = bus.recv(timeout=0.1)
                if not msg:
                    continue

                # Parse known messages (based on run_simulation_v2.py)
                updated = False
                
                # RPM (0x123)
                if msg.arbitration_id == 0x123:
                    raw = int.from_bytes(msg.data, byteorder='big')
                    self.latest_data["RPM"] = int(raw * 0.25)
                    # Rough speed estimation based on RPM and Gear (just for visuals)
                    # Assuming some ratios
                    gear = self.latest_data.get("Gear", 1)
                    if gear == 0: gear = 1 # Avoid div by zero logic if neutral
                    self.latest_data["Speed"] = int(self.latest_data["RPM"] * gear * 0.005) 
                    updated = True
                
                # Gear (0x310)
                elif msg.arbitration_id == 0x310:
                    self.latest_data["Gear"] = int(msg.data[0])
                    updated = True
                
                # Brake (0x240)
                elif msg.arbitration_id == 0x240:
                    self.latest_data["Brake"] = 1 if msg.data[0] == 1 else 0
                    updated = True

                # Notify subscribers if data changed (or periodically)
                # For high freq CAN, maybe throttle this?
                # For now, let's just update latest_data and have a separate broadcaster or broadcast on change
                # To avoid flooding WS, let's just update state here.
                # The WebSocket endpoint can poll this state or we can broadcast throttled.
                
            except Exception as e:
                print(f"Error in CAN listener: {e}")
                time.sleep(1)

        bus.shutdown()
        print("CAN listener stopped")

can_listener = CANListener()
