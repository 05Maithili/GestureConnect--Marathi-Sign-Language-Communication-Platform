import json
import logging
from pathlib import Path
from django.conf import settings
import re
import urllib.parse

logger = logging.getLogger(__name__)

class DictionaryService:
    _instance = None
    _english_map = {}
    _marathi_map = {}
    _vocab_map = {}
    _dataset_root = None
    _dataset_url_prefix = ""
    _is_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load_dictionaries()
        return cls._instance

    def load_dictionaries(self):
        if self._is_loaded:
            return

        dict_root = getattr(settings, 'MULTILINGUAL_DICTIONARY_ROOT', None)
        self._dataset_root = getattr(settings, 'OPTIMIZED_DATASET_ROOT', None)
        self._dataset_url_prefix = getattr(settings, 'OPTIMIZED_DATASET_URL', '/media/dataset/')

        if not dict_root or not self._dataset_root:
            logger.error("MULTILINGUAL_DICTIONARY_ROOT or OPTIMIZED_DATASET_ROOT not configured in settings.")
            return

        try:
            en_path = dict_root / 'English' / 'english_to_sign.json'
            with open(en_path, 'r', encoding='utf-8') as f:
                self._english_map = json.load(f)

            mr_path = dict_root / 'Marathi' / 'marathi_to_sign.json'
            with open(mr_path, 'r', encoding='utf-8') as f:
                self._marathi_map = json.load(f)

            vocab_path = dict_root / 'Vocabulary' / 'sign_vocabulary.json'
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab_list = json.load(f)
                self._vocab_map = {item['sign_id']: item for item in vocab_list}

            self._is_loaded = True
            logger.info("Successfully loaded multilingual dictionaries into memory.")
        except Exception as e:
            logger.error(f"Failed to load dictionaries: {str(e)}")

    def is_marathi(self, text):
        # Lightweight Devanagari detection
        for char in text:
            if '\u0900' <= char <= '\u097F':
                return True
        return False

    def tokenize_and_clean(self, sentence):
        """ Tokenizes text, preserving Devanagari characters, lowering English. """
        if not sentence:
            return []
        
        # Keep alphabets and Devanagari
        cleaned = re.sub(r'[^\w\s\u0900-\u097F]', '', sentence)
        tokens = cleaned.split()
        return tokens

    def lookup_word(self, word, language="auto"):
        word = word.strip()
        word_lower = word.lower()
        
        if language == "auto":
            is_mr = self.is_marathi(word)
        else:
            is_mr = (language == "mr")

        if is_mr:
            sign_ids = self._marathi_map.get(word, [])
        else:
            sign_ids = self._english_map.get(word_lower, [])

        # Deterministic: Return first mapping if polysemy exists
        if sign_ids:
            return sign_ids[0]
        return None

    def resolve_video_path(self, sign_id):
        if not sign_id or sign_id not in self._vocab_map:
            return None

        dataset_word = self._vocab_map[sign_id].get('dataset_word')
        if not dataset_word:
            return None

        # Resolve path safely
        target_dir = self._dataset_root / dataset_word
        
        # Check against path traversal implicitly by checking if it resolves inside root
        try:
            target_dir = target_dir.resolve(strict=False)
            if not str(target_dir).startswith(str(self._dataset_root.resolve(strict=False))):
                logger.warning(f"Path traversal attempt blocked: {dataset_word}")
                return None
        except Exception:
            pass

        if not target_dir.exists() or not target_dir.is_dir():
            return None

        # Find first video file deterministically
        videos = sorted([f for f in target_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.mp4', '.mov', '.webm']])
        
        if not videos:
            return None
            
        video_file = videos[0]
        # Construct URL
        # URL safe quoting for folder name containing spaces
        rel_folder = urllib.parse.quote(dataset_word)
        rel_file = urllib.parse.quote(video_file.name)
        
        video_url = f"{self._dataset_url_prefix}{rel_folder}/{rel_file}"
        return video_url

    def translate_sentence(self, sentence, language="auto"):
        tokens = self.tokenize_and_clean(sentence)
        result = {
            "success": True,
            "input_text": sentence,
            "detected_language": language,
            "tokens": [],
            "available_signs": [],
            "unknown_words": [],
            "video_sequence": []
        }

        if language == "auto" and sentence:
            result["detected_language"] = "mr" if self.is_marathi(sentence) else "en"

        for token in tokens:
            sign_id = self.lookup_word(token, language=language)
            
            if sign_id:
                video_url = self.resolve_video_path(sign_id)
                if video_url:
                    item = {
                        "word": token,
                        "status": "available",
                        "sign_id": sign_id,
                        "video_url": video_url
                    }
                    result["tokens"].append(item)
                    result["available_signs"].append(token)
                    result["video_sequence"].append(video_url)
                else:
                    item = {
                        "word": token,
                        "status": "unavailable (no video)",
                        "sign_id": sign_id,
                        "video_url": None
                    }
                    result["tokens"].append(item)
                    result["unknown_words"].append(token)
            else:
                item = {
                    "word": token,
                    "status": "unavailable",
                    "sign_id": None,
                    "video_url": None
                }
                result["tokens"].append(item)
                result["unknown_words"].append(token)

        return result
