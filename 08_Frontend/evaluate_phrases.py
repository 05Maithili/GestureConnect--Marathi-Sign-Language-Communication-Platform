import sys
import os
import django
import json

sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.services.sequence import process_translation

candidate_phrases = [
    # Greetings & Introductions
    {"en": "Hello how are you", "mr": "नमस्कार तू कसा आहेस"},
    {"en": "Good morning", "mr": "शुभ सकाळ"},
    {"en": "Good afternoon", "mr": "शुभ दुपार"},
    {"en": "Good evening", "mr": "शुभ संध्याकाळ"},
    {"en": "Good night", "mr": "शुभ रात्री"},
    {"en": "Thank you", "mr": "धन्यवाद"},
    {"en": "I am happy", "mr": "मी आनंदी आहे"},
    {"en": "You are beautiful", "mr": "तू सुंदर आहेस"},

    # Family & People
    {"en": "Mother and father", "mr": "आई आणि वडील"},
    {"en": "Brother and sister", "mr": "भाऊ आणि बहीण"},
    {"en": "My grandfather is old", "mr": "माझे आजोबा जुने आहेत"},
    {"en": "She is my wife", "mr": "ती माझी पत्नी आहे"},
    {"en": "He is a good husband", "mr": "तो एक चांगला पती आहे"},
    {"en": "The baby is sleeping", "mr": "बाळ झोपत आहे"},
    {"en": "I have a son and a daughter", "mr": "मला एक मुलगा आणि एक मुलगी आहे"},
    {"en": "They are family", "mr": "ते कुटुंब आहेत"},
    {"en": "He is my friend", "mr": "तो माझा मित्र आहे"},
    
    # Needs & Actions
    {"en": "I need medicine", "mr": "मला औषध हवे आहे"},
    {"en": "Where is the hospital", "mr": "रुग्णालय कुठे आहे"},
    {"en": "I am sick today", "mr": "मी आज आजारी आहे"},
    {"en": "Please call the doctor", "mr": "कृपया डॉक्टरला बोलावा"},
    {"en": "Where is the market", "mr": "बाजार कुठे आहे"},
    {"en": "I want money", "mr": "मला पैसे हवे आहेत"},
    {"en": "Where is the bathroom", "mr": "स्नानगृह कुठे आहे"},
    {"en": "Open the door", "mr": "दार उघडा"},
    {"en": "Close the window", "mr": "खिडकी बंद करा"},

    # Time & Days
    {"en": "Today is monday", "mr": "आज सोमवार आहे"},
    {"en": "Tomorrow is tuesday", "mr": "उद्या मंगळवार आहे"},
    {"en": "Yesterday was sunday", "mr": "काल रविवार होता"},
    {"en": "What time is it", "mr": "वेळ काय आहे"},
    {"en": "One hour and one minute", "mr": "एक तास आणि एक मिनिट"},
    {"en": "Next week", "mr": "पुढील आठवडा"},
    {"en": "Next month", "mr": "पुढील महिना"},
    {"en": "This year", "mr": "हे वर्ष"},
    {"en": "Summer season", "mr": "उन्हाळा ऋतू"},
    {"en": "Winter is cold", "mr": "हिवाळा थंड आहे"},
    {"en": "Monsoon is wet", "mr": "पावसाळा ओले आहे"},

    # Places & Transport
    {"en": "Where is the train station", "mr": "रेल्वे स्थानक कुठे आहे"},
    {"en": "I need a train ticket", "mr": "मला रेल्वे तिकीट हवे आहे"},
    {"en": "The bus is slow", "mr": "बस हळू आहे"},
    {"en": "The car is fast", "mr": "कार जलद आहे"},
    {"en": "Where is the school", "mr": "शाळा कुठे आहे"},
    {"en": "He is a student", "mr": "तो एक विद्यार्थी आहे"},
    {"en": "The teacher is good", "mr": "शिक्षक चांगले आहेत"},
    {"en": "Go to the office", "mr": "कार्यालय जा"},
    {"en": "Where is the temple", "mr": "मंदिर कुठे आहे"},
    {"en": "Where is the bank", "mr": "बँक कुठे आहे"},

    # Objects & Description
    {"en": "The book is heavy", "mr": "पुस्तक जड आहे"},
    {"en": "The pen is cheap", "mr": "पेन स्वस्त आहे"},
    {"en": "The laptop is expensive", "mr": "लॅपटॉप महाग आहे"},
    {"en": "Red blue and green", "mr": "लाल निळा आणि हिरवा"},
    {"en": "Black and white", "mr": "काळा आणि पांढरा"},
    {"en": "The chair is comfortable", "mr": "खुर्ची आरामदायक आहे"},
    {"en": "Turn on the light", "mr": "प्रकाश चालू करा"},
    {"en": "Turn on the television", "mr": "दूरदर्शन चालू करा"},

    # Animals
    {"en": "The dog is small", "mr": "कुत्रा लहान आहे"},
    {"en": "The cat is beautiful", "mr": "मांजर सुंदर आहे"},
    {"en": "The horse is strong", "mr": "घोडा मजबूत आहे"},
    {"en": "The bird is high", "mr": "पक्षी उंच आहे"},
    {"en": "The cow is big", "mr": "गाय मोठी आहे"},
]

results = []
for p in candidate_phrases:
    eng = p["en"]
    mar = p["mr"]
    
    # Evaluate English
    res_eng = process_translation(eng, "en", log_history=False)
    seq_eng = res_eng.get('sign_sequence', [])
    fb_eng = res_eng.get('fallback_words', [])
    # Actually wait, sequence elements have dataset_status? Let's check how it maps.
    # In sequence.py, 'sign_sequence' maps to a dict that doesn't have 'dataset_status'.
    # We must check if `is_fallback` is False. If it's True, it's finger-spelled (unsupported).
    # Also if we need to check dataset_status, we can query SignVocabulary.
    
    supported_eng = [s for s in seq_eng if not s.get('is_fallback', False)]
    cov_eng = (len(supported_eng) / len(seq_eng)) * 100 if seq_eng else 0
    unsupported_eng = fb_eng
    
    # Evaluate Marathi
    res_mar = process_translation(mar, "mr", log_history=False)
    seq_mar = res_mar.get('sign_sequence', [])
    fb_mar = res_mar.get('fallback_words', [])
    
    supported_mar = [s for s in seq_mar if not s.get('is_fallback', False)]
    cov_mar = (len(supported_mar) / len(seq_mar)) * 100 if seq_mar else 0
    unsupported_mar = fb_mar

    results.append({
        "phrase_en": eng,
        "cov_eng": cov_eng,
        "unsupported_eng": unsupported_eng,
        "phrase_mr": mar,
        "cov_mar": cov_mar,
        "unsupported_mar": unsupported_mar
    })

# Output valid ones
valid_phrases = []
for r in results:
    if r['cov_eng'] >= 50 or r['cov_mar'] >= 50:
        valid_phrases.append({"en": r["phrase_en"], "mr": r["phrase_mr"]})

print(f"Total phrases generated: {len(results)}")
print(f"Valid phrases: {len(valid_phrases)}")

with open("evaluated_phrases.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
