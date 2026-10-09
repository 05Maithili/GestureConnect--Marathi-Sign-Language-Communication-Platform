import sys
import os
import django
import json

# Setup django env
sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.models import SignVocabulary

qs = SignVocabulary.objects.filter(is_active=True)
available = [s for s in qs if s.metadata.get('dataset_status') == 'Available']

english_words = [s.english_gloss.lower() for s in available]
marathi_words = [s.marathi_term for s in available]

output = {
    "english": english_words,
    "marathi": marathi_words
}

with open(r"D:\Colonel\final_year_project\08_Frontend\available_words.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
