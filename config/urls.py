from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('', include('apps.core.urls')),
    path('', include('apps.grades.urls')),
    path('', include('apps.schedule.urls')),
    path('', include('apps.requests_app.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.assignments.urls')),
    path('', include('apps.analytics.urls')),
    path('', include('apps.chat.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)