import threading
import can
import time

class VirtualECU(threading.Thread):
    def __init__(self, bus, name, fsm_instance, message_type, period):
        """
        Args:
            bus: The python-can bus object
            name: Name of the ECU (e.g. 'Engine')
            fsm_instance: The shared VehicleFSM object
            message_type: 'RPM', 'GEAR', 'ABS', 'BODY'
            period: Send interval in seconds
        """
        super().__init__()
        self.bus = bus
        self.name = name
        self.fsm = fsm_instance
        self.message_type = message_type
        self.period = period
        self.stopped_event = threading.Event()
        self.daemon = True

    def run(self):
        while not self.stopped_event.is_set():
            start_time = time.time()
            
            try:
                msg = self._generate_message()
                self.bus.send(msg)
            except can.CanError:
                pass
            
            elapsed = time.time() - start_time
            time.sleep(max(0, self.period - elapsed))

    def _generate_message(self):
        # Fetch the SINGLE SOURCE OF TRUTH (The FSM)
        state = self.fsm.get_state_data()
        
        if self.message_type == 'RPM':
            # ID 0x123: Engine RPM
            rpm_raw = int(state['rpm'] / 0.25)
            data = rpm_raw.to_bytes(2, byteorder='big')
            return can.Message(arbitration_id=0x123, data=data, is_extended_id=False)
            
        elif self.message_type == 'GEAR':
            # ID 0x310: Transmission
            data = state['gear'].to_bytes(1, byteorder='big') + b'\x00\x00\x00'
            return can.Message(arbitration_id=0x310, data=data, is_extended_id=False)
            
        elif self.message_type == 'ABS':
            # ID 0x240: ABS Status (1 if Braking)
            val = 1 if state['brake'] > 0 else 0
            data = bytes([val, 0x00])
            return can.Message(arbitration_id=0x240, data=data, is_extended_id=False)
            
        elif self.message_type == 'BODY':
            # ID 0x500: Body Control (Heartbeat)
            return can.Message(arbitration_id=0x500, data=b'\x0D\x0E\x0F\x10', is_extended_id=False)

    def stop(self):
        self.stopped_event.set()
