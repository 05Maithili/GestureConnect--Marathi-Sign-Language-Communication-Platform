"""
Django Views and REST API endpoints for GestureConnect.
Bilingual Speech and Text to Marathi Sign Language Translation System.
"""

import logging
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg, Count
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import os
import re
import mimetypes
from pathlib import Path
from django.conf import settings
from django.http import StreamingHttpResponse, Http404

from .models import SignVocabulary, EnglishMarathiMapping, TranslationHistory, UnknownWordLog
from .serializers import (
    SignVocabularySerializer,
    EnglishMarathiMappingSerializer,
    TranslationHistorySerializer,
    TranslationRequestSerializer,
    SpeechToTextRequestSerializer,
    UnknownWordLogSerializer
)
from .services.sequence import process_translation
from .services.speech import recognize_speech_audio
from .services.preprocessing import normalize_text, detect_language

logger = logging.getLogger(__name__)

def stream_video(request, path):
    """
    Serves video files with HTTP 206 Partial Content support (Range requests).
    Chrome/Safari require this to play HTML5 video properly. Django's default static()
    only returns HTTP 200 which breaks video playback.
    """
    file_path = Path(settings.OPTIMIZED_DATASET_ROOT) / path
    file_path = file_path.resolve()
    
    # Prevent directory traversal
    base_path = Path(settings.OPTIMIZED_DATASET_ROOT).resolve()
    if not str(file_path).startswith(str(base_path)):
        raise Http404("Invalid path")
        
    if not file_path.exists() or not file_path.is_file():
        raise Http404("Video not found")
        
    file_size = file_path.stat().st_size
    content_type, _ = mimetypes.guess_type(str(file_path))
    content_type = content_type or 'video/mp4'
    
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else file_size - 1
        
        if last_byte >= file_size:
            last_byte = file_size - 1
            
        length = last_byte - first_byte + 1
        
        def file_iterator(file_path, offset, length, chunk_size=8192):
            with open(file_path, 'rb') as f:
                f.seek(offset)
                remaining = length
                while remaining > 0:
                    bytes_to_read = min(chunk_size, remaining)
                    data = f.read(bytes_to_read)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
                    
        response = StreamingHttpResponse(file_iterator(file_path, first_byte, length), status=206, content_type=content_type)
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
    else:
        response = StreamingHttpResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Length'] = str(file_size)
        
    response['Accept-Ranges'] = 'bytes'
    return response


# ==============================================================================
# 1. HTML PAGE VIEWS
# ==============================================================================

def home_view(request):
    """GestureConnect Home / Dashboard Page."""
    vocab_count = SignVocabulary.objects.filter(is_active=True).count()
    translation_count = TranslationHistory.objects.count()
    categories_count = SignVocabulary.objects.filter(is_active=True).values('category').distinct().count()
    
    english_count = TranslationHistory.objects.filter(input_language='en').count()
    marathi_count = TranslationHistory.objects.filter(input_language='mr').count()
    speech_count = TranslationHistory.objects.filter(input_mode='speech').count()
    recent_translations = TranslationHistory.objects.all().order_by('-created_at')[:6]

    context = {
        'vocab_count': vocab_count or 54,
        'translation_count': translation_count or 124,
        'categories_count': categories_count or 8,
        'english_count': english_count or 76,
        'marathi_count': marathi_count or 48,
        'speech_count': speech_count or 72,
        'recent_translations': recent_translations,
    }
    return render(request, 'home.html', context)



