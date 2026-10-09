"""
REST API Serializers for GestureConnect.
"""

from rest_framework import serializers
from .models import SignVocabulary, EnglishMarathiMapping, TranslationHistory, UnknownWordLog


class SignVocabularySerializer(serializers.ModelSerializer):
    animation_url = serializers.SerializerMethodField()

    class Meta:
        model = SignVocabulary
        fields = [
            'id',
            'sign_id',
            'marathi_term',
            'english_gloss',
            'category',
            'sign_type',
            'animation_asset',
            'animation_url',
            'metadata',
            'synonyms',
            'is_active',
            'created_at',
            'updated_at'
        ]

    def get_animation_url(self, obj):
        from .services.animation import get_animation
        res = get_animation(obj.sign_id, obj.animation_asset, obj.metadata)
        return res.get('animation_url')


class EnglishMarathiMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnglishMarathiMapping
        fields = ['id', 'english_term', 'marathi_term', 'is_phrase', 'notes', 'created_at']


class TranslationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationHistory
        fields = [
            'id',
            'input_text',
            'input_language',
            'input_mode',
            'normalized_text',
            'generated_sign_sequence',
            'fallback_words',
            'processing_time_ms',
            'created_at'
        ]


class TranslationRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, allow_blank=False, max_length=2000)
    language = serializers.ChoiceField(choices=['mr', 'en', 'auto'], default='auto', required=False)
    input_mode = serializers.ChoiceField(choices=['text', 'speech'], default='text', required=False)


class SpeechToTextRequestSerializer(serializers.Serializer):
    audio = serializers.FileField(required=False)
    language = serializers.ChoiceField(choices=['mr', 'en'], default='mr', required=False)
    transcript = serializers.CharField(required=False, allow_blank=True)


class UnknownWordLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnknownWordLog
        fields = ['id', 'word', 'language', 'occurrence_count', 'first_seen', 'last_seen']
