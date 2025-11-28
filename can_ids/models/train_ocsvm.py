import pandas as pd
import numpy as np
import joblib
import argparse
import sys
import os
from pathlib import Path
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# === PATH SETUP ===
# Find the root directory (assuming structure: root/can_ids_framework/can_ids/models/this_script.py)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent # Adjust based on nesting depth
# Actually, a safer way is to look for the file relative to where the user likely is (root)
# Or pass it as an argument. 

# Let's default to looking in the current working directory OR the project root if possible.
# But the best way is to let the user pass the path, and if they don't, try to find it.

MODEL_FILENAME = "ocsvm_model.joblib"
SCALER_FILENAME = "scaler.joblib"

def load_data(csv_path):
    print(f"📂 Loading dataset: {csv_path}...")
    if not os.path.exists(csv_path):
        # Try looking in the project root if not found in current dir
        # Assuming we are inside can_ids_framework/...
        # Let's try to go up 3 levels to find it
        potential_path = Path(__file__).resolve().parent.parent.parent.parent / csv_path
        if potential_path.exists():
            print(f"   Found at: {potential_path}")
            return pd.read_csv(potential_path)
        
        print(f"❌ Error: File {csv_path} not found.")
        sys.exit(1)
        
    return pd.read_csv(csv_path)

def train_one_class_svm(input_csv):
    # 1. Load Data
    df = load_data(input_csv)
    
    feature_cols = ['msg_count', 'unique_ids', 'id_entropy', 'payload_entropy', 'iat_mean', 'iat_std']
    
    # 2. Data Preparation
    benign_df = df[df['label'] == 0]
    attack_df = df[df['label'] == 1]
    
    print(f"   Total Rows: {len(df)}")
    print(f"   Benign Samples: {len(benign_df)}")
    print(f"   Attack Samples: {len(attack_df)}")
    
    if len(benign_df) < 100:
        print("❌ Error: Not enough benign data to train One-Class SVM.")
        return

    # 3. Split Data
    # Training Set: 80% of Benign Data
    X_train_raw, X_test_benign = train_test_split(benign_df[feature_cols], test_size=0.2, random_state=42)
    
    # Test Set: Remaining 20% Benign + All Attack Data
    X_test_raw = pd.concat([X_test_benign, attack_df[feature_cols]])
    
    # Ground Truth Labels for Test Set (0=Normal, 1=Attack)
    y_test = np.concatenate([np.zeros(len(X_test_benign)), np.ones(len(attack_df))])
    
    # 4. Scaling
    print("⚖️  Scaling features...")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test = scaler.transform(X_test_raw)
    
    # 5. Train Model
    print("🧠 Training One-Class SVM (Unsupervised)...")
    # nu=0.01 (1% allowed outliers)
    ocsvm = OneClassSVM(kernel='rbf', gamma='scale', nu=0.01)
    ocsvm.fit(X_train)
    
    # 6. Evaluation
    print("📝 Evaluating Model...")
    y_pred_raw = ocsvm.predict(X_test)
    y_pred = [0 if x == 1 else 1 for x in y_pred_raw]
    
    print("\n" + "="*40)
    print("       ONE-CLASS SVM RESULTS       ")
    print("="*40)
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Benign', 'Attack']))
    
    # 7. Save Artifacts (Save to the ROOT folder so Live IDS can find them)
    # Calculate root path: .../can_ids/
    save_dir = Path(__file__).resolve().parent.parent.parent.parent
    model_path = save_dir / MODEL_FILENAME
    scaler_path = save_dir / SCALER_FILENAME
    
    print(f"\n💾 Saving model to {model_path}...")
    joblib.dump(ocsvm, model_path)
    joblib.dump(scaler, scaler_path)
    print("✅ Training Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train One-Class SVM on Benign Data")
    parser.add_argument("input_csv", help="Path to feature matrix CSV (e.g., research_features.csv)")
    args = parser.parse_args()
    
    train_one_class_svm(args.input_csv)
