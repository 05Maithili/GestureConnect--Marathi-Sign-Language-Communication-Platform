import sys
import os
import django
import json
from pathlib import Path
import re

sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.models import SignVocabulary
from django.conf import settings

dataset_web = Path(settings.OPTIMIZED_DATASET_ROOT) # 02_INCLUDE_Dataset_Web
dataset_opt = Path(r"D:\Colonel\final_year_project\02_INCLUDE_Dataset_Optimized")
dict_file = Path(r"D:\Colonel\final_year_project\04_Multilingual_Dictionary\Vocabulary\sign_vocabulary.json")

# Build a fast mapping of available directories in both dataset folders
def get_folders_lowercase(root_path):
    if not root_path.exists(): return {}
    return {p.name.lower(): p for p in root_path.iterdir() if p.is_dir()}

web_folders_lower = get_folders_lowercase(dataset_web)
opt_folders_lower = get_folders_lowercase(dataset_opt)

with open(dict_file, 'r', encoding='utf-8') as f:
    dict_data = json.load(f)
dict_map = {item['sign_id']: item for item in dict_data}

active_signs = SignVocabulary.objects.filter(is_active=True).order_by('sign_id')

verified_matches = []
resolver_issues = []
mapping_issues = []
genuinely_missing = []
invalid_unplayable = []

def has_compatible_video(directory):
    if not directory.exists() or not directory.is_dir(): return False
    videos = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in ['.mp4', '.mov', '.webm']]
    return len(videos) > 0

for sign in active_signs:
    sign_id = sign.sign_id
    marathi = sign.marathi_term
    english = sign.english_gloss
    dataset_word = None
    
    if sign_id in dict_map:
        dataset_word = dict_map[sign_id].get('dataset_word')
        
    if not dataset_word:
        # Check mapping issue
        mapping_issues.append((sign_id, english, "No dataset_word in JSON"))
        continue
        
    # The expected directory
    expected_dir = dataset_web / dataset_word
    
    # 1. Exact match in Web Dataset
    if expected_dir.exists() and expected_dir.is_dir() and has_compatible_video(expected_dir):
        verified_matches.append((sign_id, english, expected_dir))
        continue
        
    # 2. Match but no videos (empty folder?)
    if expected_dir.exists() and expected_dir.is_dir() and not has_compatible_video(expected_dir):
        invalid_unplayable.append((sign_id, english, "Folder exists but no compatible videos"))
        continue
        
    # 3. Case-insensitive match in Web Dataset
    if dataset_word.lower() in web_folders_lower:
        actual_dir = web_folders_lower[dataset_word.lower()]
        if has_compatible_video(actual_dir):
            resolver_issues.append((sign_id, english, dataset_word, actual_dir.name, "Case-insensitive match in Web"))
            continue
            
    # 4. Check if the directory name has spaces vs underscores
    normalized_word = re.sub(r'[^a-zA-Z0-9]', '', dataset_word.lower())
    found_in_web = False
    for folder_name, folder_path in web_folders_lower.items():
        if re.sub(r'[^a-zA-Z0-9]', '', folder_name) == normalized_word:
            if has_compatible_video(folder_path):
                resolver_issues.append((sign_id, english, dataset_word, folder_path.name, "Punctuation/Space mismatch in Web"))
                found_in_web = True
                break
    if found_in_web: continue
    
    # 5. Check if it exists in the original/optimized but NOT in web?
    if dataset_word.lower() in opt_folders_lower:
        actual_dir = opt_folders_lower[dataset_word.lower()]
        if has_compatible_video(actual_dir):
            # The prompt says: "no corresponding video can be found in the configured dataset -> Genuinely missing".
            # The configured dataset is the Web dataset. So if it's only in Optimized, it is genuinely missing from the configured dataset.
            genuinely_missing.append((sign_id, english, dataset_word))
            continue
            
    # 6. Check english_gloss instead of dataset_word?
    english_normalized = re.sub(r'[^a-zA-Z0-9]', '', english.lower())
    found_in_web = False
    for folder_name, folder_path in web_folders_lower.items():
        if re.sub(r'[^a-zA-Z0-9]', '', folder_name) == english_normalized:
            if has_compatible_video(folder_path):
                mapping_issues.append((sign_id, english, f"Found via English gloss '{folder_path.name}' instead of dataset_word '{dataset_word}'"))
                found_in_web = True
                break
    if found_in_web: continue
    
    # 7. Check if synonyms match
    synonyms = dict_map[sign_id].get('english_synonyms', [])
    found_in_web = False
    for syn in synonyms:
        syn_normalized = re.sub(r'[^a-zA-Z0-9]', '', syn.lower())
        for folder_name, folder_path in web_folders_lower.items():
            if re.sub(r'[^a-zA-Z0-9]', '', folder_name) == syn_normalized:
                if has_compatible_video(folder_path):
                    mapping_issues.append((sign_id, english, f"Found via synonym '{syn}' as folder '{folder_path.name}'"))
                    found_in_web = True
                    break
        if found_in_web: break
    if found_in_web: continue
        
    # If we reach here, it's genuinely missing
    genuinely_missing.append((sign_id, english, dataset_word))


print(f"Total active canonical entries: {active_signs.count()}")
print(f"Verified video matches: {len(verified_matches)}")
print(f"Resolver issues: {len(resolver_issues)}")
print(f"Mapping issues: {len(mapping_issues)}")
print(f"Invalid/unplayable: {len(invalid_unplayable)}")
print(f"Genuinely missing: {len(genuinely_missing)}")

print("\n--- Resolver Issues ---")
for r in resolver_issues: print(r)

print("\n--- Mapping Issues ---")
for m in mapping_issues: print(m)

print("\n--- Invalid/Unplayable ---")
for i in invalid_unplayable: print(i)

print("\n--- Genuinely Missing (First 10) ---")
for g in genuinely_missing[:10]: print(g)

# Save the full report
with open('audit_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total active canonical entries: {active_signs.count()}\n")
    f.write(f"Verified video matches: {len(verified_matches)}\n")
    f.write(f"Resolver issues: {len(resolver_issues)}\n")
    f.write(f"Mapping issues: {len(mapping_issues)}\n")
    f.write(f"Invalid/unplayable: {len(invalid_unplayable)}\n")
    f.write(f"Genuinely missing: {len(genuinely_missing)}\n\n")
    f.write("Resolver Issues:\n")
    for r in resolver_issues: f.write(f"{r}\n")
    f.write("\nMapping Issues:\n")
    for m in mapping_issues: f.write(f"{m}\n")
    f.write("\nInvalid/Unplayable:\n")
    for i in invalid_unplayable: f.write(f"{i}\n")
    f.write("\nGenuinely Missing:\n")
    for g in genuinely_missing: f.write(f"{g}\n")
