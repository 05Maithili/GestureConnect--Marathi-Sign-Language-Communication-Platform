"""
Speech Recognition Service for GestureConnect.
Handles Marathi (mr-IN) and English (en-IN) speech-to-text conversion.
Audio passes into this module and returns a text transcript, which immediately
converges into the common text normalization and linguistic mapping pipeline.
"""

import io
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def recognize_speech_audio(audio_file, language: str = 'mr-IN') -> Dict[str, Any]:
    """
    Processes an uploaded audio file (WAV, FLAC, AIFF) using speech recognition.
    
    Returns:
        {
            "status": "success",
            "language": "mr",
            "transcript": "मला पाणी पाहिजे",
            "confidence": 0.95
        }
    """
    try:
        import speech_recognition as sr
    except ImportError:
        return {
            'status': 'error',
            'message': 'SpeechRecognition library is not installed on the server.',
            'language': language,
            'transcript': ''
        }

    recognizer = sr.Recognizer()

    # Map language codes to standard BCP-47
    lang_code = 'mr-IN' if 'mr' in language.lower() else 'en-IN'

    try:
        # If audio_file is a Django UploadedFile or file-like object
        with sr.AudioFile(audio_file) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)

        # Recognize using Google Web Speech Recognition API
        transcript = recognizer.recognize_google(audio_data, language=lang_code)
        
        return {
            'status': 'success',
            'language': 'mr' if 'mr' in lang_code else 'en',
            'transcript': transcript,
            'confidence': 1.0
        }

    except sr.UnknownValueError:
        return {
            'status': 'error',
            'message': 'Speech could not be understood. Please speak clearly into the microphone.',
            'language': 'mr' if 'mr' in lang_code else 'en',
            'transcript': ''
        }
    except sr.RequestError as e:
        logger.error(f"Speech recognition service error: {e}")
        return {
            'status': 'error',
            'message': f'Speech recognition service request error: {str(e)}',
            'language': 'mr' if 'mr' in lang_code else 'en',
            'transcript': ''
        }
    except Exception as e:
        logger.error(f"Unexpected speech recognition error: {e}")
        return {
            'status': 'error',
            'message': f'Failed to process audio: {str(e)}',
            'language': 'mr' if 'mr' in lang_code else 'en',
            'transcript': ''
        }
