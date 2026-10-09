"""
Django settings for GestureConnect project.
Bilingual Speech and Text to Marathi Sign Language Translation System.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-gestureconnect-academic-project-2026-key-change-in-prod'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,testserver').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'rest_framework',
    # GestureConnect core translation app
    'translator',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestureconnect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestureconnect.wsgi.application'
ASGI_APPLICATION = 'gestureconnect.asgi.application'

# Database
# Default is SQLite for development; fully compatible with MySQL in production
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
DB_NAME = os.getenv('DB_NAME', str(BASE_DIR / 'db.sqlite3'))

if 'sqlite3' in DB_ENGINE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (Blender-rendered animation MP4s)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django REST Framework configuration
# BrowsableAPIRenderer is intentionally disabled: the browser sends
# Accept: text/html which triggers the browsable renderer and returns HTML
# instead of JSON, breaking the JavaScript fetch() parsing.
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# GestureConnect specific file paths
DATA_DIR = BASE_DIR / 'data'
VOCABULARY_JSON_PATH = DATA_DIR / 'vocabulary.json'
ENGLISH_MARATHI_MAPPING_JSON_PATH = DATA_DIR / 'english_marathi_mapping.json'

# Phase 1 Config
PROJECT_ROOT = BASE_DIR.parent
OPTIMIZED_DATASET_ROOT = Path(os.getenv('GESTURECONNECT_VIDEO_ROOT', PROJECT_ROOT / '02_INCLUDE_Dataset_Web'))
MULTILINGUAL_DICTIONARY_ROOT = Path(os.getenv('GESTURECONNECT_DICT_ROOT', PROJECT_ROOT / '04_Multilingual_Dictionary'))
# NOTE: Must NOT start with /media/ — that prefix is already claimed by Django's
# MEDIA_URL handler, causing a URL collision that silently drops this route (404).
OPTIMIZED_DATASET_URL = '/dataset/'
