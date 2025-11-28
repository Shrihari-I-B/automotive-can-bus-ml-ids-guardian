import pandas as pd
import numpy as np
import math
from collections import Counter
import argparse
import sys

def calculate_entropy(data_series):
    """Calculates Shannon Entropy for a series of values."""
    if len(data_series) == 0:
        return 0.0
    counts = data_series.value_counts()
    probabilities = counts / len(data_series)
    return -sum(probabilities * np.log2(probabilities))

def hex_to_int(hex_str):
    """Converts hex string to int, handling potential errors."""
    try:
        return int(str(hex_str), 16)
    except (ValueError, TypeError):
        return 0

def process_window(window):
    """
    Aggregates a 100ms window of CAN messages into a single feature vector.
    """
    if window.empty:
        return None

    # 1. Basic Counts
    msg_count = len(window)
    
    # 2. ID Statistics
    unique_ids = window['arbitration_id'].nunique()
    id_entropy = calculate_entropy(window['arbitration_id'])
    
    # 3. Payload Statistics (Entropy of the data bytes)
    # We treat the entire data payload as a "symbol" for entropy calculation
    payload_entropy = calculate_entropy(window['data_hex'])
    
    # 4. Timing Statistics (Inter-Arrival Time)
    # Calculate time diff between consecutive messages in this window
    window = window.sort_values('timestamp')
    iat = window['timestamp'].diff().dropna()
    
    if not iat.empty:
        iat_mean = iat.mean()
        iat_std = iat.std()
        iat_min = iat.min()
        iat_max = iat.max()
    else:
        iat_mean = 0
        iat_std = 0
        iat_min = 0
        iat_max = 0

    # 5. Labeling (Ground Truth)
    # If ANY packet in this window is marked as an attack, the whole window is an attack.
    # This is a conservative approach for safety-critical systems.
    label = 1 if (window['label'] == 1).any() else 0
    
    # Return Feature Vector
    return pd.Series({
        'msg_count': msg_count,
        'unique_ids': unique_ids,
        'id_entropy': id_entropy,
        'payload_entropy': payload_entropy,
        'iat_mean': iat_mean,
        'iat_std': iat_std,
        'iat_min': iat_min,
        'iat_max': iat_max,
        'label': label
    })

def main():
    parser = argparse.ArgumentParser(description="Build Time-Windowed Features from CAN Logs")
    parser.add_argument("--input", required=True, help="Input parsed CSV file (e.g. dataset.csv)")
    parser.add_argument("--output", required=True, help="Output Feature Matrix CSV")
    parser.add_argument("--window", type=float, default=0.1, help="Window size in seconds (default 0.1s)")
    args = parser.parse_args()

    print(f"⚙️  Processing {args.input} into {args.window}s windows...")
    
    # Load Data
    try:
        df = pd.read_csv(args.input)
    except FileNotFoundError:
        print("❌ Error: Input file not found.")
        sys.exit(1)

    # Ensure timestamp is sorted
    df = df.sort_values('timestamp')
    
    # Convert timestamp to datetime for resampling (Simulated timestamp is float seconds)
    # We create a dummy datetime index starting from "now" just for pandas resampling
    start_time = pd.Timestamp.now()
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', origin=start_time)
    
    # Set Index
    df.set_index('datetime', inplace=True)
    
    # Resample and Aggregate
    # This applies 'process_window' to every 100ms chunk of data
    print("   Aggregating windows (this may take time)...")
    feature_matrix = df.resample(f'{int(args.window*1000)}ms').apply(process_window)
    
    # Drop empty windows (if simulation had gaps)
    feature_matrix.dropna(inplace=True)
    
    # Save
    feature_matrix.to_csv(args.output, index=False)
    
    print(f"✅ Feature Matrix Saved: {args.output}")
    print(f"   Original Rows: {len(df)}")
    print(f"   Windowed Rows: {len(feature_matrix)}")
    print(f"   Attack Windows: {feature_matrix['label'].sum()}")

if __name__ == "__main__":
    main()
