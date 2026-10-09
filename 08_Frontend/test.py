import urllib.request
import json

def test_api(text, language='auto'):
    url = 'http://127.0.0.1:8000/api/translate/'
    payload = {'text': text, 'language': language, 'mode': 'phase1'}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print(f'\n[TEST] Text: {text}')
            print('Status: 200 OK')
            print(f'Tokens: {len(res.get("tokens", []))}')
            print(f'Available: {res.get("available_signs", [])}')
            print(f'Unknown: {res.get("unknown_words", [])}')
            print(f'Videos: {res.get("video_sequence", [])}')
    except Exception as e:
        print(f'\n[TEST] Text: {text} - ERROR: {e}')

test_api('Hello')
test_api('Hello, how are you?')
test_api('hello')
test_api('नमस्कार')
test_api('xyzabc')
test_api('')
