from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from administration.views import *

urlpatterns = [
    path('administration/statistics', StatisticsView.as_view(), name='statistics'),
    path('administration/users', UserListView.as_view(), name='users_list'),
    path('administration/settings', SettingsDetailView.as_view(), name='system_settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)