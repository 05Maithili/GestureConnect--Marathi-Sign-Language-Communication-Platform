"""
End-to-End Translation Sequence Orchestrator for GestureConnect.
Coordinates Text Preprocessing, Language Detection, English-Marathi Lexical Mapping,
Linguistic Resolution to Canonical Sign IDs, and Final Sign Animation Sequence Composition.
"""

import time
import logging
from typing import Dict, Any, Optional
from .preprocessing import normalize_text, detect_language
from .english_marathi import map_english_to_marathi
from .mapping import resolve_sequence

logger = logging.getLogger(__name__)


def process_translation(
    raw_text: str,
    language: Optional[str] = None,
    input_mode: str = 'text',
    log_history: bool = True
) -> Dict[str, Any]:
    """
    Executes the comprehensive GestureConnect translation pipeline:

    English/Marathi Text or Speech
            ↓
    Speech-to-Text if speech input (handled upstream)
            ↓
    Text Normalization
            ↓
    Language Detection
            ↓
    English → Marathi lexical mapping if English
            ↓
    Phrase/Word/Normalized-form matching
            ↓
    Canonical Sign IDs
            ↓
    Sign Vocabulary Database
            ↓
    Blender-generated 3D sign animation assets
            ↓
    Out-of-vocabulary handling
            ↓
    Alphabet fingerspelling fallback
            ↓
    Ordered sign sequence
            ↓
    Sentence-level animation composition
    """
    start_time = time.perf_counter()

    if not raw_text or not raw_text.strip():
        return {
            'status': 'error',
            'message': 'Input text cannot be empty.',
            'input_text': '',
            'normalized_text': '',
            'sign_sequence': [],
            'fallback_words': [],
            'stats': {}
        }

    # 1. Text Normalization
    normalized_input = normalize_text(raw_text)

    # 2. Language Detection
    detected_lang = detect_language(normalized_input, specified_language=language)

    intermediate_marathi = normalized_input
    english_mapping_trace = []

    # 3. English to Marathi lexical mapping if English
    if detected_lang == 'en':
        intermediate_marathi, english_mapping_trace = map_english_to_marathi(normalized_input)
        intermediate_marathi = normalize_text(intermediate_marathi)

    # 4. Linguistic Mapping to Canonical Sign IDs and Animation Assets
    mapping_result = resolve_sequence(intermediate_marathi, language=detected_lang)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    sign_sequence = mapping_result['ordered_signs']
    fallback_words = mapping_result['fallback_words']
    stats = mapping_result['stats']
    stats['processing_time_ms'] = elapsed_ms

    # 5. Log translation to history if requested
    history_id = None
    if log_history:
        try:
            from translator.models import TranslationHistory
            history_record = TranslationHistory.objects.create(
                input_text=raw_text.strip(),
                input_language=detected_lang,
                input_mode=input_mode,
                normalized_text=intermediate_marathi,
                generated_sign_sequence=[
                    {
                        'sign_id': s.get('sign_id'),
                        'marathi_term': s.get('marathi_term'),
                        'english_gloss': s.get('english_gloss'),
                        'animation_url': s.get('animation_url'),
                        'is_fallback': s.get('is_fallback', False)
                    } for s in sign_sequence
                ],
                fallback_words=fallback_words,
                processing_time_ms=elapsed_ms
            )
            history_id = history_record.id
        except Exception as e:
            logger.warning(f"Could not save translation history: {e}")

    return {
        'status': 'success',
        'history_id': history_id,
        'input_text': raw_text.strip(),
        'input_language': detected_lang,
        'input_mode': input_mode,
        'normalized_text': intermediate_marathi,
        'english_mapping_trace': english_mapping_trace if detected_lang == 'en' else None,
        'sign_sequence': sign_sequence,
        'fallback_words': fallback_words,
        'stats': stats,
        'processing_time_ms': elapsed_ms
    }
