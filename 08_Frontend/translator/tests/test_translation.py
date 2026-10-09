"""
Automated Test Suite for GestureConnect.
Tests text preprocessing, Unicode normalization, English-Marathi mapping,
lexical & phrase matching, canonical sign ID resolution, fingerspelling fallback,
and REST API endpoints.
"""

from django.test import TestCase, Client
from django.urls import reverse
from translator.models import SignVocabulary, EnglishMarathiMapping, TranslationHistory, UnknownWordLog
from translator.services.preprocessing import (
    normalize_text,
    normalize_unicode,
    clean_whitespace,
    remove_unnecessary_punctuation,
    tokenize_text,
    detect_language
)
from translator.services.english_marathi import map_english_to_marathi, get_marathi_equivalent
from translator.services.fingerspelling import get_fingerspelling_sequence, decompose_devanagari_word
from translator.services.animation import get_animation
from translator.services.mapping import resolve_sequence, handle_unknown_word
from translator.services.sequence import process_translation


class TextPreprocessingTests(TestCase):
    """Test Suite 1 & 2: Text Preprocessing and Unicode Normalization"""

    def test_unicode_normalization(self):
        # Test Unicode NFC normalization and zero-width clean up
        raw = "नम\u200bस्कार"
        norm = normalize_unicode(raw)
        self.assertEqual(norm, "नमस्कार")

    def test_clean_whitespace(self):
        raw = "   नमस्कार    मला   पाणी   "
        self.assertEqual(clean_whitespace(raw), "नमस्कार मला पाणी")

    def test_remove_punctuation(self):
        raw = "नमस्कार!!! मला, पाणी पाहिजे??? ।"
        cleaned = remove_unnecessary_punctuation(raw)
        self.assertEqual(cleaned, "नमस्कार मला पाणी पाहिजे")

    def test_full_normalize_text(self):
        raw = "  नमस्कार!!!   मला   पाणी  पाहिजे  "
        normalized = normalize_text(raw)
        self.assertEqual(normalized, "नमस्कार मला पाणी पाहिजे")

    def test_tokenization(self):
        raw = "नमस्कार मला पाणी पाहिजे"
        tokens = tokenize_text(raw)
        self.assertEqual(tokens, ["नमस्कार", "मला", "पाणी", "पाहिजे"])

    def test_language_detection(self):
        self.assertEqual(detect_language("नमस्कार"), "mr")
        self.assertEqual(detect_language("Hello water"), "en")


class EnglishMarathiMappingTests(TestCase):
    """Test Suite 3: English to Marathi Lexical Mapping"""

    def setUp(self):
        EnglishMarathiMapping.objects.create(
            english_term="hello",
            marathi_term="नमस्कार",
            is_phrase=False
        )
        EnglishMarathiMapping.objects.create(
            english_term="water",
            marathi_term="पाणी",
            is_phrase=False
        )
        EnglishMarathiMapping.objects.create(
            english_term="i need water",
            marathi_term="मला पाणी पाहिजे",
            is_phrase=True
        )

    def test_word_mapping(self):
        marathi, trace = map_english_to_marathi("hello water")
        self.assertIn("नमस्कार", marathi)
        self.assertIn("पाणी", marathi)

    def test_phrase_mapping(self):
        marathi, trace = map_english_to_marathi("i need water")
        self.assertEqual(marathi, "मला पाणी पाहिजे")


