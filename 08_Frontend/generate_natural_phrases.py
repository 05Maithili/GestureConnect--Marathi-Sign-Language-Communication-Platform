import sys
import os
import django
import json

sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.services.sequence import process_translation

# Natural, grammatically correct phrases without trailing periods.
phrases = [
    # Greetings & Courtesies
    {"en": "Hello my friend", "mr": "नमस्कार माझ्या मित्रा"},
    {"en": "Good morning mother", "mr": "शुभ सकाळ आई"},
    {"en": "Good afternoon father", "mr": "शुभ दुपार वडील"},
    {"en": "Good evening brother", "mr": "शुभ संध्याकाळ भाऊ"},
    {"en": "Good night sister", "mr": "शुभ रात्री बहीण"},
    {"en": "Thank you doctor", "mr": "धन्यवाद डॉक्टर"},
    {"en": "Hello teacher", "mr": "नमस्कार शिक्षक"},
    {"en": "Thank you police", "mr": "धन्यवाद पोलीस"},
    
    # States & Emotions
    {"en": "I am very happy", "mr": "मी खूप आनंदी आहे"},
    {"en": "We are pleased", "mr": "आम्ही आनंदी आहोत"},
    {"en": "You are beautiful", "mr": "तू सुंदर आहेस"},
    {"en": "He is sick", "mr": "तो आजारी आहे"},
    {"en": "She is sad", "mr": "ती दुःखी आहे"},
    {"en": "They are healthy", "mr": "ते निरोगी आहेत"},
    
    # Family & People
    {"en": "My grandfather is old", "mr": "माझे आजोबा जुने आहेत"},
    {"en": "My grandmother is old", "mr": "माझी आजी जुनी आहे"},
    {"en": "The baby is young", "mr": "बाळ तरुण आहे"},
    {"en": "The family is happy", "mr": "कुटुंब आनंदी आहे"},
    {"en": "The man is tall", "mr": "माणूस उंच आहे"},
    {"en": "The woman is beautiful", "mr": "स्त्री सुंदर आहे"},
    
    # Days & Seasons
    {"en": "Today is Sunday", "mr": "आज रविवार आहे"},
    {"en": "Tomorrow is Monday", "mr": "उद्या सोमवार आहे"},
    {"en": "Yesterday was Saturday", "mr": "काल शनिवार होता"},
    {"en": "The winter is cold", "mr": "हिवाळा थंड आहे"},
    {"en": "The summer is hot", "mr": "उन्हाळा गरम आहे"},
    {"en": "The monsoon is wet", "mr": "पावसाळा ओले आहे"},
    {"en": "Spring is beautiful", "mr": "वसंत ऋतू सुंदर आहे"},
    
    # Objects & Colors
    {"en": "The shirt is red", "mr": "शर्ट लाल आहे"},
    {"en": "The shoes are black", "mr": "बूट काळे आहेत"},
    {"en": "The dress is white", "mr": "पोशाख पांढरा आहे"},
    {"en": "The bag is heavy", "mr": "पिशवी जड आहे"},
    {"en": "The book is good", "mr": "पुस्तक चांगले आहे"},
    {"en": "The pen is blue", "mr": "पेन निळा आहे"},
    {"en": "The laptop is expensive", "mr": "लॅपटॉप महाग आहे"},
    
    # Places
    {"en": "The hospital is clean", "mr": "रुग्णालय स्वच्छ आहे"},
    {"en": "The market is cheap", "mr": "बाजार स्वस्त आहे"},
    {"en": "The school is new", "mr": "शाळा नवीन आहे"},
    {"en": "The city is loud", "mr": "शहर मोठ्याने आहे"},
    {"en": "The street is quiet", "mr": "रस्ता शांत आहे"},
    {"en": "The temple is peaceful", "mr": "मंदिर शांत आहे"},
    
    # Transport
    {"en": "The train is fast", "mr": "रेल्वे जलद आहे"},
    {"en": "The bus is slow", "mr": "बस हळू आहे"},
    {"en": "The car is fast", "mr": "कार जलद आहे"},
    {"en": "I need a train ticket", "mr": "मला रेल्वे तिकीट हवे आहे"},
    
    # Animals
    {"en": "The dog is fast", "mr": "कुत्रा जलद आहे"},
    {"en": "The cat is small", "mr": "मांजर लहान आहे"},
    {"en": "The cow is big", "mr": "गाय मोठी आहे"},
    {"en": "The horse is strong", "mr": "घोडा मजबूत आहे"},
    {"en": "The bird flies high", "mr": "पक्षी उंच आहे"},
    
    # Rooms & House
    {"en": "The kitchen is clean", "mr": "स्वयंपाकघर स्वच्छ आहे"},
    {"en": "The bedroom is dirty", "mr": "शयनकक्ष अस्वच्छ आहे"},
    {"en": "The flat is big", "mr": "सपाट मोठा आहे"},
    {"en": "The chair is soft", "mr": "खुर्ची मऊ आहे"},
    {"en": "The door is wide", "mr": "दार रुंद आहे"},
    {"en": "The window is narrow", "mr": "खिडकी अरुंद आहे"},
    
    # Extra to reach 50
    {"en": "The clock is slow", "mr": "घड्याळ हळू आहे"},
    {"en": "The medicine is good", "mr": "औषध चांगले आहे"},
    {"en": "The telephone is expensive", "mr": "दूरध्वनी महाग आहे"},
    {"en": "I have a pen", "mr": "माझ्याकडे पेन आहे"},
    {"en": "The child is happy", "mr": "मूल आनंदी आहे"},
    {"en": "The student is young", "mr": "विद्यार्थी तरुण आहे"}
]

verified_phrases = []
for p in phrases:
    eng = p["en"]
    mar = p["mr"]
    
    res_eng = process_translation(eng, "en", log_history=False)
    seq_eng = res_eng.get('sign_sequence', [])
    supported_eng = [s for s in seq_eng if not s.get('is_fallback', False)]
    
    res_mar = process_translation(mar, "mr", log_history=False)
    seq_mar = res_mar.get('sign_sequence', [])
    supported_mar = [s for s in seq_mar if not s.get('is_fallback', False)]

    # Only include the phrase if it has AT LEAST 2 valid canonical signs in English, and 2 in Marathi
    # Or for shorter ones like "He is sick" (He, sick), 2 is perfect.
    if len(supported_eng) >= 2 and len(supported_mar) >= 2:
        verified_phrases.append(p)

print(f"Total phrases: {len(phrases)}")
print(f"Valid phrases with natural grammar: {len(verified_phrases)}")

with open("final_phrases.json", "w", encoding="utf-8") as f:
    json.dump(verified_phrases, f, indent=2, ensure_ascii=False)
