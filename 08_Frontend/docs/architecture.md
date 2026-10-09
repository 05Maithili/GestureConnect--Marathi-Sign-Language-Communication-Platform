# GestureConnect System Architecture

## 1. System Overview
**GestureConnect** is a bilingual assistive communication platform designed to translate English text, Marathi text, and Marathi speech into Marathi Sign Language (MSL) using a customized 3D avatar.

The system is architected around strict separation between linguistic processing and 3D visual animation rendering, with **Canonical Sign Identifiers** acting as the central decoupled bridge.

---

## 2. End-to-End Pipeline

```
English/Marathi Text or Speech Input
              ↓
  Speech-to-Text (if Speech)
              ↓
  Common Text Representation
              ↓
      Text Preprocessing
 (Unicode NFC, Punctuation, Whitespace)
              ↓
      Language Detection
              ↓
  English → Marathi Lexical Mapping (if English)
              ↓
  Hierarchical Linguistic Mapping Engine
  ├── Priority 1: Phrase-level matching
  ├── Priority 2: Exact word-level matching
  ├── Priority 3: Normalized-form matching
  ├── Priority 4: Synonym/alternative matching
  └── Priority 5: Fingerspelling fallback
              ↓
    Canonical Sign Identifiers
    (e.g., SIGN_HELLO, SIGN_WATER)
              ↓
     Sign Vocabulary Database
 (Linguistic & Biomechanical Metadata)
              ↓
 Animation Asset Resolution Layer
(media/animations/<category>/<file>.mp4)
              ↓
Ordered Sign Sequence Composition
              ↓
Sentence-Level 3D Avatar Video Player
```

---

## 3. Core Modules & Responsibilities

### 3.1 Input Acquisition & Speech-to-Text (`translator/services/speech.py`)
- Accepts Marathi (`mr-IN`) and English (`en-IN`) speech input.
- Dual-mode architecture:
  1. Client-side native Web Speech API for zero-latency in-browser recognition.
  2. Server-side REST endpoint (`/api/speech-to-text/`) for recorded audio files (WAV/FLAC/MP3).
- Output is an authentic text transcript that flows immediately into the unified text normalization pipeline.

### 3.2 Text Preprocessing (`translator/services/preprocessing.py`)
- Normalizes Unicode Devanagari using standard NFC composition.
- Strips zero-width characters (`\u200b`, `\ufeff`).
- Cleans extraneous punctuation while preserving Devanagari and Latin characters.
- Tokenizes sentence strings into structured lexical units.

### 3.3 English-to-Marathi Lexical Mapping (`translator/services/english_marathi.py`)
- Implements a controlled rule-based dictionary mapping.
- Replaces English phrases (e.g., `"i need water"` → `"मला पाणी पाहिजे"`) and words (e.g., `"water"` → `"पाणी"`).
- Avoids unpredictable generative hallucinations.

### 3.4 Linguistic Mapping Engine (`translator/services/mapping.py`)
- Evaluates tokens against active sign vocabulary using a 5-tier priority hierarchy:
  1. **Phrase Matching:** Multi-word window sliding.
  2. **Exact Word Matching:** Direct match against primary Marathi term or English gloss.
  3. **Normalized Form Matching:** Punctuation- and casing-insensitive comparison.
  4. **Synonym Matching:** Compares against `synonyms` JSON list.
  5. **Fingerspelling Fallback:** Decomposes out-of-vocabulary words into character units.

### 3.5 Canonical Sign ID System
- Persistent, immutable identifiers such as `SIGN_HELLO`, `SIGN_WATER`, `SIGN_MOTHER`.
- Ensures linguistic mapping is completely agnostic to physical video filenames or storage backends.

### 3.6 Animation Asset System (`translator/services/animation.py`)
- Resolves Canonical Sign IDs to Blender-rendered MP4 video assets stored in `media/animations/`.
- Gracefully handles missing assets with fallback metadata.

### 3.7 Sequence Composition & Player (`frontend/static/js/player.js`)
- Composes individual sign clips into an ordered sequence.
- Client-side sequential playback provides seamless sentence-level signing without expensive real-time 3D GPU rendering in the browser.
