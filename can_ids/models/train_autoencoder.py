import pandas as pd
import numpy as np
import joblib
import argparse
import sys
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Silence TensorFlow logs

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.callbacks import EarlyStopping

# === CONFIGURATION ===
MODEL_FILENAME = "autoencoder_model.keras"
THRESHOLD_FILENAME = "ae_threshold.npy"
SCALER_FILENAME = "scaler.joblib" # We share the scaler with OCSVM

def load_data(csv_path):
    print(f"📂 Loading dataset: {csv_path}...")
    if not os.path.exists(csv_path):
        # Try finding in root
        csv_path = os.path.join(os.getcwd(), csv_path)
        if not os.path.exists(csv_path):
            print(f"❌ Error: File {csv_path} not found.")
            sys.exit(1)
    return pd.read_csv(csv_path)

def train_autoencoder(input_csv):
    # 1. Load Data
    df = load_data(input_csv)
    feature_cols = ['msg_count', 'unique_ids', 'id_entropy', 'payload_entropy', 'iat_mean', 'iat_std']
    
    # Filter for Benign ONLY (Label 0)
    benign_df = df[df['label'] == 0]
    print(f"   Training on {len(benign_df)} Benign samples...")

    # 2. Scaling
    # We MUST use the same scaling logic as the OCSVM.
    # If scaler exists, load it. If not, create it.
    if os.path.exists(SCALER_FILENAME):
        print("   Loading existing scaler...")
        scaler = joblib.load(SCALER_FILENAME)
    else:
        print("   Creating new scaler...")
        scaler = StandardScaler()
        scaler.fit(benign_df[feature_cols])
        joblib.dump(scaler, SCALER_FILENAME)

    X_train = scaler.transform(benign_df[feature_cols])

    # 3. Define Autoencoder Architecture
    input_dim = X_train.shape[1] # 6 Features
    
    # Encoder
    input_layer = Input(shape=(input_dim,))
    encoder = Dense(4, activation="relu")(input_layer)
    bottleneck = Dense(2, activation="relu")(encoder) # Compress to 2 dimensions
    
    # Decoder
    decoder = Dense(4, activation="relu")(bottleneck)
    output_layer = Dense(input_dim, activation="linear")(decoder) # Linear for StandardScaled data
    
    autoencoder = Model(inputs=input_layer, outputs=output_layer)
    
    autoencoder.compile(optimizer='adam', loss='mse')
    
    # 4. Train
    print("🧠 Training Autoencoder Neural Network...")
    history = autoencoder.fit(
        X_train, X_train, # Input = Output (Reconstruction)
        epochs=50,
        batch_size=32,
        validation_split=0.1,
        shuffle=True,
        verbose=0,
        callbacks=[EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)]
    )
    
    # 5. Determine Threshold
    # We calculate the reconstruction error (MSE) for all benign training data.
    # The threshold is set to the 99th percentile (allowing 1% noise).
    print("📊 Calculating Anomaly Threshold...")
    reconstructions = autoencoder.predict(X_train, verbose=0)
    mse = np.mean(np.power(X_train - reconstructions, 2), axis=1)
    threshold = np.percentile(mse, 99.9) # Very strict threshold (99.9%)
    
    print(f"   Max Benign Error: {np.max(mse):.6f}")
    print(f"   Selected Threshold: {threshold:.6f}")

    # 6. Save Artifacts
    # Calculate root path to save alongside other models
    save_dir = os.getcwd()
    model_path = os.path.join(save_dir, MODEL_FILENAME)
    thresh_path = os.path.join(save_dir, THRESHOLD_FILENAME)
    
    print(f"\n💾 Saving model to {model_path}...")
    autoencoder.save(model_path)
    np.save(thresh_path, threshold)
    print("✅ Training Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Autoencoder on Benign Data")
    parser.add_argument("input_csv", help="Path to feature matrix CSV")
    args = parser.parse_args()
    train_autoencoder(args.input_csv)
