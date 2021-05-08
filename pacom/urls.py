from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from pacom.views import *

urlpatterns = [
    path('model/pacom/<int:id>', ParkSearchView.as_view(), name='park_search'),
    path('model/pacom/result/<int:pk>', ParkDetailView.as_view(), name='park_result'),
    path('model/pacom/<int:id>/settings', SettingsPACOMCreateView.as_view(), name='pacom_settings_create'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)