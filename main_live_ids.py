import can
import time
import joblib
import numpy as np
import pandas as pd
import math
import sys
import os
import warnings
from collections import Counter
from pathlib import Path

# Silence TF logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import tensorflow as tf
from tensorflow.keras.models import load_model

# Suppress warnings
warnings.filterwarnings("ignore")

# === CONFIGURATION ===
BASE_DIR = Path(__file__).resolve().parent.parent 
MODEL_PATH = BASE_DIR / "ocsvm_model.joblib"
SCALER_PATH = BASE_DIR / "scaler.joblib"
AE_MODEL_PATH = BASE_DIR / "autoencoder_model.keras"
AE_THRESH_PATH = BASE_DIR / "ae_threshold.npy"
INTERFACE = "vcan0"
WINDOW_SIZE = 0.1 

# Feature names must match training
FEATURE_COLS = ['msg_count', 'unique_ids', 'id_entropy', 'payload_entropy', 'iat_mean', 'iat_std']

def calculate_entropy(data_list):
    if not data_list: return 0.0
    counts = Counter(data_list)
    total = len(data_list)
    probs = [c / total for c in counts.values()]
    return -sum(p * math.log2(p) for p in probs)

def extract_window_features(messages):
    if not messages: return None
    msg_count = len(messages)
    ids = [m.arbitration_id for m in messages]
    payloads = [m.data.hex() for m in messages]
    timestamps = [m.timestamp for m in messages]

    unique_ids = len(set(ids))
    id_entropy = calculate_entropy(ids)
    payload_entropy = calculate_entropy(payloads)

    if len(timestamps) > 1:
        iats = np.diff(timestamps)
        iat_mean = np.mean(iats)
        iat_std = np.std(iats)
    else:
        iat_mean = 0.0
        iat_std = 0.0

    return pd.DataFrame([[msg_count, unique_ids, id_entropy, payload_entropy, iat_mean, iat_std]], 
                        columns=FEATURE_COLS)

def diagnose_attack(features_df):
    # Extract scalar values
    count = features_df['msg_count'].values[0]
    iat = features_df['iat_mean'].values[0]
    
    # === FINAL TUNED THRESHOLDS ===
    # Normal: ~8-12 msgs
    # New Context Spoof: ~28-35 msgs (Precision Injection)
    # Replay: ~50 msgs
    # Flooding: >1000 msgs
    
    # A safe line for "Massive Volume" vs "Injection"
    if count > 100 or iat < 0.001:
        return "FLOODING / DOS"
    elif count > 20:
        # 20-60 messages is the signature of Spoofing/Replay
        # Increased to >20 to avoid jitter false positives (Normal is ~9)
        return "SPOOFING / REPLAY"
    else:
        return "ANOMALY"

def main():
    print("🛡️  RESEARCH-GRADE IDS: DETECTION & DIAGNOSIS ACTIVE...")
    
    try:
        scaler = joblib.load(SCALER_PATH)
        ocsvm = joblib.load(MODEL_PATH)
        autoencoder = load_model(AE_MODEL_PATH)
        ae_threshold = np.load(AE_THRESH_PATH)
        print("✅ Loaded AI Models.")
        print(f"   Autoencoder Threshold: {ae_threshold:.5f}")
        
        bus = can.ThreadSafeBus(channel=INTERFACE, interface='socketcan')
        print(f"   Connected to {INTERFACE}. Monitoring...")
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        return

    print("-" * 60)
    print("   STATUS:  [🟢 MONITORING]")
    print("-" * 60)

    message_buffer = []
    next_window_end = time.time() + WINDOW_SIZE
    
    anomaly_streak = 0
    ALERT_THRESHOLD = 3 

    try:
        while True:
            remaining = next_window_end - time.time()
            if remaining > 0:
                msg = bus.recv(timeout=remaining)
                if msg: message_buffer.append(msg)
            
            if time.time() >= next_window_end:
                if message_buffer:
                    features_df = extract_window_features(message_buffer)
                    
                    if features_df is not None:
                        scaled = scaler.transform(features_df)
                        
                        # Ensemble Prediction
                        ocsvm_pred = ocsvm.predict(scaled)[0]
                        is_ocsvm_anomaly = (ocsvm_pred == -1)

                        reconstruction = autoencoder.predict(scaled, verbose=0)
                        mse = np.mean(np.power(scaled - reconstruction, 2))
                        is_ae_anomaly = (mse > ae_threshold)

                        if is_ocsvm_anomaly or is_ae_anomaly:
                            anomaly_streak += 1
                            debug_str = ""
                            if is_ocsvm_anomaly: debug_str += "[SVM]"
                            if is_ae_anomaly: debug_str += f"[AE:{mse:.1f}]"
                        else:
                            anomaly_streak = 0
                        
                        # Display
                        count = len(message_buffer)
                        
                        if os.environ.get("WEB_UI"):
                            # Web Mode: Print newlines for backend capture
                            if anomaly_streak >= ALERT_THRESHOLD:
                                attack_name = diagnose_attack(features_df)
                                if attack_name == "ANOMALY":
                                    # Don't trigger a full red ALERT for low-volume anomalies (likely false positives)
                                    pass 
                                else:
                                    print(f"🚨 ALERT: {attack_name} | Vol: {count} | {debug_str}", flush=True)
                        else:
                            # Terminal Mode: Use \r for inplace updates
                            if anomaly_streak >= ALERT_THRESHOLD:
                                attack_name = diagnose_attack(features_df)
                                print(f"\r🚨 ALERT: {attack_name:<18} | Vol: {count:<4} | {debug_str}            ", end="")
                            elif anomaly_streak > 0:
                                print(f"\r⚠️  CHECKING...              | Vol: {count:<4} | {debug_str}            ", end="")
                            else:
                                print(f"\r🟢 NORMAL                   | Vol: {count:<4} | AE: {mse:.4f}      ", end="")
                
                message_buffer = []
                next_window_end = time.time() + WINDOW_SIZE
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n🛑 IDS Stopped.")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()
