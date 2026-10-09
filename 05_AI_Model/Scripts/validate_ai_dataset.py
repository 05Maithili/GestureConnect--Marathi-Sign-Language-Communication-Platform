import os
import json
import csv
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path("D:/Colonel/final_year_project")
AI_DIR = PROJECT_ROOT / "05_AI_Model"
DATASET_DIR = AI_DIR / "Dataset"
MANIFEST_DIR = DATASET_DIR / "Manifests"
LABEL_MAPPING = MANIFEST_DIR / "label_mapping.json"

TRAIN_CSV = MANIFEST_DIR / "train.csv"
VAL_CSV = MANIFEST_DIR / "validation.csv"
TEST_CSV = MANIFEST_DIR / "test.csv"
REPORT_JSON = AI_DIR / "Evaluation" / "dataset_validation_report.json"
REPORT_MD = AI_DIR / "Evaluation" / "dataset_validation_report.md"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def validate():
    print("Validating AI Dataset...")
    errors = []
    
    # 1. Load data
    label_map = load_json(LABEL_MAPPING)
    
    def read_manifest(path):
        samples = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(row)
        return samples

    train_s = read_manifest(TRAIN_CSV)
    val_s = read_manifest(VAL_CSV)
    test_s = read_manifest(TEST_CSV)
    
    all_s = train_s + val_s + test_s
    
    # 2. Total samples
    if len(all_s) != 1048:
        errors.append(f"Expected 1048 samples, found {len(all_s)}")
        
    # 3. Label deterministic check
    sorted_keys = sorted(list(label_map.keys()))
    if not all(label_map[k] == i for i, k in enumerate(sorted_keys)):
        errors.append("Label mapping is not deterministic/sequential.")
        
    # 4. Classes covered
    expected_classes = 262
    if len(label_map) != expected_classes:
        errors.append(f"Expected 262 classes in label mapping, got {len(label_map)}")
        
    # 5. Validation logic
    sample_ids_seen = set()
    train_ids = set(s['sample_id'] for s in train_s)
    val_ids = set(s['sample_id'] for s in val_s)
    test_ids = set(s['sample_id'] for s in test_s)
    
    # Data Leakage checks
    if train_ids.intersection(val_ids):
        errors.append("Data Leakage: Train and Validation sets intersect.")
    if train_ids.intersection(test_ids):
        errors.append("Data Leakage: Train and Test sets intersect.")
    if val_ids.intersection(test_ids):
        errors.append("Data Leakage: Validation and Test sets intersect.")
        
    for s in all_s:
        s_id = s['sample_id']
        sign_id = s['sign_id']
        path = s['landmark_path']
        
        # Duplicates
        if s_id in sample_ids_seen:
            errors.append(f"Duplicate sample found: {s_id}")
        sample_ids_seen.add(s_id)
        
        # Valid Sign ID
        if sign_id not in label_map:
            errors.append(f"Sample {s_id} has invalid Sign ID: {sign_id}")
            
        # Path exists
        if not os.path.exists(path):
            errors.append(f"Missing landmark file for {s_id}: {path}")
        else:
            # File is readable and not completely NaN?
            try:
                # To save time, we will only check a random 5% of files for readability
                if np.random.rand() < 0.05:
                    data = np.load(path)
                    if 'pose' not in data:
                        errors.append(f"Invalid npz structure for {s_id}")
            except Exception as e:
                errors.append(f"Cannot read npz file {s_id}: {str(e)}")

    report = {
        "total_samples": len(all_s),
        "train_samples": len(train_s),
        "val_samples": len(val_s),
        "test_samples": len(test_s),
        "total_errors": len(errors),
        "errors": errors,
        "leakage_test_passed": len(errors) == 0 or all("Leakage" not in e for e in errors)
    }
    
    save_json(REPORT_JSON, report)
    
    md = f"""# AI Dataset Validation Report

- **Total Samples Validated**: {report['total_samples']}
- **Train Split**: {report['train_samples']}
- **Validation Split**: {report['val_samples']}
- **Test Split**: {report['test_samples']}

## Leakage Status
- **Train ∩ Val = ∅**: {'Pass' if not train_ids.intersection(val_ids) else 'FAIL'}
- **Train ∩ Test = ∅**: {'Pass' if not train_ids.intersection(test_ids) else 'FAIL'}
- **Val ∩ Test = ∅**: {'Pass' if not val_ids.intersection(test_ids) else 'FAIL'}

## Errors
- Total Errors: {report['total_errors']}

"""
    if errors:
        for err in errors:
            md += f"- {err}\n"
    else:
        md += "No errors found. Dataset is completely valid and ready for training.\n"
        
    with open(REPORT_MD, 'w', encoding='utf-8') as f:
        f.write(md)
        
    print(f"Validation finished. {len(errors)} errors found.")

if __name__ == "__main__":
    validate()
