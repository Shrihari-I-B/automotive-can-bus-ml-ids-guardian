import unittest
import time
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add framework to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from can_ids.simulation.vehicle_fsm import VehicleFSM, VehicleState
from can_ids.processing.build_features import calculate_entropy, process_window

class TestVehiclePhysics(unittest.TestCase):
    def setUp(self):
        self.fsm = VehicleFSM()

    def test_initial_state(self):
        """Test if car starts in IDLE state."""
        self.assertEqual(self.fsm.state, VehicleState.IDLE)
        self.assertEqual(self.fsm.gear, 0)
        self.assertTrue(750 <= self.fsm.rpm <= 850)

    def test_gear_shifting_logic(self):
        """Test if engine shifts up when RPM gets too high."""
        self.fsm.state = VehicleState.ACCELERATING
        self.fsm.gear = 1
        self.fsm.rpm = 3600 # Above shift threshold (3500)
        
        self.fsm.update()
        
        # Should have shifted to Gear 2
        self.assertEqual(self.fsm.gear, 2)
        # RPM should have dropped (3600 + 120 - 1000 = 2720)
        self.assertTrue(self.fsm.rpm < 3000)

    def test_anomaly_reaction(self):
        """Test if physics engine reacts to cyber-attack (Gear mismatch)."""
        self.fsm.state = VehicleState.CRUISING
        self.fsm.gear = 5
        self.fsm.rpm = 2200
        
        # Inject Fake Bus Data (Attack)
        self.fsm.set_observed_gear(2)
        self.fsm.update()
        
        # Should trigger panic mode
        self.assertEqual(self.fsm.state, VehicleState.ANOMALY_REACTION)
        # RPM should spike (2200 + 500)
        self.assertTrue(self.fsm.rpm > 2500)

class TestFeatureEngineering(unittest.TestCase):
    def test_entropy_calculation(self):
        """Test Shannon Entropy logic."""
        # Low Entropy (All same)
        data_low = pd.Series([1, 1, 1, 1])
        self.assertEqual(calculate_entropy(data_low), 0.0)
        
        # High Entropy (All different)
        data_high = pd.Series([1, 2, 3, 4])
        # Entropy of 4 unique items = 2.0 bits
        self.assertAlmostEqual(calculate_entropy(data_high), 2.0)

    def test_window_processing(self):
        """Test if a window of messages converts to a feature vector."""
        # Create fake window dataframe
        data = {
            'timestamp': [1.0, 1.02, 1.04], # 0.02s intervals
            'arbitration_id': [123, 310, 123],
            'data_hex': ['1122', '3344', '1122'],
            'label': [0, 0, 0]
        }
        df = pd.DataFrame(data)
        
        features = process_window(df)
        
        self.assertEqual(features['msg_count'], 3)
        self.assertEqual(features['unique_ids'], 2)
        self.assertAlmostEqual(features['iat_mean'], 0.02)
        self.assertEqual(features['label'], 0)

if __name__ == '__main__':
    print("🧪 RUNNING RESEARCH FRAMEWORK TESTS...")
    unittest.main()
