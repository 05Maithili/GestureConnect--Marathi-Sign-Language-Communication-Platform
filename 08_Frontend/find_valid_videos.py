import sys
import os
import django
import json

sys.path.append(r"D:\Colonel\final_year_project\08_Frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
django.setup()

from translator.services.sequence import process_translation
from translator.services.animation import get_animation

# Let's start with a huge list of very basic 2-word combinations to see what is ACTUALLY available in the media folder!
import itertools

# First, extract all english words that have ACTUAL videos on disk!
from translator.models import SignVocabulary
vocab = SignVocabulary.objects.filter(is_active=True)

valid_words_en = []
valid_words_mr = []

for v in vocab:
    # get_animation takes sign_id, asset_path
    anim = get_animation(v.sign_id, v.animation_asset, v.metadata)
    if anim['asset_exists']:
        valid_words_en.append(v.english_gloss.lower())
        valid_words_mr.append(v.marathi_term)

print(f"Total words with physical MP4s on disk: {len(valid_words_en)}")

# Let's find valid words that we can combine.
# I will output all the valid words so I can construct a good list of phrases.
with open("valid_words_en.json", "w", encoding="utf-8") as f:
    json.dump(valid_words_en, f, indent=2, ensure_ascii=False)
with open("valid_words_mr.json", "w", encoding="utf-8") as f:
    json.dump(valid_words_mr, f, indent=2, ensure_ascii=False)
