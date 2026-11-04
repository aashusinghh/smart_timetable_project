from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/timetable/(?P<version_id>\d+)/$', consumers.TimetableConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]