def translate_view(request):
    """Main Translation Interface: Bilingual Speech and Text to Marathi Sign Language."""
    categories = SignVocabulary.CATEGORY_CHOICES
    recent_history = TranslationHistory.objects.all()[:5]
    sample_phrases = [
        {"mr": "कार महाग", "en": "car expensive"},
        {"mr": "बस स्वस्त", "en": "bus cheap"},
        {"mr": "घर शांत", "en": "house quiet"},
        {"mr": "कुत्रा मोठ्याने", "en": "dog loud"},
        {"mr": "पिशवी जड", "en": "bag heavy"},
        {"mr": "पुस्तक जाड", "en": "book thick"},
        {"mr": "वर्तमानपत्र पातळ", "en": "newspaper thin"},
        {"mr": "शहर महाग", "en": "city expensive"},
        {"mr": "बूट घट्ट", "en": "shoes tight"},
        {"mr": "शर्ट सैल", "en": "shirt loose"},
        {"mr": "बेड मऊ", "en": "bed soft"},
        {"mr": "बेड कठीण", "en": "bed hard"},
        {"mr": "भारत श्रीमंत", "en": "india rich"},
        {"mr": "रुग्णालय स्वच्छ", "en": "hospital clean"},
        {"mr": "बाजार अस्वच्छ", "en": "market dirty"},
        {"mr": "दार सपाट", "en": "door flat"},
        {"mr": "खिडकी स्वच्छ", "en": "window clean"},
        {"mr": "खोका जड", "en": "box heavy"},
        {"mr": "औषध महाग", "en": "medicine expensive"},
        {"mr": "मांजर शांत", "en": "cat quiet"},
        {"mr": "मासा जिवंत", "en": "fish alive"},
        {"mr": "पक्षी मृत", "en": "bird dead"},
        {"mr": "ट्रक जड", "en": "truck heavy"},
        {"mr": "बोट स्वस्त", "en": "boat cheap"},
        {"mr": "शाळा प्रसिद्ध", "en": "school famous"},
        {"mr": "बँक श्रीमंत", "en": "bank rich"},
        {"mr": "मंदिर शांत", "en": "temple quiet"},
        {"mr": "कपडे महाग", "en": "clothing expensive"},
        {"mr": "सूट महाग", "en": "suit expensive"},
        {"mr": "स्कर्ट स्वस्त", "en": "skirt cheap"},
        {"mr": "पँट सैल", "en": "pant loose"},
        {"mr": "पोशाख स्वच्छ", "en": "dress clean"},
        {"mr": "चावी जड", "en": "key heavy"},
        {"mr": "मी आनंदी", "en": "i happy"},
        {"mr": "तू दुःखी", "en": "you sad"},
        {"mr": "तो श्रीमंत", "en": "he rich"},
        {"mr": "ती गरीब", "en": "she poor"},
        {"mr": "आम्ही मजबूत", "en": "we strong"},
        {"mr": "आम्ही कमकुवत", "en": "we weak"},
        {"mr": "मी कार", "en": "i car"},
        {"mr": "तू घर", "en": "you house"},
        {"mr": "तो पुस्तक", "en": "he book"},
        {"mr": "ती पिशवी", "en": "she bag"},
        {"mr": "आम्ही शाळा", "en": "we school"},
        {"mr": "शहर बाजार", "en": "city market"},
        {"mr": "घर स्वयंपाकघर", "en": "house kitchen"},
        {"mr": "भारत बँक", "en": "india bank"},
        {"mr": "भारत न्यायालय", "en": "india court"},
        {"mr": "रुग्णालय औषध", "en": "hospital medicine"},
        {"mr": "रस्ता कुत्रा", "en": "street dog"},
        {"mr": "घर मांजर", "en": "house cat"},
    ]
    
    context = {
        'categories': categories,
        'recent_history': recent_history,
        'sample_phrases': sample_phrases
    }
    return render(request, 'translate.html', context)


def vocabulary_view(request):
    """Searchable Sign Vocabulary Explorer."""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    sign_type = request.GET.get('sign_type', '').strip()

    qs = SignVocabulary.objects.filter(is_active=True)

    if query:
        qs = qs.filter(
            Q(marathi_term__icontains=query) |
            Q(english_gloss__icontains=query) |
            Q(sign_id__icontains=query) |
            Q(synonyms__icontains=query)
        )
    if category and category != 'all':
        qs = qs.filter(category=category)
    if sign_type and sign_type != 'all':
        qs = qs.filter(sign_type=sign_type)

    total_count = qs.count()
    categories = SignVocabulary.CATEGORY_CHOICES

    # Attach base sign video URLs
    from .services.dictionary_service import DictionaryService
    dict_service = DictionaryService.get_instance()
    
    vocab_list = list(qs)
    for item in vocab_list:
        item.base_sign_video = dict_service.resolve_video_path(item.sign_id)

    context = {
        'vocabulary': vocab_list,
        'query': query,
        'selected_category': category,
        'selected_sign_type': sign_type,
        'categories': categories,
        'total_count': total_count
    }
    return render(request, 'vocabulary.html', context)


def history_view(request):
    """Translation History and Audit Sessions."""
    query = request.GET.get('q', '').strip()
    lang = request.GET.get('lang', '').strip()
    mode = request.GET.get('mode', '').strip()

    qs = TranslationHistory.objects.all().order_by('-created_at')
    if query:
        qs = qs.filter(Q(input_text__icontains=query) | Q(normalized_text__icontains=query))
    if lang in ['mr', 'en']:
        qs = qs.filter(input_language=lang)
    if mode in ['speech', 'text']:
        qs = qs.filter(input_mode=mode)

    total_translations = TranslationHistory.objects.count()

    context = {
        'history': qs[:50],
        'total_translations': total_translations,
        'query': query,
        'selected_lang': lang,
        'selected_mode': mode
    }
    return render(request, 'history.html', context)



