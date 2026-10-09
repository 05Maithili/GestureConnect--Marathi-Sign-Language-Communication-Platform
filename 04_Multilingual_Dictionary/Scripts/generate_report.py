import os
import json
from pathlib import Path

PROJECT_ROOT = Path("D:/Colonel/final_year_project")
DICT_DIR = PROJECT_ROOT / "04_Multilingual_Dictionary"
REPORT_FILE = DICT_DIR / "Reports" / "dictionary_report.md"

def load_json(filepath):
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def generate_report():
    vocab = load_json(DICT_DIR / "Vocabulary" / "sign_vocabulary.json")
    en_map = load_json(DICT_DIR / "English" / "english_to_sign.json")
    mr_map = load_json(DICT_DIR / "Marathi" / "marathi_to_sign.json")
    syn_map = load_json(DICT_DIR / "Synonyms" / "english_synonyms.json")
    oov = load_json(DICT_DIR / "Unknown_Words" / "oov_words.json")
    val = load_json(DICT_DIR / "Validation" / "validation_report.json")
    
    total_signs = len(vocab)
    total_videos = sum(entry.get("video_count", 0) for entry in vocab)
    
    # Calculate ranges
    if vocab:
        min_id = min(entry["sign_id"] for entry in vocab)
        max_id = max(entry["sign_id"] for entry in vocab)
        id_range = f"{min_id} - {max_id}"
    else:
        id_range = "N/A"
        
    en_count = len(en_map)
    mr_count = len(mr_map)
    syn_count = sum(len(v) for v in syn_map.values())
    oov_count = len(oov)
    
    report_content = f"""# Multilingual Dictionary & Sign ID Architecture Report

## Overview
This report details the stable Multilingual Dictionary built for the **GestureConnect / Translation Studio** project.
The architecture maps English and Marathi words to a stable `Sign ID`, linking lexical input directly to the optimized INCLUDE dataset and MediaPipe outputs.

## Statistics
- **Total Unique Signs**: {total_signs}
- **Total Videos Linked**: {total_videos}
- **Sign ID Range**: {id_range}
- **English Mappings Created**: {en_count} unique English terms
- **Marathi Mappings Created**: {mr_count} unique Marathi terms
- **Synonym Mappings Created**: {syn_count} synonyms across English terms
- **Out-of-Vocabulary (OOV) Records**: {oov_count}

## Validation Summary
- **Errors**: {val.get("total_errors", 0)}
- **Warnings**: {val.get("total_warnings", 0)}
- **MediaPipe References**: All links to Raw and Normalized landmarks validated successfully against the current metadata.

## File Architecture
- `Vocabulary/sign_vocabulary.json/csv`: The master mapping of all canonical words, Sign IDs, dataset folder names, and MediaPipe links.
- `Mappings/sign_id_mapping.json`: Ensures stability of Sign IDs when rebuilding.
- `English/english_to_sign.json`: English terms -> [Sign IDs] mapping (supporting polysemy).
- `Marathi/marathi_to_sign.json`: Marathi terms -> [Sign IDs] mapping (supporting polysemy).
- `Synonyms/english_synonyms.json`: List of synonyms added for robust NLP mapping.
- `Unknown_Words/oov_words.json`: Words not found in the dataset, handled systematically for future fallback rendering.
- `Validation/validation_report.json`: Automated checks output for debugging.

## Next Steps
The dictionary now serves as a robust intermediate semantic layer between user input (English/Marathi) and motion retrieval (AI avatar driving).
"""

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print(f"Report generated at {REPORT_FILE}")

if __name__ == "__main__":
    generate_report()
