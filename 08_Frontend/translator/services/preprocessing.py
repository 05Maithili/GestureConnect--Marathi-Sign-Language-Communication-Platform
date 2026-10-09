"""
Text Preprocessing & Normalization Module for GestureConnect.
Handles Unicode Devanagari normalization, punctuation cleaning,
whitespace trimming, tokenization, and language detection.
"""

import re
import unicodedata
from typing import List, Tuple

# Devanagari Unicode range: \u0900 - \u097F
DEVANAGARI_RANGE = re.compile(r'[\u0900-\u097F]')

# Punctuation to strip while preserving meaningful text
PUNCTUATION_PATTERN = re.compile(r'[।॥!?,:;"\'\(\)\[\]\{\}<>\-~@#$%^\*_+=|\\/`]+')

# Extra whitespace pattern
WHITESPACE_PATTERN = re.compile(r'\s+')


def normalize_unicode(text: str) -> str:
    """
    Normalizes Unicode representation using NFC format.
    Cleans up zero-width characters and unusual whitespace.
    """
    if not text:
        return ""
    
    # Standardize to Unicode NFC
    normalized = unicodedata.normalize('NFC', str(text))
    
    # Remove zero-width non-joiners and zero-width spaces unless required
    normalized = normalized.replace('\u200b', '')  # zero-width space
    normalized = normalized.replace('\ufeff', '')  # byte order mark
    
    return normalized


def clean_whitespace(text: str) -> str:
    """
    Trims leading/trailing whitespace and compresses multiple consecutive spaces into one.
    """
    if not text:
        return ""
    return WHITESPACE_PATTERN.sub(' ', text).strip()


def remove_unnecessary_punctuation(text: str) -> str:
    """
    Removes extraneous punctuation characters from Marathi and English text.
    Preserves alphanumeric and Devanagari characters.
    """
    if not text:
        return ""
    cleaned = PUNCTUATION_PATTERN.sub(' ', text)
    return clean_whitespace(cleaned)


def normalize_text(text: str) -> str:
    """
    Complete normalization pipeline for input text.
    
    Example:
        Input:  "  नमस्कार!!!   मला   पाणी  पाहिजे  "
        Output: "नमस्कार मला पाणी पाहिजे"
    """
    if not text:
        return ""
    
    # 1. Unicode normalization
    step1 = normalize_unicode(text)
    
    # 2. Punctuation removal
    step2 = remove_unnecessary_punctuation(step1)
    
    # 3. Whitespace normalization
    step3 = clean_whitespace(step2)
    
    return step3


def tokenize_text(text: str) -> List[str]:
    """
    Tokenizes normalized text into words/tokens.
    """
    normalized = normalize_text(text)
    if not normalized:
        return []
    return normalized.split()


def detect_language(text: str, specified_language: str = None) -> str:
    """
    Detects whether text is primarily Marathi ('mr') or English ('en').
    If a valid specified_language is given ('mr' or 'en'), uses that as primary context,
    but falls back to character inspection if specified language contradicts script.
    """
    if not text:
        return specified_language or 'mr'
    
    # Count Devanagari characters
    devanagari_chars = len(DEVANAGARI_RANGE.findall(text))
    total_letters = sum(1 for c in text if c.isalpha())
    
    if total_letters == 0:
        return specified_language or 'mr'
    
    devanagari_ratio = devanagari_chars / total_letters
    
    if devanagari_ratio > 0.4:
        return 'mr'
    
    if specified_language in ['mr', 'en']:
        return specified_language
        
    return 'en'
