"""
URL configuration for GestureConnect project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('translator.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    
    # Serve optimized dataset with Range support
    if hasattr(settings, 'OPTIMIZED_DATASET_URL') and hasattr(settings, 'OPTIMIZED_DATASET_ROOT'):
        from translator.views import stream_video
        from django.urls import re_path
        
        # Remove trailing slash from URL for regex mapping
        base_url = settings.OPTIMIZED_DATASET_URL.strip('/')
        urlpatterns += [
            re_path(r'^' + base_url + r'/(?P<path>.*)$', stream_video),
        ]
