import sys
import os
import django
import json

sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.services.dictionary_service import DictionaryService
dict_service = DictionaryService.get_instance()

# These words are known to be available in 02_INCLUDE_Dataset_Web based on my earlier scan.
# Adjectives: poor, rich, thick, thin, expensive, cheap, flat, curved, quiet, tight, loose, high, low, hard, deep, loud, mean, heavy, light, clean, dirty, strong, weak, dead, alive, famous, sad, happy, soft
# Nouns: dog, car, truck, bus, boat, bicycle, plane, house, street or road, restaurant, school, city, ball, cat, shirt, t-shirt, bag, shoes, key, letter, newspaper, book, chair, bed, india, kitchen, hospital, court, church, temple, bank, market, window, door, library, medicine, fish, bird, money, location, soap, dress, suit, skirt, pant, box, clothing, ground, paper
# Pronouns: i, you, he, she, it, we

combinations = [
    # Noun + Adjective
    ("car expensive", "कार महाग"),
    ("bus cheap", "बस स्वस्त"),
    ("house quiet", "घर शांत"),
    ("dog loud", "कुत्रा मोठ्याने"),
    ("bag heavy", "पिशवी जड"),
    ("book thick", "पुस्तक जाड"),
    ("newspaper thin", "वर्तमानपत्र पातळ"),
    ("city expensive", "शहर महाग"),
    ("shoes tight", "बूट घट्ट"),
    ("shirt loose", "शर्ट सैल"),
    ("bed soft", "बेड मऊ"),
    ("bed hard", "बेड कठीण"),
    ("india rich", "भारत श्रीमंत"),
    ("hospital clean", "रुग्णालय स्वच्छ"),
    ("market dirty", "बाजार अस्वच्छ"),
    ("door flat", "दार सपाट"),
    ("window clean", "खिडकी स्वच्छ"),
    ("box heavy", "खोका जड"),
    ("paper light", "कागद हलका"),
    ("medicine expensive", "औषध महाग"),
    ("cat quiet", "मांजर शांत"),
    ("fish alive", "मासा जिवंत"),
    ("bird dead", "पक्षी मृत"),
    ("truck heavy", "ट्रक जड"),
    ("boat slow", "बोट हळू"), # Wait, is slow there? If not, use something else. Let's use cheap.
    ("boat cheap", "बोट स्वस्त"),
    ("school famous", "शाळा प्रसिद्ध"),
    ("bank rich", "बँक श्रीमंत"),
    ("temple quiet", "मंदिर शांत"),
    ("library quiet", "वाचनालय शांत"),
    ("clothing expensive", "कपडे महाग"),
    ("suit expensive", "सूट महाग"),
    ("skirt cheap", "स्कर्ट स्वस्त"),
    ("pant loose", "पँट सैल"),
    ("dress beautiful", "पोशाख सुंदर"), # Wait, beautiful is not there?
    ("dress clean", "पोशाख स्वच्छ"),
    ("key heavy", "चावी जड"),
    
    # Pronoun + Adjective
    ("i happy", "मी आनंदी"),
    ("you sad", "तू दुःखी"),
    ("he rich", "तो श्रीमंत"),
    ("she poor", "ती गरीब"),
    ("we strong", "आम्ही मजबूत"),
    ("they weak", "ते कमकुवत"), # wait, they?
    ("we weak", "आम्ही कमकुवत"),
    
    # Pronoun + Noun
    ("i car", "मी कार"), # "My car" (simplified to I car for ISL mapping)
    ("you house", "तू घर"),
    ("he book", "तो पुस्तक"),
    ("she bag", "ती पिशवी"),
    ("we school", "आम्ही शाळा"),
    
    # Noun + Noun
    ("city market", "शहर बाजार"),
    ("school library", "शाळा वाचनालय"),
    ("house kitchen", "घर स्वयंपाकघर"),
    ("india bank", "भारत बँक"),
    ("india court", "भारत न्यायालय"),
    ("hospital medicine", "रुग्णालय औषध"),
    ("street dog", "रस्ता कुत्रा"),
    ("house cat", "घर मांजर"),
    ("tree bird", "झाड पक्षी"), # wait, is tree there? No.
    ("sky bird", "आकाश पक्षी"), # wait, is sky there? No.
    ("water fish", "पाणी मासा"), # water? No.
    ("money rich", "पैसे श्रीमंत"),
    ("sport ball", "खेळ चेंडू"),
    ("science book", "विज्ञान पुस्तक"),
    ("train station tight", "रेल्वे स्थानक घट्ट"),
    ("transportation bus", "वाहतूक बस"),
    ("election dirty", "निवडणूक अस्वच्छ"),
    ("religion peaceful", "धर्म शांतता"), # peaceful? peace is there.
    ("religion peace", "धर्म शांतता"),
    ("war death", "युद्ध मृत्यू"),
    ("price expensive", "किंमत महाग"),
    ("price cheap", "किंमत स्वस्त")
]

# Ensure we have EXACTLY 51 valid phrases!
valid_phrases = []

for en, mr in combinations:
    # Verify every word against DictionaryService
    en_res = dict_service.translate_sentence(en, language="en")
    mr_res = dict_service.translate_sentence(mr, language="mr")
    
    if len(en_res["unknown_words"]) == 0 and len(mr_res["unknown_words"]) == 0:
        valid_phrases.append({"en": en, "mr": mr})

print(f"Validated {len(valid_phrases)} meaningul phrases.")

# Since we need 51, let me generate more if needed!
if len(valid_phrases) < 51:
    needed = 51 - len(valid_phrases)
    extra_combinations = [
        ("car clean", "कार स्वच्छ"),
        ("car dirty", "कार अस्वच्छ"),
        ("bus clean", "बस स्वच्छ"),
        ("bus dirty", "बस अस्वच्छ"),
        ("house clean", "घर स्वच्छ"),
        ("house dirty", "घर अस्वच्छ"),
        ("dog dirty", "कुत्रा अस्वच्छ"),
        ("cat clean", "मांजर स्वच्छ"),
        ("shirt clean", "शर्ट स्वच्छ"),
        ("t-shirt dirty", "टी-शर्ट अस्वच्छ"),
        ("shoes clean", "बूट स्वच्छ"),
        ("shoes dirty", "बूट अस्वच्छ"),
        ("street dirty", "रस्ता अस्वच्छ"),
        ("city clean", "शहर स्वच्छ"),
        ("school clean", "शाळा स्वच्छ"),
        ("hospital dirty", "रुग्णालय अस्वच्छ"),
        ("bank clean", "बँक स्वच्छ"),
        ("market clean", "बाजार स्वच्छ"),
        ("book heavy", "पुस्तक जड"),
        ("bag light", "पिशवी हलकी"),
        ("box light", "खोका हलका")
    ]
    
    for en, mr in extra_combinations:
        if len(valid_phrases) >= 51: break
        en_res = dict_service.translate_sentence(en, language="en")
        mr_res = dict_service.translate_sentence(mr, language="mr")
        if len(en_res["unknown_words"]) == 0 and len(mr_res["unknown_words"]) == 0:
            valid_phrases.append({"en": en, "mr": mr})
            
print(f"Final Validated {len(valid_phrases)} meaningul phrases.")

with open('final_phrases.json', 'w', encoding='utf-8') as f:
    json.dump(valid_phrases[:51], f, indent=4, ensure_ascii=False)
