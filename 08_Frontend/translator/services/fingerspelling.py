"""
Fingerspelling Fallback Service.
Handles out-of-vocabulary (OOV) words by decomposing words into character units
and mapping each character to Devanagari or Latin fingerspelling animations.
"""

import unicodedata
from typing import List, Dict, Any

# Mapping Devanagari characters to canonical fingerspelling sign IDs
DEVANAGARI_FINGERSPELLING_MAP = {
    # Vowels (स्वर)
    'अ': 'SIGN_FS_MR_A',
    'आ': 'SIGN_FS_MR_AA',
    'इ': 'SIGN_FS_MR_I',
    'ई': 'SIGN_FS_MR_EE',
    'उ': 'SIGN_FS_MR_U',
    'ऊ': 'SIGN_FS_MR_OO',
    'ऋ': 'SIGN_FS_MR_RU',
    'ए': 'SIGN_FS_MR_E',
    'ऐ': 'SIGN_FS_MR_AI',
    'ओ': 'SIGN_FS_MR_O',
    'औ': 'SIGN_FS_MR_AU',
    'अं': 'SIGN_FS_MR_AM',
    'अः': 'SIGN_FS_MR_AHA',
    
    # Consonants (व्यंजन)
    'क': 'SIGN_FS_MR_KA',
    'ख': 'SIGN_FS_MR_KHA',
    'ग': 'SIGN_FS_MR_GA',
    'घ': 'SIGN_FS_MR_GHA',
    'ङ': 'SIGN_FS_MR_NGA',
    'च': 'SIGN_FS_MR_CHA',
    'छ': 'SIGN_FS_MR_CHHA',
    'ज': 'SIGN_FS_MR_JA',
    'झ': 'SIGN_FS_MR_JHA',
    'ञ': 'SIGN_FS_MR_NYA',
    'ट': 'SIGN_FS_MR_TTA',
    'ठ': 'SIGN_FS_MR_TTHA',
    'ड': 'SIGN_FS_MR_DDA',
    'ढ': 'SIGN_FS_MR_DDHA',
    'ण': 'SIGN_FS_MR_NNA',
    'त': 'SIGN_FS_MR_TA',
    'थ': 'SIGN_FS_MR_THA',
    'द': 'SIGN_FS_MR_DA',
    'ध': 'SIGN_FS_MR_DHA',
    'न': 'SIGN_FS_MR_NA',
    'प': 'SIGN_FS_MR_PA',
    'फ': 'SIGN_FS_MR_PHA',
    'ब': 'SIGN_FS_MR_BA',
    'भ': 'SIGN_FS_MR_BHA',
    'म': 'SIGN_FS_MR_MA',
    'य': 'SIGN_FS_MR_YA',
    'र': 'SIGN_FS_MR_RA',
    'ल': 'SIGN_FS_MR_LA',
    'व': 'SIGN_FS_MR_VA',
    'श': 'SIGN_FS_MR_SHA',
    'ष': 'SIGN_FS_MR_SSA',
    'स': 'SIGN_FS_MR_SA',
    'ह': 'SIGN_FS_MR_HA',
    'ळ': 'SIGN_FS_MR_LLA',
    'क्ष': 'SIGN_FS_MR_KSHA',
    'ज्ञ': 'SIGN_FS_MR_GYA',
    
    # Devanagari Digits
    '०': 'SIGN_FS_MR_0',
    '१': 'SIGN_FS_MR_1',
    '२': 'SIGN_FS_MR_2',
    '३': 'SIGN_FS_MR_3',
    '४': 'SIGN_FS_MR_4',
    '५': 'SIGN_FS_MR_5',
    '६': 'SIGN_FS_MR_6',
    '७': 'SIGN_FS_MR_7',
    '८': 'SIGN_FS_MR_8',
    '९': 'SIGN_FS_MR_9',
}

# Devanagari Matras (Vowel Signs)
DEVANAGARI_MATRA_MAP = {
    'ा': 'SIGN_FS_MR_AA',
    'ि': 'SIGN_FS_MR_I',
    'ी': 'SIGN_FS_MR_EE',
    'ु': 'SIGN_FS_MR_U',
    'ू': 'SIGN_FS_MR_OO',
    'ृ': 'SIGN_FS_MR_RU',
    'े': 'SIGN_FS_MR_E',
    'ै': 'SIGN_FS_MR_AI',
    'ो': 'SIGN_FS_MR_O',
    'ौ': 'SIGN_FS_MR_AU',
    'ं': 'SIGN_FS_MR_AM',
    'ः': 'SIGN_FS_MR_AHA',
    'ॉ': 'SIGN_FS_MR_O',
    'ॅ': 'SIGN_FS_MR_E',
}

