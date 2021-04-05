from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from spbpu import views
from spbpu.views import (DownloadCSVView, ParkDetailView,
                         SettingsPACOMCreateView, UploadView)

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login', views.LoginView.as_view(), name='login'),
    path('registration', views.RegistrationView.as_view(), name='registration'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('upload', UploadView.as_view(), name='upload'),
    path('download', DownloadCSVView.as_view(), name='download'),
    path('models', views.ModelListCreateView.as_view(), name='models'),
    path('models/<int:id>', views.ModelView.as_view(), name='models_id'),
    path('model/create', views.ModelCreateView.as_view(), name='create_model'),
    path('model/snod/<int:id>', views.SnodSearchView.as_view(), name='snod_search'),
    path('model/snod/result/<int:id>', views.SnodDetailView.as_view(), name='snod_result'),
    path('model/demo/create', views.DemoModelCreateView.as_view(), name='demo_create'),

    path('model/park/<int:id>', views.ParkSearchView.as_view(), name='park_search'),
    path('model/park/result/<int:pk>', ParkDetailView.as_view(), name='park_result'),
    path('model/park/<int:id>/settings', SettingsPACOMCreateView.as_view(), name='pacom_settings_create'),

    path('model/origianl_snod/<int:id>', views.OriginalSnodSearchView.as_view(), name='snod_original_search'),
    path('model/origianl_snod/result/<int:id>', views.OriginalSnodDetailView.as_view(), name='snod_original_result'),

    path('statistics', views.StatisticsView.as_view(), name='statistics')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)