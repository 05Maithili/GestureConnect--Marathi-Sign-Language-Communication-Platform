"""
English to Marathi Lexical Mapping Engine.
Provides a controlled, rule-based lexical mapping layer from English terms/phrases
to Marathi linguistic representations without uncontrolled generative hallucinations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache for in-memory mapping dictionary
_MAPPING_CACHE: Dict[str, Dict[str, str]] = {}


def load_mapping_dictionary() -> Dict[str, Dict[str, str]]:
    """
    Loads lexical mapping from the database and fallback JSON seed file.
    Returns a dictionary with 'phrases' and 'words' keys.
    """
    global _MAPPING_CACHE
    if _MAPPING_CACHE:
        return _MAPPING_CACHE

    phrases_map: Dict[str, str] = {}
    words_map: Dict[str, str] = {}

    # 1. Load from JSON seed file
    json_path = getattr(settings, 'ENGLISH_MARATHI_MAPPING_JSON_PATH', None)
    if json_path and Path(json_path).exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                phrases_map.update({k.lower().strip(): v.strip() for k, v in data.get('phrases', {}).items()})
                words_map.update({k.lower().strip(): v.strip() for k, v in data.get('words', {}).items()})
        except Exception as e:
            logger.warning(f"Failed to load English-Marathi mapping JSON: {e}")

    # 2. Overlay with database records if available
    try:
        from translator.models import EnglishMarathiMapping
        db_mappings = EnglishMarathiMapping.objects.all()
        for item in db_mappings:
            term = item.english_term.lower().strip()
            target = item.marathi_term.strip()
            if item.is_phrase or ' ' in term:
                phrases_map[term] = target
            else:
                words_map[term] = target
    except Exception:
        pass  # DB might not be migrated during initial setup

    _MAPPING_CACHE = {
        'phrases': phrases_map,
        'words': words_map
    }
    return _MAPPING_CACHE


def reload_mapping_cache():
    """Forces cache refresh when database or file is updated."""
    global _MAPPING_CACHE
    _MAPPING_CACHE = {}
    return load_mapping_dictionary()


def map_english_to_marathi(english_text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Translates an English sentence/phrase into a normalized Marathi representation.
    Preserves phrase boundaries and falls back to word-level lookup.
    
    Returns:
        tuple (marathi_sentence, mapping_trace_list)
        
    Example:
        Input: "Hello I need water"
        Output: ("नमस्कार मला पाणी पाहिजे", [
            {"english": "hello", "marathi": "नमस्कार", "type": "word"},
            {"english": "i need water", "marathi": "मला पाणी पाहिजे", "type": "phrase"}
        ])
    """
    if not english_text:
        return "", []

    mapping = load_mapping_dictionary()
    phrases = mapping.get('phrases', {})
    words = mapping.get('words', {})

    cleaned_text = english_text.lower().strip()
    words_list = cleaned_text.split()
    n = len(words_list)
    
    marathi_tokens: List[str] = []
    mapping_trace: List[Dict[str, str]] = []
    i = 0

    while i < n:
        matched = False
        # Try phrase matching from largest window (up to 4 words) down to 2 words
        for window_size in range(min(5, n - i), 1, -1):
            phrase_candidate = " ".join(words_list[i:i + window_size])
            if phrase_candidate in phrases:
                marathi_term = phrases[phrase_candidate]
                marathi_tokens.append(marathi_term)
                mapping_trace.append({
                    'english': phrase_candidate,
                    'marathi': marathi_term,
                    'type': 'phrase_match'
                })
                i += window_size
                matched = True
                break

        if matched:
            continue

        # Single word lookup
        word_candidate = words_list[i]
        if word_candidate in words:
            marathi_term = words[word_candidate]
            marathi_tokens.append(marathi_term)
            mapping_trace.append({
                'english': word_candidate,
                'marathi': marathi_term,
                'type': 'word_match'
            })
        else:
            # Word not in mapping table -> pass through for character fingerspelling
            marathi_tokens.append(word_candidate)
            mapping_trace.append({
                'english': word_candidate,
                'marathi': word_candidate,
                'type': 'unmapped_word'
            })
        i += 1

    marathi_sentence = " ".join(marathi_tokens)
    return marathi_sentence, mapping_trace


def get_marathi_equivalent(english_token: str) -> Optional[str]:
    """Helper for single token lookup."""
    mapping = load_mapping_dictionary()
    token = english_token.lower().strip()
    return mapping.get('phrases', {}).get(token) or mapping.get('words', {}).get(token)
