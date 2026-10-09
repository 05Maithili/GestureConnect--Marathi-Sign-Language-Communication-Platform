from django.core.management.base import BaseCommand
from django.db import transaction
import json
import os
from translator.models import SignVocabulary

class Command(BaseCommand):
    help = 'Synchronizes the SignVocabulary model with the master JSON dictionary and dataset.'

    def handle(self, *args, **options):
        base_dir = r"D:\Colonel\final_year_project"
        vocab_path = os.path.join(base_dir, "04_Multilingual_Dictionary", "Vocabulary", "sign_vocabulary.json")
        marathi_mapping_path = os.path.join(base_dir, "04_Multilingual_Dictionary", "Marathi", "marathi_to_sign.json")
        from django.conf import settings
        dataset_optimized_path = str(settings.OPTIMIZED_DATASET_ROOT)

        self.stdout.write(f"Reading master vocabulary from {vocab_path}")
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                vocab_data = json.load(f)
        except Exception as e:
            self.stderr.write(f"Failed to read vocabulary: {e}")
            return

        self.stdout.write(f"Reading Marathi mappings from {marathi_mapping_path}")
        try:
            with open(marathi_mapping_path, "r", encoding="utf-8") as f:
                marathi_mapping = json.load(f)
        except Exception as e:
            self.stderr.write(f"Failed to read Marathi mapping: {e}")
            return

        # Invert Marathi mapping
        sign_id_to_marathi = {}
        for mr_term, sign_ids in marathi_mapping.items():
            for sid in sign_ids:
                if sid not in sign_id_to_marathi:
                    sign_id_to_marathi[sid] = []
                sign_id_to_marathi[sid].append(mr_term)

        # Get available dataset folders
        available_folders = set()
        if os.path.exists(dataset_optimized_path):
            available_folders = {
                d for d in os.listdir(dataset_optimized_path)
                if os.path.isdir(os.path.join(dataset_optimized_path, d))
            }

        prev_count = SignVocabulary.objects.count()
        self.stdout.write(f"Previous database vocabulary count: {prev_count}")

        inserted = 0
        updated = 0
        verified_english = 0
        verified_marathi = 0
        verified_dataset = 0
        needs_review = 0

        valid_categories = ['greetings', 'family', 'pronouns', 'numbers', 'time', 'verbs', 'questions', 'objects', 'fingerspelling', 'other']

        with transaction.atomic():
            # First, assume all existing signs are inactive, then reactivate them.
            # But wait, what if we just deactivate the ones not in the JSON?
            valid_sign_ids = [item['sign_id'] for item in vocab_data]
            
            # Deactivate old signs that are not in the JSON (e.g., SIGN_HELLO)
            old_signs = SignVocabulary.objects.exclude(sign_id__in=valid_sign_ids)
            old_count = old_signs.count()
            old_signs.update(is_active=False)

            for item in vocab_data:
                sign_id = item['sign_id']
                canonical_word = item['canonical_word']
                dataset_word = item.get('dataset_word', '')
                
                # Verify Dataset
                dataset_available = dataset_word in available_folders
                dataset_status = "Available" if dataset_available else "Missing"
                if dataset_available:
                    verified_dataset += 1
                
                # Determine Marathi term
                mr_terms = sign_id_to_marathi.get(sign_id, [])
                if mr_terms:
                    primary_marathi = mr_terms[0]
                    verified_marathi += 1
                else:
                    primary_marathi = "Unavailable (Needs Review)"
                    needs_review += 1
                    
                if canonical_word:
                    verified_english += 1

                # Gather synonyms
                synonyms = []
                for term in item.get('english_terms', []):
                    if term != canonical_word and term not in synonyms:
                        synonyms.append(term)
                for term in mr_terms[1:]:
                    if term not in synonyms:
                        synonyms.append(term)

                category = item.get('source_category', 'other')
                if category not in valid_categories:
                    category = 'other'

                # Update or create
                obj, created = SignVocabulary.objects.update_or_create(
                    sign_id=sign_id,
                    defaults={
                        'english_gloss': canonical_word,
                        'marathi_term': primary_marathi,
                        'category': category,
                        'sign_type': 'lexical',
                        'animation_asset': 'Unavailable (Phase 2)',
                        'synonyms': synonyms,
                        'is_active': dataset_available
                    }
                )
                
                # Safely update metadata without overwriting unrelated fields
                meta = obj.metadata if isinstance(obj.metadata, dict) else {}
                meta['dataset_word'] = dataset_word
                meta['dataset_status'] = dataset_status
                obj.metadata = meta
                obj.save(update_fields=['metadata'])

                if created:
                    inserted += 1
                else:
                    updated += 1

        new_count = SignVocabulary.objects.count()
        
        self.stdout.write(self.style.SUCCESS("Synchronization Complete!"))
        self.stdout.write(f"Previous count: {prev_count}")
        self.stdout.write(f"Actual canonical vocabulary count: {new_count}")
        self.stdout.write(f"Records inserted: {inserted}")
        self.stdout.write(f"Records updated: {updated}")
        self.stdout.write(f"Duplicate records avoided: (Managed safely via update_or_create by sign_id)")
        self.stdout.write(f"Old legacy records deactivated: {old_count}")
        self.stdout.write(f"Verified English glosses: {verified_english}")
        self.stdout.write(f"Verified Marathi terms: {verified_marathi}")
        self.stdout.write(f"Verified dataset folders/videos: {verified_dataset}")
        self.stdout.write(f"Entries needing manual review: {needs_review}")
