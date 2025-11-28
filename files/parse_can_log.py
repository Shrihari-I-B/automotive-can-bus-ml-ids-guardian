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
        print(f"❌ Error: Input file '{input_file}' not found.")
        return

    print(f"Parsing {input_file}...")
    pattern = re.compile(r"\((\d+\.\d+)\)\s+(\w+)\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)")

    try:
        with open(input_file, 'r') as f:
            for line in f:
                m = pattern.match(line.strip())
                if m:
                    ts, iface, can_id, data = float(m.group(1)), m.group(2), m.group(3).upper(), m.group(4).upper()
                    name = ECU_MAPPING.get(can_id, "unknown")
                    label = 0 
                    
                    if can_id == "000":
                        label = 1
                        name = "attack_flood"
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
    except Exception as e:
        print(f"❌ Error reading log: {e}")

    # Create DataFrame
    df = pd.DataFrame(rows)

    # FORCE COLUMNS if empty or missing
    required_cols = ["timestamp", "arbitration_id", "data_hex", "label", "type"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    if df.empty:
        print("⚠️  Log file produced 0 valid rows.")
    else:
        # Timing Logic
        total_duration = df['timestamp'].max() - df['timestamp'].min()
        start_time = df['timestamp'].min()
        
        print(f"   Log Duration: {total_duration:.1f}s")
        
        attack_start = 0
        attack_end = 0
        
        # Detect Run Type
        if total_duration > 400: # Huge Run
            attack_start = start_time + 480
            attack_end = start_time + 510
            print("   Mode: Huge Dataset (T+480 start)")
        elif total_duration > 90: # Balanced Run
            attack_start = start_time + 60
            attack_end = start_time + 70
            print("   Mode: Balanced Dataset (T+60 start)")
        else: # Short Run
            attack_start = start_time + 15
            attack_end = start_time + 30
            print("   Mode: Short Dataset (T+15 start)")
            
        # Apply Context Labels
        mask = (df['timestamp'] >= attack_start) & (df['timestamp'] <= attack_end) & (df['arbitration_id'] == "310")
        if mask.any():
            df.loc[mask, 'label'] = 1
            df.loc[mask, 'type'] = "context_spoof_injected"
            print(f"   Labeled {mask.sum()} context spoof packets.")

    # Save
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved {output_csv} ({len(df)} rows)")
    
    # Safe Print Stats
    if not df.empty and 'label' in df.columns:
        # Convert label to numeric just in case
        df['label'] = pd.to_numeric(df['label'], errors='coerce').fillna(0)
        n_benign = len(df[df['label'] == 0])
        n_attack = len(df[df['label'] == 1])
        print(f"   Benign: {n_benign}")
        print(f"   Attack: {n_attack}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_can_log.py <logfile> [output.csv]")
    elif len(sys.argv) == 3:
        parse_log(sys.argv[1], sys.argv[2])
    else:
        # Smart Output Naming
        base = os.path.splitext(sys.argv[1])[0]
        if "raw" in base:
            out = base.replace("raw", "parsed") + ".csv"
        else:
            out = base + ".csv"
        parse_log(sys.argv[1], out)
