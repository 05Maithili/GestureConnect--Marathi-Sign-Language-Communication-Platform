"""
Linguistic Mapping Engine for GestureConnect.
Implements the 5-tier hierarchical mapping pipeline:
  Priority 1: Phrase-level matching
  Priority 2: Exact word-level matching
  Priority 3: Normalized-form matching
  Priority 4: Synonym / alternative mapping
  Priority 5: Out-of-vocabulary handling & Fingerspelling fallback
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q
from .preprocessing import normalize_text, tokenize_text, normalize_unicode
from .fingerspelling import get_fingerspelling_sequence
from .animation import get_animation

logger = logging.getLogger(__name__)


def get_active_vocabulary_cache() -> List[Dict[str, Any]]:
    """
    Retrieves active vocabulary entries. Uses database query or fallback.
    """
    from translator.models import SignVocabulary
    try:
        vocab = SignVocabulary.objects.filter(is_active=True).values(
            'sign_id', 'marathi_term', 'english_gloss', 'category',
            'sign_type', 'animation_asset', 'metadata', 'synonyms'
        )
        return list(vocab)
    except Exception as e:
        logger.warning(f"Database lookup failed, returning empty vocab cache: {e}")
        return []


def match_phrase(tokens: List[str], start_idx: int, vocab_list: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Priority 1: Phrase-level matching.
    Checks multi-word token sequences (from 4 words down to 2 words).
    """
    n = len(tokens)
    for window in range(min(4, n - start_idx), 1, -1):
        candidate = " ".join(tokens[start_idx:start_idx + window])
        candidate_norm = normalize_text(candidate)

        for item in vocab_list:
            # Check marathi phrase
            if normalize_text(item['marathi_term']) == candidate_norm:
                return item, window
            # Check english phrase gloss
            if normalize_text(item['english_gloss']).lower() == candidate_norm.lower():
                return item, window
            # Check synonyms for phrase
            synonyms = item.get('synonyms') or []
            if any(normalize_text(s) == candidate_norm for s in synonyms):
                return item, window

    return None, 0


def match_word(token: str, vocab_list: List[Dict[str, Any]]) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Evaluates Priorities 2, 3, and 4 for a single word token.
    Returns: (matched_vocab_item, match_type_str) or None.
    """
    token_raw = token.strip()
    token_norm = normalize_text(token_raw)
    token_lower = token_norm.lower()

    # Priority 2: Exact word-level matching
    for item in vocab_list:
        if item['marathi_term'] == token_raw or item['english_gloss'].lower() == token_lower:
            return item, 'exact_word'

    # Priority 3: Normalized-form matching
    for item in vocab_list:
        if normalize_text(item['marathi_term']) == token_norm:
            return item, 'normalized_form'
        if normalize_text(item['english_gloss']).lower() == token_lower:
            return item, 'normalized_form'

    # Priority 4: Synonym / alternative matching
    for item in vocab_list:
        synonyms = item.get('synonyms') or []
        for syn in synonyms:
            if normalize_text(syn) == token_norm or normalize_text(syn).lower() == token_lower:
                return item, 'synonym_match'

    return None


def handle_unknown_word(word: str, language: str = 'mr') -> Tuple[List[Dict[str, Any]], str]:
    """
    Priority 5: Out-of-vocabulary handling and fingerspelling fallback.
    Logs the unknown word to the database for administrative review.
    """
    # 1. Log to UnknownWordLog
    try:
        from translator.models import UnknownWordLog
        log_entry, created = UnknownWordLog.objects.get_or_create(
            word=word,
            defaults={'language': language, 'occurrence_count': 1}
        )
        if not created:
            log_entry.occurrence_count += 1
            log_entry.save(update_fields=['occurrence_count', 'last_seen'])
    except Exception as e:
        logger.warning(f"Failed to log unknown word '{word}': {e}")

    # 2. Decompose into fingerspelling sequence
    fs_sequence = get_fingerspelling_sequence(word, language=language)
    
    # Resolve animation items for each fingerspelled character
    resolved_fs: List[Dict[str, Any]] = []
    for fs_item in fs_sequence:
        anim_info = get_animation(
            sign_id=fs_item['sign_id'],
            asset_path=fs_item['animation_asset']
        )
        fs_item.update(anim_info)
        resolved_fs.append(fs_item)

    return resolved_fs, word


def resolve_sequence(normalized_text: str, language: str = 'mr') -> Dict[str, Any]:
    """
    Executes the full linguistic mapping pipeline on normalized text.
    Produces an ordered sequence of canonical sign objects with animation resolutions.
    """
    tokens = tokenize_text(normalized_text)
    vocab_list = get_active_vocabulary_cache()

    ordered_signs: List[Dict[str, Any]] = []
    fallback_words: List[str] = []
    in_vocab_count = 0
    fingerspelled_count = 0

    i = 0
    n = len(tokens)

    while i < n:
        # Priority 1: Phrase-level matching
        phrase_match, consumed = match_phrase(tokens, i, vocab_list)
        if phrase_match:
            anim_info = get_animation(
                sign_id=phrase_match['sign_id'],
                asset_path=phrase_match['animation_asset'],
                metadata=phrase_match.get('metadata')
            )
            sign_entry = {
                'sign_id': phrase_match['sign_id'],
                'marathi_term': phrase_match['marathi_term'],
                'english_gloss': phrase_match['english_gloss'],
                'category': phrase_match['category'],
                'sign_type': phrase_match['sign_type'],
                'match_priority': 1,
                'match_type': 'phrase_match',
                'matched_tokens': tokens[i:i + consumed],
                'is_fallback': False,
                **anim_info
            }
            ordered_signs.append(sign_entry)
            in_vocab_count += 1
            i += consumed
            continue

        # Single word matching (Priorities 2, 3, 4)
        token = tokens[i]
        word_match_res = match_word(token, vocab_list)

        if word_match_res:
            matched_item, match_type = word_match_res
            priority_num = 2 if match_type == 'exact_word' else (3 if match_type == 'normalized_form' else 4)
            anim_info = get_animation(
                sign_id=matched_item['sign_id'],
                asset_path=matched_item['animation_asset'],
                metadata=matched_item.get('metadata')
            )
            sign_entry = {
                'sign_id': matched_item['sign_id'],
                'marathi_term': matched_item['marathi_term'],
                'english_gloss': matched_item['english_gloss'],
                'category': matched_item['category'],
                'sign_type': matched_item['sign_type'],
                'match_priority': priority_num,
                'match_type': match_type,
                'matched_tokens': [token],
                'is_fallback': False,
                **anim_info
            }
            ordered_signs.append(sign_entry)
            in_vocab_count += 1
        else:
            # Priority 5: Unknown word -> Fingerspelling fallback
            fs_items, unk_word = handle_unknown_word(token, language=language)
            fallback_words.append(unk_word)
            fingerspelled_count += 1
            for item in fs_items:
                ordered_signs.append(item)

        i += 1

    return {
        'input_text': normalized_text,
        'tokens': tokens,
        'ordered_signs': ordered_signs,
        'fallback_words': fallback_words,
        'stats': {
            'total_tokens': len(tokens),
            'in_vocabulary_signs': in_vocab_count,
            'fingerspelled_words': fingerspelled_count,
            'total_sign_sequence_length': len(ordered_signs)
        }
    }
