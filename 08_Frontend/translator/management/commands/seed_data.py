"""
Management command to populate database with core Sign Vocabulary,
English-Marathi lexical mappings, and create default admin user.
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from translator.models import SignVocabulary, EnglishMarathiMapping
from translator.services.english_marathi import reload_mapping_cache

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with Sign Vocabulary and English-Marathi mappings from data/ files"

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create default superuser admin:admin if not existing'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting database seeding for GestureConnect..."))

        # 1. Seed Sign Vocabulary
        vocab_path = getattr(settings, 'VOCABULARY_JSON_PATH', settings.BASE_DIR / 'data' / 'vocabulary.json')
        if Path(vocab_path).exists():
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)

            created_count = 0
            updated_count = 0

            for entry in vocab_data:
                obj, created = SignVocabulary.objects.update_or_create(
                    sign_id=entry['sign_id'],
                    defaults={
                        'marathi_term': entry['marathi_term'],
                        'english_gloss': entry['english_gloss'],
                        'category': entry.get('category', 'other'),
                        'sign_type': entry.get('sign_type', 'lexical'),
                        'animation_asset': entry.get('animation_asset', f"animations/{entry['sign_id'].lower()}.mp4"),
                        'synonyms': entry.get('synonyms', []),
                        'metadata': entry.get('metadata', {}),
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Successfully seeded Sign Vocabulary: {created_count} created, {updated_count} updated. Total: {SignVocabulary.objects.count()}"
            ))
        else:
            self.stdout.write(self.style.WARNING(f"Vocabulary JSON not found at {vocab_path}"))

        # 2. Seed English-Marathi Mappings
        em_path = getattr(settings, 'ENGLISH_MARATHI_MAPPING_JSON_PATH', settings.BASE_DIR / 'data' / 'english_marathi_mapping.json')
        if Path(em_path).exists():
            with open(em_path, 'r', encoding='utf-8') as f:
                em_data = json.load(f)

            em_created = 0
            for phrase, marathi in em_data.get('phrases', {}).items():
                _, created = EnglishMarathiMapping.objects.update_or_create(
                    english_term=phrase.lower().strip(),
                    defaults={'marathi_term': marathi.strip(), 'is_phrase': True}
                )
                if created:
                    em_created += 1

            for word, marathi in em_data.get('words', {}).items():
                _, created = EnglishMarathiMapping.objects.update_or_create(
                    english_term=word.lower().strip(),
                    defaults={'marathi_term': marathi.strip(), 'is_phrase': False}
                )
                if created:
                    em_created += 1

            self.stdout.write(self.style.SUCCESS(
                f"Successfully seeded English-Marathi Mappings. Total: {EnglishMarathiMapping.objects.count()}"
            ))
            reload_mapping_cache()
        else:
            self.stdout.write(self.style.WARNING(f"Mapping JSON not found at {em_path}"))

        # 3. Create default superuser if requested
        if options.get('create_admin'):
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@gestureconnect.org', 'admin123')
                self.stdout.write(self.style.SUCCESS("Created default superuser: admin / admin123"))
            else:
                self.stdout.write(self.style.NOTICE("Superuser 'admin' already exists."))