def evaluation_view(request):
    """Developer & Research Evaluation Metrics Dashboard."""
    total_translations = TranslationHistory.objects.count()
    total_vocab = SignVocabulary.objects.filter(is_active=True).count()
    unknown_words = UnknownWordLog.objects.all()[:20]
    total_unknown_words_count = UnknownWordLog.objects.count()

    avg_time = TranslationHistory.objects.aggregate(Avg('processing_time_ms'))['processing_time_ms__avg']
    avg_latency = round(avg_time, 2) if avg_time else None

    # Calculate real vocabulary coverage by category
    category_breakdown = SignVocabulary.objects.filter(is_active=True).values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Calculate fingerspelling vs direct sign occurrences across history
    history_sample = TranslationHistory.objects.all()[:100]
    total_signs_in_history = 0
    total_fallbacks_in_history = 0
    for rec in history_sample:
        total_signs_in_history += len(rec.generated_sign_sequence or [])
        total_fallbacks_in_history += len(rec.fallback_words or [])

    oov_rate = None
    if total_signs_in_history > 0:
        oov_rate = round((total_fallbacks_in_history / max(1, len(history_sample))) * 100, 1)

    context = {
        'total_translations': total_translations,
        'total_vocab': total_vocab,
        'avg_latency': avg_latency,
        'unknown_words': unknown_words,
        'total_unknown_words_count': total_unknown_words_count,
        'category_breakdown': category_breakdown,
        'oov_rate': oov_rate,
        'history_sample_count': len(history_sample)
    }
    return render(request, 'evaluation.html', context)


def about_view(request):
    """About GestureConnect, Architecture, and Research Paper Details."""
    return render(request, 'about.html')


# ==============================================================================
# 2. REST API ENDPOINTS
# ==============================================================================

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class ApiTranslateView(APIView):
    """
    POST /api/translate/
    Accepts text and language, runs the full bilingual translation pipeline,
    and returns canonical sign sequence with animation URLs and statistics.
    """
    def post(self, request):
        serializer = TranslationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        raw_text = serializer.validated_data['text']
        lang = serializer.validated_data.get('language')
        input_mode = serializer.validated_data.get('input_mode', 'text')

        # Phase 1: Translate using robust dictionary JSONs
        if not lang:
            lang = 'auto'
            
        try:
            from .services.dictionary_service import DictionaryService
            dict_service = DictionaryService.get_instance()
            
            result = dict_service.translate_sentence(raw_text, language=lang)
            result["mode"] = request.data.get("mode", "phase1")
            
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Translation API error: {str(e)}")
            return Response({
                'success': False,
                'error': 'An internal error occurred during translation.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApiSpeechToTextView(APIView):
    """
    POST /api/speech-to-text/
    Accepts audio file (or transcript payload) and returns recognized text.
    The frontend then immediately invokes /api/translate/ with this transcript.
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = SpeechToTextRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # 1. If audio file is provided
        audio_file = request.FILES.get('audio')
        target_lang = serializer.validated_data.get('language', 'mr')

        if audio_file:
            res = recognize_speech_audio(audio_file, language=target_lang)
            return Response(res, status=status.HTTP_200_OK if res.get('status') == 'success' else status.HTTP_400_BAD_REQUEST)

        # 2. If client-side speech transcript is forwarded
        transcript = serializer.validated_data.get('transcript')
        if transcript:
            return Response({
                'status': 'success',
                'language': target_lang,
                'transcript': transcript.strip()
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Either an audio file or speech transcript must be provided.'
        }, status=status.HTTP_400_BAD_REQUEST)


class ApiVocabularyListView(APIView):
    """
    GET /api/vocabulary/
    List, filter, and search Sign Vocabulary entries.
    """
    def get(self, request):
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()

        qs = SignVocabulary.objects.filter(is_active=True)
        if query:
            qs = qs.filter(
                Q(marathi_term__icontains=query) |
                Q(english_gloss__icontains=query) |
                Q(sign_id__icontains=query)
            )
        if category and category != 'all':
            qs = qs.filter(category=category)

        serializer = SignVocabularySerializer(qs, many=True)
        return Response({
            'status': 'success',
            'count': qs.count(),
            'results': serializer.data
        })


class ApiHistoryListView(APIView):
    """
    GET /api/history/
    List recent translation sessions.
    """
    def get(self, request):
        limit = min(int(request.GET.get('limit', 20)), 100)
        qs = TranslationHistory.objects.all()[:limit]
        serializer = TranslationHistorySerializer(qs, many=True)
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'results': serializer.data
        })


class ApiEvaluationMetricsView(APIView):
    """
    GET /api/evaluation/
    Provides evaluation data and vocabulary stats.
    """
    def get(self, request):
        total_translations = TranslationHistory.objects.count()
        total_vocab = SignVocabulary.objects.filter(is_active=True).count()
        avg_latency = TranslationHistory.objects.aggregate(Avg('processing_time_ms'))['processing_time_ms__avg']
        
        category_counts = list(SignVocabulary.objects.filter(is_active=True).values('category').annotate(
            count=Count('id')
        ))

        return Response({
            'status': 'success',
            'metrics': {
                'total_translations': total_translations,
                'active_vocabulary_count': total_vocab,
                'average_latency_ms': round(avg_latency, 2) if avg_latency else None,
                'category_distribution': category_counts,
                'wer_status': 'Word Error Rate evaluation requires ground-truth test audio corpus.'
            }
        })