# English Alphabet A-Z Fingerspelling
ENGLISH_FINGERSPELLING_MAP = {
    chr(i): f"SIGN_FS_EN_{chr(i)}" for i in range(ord('A'), ord('Z') + 1)
}
for d in "0123456789":
    ENGLISH_FINGERSPELLING_MAP[d] = f"SIGN_FS_EN_{d}"


def decompose_devanagari_word(word: str) -> List[str]:
    """
    Decomposes a Devanagari word into meaningful readable characters.
    Handles consonant + virama combinations and matras smoothly.
    """
    chars: List[str] = []
    i = 0
    n = len(word)
    
    while i < n:
        c = word[i]
        
        # Check compound characters like क्ष (क + ् + ष) or ज्ञ (ज + ् + ञ)
        if i + 2 < n and c == 'क' and word[i+1] == '्' and word[i+2] == 'ष':
            chars.append('क्ष')
            i += 3
            continue
        if i + 2 < n and c == 'ज' and word[i+1] == '्' and word[i+2] == 'ञ':
            chars.append('ज्ञ')
            i += 3
            continue
            
        if c in DEVANAGARI_FINGERSPELLING_MAP:
            chars.append(c)
        elif c in DEVANAGARI_MATRA_MAP:
            chars.append(c)
        elif c == '्':  # Virama / Halant
            pass  # Half-letter modification is conveyed via consonant sign
        elif not c.isspace():
            chars.append(c)
        i += 1
        
    return chars


def get_fingerspelling_sequence(word: str, language: str = 'mr') -> List[Dict[str, Any]]:
    """
    Converts an unknown word into an ordered sequence of fingerspelling sign items.
    
    Example:
        Input: "कॉलेज"
        Output: [
            {"char": "क", "sign_id": "SIGN_FS_MR_KA", "english_gloss": "K", "sign_type": "fingerspell", "is_fallback": True},
            {"char": "ॉ", "sign_id": "SIGN_FS_MR_O", "english_gloss": "O", "sign_type": "fingerspell", "is_fallback": True},
            {"char": "ल", "sign_id": "SIGN_FS_MR_LA", "english_gloss": "L", "sign_type": "fingerspell", "is_fallback": True},
            {"char": "े", "sign_id": "SIGN_FS_MR_E", "english_gloss": "E", "sign_type": "fingerspell", "is_fallback": True},
            {"char": "ज", "sign_id": "SIGN_FS_MR_JA", "english_gloss": "J", "sign_type": "fingerspell", "is_fallback": True}
        ]
    """
    if not word:
        return []

    sequence: List[Dict[str, Any]] = []

    # Check if word contains Devanagari
    is_devanagari = any('\u0900' <= char <= '\u097F' for char in word)

    if is_devanagari:
        chars = decompose_devanagari_word(word)
        for ch in chars:
            sign_id = DEVANAGARI_FINGERSPELLING_MAP.get(ch) or DEVANAGARI_MATRA_MAP.get(ch)
            if not sign_id:
                sign_id = f"SIGN_FS_CHAR_{ord(ch):04X}"
            
            sequence.append({
                'char': ch,
                'sign_id': sign_id,
                'marathi_term': ch,
                'english_gloss': f"Fingerspell '{ch}'",
                'category': 'fingerspelling',
                'sign_type': 'fingerspell',
                'animation_asset': f"animations/fingerspelling/mr_{sign_id.lower().replace('sign_fs_mr_', '')}.mp4",
                'is_fallback': True,
                'parent_word': word
            })
    else:
        # Latin / English alphabetic fingerspelling
        for ch in word.upper():
            if ch.isspace():
                continue
            sign_id = ENGLISH_FINGERSPELLING_MAP.get(ch, f"SIGN_FS_EN_{ch}")
            sequence.append({
                'char': ch,
                'sign_id': sign_id,
                'marathi_term': ch,
                'english_gloss': f"Letter {ch}",
                'category': 'fingerspelling',
                'sign_type': 'fingerspell',
                'animation_asset': f"animations/fingerspelling/en_{ch.lower()}.mp4",
                'is_fallback': True,
                'parent_word': word
            })

    return sequence
