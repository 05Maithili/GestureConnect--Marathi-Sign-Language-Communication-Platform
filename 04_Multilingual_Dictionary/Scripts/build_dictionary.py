import os
import json
import csv
import re
from pathlib import Path
from collections import OrderedDict

PROJECT_ROOT = Path("D:/Colonel/final_year_project")
DATASET_DIR = PROJECT_ROOT / "02_INCLUDE_Dataset_Optimized"
MEDIAPIPE_DIR = PROJECT_ROOT / "03_MediaPipe_Landmarks"
DICT_DIR = PROJECT_ROOT / "04_Multilingual_Dictionary"

# Output files
VOCAB_JSON = DICT_DIR / "Vocabulary" / "sign_vocabulary.json"
VOCAB_CSV = DICT_DIR / "Vocabulary" / "sign_vocabulary.csv"
MAPPING_FILE = DICT_DIR / "Mappings" / "sign_id_mapping.json"
EN_MAPPING_FILE = DICT_DIR / "English" / "english_to_sign.json"
MR_MAPPING_FILE = DICT_DIR / "Marathi" / "marathi_to_sign.json"
SYNONYM_FILE = DICT_DIR / "Synonyms" / "english_synonyms.json"
OOV_FILE = DICT_DIR / "Unknown_Words" / "oov_words.json"

