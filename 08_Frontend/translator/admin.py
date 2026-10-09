"""
Django Admin interface for GestureConnect.
Provides management for SignVocabulary, EnglishMarathiMapping,
TranslationHistory, and UnknownWordLog.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import SignVocabulary, EnglishMarathiMapping, TranslationHistory, UnknownWordLog


@admin.register(SignVocabulary)
class SignVocabularyAdmin(admin.ModelAdmin):
    list_display = (
        'sign_id',
        'marathi_term',
        'english_gloss',
        'category',
        'sign_type',
        'is_active',
        'animation_status',
        'updated_at'
    )
    list_filter = ('category', 'sign_type', 'is_active')
    search_fields = ('sign_id', 'marathi_term', 'english_gloss')
    ordering = ('category', 'marathi_term')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Identification', {
            'fields': ('sign_id', 'marathi_term', 'english_gloss', 'category', 'sign_type', 'is_active')
        }),
        ('Animation Asset', {
            'fields': ('animation_asset',)
        }),
        ('Linguistic & Biomechanical Metadata', {
            'fields': ('synonyms', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def animation_status(self, obj):
        from .services.animation import get_animation
        res = get_animation(obj.sign_id, obj.animation_asset)
        if res.get('asset_exists'):
            return format_html('<span style="color: green; font-weight: bold;">● Active MP4</span>')
        return format_html('<span style="color: orange;">○ Placeholder</span>')
    animation_status.short_description = "Asset"


@admin.register(EnglishMarathiMapping)
class EnglishMarathiMappingAdmin(admin.ModelAdmin):
    list_display = ('english_term', 'marathi_term', 'is_phrase', 'created_at')
    list_filter = ('is_phrase',)
    search_fields = ('english_term', 'marathi_term')
    ordering = ('english_term',)


@admin.register(TranslationHistory)
class TranslationHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'input_mode_badge',
        'input_language',
        'short_input',
        'short_normalized',
        'sequence_length',
        'fallback_count',
        'processing_time_ms',
        'created_at'
    )
    list_filter = ('input_language', 'input_mode', 'created_at')
    search_fields = ('input_text', 'normalized_text')
    readonly_fields = (
        'input_text',
        'input_language',
        'input_mode',
        'normalized_text',
        'generated_sign_sequence',
        'fallback_words',
        'processing_time_ms',
        'created_at'
    )

    def short_input(self, obj):
        return obj.input_text[:35] + ('...' if len(obj.input_text) > 35 else '')
    short_input.short_description = "Input Text"

    def short_normalized(self, obj):
        return obj.normalized_text[:35] + ('...' if len(obj.normalized_text) > 35 else '')
    short_normalized.short_description = "Normalized Text"

    def sequence_length(self, obj):
        return len(obj.generated_sign_sequence or [])
    sequence_length.short_description = "Signs"

    def fallback_count(self, obj):
        count = len(obj.fallback_words or [])
        if count > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return "0"
    fallback_count.short_description = "Fingerspelled"

    def input_mode_badge(self, obj):
        if obj.input_mode == 'speech':
            return format_html('<span style="background: #e1f5fe; color: #0288d1; padding: 2px 6px; border-radius: 4px; font-weight: bold;">🎤 Speech</span>')
        return format_html('<span style="background: #f5f5f5; color: #616161; padding: 2px 6px; border-radius: 4px;">⌨ Text</span>')
    input_mode_badge.short_description = "Mode"


@admin.register(UnknownWordLog)
class UnknownWordLogAdmin(admin.ModelAdmin):
    list_display = ('word', 'language', 'occurrence_count', 'first_seen', 'last_seen')
    list_filter = ('language',)
    search_fields = ('word',)
    ordering = ('-occurrence_count', '-last_seen')
    readonly_fields = ('first_seen', 'last_seen')
