"""
Database models for GestureConnect:
Bilingual Speech and Text to Marathi Sign Language Translation System.
"""

from django.db import models

class SignVocabulary(models.Model):
    """
    Main model storing canonical sign vocabulary and association
    with Blender-rendered 3D sign animation assets.
    """
    CATEGORY_CHOICES = [
        ('greetings', 'Greetings'),
        ('family', 'Family'),
        ('pronouns', 'Pronouns'),
        ('numbers', 'Numbers'),
        ('time', 'Time'),
        ('verbs', 'Common Verbs'),
        ('questions', 'Question Words'),
        ('objects', 'Everyday Objects'),
        ('fingerspelling', 'Alphabet / Fingerspelling'),
        ('other', 'Other'),
    ]

    SIGN_TYPE_CHOICES = [
        ('lexical', 'Lexical Sign'),
        ('phrase', 'Phrase Sign'),
        ('number', 'Numeric Sign'),
        ('fingerspell', 'Fingerspelling Character'),
    ]

    sign_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Canonical sign identifier (e.g. SIGN_HELLO, SIGN_WATER)"
    )
    marathi_term = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Primary Marathi term in Devanagari script"
    )
    english_gloss = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Standard English gloss / equivalent term"
    )
    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        default='other',
        db_index=True
    )
    sign_type = models.CharField(
        max_length=50,
        choices=SIGN_TYPE_CHOICES,
        default='lexical'
    )
    animation_asset = models.CharField(
        max_length=500,
        help_text="Relative path to MP4 animation inside MEDIA_ROOT (e.g. animations/greetings/hello.mp4)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Linguistic/biomechanical metadata (hand shape, motion, two_handed, description)"
    )
    synonyms = models.JSONField(
        default=list,
        blank=True,
        help_text="List of Marathi/English synonyms and alternate representations"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this sign is active in the translation engine"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sign Vocabulary Entry"
        verbose_name_plural = "Sign Vocabulary Entries"
        ordering = ['category', 'marathi_term']

    def __str__(self):
        return f"{self.sign_id} ({self.marathi_term} / {self.english_gloss})"


class EnglishMarathiMapping(models.Model):
    """
    Controlled lexical mapping between English terms/phrases and Marathi terms.
    """
    english_term = models.CharField(max_length=200, unique=True, db_index=True)
    marathi_term = models.CharField(max_length=200, db_index=True)
    is_phrase = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "English-Marathi Lexical Mapping"
        verbose_name_plural = "English-Marathi Lexical Mappings"
        ordering = ['english_term']

    def __str__(self):
        return f"{self.english_term} → {self.marathi_term}"


class TranslationHistory(models.Model):
    """
    Stores translation sessions for auditable history and evaluation metrics.
    """
    LANGUAGE_CHOICES = [
        ('mr', 'Marathi'),
        ('en', 'English'),
    ]

    MODE_CHOICES = [
        ('text', 'Text Input'),
        ('speech', 'Speech Input'),
    ]

    input_text = models.TextField(help_text="Original raw input text or speech transcript")
    input_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='mr')
    input_mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='text')
    normalized_text = models.TextField(help_text="Normalized text representation")
    generated_sign_sequence = models.JSONField(
        default=list,
        help_text="Ordered list of resolved canonical sign objects"
    )
    fallback_words = models.JSONField(
        default=list,
        blank=True,
        help_text="Words that underwent fingerspelling fallback"
    )
    processing_time_ms = models.FloatField(
        default=0.0,
        help_text="Total end-to-end processing time in milliseconds"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Translation History"
        verbose_name_plural = "Translation Histories"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_input_language_display()}|{self.input_mode}] {self.input_text[:40]} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class UnknownWordLog(models.Model):
    """
    Logs out-of-vocabulary words for administrative review and vocabulary expansion.
    """
    word = models.CharField(max_length=200, unique=True, db_index=True)
    language = models.CharField(max_length=10, default='mr')
    occurrence_count = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Unknown Word Log"
        verbose_name_plural = "Unknown Word Logs"
        ordering = ['-occurrence_count', '-last_seen']

    def __str__(self):
        return f"{self.word} (x{self.occurrence_count})"