# A base dictionary for some synonyms and marathi equivalents
MARATHI_TRANSLATIONS = {
    "actor": "अभिनेता", "adult": "प्रौढ", "afternoon": "दुपार", "alive": "जिवंत", "alright": "ठीक आहे", 
    "animal": "प्राणी", "artist": "कलाकार", "attack": "हल्ला", "author": "लेखक", "baby": "बाळ", 
    "bad": "वाईट", "bag": "पिशवी", "ball": "चेंडू", "bank": "बँक", "bathroom": "स्नानगृह", 
    "beautiful": "सुंदर", "bed": "बेड", "bedroom": "शयनकक्ष", "bicycle": "सायकल", "big large": "मोठा", 
    "bill": "बिल", "bird": "पक्षी", "black": "काळा", "blind": "अंध", "blue": "निळा", 
    "boat": "बोट", "book": "पुस्तक", "box": "खोका", "boy": "मुलगा", "brother": "भाऊ", 
    "brown": "तपकिरी", "bus": "बस", "camera": "कॅमेरा", "car": "कार", "card": "कार्ड", 
    "cat": "मांजर", "cell phone": "मोबाईल", "chair": "खुर्ची", "cheap": "स्वस्त", "child": "मूल", 
    "city": "शहर", "clean": "स्वच्छ", "clock": "घड्याळ", "clothing": "कपडे", "cold": "थंड", 
    "colour": "रंग", "computer": "संगणक", "cool": "थंडगार", "court": "न्यायालय", "cow": "गाय", 
    "crowd": "गर्दी", "curved": "वक्र", "daughter": "मुलगी", "dead": "मृत", "deaf": "बधिर", 
    "death": "मृत्यू", "deep": "खोल", "dirty": "अस्वच्छ", "doctor": "डॉक्टर", "dog": "कुत्रा", 
    "door": "दार", "dream": "स्वप्न", "dress": "पोशाख", "dry": "कोरडा", "election": "निवडणूक", 
    "energy": "ऊर्जा", "evening": "संध्याकाळ", "exercise": "व्यायाम", "expensive": "महाग", "fall": "पडणे", 
    "family": "कुटुंब", "famous": "प्रसिद्ध", "fan": "पंखा", "fast": "जलद", "father": "वडील", 
    "female": "स्त्री", "fish": "मासा", "flat": "सपाट", "friday": "शुक्रवार", "friend": "मित्र", 
    "gift": "भेटवस्तू", "girl": "मुलगी", "god": "देव", "good": "चांगले", "good afternoon": "शुभ दुपार", 
    "good evening": "शुभ संध्याकाळ", "good morning": "शुभ सकाळ", "good night": "शुभ रात्री", "grandfather": "आजोबा", 
    "grandmother": "आजी", "green": "हिरवा", "grey": "राखाडी", "ground": "जमीन", "gun": "बंदूक", 
    "happy": "आनंदी", "hard": "कठीण", "hat": "टोपी", "he": "तो", "healthy": "निरोगी", 
    "heavy": "जड", "hello": "नमस्कार", "high": "उंच", "horse": "घोडा", "hospital": "रुग्णालय", 
    "hot": "गरम", "hour": "तास", "house": "घर", "how are you": "तू कसा आहेस", "husband": "पती", 
    "i": "मी", "india": "भारत", "it": "ते", "job": "नोकरी", "key": "चावी", 
    "king": "राजा", "kitchen": "स्वयंपाकघर", "lamp": "दिवा", "laptop": "लॅपटॉप", "lawyer": "वकील", 
    "letter": "पत्र", "library": "ग्रंथालय", "light": "प्रकाश", "location": "ठिकाण", "lock": "कुलूप", 
    "long": "लांब", "loose": "सैल", "loud": "मोठ्याने", "low": "कमी", "male": "पुरुष", 
    "man": "माणूस", "manager": "व्यवस्थापक", "market": "बाजार", "marriage": "लग्न", "mean": "अर्थ", 
    "medicine": "औषध", "minute": "मिनिट", "monday": "सोमवार", "money": "पैसे", "monsoon": "पावसाळा", 
    "month": "महिना", "morning": "सकाळ", "mother": "आई", "mouse": "उंदीर", "narrow": "अरुंद", 
    "neighbour": "शेजारी", "new": "नवीन", "newspaper": "वर्तमानपत्र", "nice": "छान", "night": "रात्र", 
    "office": "कार्यालय", "old": "जुने", "orange": "नारंगी", "page": "पान", "paint": "रंगविणे", 
    "pant": "पँट", "paper": "कागद", "parent": "पालक", "park": "उद्यान", "patient": "रुग्ण", 
    "peace": "शांतता", "pen": "पेन", "pencil": "पेन्सिल", "photograph": "छायाचित्र", "pink": "गुलाबी", 
    "plane": "विमान", "player": "खेळाडू", "pleased": "आनंदी", "pocket": "खिसा", "police": "पोलीस", 
    "poor": "गरीब", "president": "अध्यक्ष", "price": "किंमत", "priest": "पुजारी", "queen": "राणी", 
    "quiet": "शांत", "race (ethnicity)": "वंश", "radio": "रेडिओ", "red": "लाल", "religion": "धर्म", 
    "reporter": "पत्रकार", "restaurant": "उपहारगृह", "rich": "श्रीमंत", "ring": "अंगठी", "sad": "दुःखी", 
    "saturday": "शनिवार", "school": "शाळा", "science": "विज्ञान", "screen": "पडदा", "season": "ऋतू", 
    "second": "सेकंद", "secretary": "सचिव", "shallow": "उथळ", "she": "ती", "shirt": "शर्ट", 
    "shoes": "बूट", "short": "लहान", "sick": "आजारी", "sign": "खूण", "sister": "बहीण", 
    "skirt": "स्कर्ट", "slow": "हळू", "small little": "लहान", "soap": "साबण", "soft": "मऊ", 
    "soldier": "सैनिक", "son": "मुलगा", "sport": "खेळ", "spring": "वसंत ऋतू", "store or shop": "दुकान", 
    "street or road": "रस्ता", "strong": "मजबूत", "student": "विद्यार्थी", "suit": "सूट", "summer": "उन्हाळा", 
    "sunday": "रविवार", "t-shirt": "टी-शर्ट", "table": "टेबल", "tall": "उंच", "teacher": "शिक्षक", 
    "team": "संघ", "technology": "तंत्रज्ञान", "telephone": "दूरध्वनी", "television": "दूरदर्शन", "temple": "मंदिर", 
    "thank you": "धन्यवाद", "they": "ते", "thick": "जाड", "thin": "पातळ", "thursday": "गुरुवार", 
    "tight": "घट्ट", "time": "वेळ", "today": "आज", "tomorrow": "उद्या", "tool": "साधन", 
    "train": "रेल्वे", "train station": "रेल्वे स्थानक", "train ticket": "रेल्वे तिकीट", "transportation": "वाहतूक", "truck": "ट्रक", 
    "tuesday": "मंगळवार", "ugly": "कुरूप", "university": "विद्यापीठ", "waiter": "वेटर", "war": "युद्ध", 
    "warm": "उबदार", "we": "आम्ही", "weak": "कमकुवत", "wednesday": "बुधवार", "week": "आठवडा", 
    "wet": "ओले", "white": "पांढरा", "wide": "रुंद", "wife": "पत्नी", "window": "खिडकी", 
    "winter": "हिवाळा", "woman": "स्त्री", "year": "वर्ष", "yellow": "पिवळा", "yesterday": "काल", 
    "you": "तू", "you (plural)": "तुम्ही", "young": "तरुण"
}

ENGLISH_SYNONYMS = {
    "big large": ["big", "large", "huge", "giant", "massive"],
    "small little": ["small", "little", "tiny"],
    "store or shop": ["store", "shop", "market"],
    "street or road": ["street", "road", "path"],
    "car": ["automobile", "vehicle"],
    "dad": ["father"],
    "mom": ["mother"],
    "sick": ["ill", "unwell"],
    "beautiful": ["pretty", "gorgeous", "lovely"],
    "student": ["pupil"],
    "doctor": ["physician"]
}

