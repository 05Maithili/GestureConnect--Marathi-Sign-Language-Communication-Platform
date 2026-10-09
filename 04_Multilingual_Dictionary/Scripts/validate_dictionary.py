import os
import json
import csv
from pathlib import Path

PROJECT_ROOT = Path("D:/Colonel/final_year_project")
DATASET_DIR = PROJECT_ROOT / "02_INCLUDE_Dataset_Optimized"
MEDIAPIPE_DIR = PROJECT_ROOT / "03_MediaPipe_Landmarks"
DICT_DIR = PROJECT_ROOT / "04_Multilingual_Dictionary"

VOCAB_JSON = DICT_DIR / "Vocabulary" / "sign_vocabulary.json"
EN_MAPPING_FILE = DICT_DIR / "English" / "english_to_sign.json"
MR_MAPPING_FILE = DICT_DIR / "Marathi" / "marathi_to_sign.json"
OOV_FILE = DICT_DIR / "Unknown_Words" / "oov_words.json"
REPORT_FILE = DICT_DIR / "Validation" / "validation_report.json"

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def validate():
    print("Validating Dictionary...")
    errors = []
    warnings = []
    
    vocab = load_json(VOCAB_JSON)
    if vocab is None:
        errors.append(f"Could not load or parse {VOCAB_JSON.name}")
        vocab = []
        
    en_map = load_json(EN_MAPPING_FILE) or {}
    mr_map = load_json(MR_MAPPING_FILE) or {}
    oov_list = load_json(OOV_FILE) or []
    
    sign_ids = set()
    canonical_terms = set()
    
    # Check for OOV assigned IDs
    oov_terms = {o.get('term') if isinstance(o, dict) else o for o in oov_list}
    
    mp_meta_file = MEDIAPIPE_DIR / "Metadata" / "extraction_metadata.csv"
    mp_meta = []
    if mp_meta_file.exists():
        with open(mp_meta_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mp_meta.append(row)
                
    for entry in vocab:
        sign_id = entry.get("sign_id")
        canonical = entry.get("canonical_word")
        ds_word = entry.get("dataset_word")
        
        # 1. duplicates
        if sign_id in sign_ids:
            errors.append(f"Duplicate Sign ID found: {sign_id}")
        else:
            sign_ids.add(sign_id)
            
        if canonical in canonical_terms:
            errors.append(f"Duplicate Canonical Term found: {canonical}")
        else:
            canonical_terms.add(canonical)
            
        # 2. Missing fields
        if not sign_id:
            errors.append(f"Missing Sign ID for entry: {canonical}")
        if not canonical:
            errors.append(f"Missing Canonical Word for Sign ID: {sign_id}")
            
        # 3. Mappings exist?
        if canonical not in en_map:
            errors.append(f"Missing English mapping for Canonical: {canonical}")
        elif sign_id not in en_map[canonical]:
            errors.append(f"Inconsistent English mapping for {canonical}: {sign_id} not in {en_map[canonical]}")
            
        if not entry.get("marathi_terms"):
            warnings.append(f"Missing Marathi terms for: {canonical}")
        else:
            for mr in entry["marathi_terms"]:
                if mr not in mr_map:
                    errors.append(f"Missing Marathi mapping for {mr}")
                elif sign_id not in mr_map[mr]:
                    errors.append(f"Inconsistent Marathi mapping for {mr}: {sign_id} not in {mr_map[mr]}")
                    
        # 4. Paths and references
        # Check dataset folder
        ds_path = DATASET_DIR / ds_word
        if not ds_path.exists():
            errors.append(f"Broken dataset path for {ds_word}")
            
        # Check media pipe files
        # Find all videos for this dataset word in metadata
        related_videos = [row for row in mp_meta if row['word'] == ds_word]
        for vid in related_videos:
            raw_path = vid.get('raw_file', '')
            norm_path = vid.get('norm_file', '')
            
            # Since paths in CSV might be absolute to another drive, let's just check the filename in our local path
            if raw_path and 'success' in vid.get('extraction_status', ''):
                local_raw = MEDIAPIPE_DIR / "Raw_Landmarks" / Path(raw_path).name
                if not local_raw.exists():
                    errors.append(f"Missing raw landmark file: {local_raw.name}")
                    
            if norm_path and 'success' in vid.get('normalization_status', ''):
                local_norm = MEDIAPIPE_DIR / "Normalized_Landmarks" / Path(norm_path).name
                if not local_norm.exists():
                    errors.append(f"Missing normalized landmark file: {local_norm.name}")
                    
        if canonical in oov_terms:
            errors.append(f"OOV word {canonical} is incorrectly assigned a Sign ID {sign_id}")

    # Check for OOV assigned valid IDs (reverse check)
    for oov in oov_terms:
        if oov in en_map:
            errors.append(f"OOV term '{oov}' exists in English mappings!")
            
    report = {
        "total_signs": len(vocab),
        "total_errors": len(errors),
        "total_warnings": len(warnings),
        "errors": errors,
        "warnings": warnings
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    print(f"Validation Complete. {len(errors)} Errors, {len(warnings)} Warnings.")
    if errors:
        print("See Validation/validation_report.json for details.")
        
if __name__ == "__main__":
    validate()
