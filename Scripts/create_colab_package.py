import os
import shutil
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path("D:/Colonel/final_year_project")
SRC_NPZ_DIR = PROJECT_ROOT / "03_MediaPipe_Landmarks" / "Normalized_Landmarks"
SRC_MANIFEST_DIR = PROJECT_ROOT / "05_AI_Model" / "Dataset" / "Manifests"

BASE_PACKAGE_NAME = "Colab_Training_Package"
BASE_ZIP_NAME = "GestureConnect_Colab_Training_Data"

REQUIRED_FILES = [
    SRC_NPZ_DIR,
    SRC_MANIFEST_DIR / "train.csv",
    SRC_MANIFEST_DIR / "validation.csv",
    SRC_MANIFEST_DIR / "test.csv",
    SRC_MANIFEST_DIR / "label_mapping.json",
    SRC_MANIFEST_DIR / "dataset_summary.json"
]

def get_unique_path(base_path, is_dir=True):
    path = PROJECT_ROOT / base_path
    if not path.exists():
        return path
    
    counter = 1
    while True:
        new_path = PROJECT_ROOT / f"{base_path}_{counter}"
        if not new_path.exists():
            return new_path
        counter += 1

def main():
    print("Verifying source paths...")
    missing = []
    for req in REQUIRED_FILES:
        if not req.exists():
            missing.append(str(req))
            
    if missing:
        print("ERROR: Missing required source paths:")
        for m in missing:
            print(f" - {m}")
        return

    # Count source npz
    src_npz_files = list(SRC_NPZ_DIR.glob("*.npz"))
    src_npz_count = len(src_npz_files)
    print(f"Found {src_npz_count} source .npz files.")

    # Create safe package folder
    package_dir = get_unique_path(BASE_PACKAGE_NAME)
    print(f"Creating package directory at: {package_dir}")
    os.makedirs(package_dir)
    
    dest_npz_dir = package_dir / "Normalized_Landmarks"
    dest_manifest_dir = package_dir / "Manifests"
    
    os.makedirs(dest_npz_dir)
    os.makedirs(dest_manifest_dir)
    
    print("Copying .npz files (This might take a moment)...")
    for npz_file in src_npz_files:
        shutil.copy2(npz_file, dest_npz_dir / npz_file.name)
        
    copied_npz_count = len(list(dest_npz_dir.glob("*.npz")))
    
    print("Copying and converting CSV manifests to use relative paths...")
    manifests = ["train.csv", "validation.csv", "test.csv"]
    sample_counts = {}
    
    for m in manifests:
        src_csv = SRC_MANIFEST_DIR / m
        dest_csv = dest_manifest_dir / m
        
        count = 0
        with open(src_csv, 'r', encoding='utf-8') as fin, \
             open(dest_csv, 'w', encoding='utf-8', newline='') as fout:
            
            reader = csv.DictReader(fin)
            writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
            writer.writeheader()
            
            for row in reader:
                # Convert absolute path to relative
                old_path = Path(row['landmark_path'])
                new_path = f"Normalized_Landmarks/{old_path.name}"
                row['landmark_path'] = new_path
                writer.writerow(row)
                count += 1
                
        sample_counts[m] = count
        
    print("Copying JSON manifests...")
    shutil.copy2(SRC_MANIFEST_DIR / "label_mapping.json", dest_manifest_dir / "label_mapping.json")
    shutil.copy2(SRC_MANIFEST_DIR / "dataset_summary.json", dest_manifest_dir / "dataset_summary.json")
    
    print("Writing README.txt...")
    readme_content = """This package is for Google Colab training.
It contains 1,048 normalized MediaPipe landmark .npz files.
It contains train/validation/test manifests.
The manifests use relative paths.
Original project files were not modified.
The package is intended for Stage 5C BiLSTM + Attention training.
"""
    with open(package_dir / "README.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
        
    print("Validating the package...")
    validation_passed = True
    
    # 1. Exactly expected npz count
    if copied_npz_count != 1048:
        print(f"Validation Failed: Expected 1048 .npz files, found {copied_npz_count}")
        validation_passed = False
        
    # 2. Manifest match
    for m in manifests:
        dest_csv = dest_manifest_dir / m
        with open(dest_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rel_path = row['landmark_path']
                full_path = package_dir / rel_path
                if not full_path.exists():
                    print(f"Validation Failed: Manifest {m} references missing file {rel_path}")
                    validation_passed = False
                    
    # 3. JSON presence
    if not (dest_manifest_dir / "label_mapping.json").exists():
        print("Validation Failed: Missing label_mapping.json")
        validation_passed = False
    if not (dest_manifest_dir / "dataset_summary.json").exists():
        print("Validation Failed: Missing dataset_summary.json")
        validation_passed = False
        
    # 4. Unmodified source count
    current_src_npz_count = len(list(SRC_NPZ_DIR.glob("*.npz")))
    if current_src_npz_count != src_npz_count:
        print("Validation Failed: Source .npz count has changed! Data was modified!")
        validation_passed = False

    if not validation_passed:
        print("VALIDATION FAILED. Aborting ZIP creation.")
        return
        
    print("Validation passed successfully!")
    
    # Zipping
    zip_path_base = get_unique_path(BASE_ZIP_NAME)
    print(f"Creating ZIP file: {zip_path_base}.zip...")
    
    # Make archive creates .zip automatically if format is zip
    shutil.make_archive(str(zip_path_base), 'zip', package_dir)
    
    final_zip = Path(f"{zip_path_base}.zip")
    zip_size_mb = final_zip.stat().st_size / (1024 * 1024)
    
    print("\n================ FINAL REPORT ================")
    print("1. ZIP created successfully: Yes")
    print(f"2. Exact ZIP path: {final_zip}")
    print(f"3. ZIP size: {zip_size_mb:.2f} MB")
    print(f"4. Number of .npz files inside: {copied_npz_count}")
    print(f"5. Manifest validation result: Passed")
    print("6. Confirmation: NO original project files were modified, moved, renamed, or deleted.")
    print("==============================================")
    print(f"Source NPZ count: {src_npz_count}")
    print(f"Train samples: {sample_counts['train.csv']}")
    print(f"Validation samples: {sample_counts['validation.csv']}")
    print(f"Test samples: {sample_counts['test.csv']}")

if __name__ == "__main__":
    main()