def load_json(filepath):
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    print("Building dictionary...")
    
    # Existing IDs mapping to maintain stability
    existing_mapping = load_json(MAPPING_FILE)
    
    # Load dataset words
    dataset_words = []
    for d in DATASET_DIR.iterdir():
        if d.is_dir():
            folder_name = d.name
            # E.g. "1. Dog" -> "dog", "Ex. Monsoon" -> "monsoon"
            clean_word = re.sub(r'^(?:\d+|Ex)\.\s*', '', folder_name).strip().lower()
            dataset_words.append((folder_name, clean_word))
            
    dataset_words.sort(key=lambda x: x[1])
    
    # Find next available SIGN_ID
    existing_ids = [int(v.replace("SIGN_", "")) for v in existing_mapping.values()]
    next_id_num = max(existing_ids) + 1 if existing_ids else 1
    
    # Load mediapipe metadata
    mediapipe_meta_path = MEDIAPIPE_DIR / "Metadata" / "extraction_metadata.csv"
    mp_info = {}
    if mediapipe_meta_path.exists():
        with open(mediapipe_meta_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row['word']
                if word not in mp_info:
                    mp_info[word] = {'video_count': 0, 'raw_available': False, 'normalized_available': False}
                mp_info[word]['video_count'] += 1
                if row.get('raw_file') and 'success' in row.get('extraction_status', ''):
                    mp_info[word]['raw_available'] = True
                if row.get('norm_file') and 'success' in row.get('normalization_status', ''):
                    mp_info[word]['normalized_available'] = True

    # Process vocabulary
    vocab = []
    english_map = load_json(EN_MAPPING_FILE)
    marathi_map = load_json(MR_MAPPING_FILE)
    synonym_map = load_json(SYNONYM_FILE)
    
    for original_folder, canonical_word in dataset_words:
        # Get or create Sign ID
        if canonical_word in existing_mapping:
            sign_id = existing_mapping[canonical_word]
        else:
            sign_id = f"SIGN_{next_id_num:04d}"
            existing_mapping[canonical_word] = sign_id
            next_id_num += 1
            
        # Get MediaPipe Info
        info = mp_info.get(original_folder, {'video_count': 0, 'raw_available': False, 'normalized_available': False})
        
        # Marathi translation
        marathi_term = MARATHI_TRANSLATIONS.get(canonical_word, "")
        if marathi_term:
            if marathi_term not in marathi_map:
                marathi_map[marathi_term] = []
            if sign_id not in marathi_map[marathi_term]:
                marathi_map[marathi_term].append(sign_id)
            
        # English mapping
        if canonical_word not in english_map:
            english_map[canonical_word] = []
        if sign_id not in english_map[canonical_word]:
            english_map[canonical_word].append(sign_id)
        
        # Synonyms
        syns = ENGLISH_SYNONYMS.get(canonical_word, [])
        for syn in syns:
            if syn not in english_map:
                english_map[syn] = []
            if sign_id not in english_map[syn]:
                english_map[syn].append(sign_id)
                
            if canonical_word not in synonym_map:
                synonym_map[canonical_word] = []
            if syn not in synonym_map[canonical_word]:
                synonym_map[canonical_word].append(syn)
                
        vocab.append({
            "sign_id": sign_id,
            "canonical_word": canonical_word,
            "dataset_word": original_folder,
            "english_terms": [canonical_word] + syns,
            "english_synonyms": syns,
            "marathi_terms": [marathi_term] if marathi_term else [],
            "source_category": "unknown", # From metadata if available, currently mostly unknown
            "video_count": info['video_count'],
            "media_pipe": {
                "raw_available": info['raw_available'],
                "normalized_available": info['normalized_available']
            }
        })
        
    # Ensure OOV exists
    if not OOV_FILE.exists():
        save_json(OOV_FILE, [])

    # Save everything
    save_json(MAPPING_FILE, existing_mapping)
    save_json(VOCAB_JSON, vocab)
    save_json(EN_MAPPING_FILE, english_map)
    save_json(MR_MAPPING_FILE, marathi_map)
    save_json(SYNONYM_FILE, synonym_map)
    
    # Save CSV
    with open(VOCAB_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Sign ID", "Canonical Word", "Dataset Word", "Marathi", "Video Count", "Raw MP", "Norm MP"])
        for v in vocab:
            mr_term = v["marathi_terms"][0] if v["marathi_terms"] else ""
            writer.writerow([
                v["sign_id"], v["canonical_word"], v["dataset_word"], mr_term, 
                v["video_count"], v["media_pipe"]["raw_available"], v["media_pipe"]["normalized_available"]
            ])
            
    print(f"Dictionary built successfully. Found {len(vocab)} unique signs.")

if __name__ == "__main__":
    main()
