import sys
import os
import re
import pandas as pd

ECU_MAPPING = {
    "123": "ecu_engine_rpm",
    "240": "ecu_abs_status",
    "310": "ecu_transmission",
    "4F0": "ecu_infotainment",
    "500": "ecu_body_control",
    "000": "attack_flood",
}

def parse_log(input_file, output_csv):
    rows = []
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    print(f"Parsing {input_file}...")
    # Regex matches: (16200.00) vcan0 123#112233
    pattern = re.compile(r"\((\d+\.\d+)\)\s+(\w+)\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)")

    with open(input_file, 'r') as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                ts, iface, can_id, data = float(m.group(1)), m.group(2), m.group(3).upper(), m.group(4).upper()
                name = ECU_MAPPING.get(can_id, "unknown")
                
                label = 0 
                
                # 1. Flood Attack
                if can_id == "000":
                    label = 1
                    name = "attack_flood"
                
                # 2. Fuzzing (Unknown IDs)
                elif can_id not in ECU_MAPPING and can_id != "000":
                    label = 1
                    name = "attack_fuzz"

                rows.append({
                    "timestamp": ts,
                    "arbitration_id": can_id,
                    "data_hex": data,
                    "label": label,
                    "type": name
                })

    df = pd.DataFrame(rows)

    # 3. Label Context Attack (Heuristic)
    # The Context attack happens in the middle phase (approx 15s to 30s in a 35s run)
    # Since we can't easily detect "Context Spoof" by ID alone (it looks valid),
    # we label the middle chunk of the dataset if we detect anomalies.
    # For research, we often use the explicit timestamps from the orchestrator,
    # but here we will use a time-window heuristic.
    
    if not df.empty:
        total_duration = df['timestamp'].max() - df['timestamp'].min()
        start_time = df['timestamp'].min()
        
        # Attack Phase is roughly from T+15s to T+30s
        attack_start = start_time + 15
        attack_end = start_time + 30
        
        # Mark rows in this window as potential attacks if they match the spoof ID
        mask = (df['timestamp'] >= attack_start) & (df['timestamp'] <= attack_end) & (df['arbitration_id'] == "310")
        df.loc[mask, 'label'] = 1
        df.loc[mask, 'type'] = "context_spoof_injected"

    df.to_csv(output_csv, index=False)
    print(f"✅ Saved {output_csv} ({len(df)} rows)")
    print(f"   Benign: {len(df[df['label']==0])}")
    print(f"   Attack: {len(df[df['label']==1])}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_can_log.py <logfile> [output.csv]")
    elif len(sys.argv) == 3:
        parse_log(sys.argv[1], sys.argv[2])
    else:
        parse_log(sys.argv[1], sys.argv[1] + ".csv")
