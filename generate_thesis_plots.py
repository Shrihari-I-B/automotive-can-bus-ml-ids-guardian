import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import sys
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
from pathlib import Path

# Mute TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from tensorflow.keras.models import load_model

# === CONFIGURATION ===
BASE_DIR = Path(__file__).resolve().parent.parent # .../can_ids
DATA_FILE = BASE_DIR / "research_features.csv"
MODEL_OCSVM = BASE_DIR / "ocsvm_model.joblib"
MODEL_AE = BASE_DIR / "autoencoder_model.keras"
SCALER_PATH = BASE_DIR / "scaler.joblib"
THRESH_PATH = BASE_DIR / "ae_threshold.npy"
OUTPUT_DIR = BASE_DIR / "thesis_results"

# Feature Columns (Must match training)
FEATURE_COLS = ['msg_count', 'unique_ids', 'id_entropy', 'payload_entropy', 'iat_mean', 'iat_std']

def generate_plots():
    print("📊 GENERATING THESIS RESULTS...")
    
    # 1. Create Output Directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 2. Load Data & Models
    if not DATA_FILE.exists():
        print(f"❌ Error: Data file {DATA_FILE} not found.")
        return

    print("   Loading Data & Models...", end=" ")
    df = pd.read_csv(DATA_FILE)
    scaler = joblib.load(SCALER_PATH)
    ocsvm = joblib.load(MODEL_OCSVM)
    autoencoder = load_model(MODEL_AE)
    ae_threshold = np.load(THRESH_PATH)
    print("✅ Done.")

    # 3. Preprocessing
    X = df[FEATURE_COLS]
    y_true = df['label']
    X_scaled = scaler.transform(X)

    # 4. Run Predictions
    print("   Running Predictions for Evaluation...")
    
    # OCSVM
    y_pred_ocsvm = ocsvm.predict(X_scaled)
    y_pred_ocsvm = [1 if x == -1 else 0 for x in y_pred_ocsvm] # Convert -1 to 1 (Attack)

    # Autoencoder
    reconstructions = autoencoder.predict(X_scaled, verbose=0)
    mse = np.mean(np.power(X_scaled - reconstructions, 2), axis=1)
    y_pred_ae = [1 if error > ae_threshold else 0 for error in mse]

    # Ensemble (OR Gate)
    y_pred_ensemble = [1 if (o == 1 or a == 1) else 0 for o, a in zip(y_pred_ocsvm, y_pred_ae)]

    # 5. Generate Confusion Matrices
    print("   Plotting Confusion Matrices...")
    
    models = {
        "One-Class SVM": y_pred_ocsvm,
        "Autoencoder": y_pred_ae,
        "Ensemble (Hybrid)": y_pred_ensemble
    }

    plt.figure(figsize=(18, 5))
    for i, (name, preds) in enumerate(models.items()):
        plt.subplot(1, 3, i+1)
        cm = confusion_matrix(y_true, preds)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.title(f'{name} Confusion Matrix')
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.xticks([0.5, 1.5], ['Benign', 'Attack'])
        plt.yticks([0.5, 1.5], ['Benign', 'Attack'])
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "confusion_matrices.png")
    plt.close()

    # 6. Generate Reconstruction Error Histogram (Critical for AE)
    print("   Plotting Reconstruction Error Distribution...")
    plt.figure(figsize=(10, 6))
    
    # Separate Benign and Attack MSE
    benign_mse = mse[y_true == 0]
    attack_mse = mse[y_true == 1]
    
    plt.hist(benign_mse, bins=50, alpha=0.6, color='green', label='Benign Traffic', range=(0, 10))
    plt.hist(attack_mse, bins=50, alpha=0.6, color='red', label='Attack Traffic', range=(0, 10))
    plt.axvline(ae_threshold, color='black', linestyle='dashed', linewidth=2, label=f'Threshold ({ae_threshold:.2f})')
    
    plt.title('Autoencoder Reconstruction Error Separation')
    plt.xlabel('Mean Squared Error (MSE)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(OUTPUT_DIR / "reconstruction_error_dist.png")
    plt.close()

    # 7. Save Text Report
    print("   Saving Performance Metrics...")
    with open(OUTPUT_DIR / "performance_report.txt", "w") as f:
        f.write("=== THESIS PERFORMANCE REPORT ===\n\n")
        for name, preds in models.items():
            f.write(f"--- {name} ---\n")
            f.write(classification_report(y_true, preds, target_names=['Benign', 'Attack']))
            f.write("\n\n")

    print(f"\n✅ COMPLETED. Results saved in: {OUTPUT_DIR}")
    print("   1. confusion_matrices.png (Visual proof of accuracy)")
    print("   2. reconstruction_error_dist.png (Visual proof of anomaly separation)")
    print("   3. performance_report.txt (Precision/Recall numbers)")

if __name__ == "__main__":
    generate_plots()

