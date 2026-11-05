from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # OpenAPI 3 Schema & Interactive Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Application APIs
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.academics.urls')),
    path('api/', include('apps.facilities.urls')),
    path('api/', include('apps.faculty.urls')),
    path('api/', include('apps.imports.urls')),
    path('api/', include('apps.timetable.urls')),
    path('api/', include('apps.scheduler.urls')),
]
