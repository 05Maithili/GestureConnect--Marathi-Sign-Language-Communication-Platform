# GestureConnect 🤟

> **Bilingual Speech and Text to Marathi Sign Language Translation System**

GestureConnect is an assistive communication web platform designed to bridge communication gaps for the deaf and hard-of-hearing community. The system accepts **Marathi text**, **English text**, and **Marathi speech**, and translates the input into Marathi Sign Language (MSL) animations using a customized 3D humanoid avatar.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Key Features](#key-features)
4. [System Architecture](#system-architecture)
5. [Technology Stack](#technology-stack)
6. [Installation & Setup](#installation--setup)
7. [Running the Application](#running-the-application)
8. [Adding Sign Vocabulary & Mappings](#adding-sign-vocabulary--mappings)
9. [Adding Blender 3D Animation Assets](#adding-blender-3d-animation-assets)
10. [REST API Documentation](#rest-api-documentation)
11. [Automated Testing](#automated-testing)
12. [Evaluation Dashboard](#evaluation-dashboard)
13. [Project Limitations & Future Scope](#project-limitations--future-scope)

---

## 1. Project Overview
GestureConnect implements a linguistic-to-visual translation architecture where linguistic rules, tokenization, and canonical sign mappings remain completely decoupled from 3D visual rendering resources. Individual sign video clips are sequenced and played smoothly on a web video player to present continuous, sentence-level Marathi Sign Language output.

---

## 2. Problem Statement
Individuals with hearing and speech impairments often face significant communication barriers when interacting with spoken and written languages. While Marathi is spoken by over 80 million people, assistive technological solutions for Marathi Sign Language (MSL) are severely limited. GestureConnect provides an accessible, bilingual, speech- and text-enabled translation platform that converts daily communication into standard MSL visual signs.

---

## 3. Key Features
- **Bilingual Input Support:** Accepts Marathi text, English text, and Marathi speech dictation.
- **Unified NLP Preprocessing:** Unicode NFC Devanagari normalization, punctuation cleaning, and whitespace trimming.
- **Controlled Lexical Mapping:** Rule-based English-to-Marathi translation dictionary avoiding generative hallucinations.
- **Hierarchical 5-Priority Linguistic Mapping:**
  - Priority 1: Phrase-level matching
  - Priority 2: Exact word-level matching
  - Priority 3: Normalized-form matching
  - Priority 4: Synonym/alternative mapping
  - Priority 5: Out-of-vocabulary fingerspelling fallback
- **Canonical Sign Identifiers:** Persistent ID layer (`SIGN_HELLO`, `SIGN_WATER`, etc.) bridging language and visuals.
- **Fingerspelling Fallback:** Out-of-vocabulary words are decomposed into Devanagari and Latin alphabet animations without data loss.
- **Sentence-Level Sequential Video Player:** Smooth, continuous playback of individual sign MP4 clips with autoplay, step navigation, and active sign highlighting.
- **Audit History & Unknown Word Logging:** Automatically records translation sessions and flags unfamiliar terms for administrative expansion.
- **Django Admin Interface:** Full management interface for sign vocabulary, metadata, synonyms, mappings, and audit logs.

---

## 4. System Architecture

```
English/Marathi Text or Speech
              ↓
  Speech-to-Text (if Speech)
              ↓
  Common Text Representation
              ↓
      Text Preprocessing
              ↓
      Language Detection
              ↓
  English → Marathi Lexical Mapping (if English)
              ↓
  Hierarchical Linguistic Mapping Engine
  (Phrase → Word → Normalized → Synonyms → Fallback)
              ↓
    Canonical Sign Identifiers
              ↓
     Sign Vocabulary Database
              ↓
 Animation Asset Resolution Layer
(media/animations/<category>/<file>.mp4)
              ↓
Ordered Sign Sequence Composition
              ↓
Sentence-Level 3D Avatar Video Player
```

---

## 5. Technology Stack
- **Backend:** Python 3.11+ / 3.12, Django 5.1+, Django REST Framework
- **Database:** SQLite (default for development; compatible with MySQL)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons
- **Speech Recognition:** Web Speech API (`mr-IN` / `en-IN`) with server-side SpeechRecognition fallback
- **Computer Vision & Video:** OpenCV and PIL for rendering demonstration 3D avatar clips
- **3D Animation Authoring:** Blender 3D (offline authoring of MP4 clips)

---

## 6. Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Git

### Clone the Repository
```bash
git clone https://github.com/your-username/GestureConnect.git
cd GestureConnect
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

---

## 7. Running the Application

### 1. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Seed Sign Vocabulary & Create Admin User
```bash
python manage.py seed_data --create-admin
```
*(Default superuser credentials: Username: `admin` | Password: `admin123`)*

### 3. Generate Demonstration 3D Avatar Animation Assets
```bash
python manage.py generate_sample_assets
```

### 4. Start the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## 8. Adding Sign Vocabulary & Mappings

### Adding via Django Admin Panel
1. Visit `http://127.0.0.1:8000/admin/` and log in.
2. Go to **Sign Vocabulary Entries** → **Add Sign Vocabulary Entry**.
3. Specify `sign_id`, `marathi_term`, `english_gloss`, `category`, `animation_asset`, and `synonyms`.

### Adding via Seed JSON (`data/vocabulary.json`)
```json
{
  "sign_id": "SIGN_DOCTOR",
  "marathi_term": "डॉक्टर",
  "english_gloss": "doctor",
  "category": "objects",
  "sign_type": "lexical",
  "animation_asset": "animations/objects/doctor.mp4",
  "synonyms": ["वैद्य", "दवाखाना"],
  "metadata": {
    "hand_shape": "c_hand",
    "motion": "wrist_pulse_tap",
    "two_handed": true,
    "description": "Fingertips tap opposite wrist measuring pulse."
  }
}
```

---

## 9. Adding Blender 3D Animation Assets

1. Author the sign animation on a humanoid avatar rig in Blender at 24 FPS.
2. Ensure Frame 1 and the final frame start and end in neutral resting transition posture.
3. Export the animation as an H.264 MP4 video (`yuv420p` pixel format).
4. Save the file in `media/animations/<category>/<filename>.mp4`.
5. Associate the asset path with its `Canonical Sign ID` in the database.
6. The web player will immediately resolve and play the animation.

---

## 10. REST API Documentation

### 1. Translation Endpoint
- **URL:** `POST /api/translate/`
- **Payload:**
```json
{
  "text": "नमस्कार मला पाणी पाहिजे",
  "language": "mr",
  "input_mode": "text"
}
```
- **Response:**
```json
{
  "status": "success",
  "input_text": "नमस्कार मला पाणी पाहिजे",
  "normalized_text": "नमस्कार मला पाणी पाहिजे",
  "sign_sequence": [
    {
      "sign_id": "SIGN_HELLO",
      "marathi_term": "नमस्कार",
      "english_gloss": "hello",
      "animation_url": "/media/animations/greetings/hello.mp4",
      "is_fallback": false
    },
    {
      "sign_id": "SIGN_I_ME",
      "marathi_term": "मी",
      "english_gloss": "i",
      "animation_url": "/media/animations/pronouns/me.mp4",
      "is_fallback": false
    },
    {
      "sign_id": "SIGN_WATER",
      "marathi_term": "पाणी",
      "english_gloss": "water",
      "animation_url": "/media/animations/objects/water.mp4",
      "is_fallback": false
    },
    {
      "sign_id": "SIGN_WANT_NEED",
      "marathi_term": "पाहिजे",
      "english_gloss": "want",
      "animation_url": "/media/animations/verbs/want.mp4",
      "is_fallback": false
    }
  ],
  "fallback_words": [],
  "stats": {
    "total_tokens": 4,
    "in_vocabulary_signs": 4,
    "fingerspelled_words": 0,
    "processing_time_ms": 4.8
  },
  "processing_time_ms": 4.8
}
```

### 2. Speech-to-Text Endpoint
- **URL:** `POST /api/speech-to-text/`
- **Payload (Multipart):** `audio` (file) or `transcript` (string), `language` (`mr` or `en`)
- **Response:**
```json
{
  "status": "success",
  "language": "mr",
  "transcript": "मला पाणी पाहिजे"
}
```

### 3. Vocabulary API
- **URL:** `GET /api/vocabulary/?q=पाणी&category=objects`

---

## 11. Automated Testing

Run the test suite to verify preprocessing, lexical mappings, canonical sign ID generation, fallback logic, and REST endpoints:

```bash
python manage.py test
```

---

## 12. Evaluation Dashboard
Visit `/evaluation/` to view live performance analytics:
- Real-time translation throughput and latency (ms)
- Active sign vocabulary distribution across categories
- Out-of-vocabulary (OOV) fingerspelling frequency
- Unknown word log for vocabulary expansion

---

## 13. Project Limitations & Future Scope

### Current Limitations
- Sign vocabulary relies on pre-authored and rendered 3D animation assets.
- English-to-Marathi translation is rule-based and vocabulary-scoped to prevent uncontrolled generative text distortion.

### Future Scope
- Continuous sign blending using WebGL/Three.js bone transitions.
- Expansion of Marathi regional dialect vocabularies.
- Two-way conversation logging for institutional assistive deployment.
