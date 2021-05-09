from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from snod.views import *

urlpatterns = [
    path('model/snod/<int:id>', SnodSearchView.as_view(), name='snod_search'),
    path('model/snod/result/<int:id>', SnodDetailView.as_view(), name='snod_result'),

    path('model/origianl_snod/<int:id>', OriginalSnodSearchView.as_view(), name='snod_original_search'),
    path('model/origianl_snod/result/<int:id>', OriginalSnodDetailView.as_view(), name='snod_original_result'),
    path('model/origianl_snod/<int:id>/settings', SettingsOriginalSnodCreateView.as_view(), name='snod_original_settings_create'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)