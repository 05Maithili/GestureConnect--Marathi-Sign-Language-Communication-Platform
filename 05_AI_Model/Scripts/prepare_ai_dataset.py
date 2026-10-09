import os
import json
import csv
import random
from pathlib import Path

PROJECT_ROOT = Path("D:/Colonel/final_year_project")
METADATA_CSV = PROJECT_ROOT / "03_MediaPipe_Landmarks" / "Metadata" / "extraction_metadata.csv"
VOCAB_JSON = PROJECT_ROOT / "04_Multilingual_Dictionary" / "Vocabulary" / "sign_vocabulary.json"

AI_DIR = PROJECT_ROOT / "05_AI_Model"
DATASET_DIR = AI_DIR / "Dataset"
MANIFEST_DIR = DATASET_DIR / "Manifests"
LABEL_MAPPING = MANIFEST_DIR / "label_mapping.json"
DATASET_SUMMARY = MANIFEST_DIR / "dataset_summary.json"
DATASET_SUMMARY_MD = MANIFEST_DIR / "dataset_summary.md"

TRAIN_CSV = MANIFEST_DIR / "train.csv"
VAL_CSV = MANIFEST_DIR / "validation.csv"
TEST_CSV = MANIFEST_DIR / "test.csv"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def prepare_dataset():
    print("Preparing AI Dataset Manifests...")
    random.seed(42)  # Fixed random seed for reproducibility
    
    vocab = load_json(VOCAB_JSON)
    # Sort vocab by sign_id to ensure deterministic label mapping
    vocab = sorted(vocab, key=lambda x: x['sign_id'])
    
    # 1. Create label mapping
    label_map = {}
    for idx, entry in enumerate(vocab):
        label_map[entry['sign_id']] = idx
    save_json(LABEL_MAPPING, label_map)
    print(f"Created label mapping for {len(label_map)} classes.")
    
    # Dataset word to sign ID lookup
    word_to_sign_id = {v['dataset_word']: v['sign_id'] for v in vocab}
    
    # 2. Collect valid samples
    samples_by_sign = {sign_id: [] for sign_id in label_map.keys()}
    total_valid = 0
    missing_invalid = 0
    seen_sample_ids = set()
    
    # Read metadata
    with open(METADATA_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row['word']
            sign_id = word_to_sign_id.get(word)
            if not sign_id:
                missing_invalid += 1
                continue
                
            if row.get('normalization_status') != 'success' or not row.get('norm_file'):
                missing_invalid += 1
                continue
                
            norm_file = row['norm_file']
            file_name = Path(norm_file).name
            
            sample_id = f"{sign_id}_{file_name.replace('.npz', '')}"
            if sample_id in seen_sample_ids:
                continue
            seen_sample_ids.add(sample_id)
            
            reliable_path = str(PROJECT_ROOT / "03_MediaPipe_Landmarks" / "Normalized_Landmarks" / file_name)
            
            sample = {
                'sample_id': sample_id,
                'sign_id': sign_id,
                'label_index': label_map[sign_id],
                'canonical_word': next(v['canonical_word'] for v in vocab if v['sign_id'] == sign_id),
                'landmark_path': reliable_path,
                'sequence_length': row['sequence_length'],
                'source_video_path': row['source_path']
            }
            samples_by_sign[sign_id].append(sample)
            total_valid += 1

    # 3. Stratified Train/Val/Test Split
    # Strategy: 4 videos per sign. We want approx 70/15/15.
    # To maximize training balance, assign 3 samples per sign to Train (75%).
    # The remaining 1 sample per sign alternates between Val and Test.
    # Total: Train=75%, Val=12.5%, Test=12.5%.
    
    train_samples = []
    val_samples = []
    test_samples = []
    
    val_test_toggle = 0 # 0 for Val, 1 for Test
    
    seq_lengths = []
    
    for sign_id in sorted(samples_by_sign.keys()):
        class_samples = samples_by_sign[sign_id]
        random.shuffle(class_samples)
        
        for sample in class_samples:
            seq_lengths.append(int(sample['sequence_length']))
            
        if len(class_samples) == 4:
            train_samples.extend(class_samples[:3])
            
            if val_test_toggle == 0:
                val_samples.append(class_samples[3])
            else:
                test_samples.append(class_samples[3])
            val_test_toggle = 1 - val_test_toggle
            
        elif len(class_samples) == 3:
            train_samples.extend(class_samples[:2])
            val_samples.append(class_samples[2]) if val_test_toggle == 0 else test_samples.append(class_samples[2])
            val_test_toggle = 1 - val_test_toggle
            
        else:
            # If less, just put 70% in train
            n_train = max(1, int(len(class_samples) * 0.75))
            train_samples.extend(class_samples[:n_train])
            rem = class_samples[n_train:]
            for r in rem:
                val_samples.append(r) if val_test_toggle == 0 else test_samples.append(r)
                val_test_toggle = 1 - val_test_toggle

    # 4. Write CSV manifests
    fieldnames = ['sample_id', 'sign_id', 'label_index', 'canonical_word', 'landmark_path', 'sequence_length', 'source_video_path']
    
    for filename, samples in [(TRAIN_CSV, train_samples), (VAL_CSV, val_samples), (TEST_CSV, test_samples)]:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(samples)
            
    # 5. Generate Summary
    summary = {
        "total_source_samples_detected": total_valid + missing_invalid,
        "total_valid_samples": total_valid,
        "missing_invalid_samples": missing_invalid,
        "total_sign_ids": len(label_map),
        "train_count": len(train_samples),
        "val_count": len(val_samples),
        "test_count": len(test_samples),
        "split_percentages": {
            "train": round(len(train_samples) / total_valid * 100, 2),
            "val": round(len(val_samples) / total_valid * 100, 2),
            "test": round(len(test_samples) / total_valid * 100, 2)
        },
        "sequence_length_statistics": {
            "min": min(seq_lengths) if seq_lengths else 0,
            "max": max(seq_lengths) if seq_lengths else 0,
            "avg": round(sum(seq_lengths) / len(seq_lengths), 2) if seq_lengths else 0
        },
        "feature_dimensions": {
            "pose": "33x4",
            "left_hand": "21x3",
            "right_hand": "21x3"
        },
        "preprocessing_strategy": "dynamic_padding_and_masking",
        "random_seed": 42
    }
    
    save_json(DATASET_SUMMARY, summary)
    
    # Generate Markdown Summary
    md_content = f"""# AI Dataset Preparation (Stage 5A)

## Overview
This document outlines the dataset preprocessing and train/validation/test split strategies employed for the BiLSTM Sign Language AI Model.

## Feature Dimensions
The `.npz` files produced by MediaPipe contain:
- `pose`: 33 landmarks x 4 coordinates (x, y, z, visibility)
- `left_hand`: 21 landmarks x 3 coordinates (x, y, z)
- `right_hand`: 21 landmarks x 3 coordinates (x, y, z)

## Preprocessing & Sequence Handling
The video samples vary in frame length (Sequence Length stats: Min {summary['sequence_length_statistics']['min']}, Max {summary['sequence_length_statistics']['max']}, Avg {summary['sequence_length_statistics']['avg']}).
**Strategy chosen:** `Dynamic Padding + Masking`. 
Instead of modifying the normalized `.npz` files and risking temporal data loss or artificially creating bloated zero-padded files on disk, padding will be dynamically performed at the PyTorch/TensorFlow `DataLoader` stage using masking tensors. This ensures original sequence integrity is maintained.

## Label Mapping
Deterministic label indexes are mapped from `SIGN_0001` -> `0`, `SIGN_0002` -> `1`, etc. (See `label_mapping.json`).

## Split Strategy (Stage 5B)
Given there are precisely 4 samples per sign, achieving a randomized 70/15/15 global split while maintaining class distribution presents a mathematical challenge.

**Class-Aware Split Rules applied (Random Seed {summary['random_seed']}):**
1. 3 samples of each class are explicitly assigned to the **Training** set (Ensuring 100% class coverage and perfect balance for training).
2. The remaining 1 sample per class alternates between the **Validation** and **Test** sets.
3. This yields exactly **{summary['split_percentages']['train']}% Training**, **{summary['split_percentages']['val']}% Validation**, and **{summary['split_percentages']['test']}% Test** distribution globally, guaranteeing no class imbalance during model training.

## Dataset Statistics
- Total valid samples: {summary['total_valid_samples']}
- Train count: {summary['train_count']}
- Validation count: {summary['val_count']}
- Test count: {summary['test_count']}
"""

    with open(DATASET_SUMMARY_MD, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"Dataset preparation complete. Train: {len(train_samples)}, Val: {len(val_samples)}, Test: {len(test_samples)}")

if __name__ == "__main__":
    prepare_dataset()
