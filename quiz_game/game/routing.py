from django.urls import re_path
from . import consumer

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<room_name>\w+)/$', consumer.QuizConsumer.as_asgi()),
    re_path(r'ws/game/', consumer.QuizConsumer.as_asgi()),
]
