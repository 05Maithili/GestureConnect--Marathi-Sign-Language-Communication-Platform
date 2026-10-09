import json

# Read valid phrases
with open(r"D:\Colonel\final_year_project\08_Frontend\final_phrases.json", "r", encoding="utf-8") as f:
    phrases = json.load(f)

# Keep only 'mr' and 'en'
clean_phrases = []
for p in phrases:
    clean_phrases.append({"mr": p["mr"], "en": p["en"]})

# Read views.py
views_path = r"D:\Colonel\final_year_project\08_Frontend\translator\views.py"
with open(views_path, "r", encoding="utf-8") as f:
    views_code = f.read()

import re

# We want to replace the block:
#     sample_phrases = [
#         {"mr": "नमस्कार", "en": "Hello"},
#         ...
#         {"mr": "मी शाळेत जातो", "en": "I go to school"}
#     ]
# with our new JSON dump.

# Build the new string
new_code = "    sample_phrases = [\n"
for p in clean_phrases:
    new_code += f'        {{"mr": "{p["mr"]}", "en": "{p["en"]}"}},\n'
new_code += "    ]"

# Let's do a regex substitution
pattern = re.compile(r"    sample_phrases = \[\n.*?    \]", re.DOTALL)
updated_views = pattern.sub(new_code, views_code)

with open(views_path, "w", encoding="utf-8") as f:
    f.write(updated_views)

print("Replaced sample_phrases in views.py successfully!")
