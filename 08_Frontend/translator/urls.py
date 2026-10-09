"""
URL patterns for GestureConnect Translation Application.
"""

from django.urls import path
from . import views

app_name = 'translator'

urlpatterns = [
    # Frontend HTML Pages
    path('', views.home_view, name='home'),
    path('translate/', views.translate_view, name='translate'),
    path('vocabulary/', views.vocabulary_view, name='vocabulary'),
    path('history/', views.history_view, name='history'),
    path('evaluation/', views.evaluation_view, name='evaluation'),
    path('about/', views.about_view, name='about'),

    # REST API Endpoints
    path('api/translate/', views.ApiTranslateView.as_view(), name='api_translate'),
    path('api/speech-to-text/', views.ApiSpeechToTextView.as_view(), name='api_speech_to_text'),
    path('api/vocabulary/', views.ApiVocabularyListView.as_view(), name='api_vocabulary'),
    path('api/history/', views.ApiHistoryListView.as_view(), name='api_history'),
    path('api/evaluation/', views.ApiEvaluationMetricsView.as_view(), name='api_evaluation'),
]
