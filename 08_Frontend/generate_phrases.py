import sys
import os
import django
import json

sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.services.sequence import process_translation
from translator.models import SignVocabulary

phrases = [
    # Greetings
    {"en": "Hello how are you", "mr": "नमस्कार तू कसा आहेस"},
    {"en": "Good morning mother", "mr": "शुभ सकाळ आई"},
    {"en": "Good afternoon father", "mr": "शुभ दुपार वडील"},
    {"en": "Good evening friend", "mr": "शुभ संध्याकाळ मित्र"},
    {"en": "Good night", "mr": "शुभ रात्री"},
    {"en": "Thank you", "mr": "धन्यवाद"},
    
    # Pronouns & People
    {"en": "I am a student", "mr": "मी विद्यार्थी आहे"},
    {"en": "You are a teacher", "mr": "तू शिक्षक आहेस"},
    {"en": "He is a doctor", "mr": "तो डॉक्टर आहे"},
    {"en": "She is a lawyer", "mr": "ती वकील आहे"},
    {"en": "They are family", "mr": "ते कुटुंब आहेत"},
    {"en": "We are happy", "mr": "आम्ही आनंदी आहोत"},
    
    # Adjectives & Description
    {"en": "The boy is tall", "mr": "मुलगा उंच आहे"},
    {"en": "The girl is young", "mr": "मुलगी तरुण आहे"},
    {"en": "The man is old", "mr": "माणूस जुना आहे"},
    {"en": "The woman is beautiful", "mr": "स्त्री सुंदर आहे"},
    {"en": "The baby is healthy", "mr": "बाळ निरोगी आहे"},
    
    # Time & Weather
    {"en": "Today is sunday", "mr": "आज रविवार आहे"},
    {"en": "Tomorrow is monday", "mr": "उद्या सोमवार आहे"},
    {"en": "Yesterday was saturday", "mr": "काल शनिवार होता"},
    {"en": "Winter is cold", "mr": "हिवाळा थंड आहे"},
    {"en": "Summer is hot", "mr": "उन्हाळा गरम आहे"},
    {"en": "Monsoon is wet", "mr": "पावसाळा ओले आहे"},
    {"en": "Spring is beautiful", "mr": "वसंत ऋतू सुंदर आहे"},
    
    # Objects & Colors
    {"en": "The shirt is red", "mr": "शर्ट लाल आहे"},
    {"en": "The shoes are black", "mr": "बूट काळा आहेत"},
    {"en": "The dress is white", "mr": "पोशाख पांढरा आहे"},
    {"en": "The bag is heavy", "mr": "पिशवी जड आहे"},
    {"en": "The book is good", "mr": "पुस्तक चांगले आहे"},
    {"en": "The pen is blue", "mr": "पेन निळा आहे"},
    {"en": "The laptop is expensive", "mr": "लॅपटॉप महाग आहे"},
    
    # Places & Transport
    {"en": "The hospital is clean", "mr": "रुग्णालय स्वच्छ आहे"},
    {"en": "The market is cheap", "mr": "बाजार स्वस्त आहे"},
    {"en": "The school is new", "mr": "शाळा नवीन आहे"},
    {"en": "The city is loud", "mr": "शहर मोठ्याने आहे"},
    {"en": "The street is quiet", "mr": "रस्ता शांत आहे"},
    {"en": "The train is fast", "mr": "रेल्वे जलद आहे"},
    {"en": "The bus is slow", "mr": "बस हळू आहे"},
    {"en": "I need a train ticket", "mr": "मला रेल्वे तिकीट हवे आहे"},
    
    # Animals
    {"en": "The dog is fast", "mr": "कुत्रा जलद आहे"},
    {"en": "The cat is small", "mr": "मांजर लहान आहे"},
    {"en": "The cow is big", "mr": "गाय मोठी आहे"},
    {"en": "The horse is strong", "mr": "घोडा मजबूत आहे"},
    {"en": "The bird is high", "mr": "पक्षी उंच आहे"},
    
    # Rooms & Furniture
    {"en": "The kitchen is clean", "mr": "स्वयंपाकघर स्वच्छ आहे"},
    {"en": "The bedroom is dirty", "mr": "शयनकक्ष अस्वच्छ आहे"},
    {"en": "The flat is big", "mr": "सपाट मोठा आहे"},
    {"en": "The chair is soft", "mr": "खुर्ची मऊ आहे"},
    {"en": "The door is wide", "mr": "दार रुंद आहे"},
    {"en": "The window is narrow", "mr": "खिडकी अरुंद आहे"}
]

# Verify against translation pipeline to ensure good coverage
verified_phrases = []
for p in phrases:
    eng = p["en"]
    mar = p["mr"]
    
    res_eng = process_translation(eng, "en", log_history=False)
    seq_eng = res_eng.get('sign_sequence', [])
    fb_eng = res_eng.get('fallback_words', [])
    supported_eng = [s for s in seq_eng if not s.get('is_fallback', False)]
    cov_eng = (len(supported_eng) / len(seq_eng)) * 100 if seq_eng else 0
    
    res_mar = process_translation(mar, "mr", log_history=False)
    seq_mar = res_mar.get('sign_sequence', [])
    fb_mar = res_mar.get('fallback_words', [])
    supported_mar = [s for s in seq_mar if not s.get('is_fallback', False)]
    cov_mar = (len(supported_mar) / len(seq_mar)) * 100 if seq_mar else 0

    p['cov_eng'] = cov_eng
    p['cov_mar'] = cov_mar
    p['unsupported_eng'] = fb_eng
    p['unsupported_mar'] = fb_mar

    # We want at least 80% coverage to consider it fully/partially supported
    if cov_eng >= 50 or cov_mar >= 50:
        verified_phrases.append(p)

print(f"Total phrases defined: {len(phrases)}")
print(f"Verified phrases (>=50% coverage): {len(verified_phrases)}")

with open("verified_phrases.json", "w", encoding="utf-8") as f:
    json.dump(verified_phrases, f, indent=2, ensure_ascii=False)
