import sys
import os
import django
import json

sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.services.sequence import process_translation

phrases = [
    # Greetings & Courtesies
    {"en": "Hello friend", "mr": "नमस्कार मित्र"},
    {"en": "Good morning mother", "mr": "शुभ सकाळ आई"},
    {"en": "Good afternoon father", "mr": "शुभ दुपार वडील"},
    {"en": "Good evening brother", "mr": "शुभ संध्याकाळ भाऊ"},
    {"en": "Good night sister", "mr": "शुभ रात्री बहीण"},
    {"en": "Thank you doctor", "mr": "धन्यवाद डॉक्टर"},
    {"en": "Hello teacher", "mr": "नमस्कार शिक्षक"},
    {"en": "Thank you police", "mr": "धन्यवाद पोलीस"},
    
    # States & Emotions
    {"en": "I happy", "mr": "मी आनंदी"},
    {"en": "We pleased", "mr": "आम्ही आनंदी"},
    {"en": "You beautiful", "mr": "तू सुंदर"},
    {"en": "He sick", "mr": "तो आजारी"},
    {"en": "She sad", "mr": "ती दुःखी"},
    {"en": "They healthy", "mr": "ते निरोगी"},
    
    # Family & People
    {"en": "Grandfather old", "mr": "आजोबा जुने"},
    {"en": "Grandmother old", "mr": "आजी जुने"},
    {"en": "Baby young", "mr": "बाळ तरुण"},
    {"en": "Family happy", "mr": "कुटुंब आनंदी"},
    {"en": "Man tall", "mr": "माणूस उंच"},
    {"en": "Woman beautiful", "mr": "स्त्री सुंदर"},
    
    # Days & Seasons
    {"en": "Today sunday", "mr": "आज रविवार"},
    {"en": "Tomorrow monday", "mr": "उद्या सोमवार"},
    {"en": "Yesterday saturday", "mr": "काल शनिवार"},
    {"en": "Winter cold", "mr": "हिवाळा थंड"},
    {"en": "Summer hot", "mr": "उन्हाळा गरम"},
    {"en": "Monsoon wet", "mr": "पावसाळा ओले"},
    {"en": "Spring beautiful", "mr": "वसंत ऋतू सुंदर"},
    
    # Objects & Colors
    {"en": "Shirt red", "mr": "शर्ट लाल"},
    {"en": "Shoes black", "mr": "बूट काळा"},
    {"en": "Dress white", "mr": "पोशाख पांढरा"},
    {"en": "Bag heavy", "mr": "पिशवी जड"},
    {"en": "Book good", "mr": "पुस्तक चांगले"},
    {"en": "Pen blue", "mr": "पेन निळा"},
    {"en": "Laptop expensive", "mr": "लॅपटॉप महाग"},
    
    # Places
    {"en": "Hospital clean", "mr": "रुग्णालय स्वच्छ"},
    {"en": "Market cheap", "mr": "बाजार स्वस्त"},
    {"en": "School new", "mr": "शाळा नवीन"},
    {"en": "City loud", "mr": "शहर मोठ्याने"},
    {"en": "Street quiet", "mr": "रस्ता शांत"},
    {"en": "Temple peace", "mr": "मंदिर शांतता"},
    
    # Transport
    {"en": "Train fast", "mr": "रेल्वे जलद"},
    {"en": "Bus slow", "mr": "बस हळू"},
    {"en": "Car fast", "mr": "कार जलद"},
    {"en": "I train ticket", "mr": "मी रेल्वे तिकीट"},
    
    # Animals
    {"en": "Dog fast", "mr": "कुत्रा जलद"},
    {"en": "Cat small", "mr": "मांजर लहान"},
    {"en": "Cow big", "mr": "गाय मोठी"},
    {"en": "Horse strong", "mr": "घोडा मजबूत"},
    {"en": "Bird high", "mr": "पक्षी उंच"},
    
    # Rooms & House
    {"en": "Kitchen clean", "mr": "स्वयंपाकघर स्वच्छ"},
    {"en": "Bedroom dirty", "mr": "शयनकक्ष अस्वच्छ"},
    {"en": "Flat big", "mr": "सपाट मोठा"},
    {"en": "Chair soft", "mr": "खुर्ची मऊ"},
    {"en": "Door wide", "mr": "दार रुंद"},
    {"en": "Window narrow", "mr": "खिडकी अरुंद"}
]

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

    if cov_eng == 100 and cov_mar == 100:
        verified_phrases.append(p)

print(f"Total phrases: {len(phrases)}")
print(f"100% Valid phrases: {len(verified_phrases)}")

with open("final_phrases.json", "w", encoding="utf-8") as f:
    json.dump(verified_phrases, f, indent=2, ensure_ascii=False)
