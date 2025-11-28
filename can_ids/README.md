Research-Grade Intrusion Detection System for Automotive CAN Bus

🎓 Project Overview

This framework implements a Cyber-Physical Intrusion Detection System (IDS) for Controller Area Networks (CAN). Unlike traditional IDSs that rely on simple rule-based detection, this system uses a Stateful Finite State Machine (FSM) to simulate realistic vehicle physics and an Ensemble Machine Learning Model (One-Class SVM + Autoencoder) to detect Context-Aware attacks.

Key Capabilities:

Stateful Simulation: Models the correlation between Engine RPM, Gear, and Speed (Physics-Aware).

Context-Aware Attacks: Attackers that listen to the bus and strike only during vulnerable states (e.g., forcing a downshift while cruising).

Unsupervised Learning: Trained exclusively on benign data to detect zero-day anomalies.

Real-Time Diagnosis: Classifies attacks as Flooding (DoS) or Context Spoofing/Replay in real-time.

📂 Directory Structure

can_ids/
├── can_ids_framework/
│   ├── main_orchestrator.py    # Automated Dataset Generator
│   ├── main_live_ids.py        # Real-Time IDS Engine
│   ├── run_simulation_v2.py    # Physics-Based Vehicle Simulator
│   ├── run_tests.py            # Unit Testing Suite
│   ├── generate_thesis_plots.py# Results Visualization
│   ├── can_ids/
│   │   ├── simulation/         # FSM & Virtual ECUs
│   │   ├── attacks/            # Flood, Replay, Context Spoof
│   │   ├── processing/         # Feature Engineering (Entropy, IAT)
│   │   └── models/             # ML Training Scripts
├── parse_can_log.py            # Log Parser & Labeler
└── README.md


🚀 Usage Instructions

Phase 1: Setup

Ensure your virtual CAN interface is active.

./setup_vcan.sh


Phase 2: Data Generation (The Experiment)

Run the orchestrator to generate a balanced, high-quality dataset (~10 minutes).

python3 can_ids_framework/main_orchestrator.py


Output: research_features.csv

Phase 3: Training the Models

Train the unsupervised models on the benign data extracted from the experiment.

# Train One-Class SVM (Statistical Boundary)
python3 can_ids_framework/can_ids/models/train_ocsvm.py research_features.csv

# Train Autoencoder (Reconstruction Error)
python3 can_ids_framework/can_ids/models/train_autoencoder.py research_features.csv


Phase 4: Live Demonstration (The "Demo")

Open 3 separate terminals to demonstrate the full cyber-physical loop.

Terminal 1 (Simulator):

python3 can_ids_framework/run_simulation_v2.py


Terminal 2 (IDS Monitor):

python3 can_ids_framework/main_live_ids.py


Terminal 3 (Attacker):

# Attack 1: Context Spoofing (Wait for 'Target Acquired')
python3 can_ids_framework/can_ids/attacks/context_spoof.py

# Attack 2: Flooding (DoS)
python3 can_ids_framework/can_ids/attacks/flood.py


📊 Scientific Methodology

1. Feature Engineering

Instead of raw packet inspection, we aggregate traffic into 0.1s Time Windows and extract:

Entropy: Information density of payloads (Detects Random Fuzzing).

Inter-Arrival Time (IAT): Mean/Std Dev of message timing (Detects Flooding).

Message Volume: Traffic density (Detects DoS).

2. Ensemble Detection Logic

The IDS uses a logical OR-Gate architecture:

Model A (OC-SVM): Detects statistical outliers in feature space.

Model B (Autoencoder): Detects structural anomalies via Reconstruction Error (MSE).

Decision: Alarm = (SVM_Anomaly) OR (MSE > Threshold)

3. Diagnostic Expert System

Once an anomaly is flagged, a heuristic rule-base classifies the threat:

High Volume OR Low IAT $\rightarrow$ FLOODING / DOS

High Entropy $\rightarrow$ FUZZING

Normal Volume + Anomaly $\rightarrow$ SPOOFING / REPLAY

📈 Results & Performance

To generate the confusion matrices and reconstruction error histograms for your thesis report:

python3 can_ids_framework/generate_thesis_plots.py


Results will be saved in thesis_results/.

Author: Shrihari B
Institution: K.S. Institute of Technology
Project: BCS586 - Simulation Based IDS for Automotive CAN Bus
