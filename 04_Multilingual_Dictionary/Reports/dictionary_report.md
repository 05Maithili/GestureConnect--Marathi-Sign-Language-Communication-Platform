# Multilingual Dictionary & Sign ID Architecture Report

## Overview
This report details the stable Multilingual Dictionary built for the **GestureConnect / Translation Studio** project.
The architecture maps English and Marathi words to a stable `Sign ID`, linking lexical input directly to the optimized INCLUDE dataset and MediaPipe outputs.

## Statistics
- **Total Unique Signs**: 262
- **Total Videos Linked**: 1241
- **Sign ID Range**: SIGN_0001 - SIGN_0262
- **English Mappings Created**: 284 unique English terms
- **Marathi Mappings Created**: 255 unique Marathi terms
- **Synonym Mappings Created**: 23 synonyms across English terms
- **Out-of-Vocabulary (OOV) Records**: 0

## Validation Summary
- **Errors**: 0
- **Warnings**: 0
- **MediaPipe References**: All links to Raw and Normalized landmarks validated successfully against the current metadata.

## File Architecture
- `Vocabulary/sign_vocabulary.json/csv`: The master mapping of all canonical words, Sign IDs, dataset folder names, and MediaPipe links.
- `Mappings/sign_id_mapping.json`: Ensures stability of Sign IDs when rebuilding.
- `English/english_to_sign.json`: English terms -> [Sign IDs] mapping (supporting polysemy).
- `Marathi/marathi_to_sign.json`: Marathi terms -> [Sign IDs] mapping (supporting polysemy).
- `Synonyms/english_synonyms.json`: List of synonyms added for robust NLP mapping.
- `Unknown_Words/oov_words.json`: Words not found in the dataset, handled systematically for future fallback rendering.
- `Validation/validation_report.json`: Automated checks output for debugging.

## Next Steps
The dictionary now serves as a robust intermediate semantic layer between user input (English/Marathi) and motion retrieval (AI avatar driving).
