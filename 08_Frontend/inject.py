import json
import re

phrases = json.load(open('final_phrases.json', encoding='utf-8'))
code = open('translator/views.py', encoding='utf-8').read()

new_code = '    sample_phrases = [\n'
for p in phrases:
    new_code += f'        {{"mr": "{p["mr"]}", "en": "{p["en"]}"}},\n'
new_code += '    ]'

pattern = re.compile(r'    sample_phrases = \[\n.*?    \]', re.DOTALL)
code = pattern.sub(new_code, code)

with open('translator/views.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Views updated successfully!')
