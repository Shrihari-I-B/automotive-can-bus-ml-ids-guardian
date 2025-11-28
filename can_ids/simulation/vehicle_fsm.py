import random
import time
import math
from enum import Enum

class VehicleState(Enum):
    IDLE = 0
    ACCELERATING = 1
    CRUISING = 2
    BRAKING = 3
    ANOMALY_REACTION = 4

class VehicleFSM:
    def __init__(self):
        self.state = VehicleState.IDLE
        self.rpm = 800
        self.gear = 0
        self.brake_pedal = 0
        self.last_update = time.time()
        self.bus_gear = 0 
        self.anomaly_timer = 0
        self.cruise_timer = 0

    def set_observed_gear(self, gear):
        self.bus_gear = gear

    def update(self):
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time

        # === DEBUG: PRINT IF WE SEE THE ATTACK ===
        # If the bus says Gear 2 but we are in Gear 5 logic
        if self.bus_gear == 2 and self.gear == 5:
            # This print will ruin the dashboard layout but will prove the logic works
            # print(f"DEBUG: Saw Attack! State={self.state}") 
            pass

        # === CYBER-PHYSICAL ANOMALY DETECTION ===
        # Trigger: High Speed (Cruising) + Low Gear on Bus (Attack)
        # RELAXED CONDITION: Just check if we are in high gear logic but bus says low gear
        if self.gear == 5 and self.bus_gear == 2:
            self.state = VehicleState.ANOMALY_REACTION
            self.anomaly_timer = 0 

        # === STATE LOGIC ===
        if self.state == VehicleState.IDLE:
            self.gear = 0
            self.rpm = 800 + random.randint(-50, 50)
            if random.random() < 0.02: self.state = VehicleState.ACCELERATING

        elif self.state == VehicleState.ACCELERATING:
            self.rpm += 120 
            if self.rpm > 3500 and self.gear < 5:
                self.gear += 1
                self.rpm -= 1000
            elif self.gear == 0: self.gear = 1
            
            if self.gear == 5 and self.rpm > 2200:
                self.state = VehicleState.CRUISING
                self.cruise_timer = 0

        elif self.state == VehicleState.CRUISING:
            self.gear = 5
            self.cruise_timer += dt
            oscillation = math.sin(current_time * 0.5) * 200
            target_rpm = 2200 + oscillation + random.randint(-50, 50)
            if self.rpm < target_rpm: self.rpm += 10
            else: self.rpm -= 10
            
            if self.cruise_timer > 20.0 or random.random() < 0.005: 
                self.state = VehicleState.BRAKING

        elif self.state == VehicleState.BRAKING:
            self.rpm -= 200
            self.brake_pedal = 100
            if self.rpm < 1500 and self.gear > 0:
                self.gear -= 1
                self.rpm += 800
            if self.gear == 0 or self.rpm < 800:
                self.state = VehicleState.IDLE
                self.rpm = 800
                self.brake_pedal = 0

        elif self.state == VehicleState.ANOMALY_REACTION:
            # FORCE THE GLITCH VISUALS
            self.gear = 2 
            self.rpm = 7000 + random.randint(0, 500) # Redline bouncing
            self.brake_pedal = 0
            
            # Recovery Logic
            self.anomaly_timer += dt
            # If bus returns to Gear 5 (Normal) OR timeout
            if self.bus_gear == 5:
                if self.anomaly_timer > 2.0: self._recover()
            elif self.anomaly_timer > 4.0:
                self._recover()

        self.rpm = max(0, min(8000, self.rpm))

    def _recover(self):
        self.state = VehicleState.CRUISING
        self.rpm = 2200
        self.gear = 5
        self.anomaly_timer = 0
        self.cruise_timer = 0

    def get_state_data(self):
        return {
            "state": self.state.name,
            "rpm": int(self.rpm),
            "gear": self.gear,
            "brake": self.brake_pedal
        }
