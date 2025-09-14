# careconnect/urls.py
from django.contrib import admin
from django.urls import path, include
from users.views import landpage_view, mental_health_test  
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),  
    path('', landpage_view, name='landpage'),
    path('meditation/', include('meditation.urls')),
    path('games/', include('games.urls', namespace='games')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)