class LinguisticMappingAndCanonicalSignTests(TestCase):
    """Test Suites 4, 5, 6, 7: Vocabulary Matching, Phrase Matching, Canonical Sign IDs"""

    def setUp(self):
        # Seed test signs
        self.sign_hello = SignVocabulary.objects.create(
            sign_id="SIGN_HELLO",
            marathi_term="नमस्कार",
            english_gloss="hello",
            category="greetings",
            sign_type="lexical",
            animation_asset="animations/greetings/hello.mp4",
            synonyms=["नमस्ते", "हाय"]
        )
        self.sign_water = SignVocabulary.objects.create(
            sign_id="SIGN_WATER",
            marathi_term="पाणी",
            english_gloss="water",
            category="objects",
            sign_type="lexical",
            animation_asset="animations/objects/water.mp4",
            synonyms=["जल"]
        )
        self.sign_good_morning = SignVocabulary.objects.create(
            sign_id="SIGN_GOOD_MORNING",
            marathi_term="शुभ प्रभात",
            english_gloss="good morning",
            category="greetings",
            sign_type="phrase",
            animation_asset="animations/greetings/good_morning.mp4",
            synonyms=["सुप्रभात"]
        )

    def test_exact_word_matching(self):
        res = resolve_sequence("नमस्कार")
        self.assertEqual(len(res['ordered_signs']), 1)
        self.assertEqual(res['ordered_signs'][0]['sign_id'], "SIGN_HELLO")
        self.assertEqual(res['ordered_signs'][0]['match_priority'], 2)

    def test_synonym_matching(self):
        res = resolve_sequence("नमस्ते")
        self.assertEqual(len(res['ordered_signs']), 1)
        self.assertEqual(res['ordered_signs'][0]['sign_id'], "SIGN_HELLO")
        self.assertEqual(res['ordered_signs'][0]['match_type'], "synonym_match")

    def test_phrase_matching(self):
        res = resolve_sequence("शुभ प्रभात")
        self.assertEqual(len(res['ordered_signs']), 1)
        self.assertEqual(res['ordered_signs'][0]['sign_id'], "SIGN_GOOD_MORNING")
        self.assertEqual(res['ordered_signs'][0]['match_priority'], 1)

    def test_multi_sign_ordered_sequence(self):
        res = resolve_sequence("नमस्कार पाणी")
        self.assertEqual(len(res['ordered_signs']), 2)
        self.assertEqual(res['ordered_signs'][0]['sign_id'], "SIGN_HELLO")
        self.assertEqual(res['ordered_signs'][1]['sign_id'], "SIGN_WATER")


class FingerspellingAndUnknownWordTests(TestCase):
    """Test Suites 8 & 9: Unknown Word Handling & Fingerspelling Fallback"""

    def test_devanagari_fingerspelling_decomposition(self):
        chars = decompose_devanagari_word("कॉलेज")
        self.assertIn("क", chars)
        self.assertIn("ल", chars)
        self.assertIn("ज", chars)

    def test_fingerspelling_fallback_sequence(self):
        seq = get_fingerspelling_sequence("कॉलेज")
        self.assertTrue(len(seq) >= 3)
        self.assertTrue(all(item['is_fallback'] for item in seq))
        self.assertEqual(seq[0]['char'], 'क')

    def test_unknown_word_logging(self):
        res, unk = handle_unknown_word("अज्ञातशब्द")
        self.assertEqual(unk, "अज्ञातशब्द")
        self.assertTrue(UnknownWordLog.objects.filter(word="अज्ञातशब्द").exists())


class AnimationResolverTests(TestCase):
    """Test Suite 10: Animation Asset Resolution & Fallback"""

    def test_animation_resolution(self):
        anim = get_animation("SIGN_HELLO", "animations/greetings/hello.mp4")
        self.assertEqual(anim['sign_id'], "SIGN_HELLO")
        self.assertIn("hello.mp4", anim['animation_url'])


class ApiAndEndToEndPipelineTests(TestCase):
    """Test Suites 11 & 12: End-to-End API Translation, Empty Input & Edge Cases"""

    def setUp(self):
        self.client = Client()
        SignVocabulary.objects.create(
            sign_id="SIGN_HELLO",
            marathi_term="नमस्कार",
            english_gloss="hello",
            category="greetings",
            sign_type="lexical",
            animation_asset="animations/greetings/hello.mp4"
        )
        SignVocabulary.objects.create(
            sign_id="SIGN_WATER",
            marathi_term="पाणी",
            english_gloss="water",
            category="objects",
            sign_type="lexical",
            animation_asset="animations/objects/water.mp4"
        )
        EnglishMarathiMapping.objects.create(
            english_term="hello",
            marathi_term="नमस्कार"
        )
        EnglishMarathiMapping.objects.create(
            english_term="water",
            marathi_term="पाणी"
        )

    def test_marathi_text_api_translation(self):
        url = reverse('translator:api_translate')
        response = self.client.post(
            url,
            {'text': 'नमस्कार पाणी', 'language': 'mr'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['sign_sequence']), 2)
        self.assertEqual(data['sign_sequence'][0]['sign_id'], 'SIGN_HELLO')
        self.assertEqual(data['sign_sequence'][1]['sign_id'], 'SIGN_WATER')

    def test_english_text_api_translation(self):
        url = reverse('translator:api_translate')
        response = self.client.post(
            url,
            {'text': 'hello water', 'language': 'en'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['sign_sequence']), 2)
        self.assertEqual(data['sign_sequence'][0]['sign_id'], 'SIGN_HELLO')

    def test_empty_input_handling(self):
        url = reverse('translator:api_translate')
        response = self.client.post(
            url,
            {'text': '   ', 'language': 'mr'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_translation_history_recording(self):
        process_translation("नमस्कार", language="mr", log_history=True)
        self.assertTrue(TranslationHistory.objects.filter(input_text="नमस्कार").exists())
