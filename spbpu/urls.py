from spbpu import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from spbpu.views import SettingsPACOMCreateView, ParkDetailView

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login', views.login_view, name='login'),
    path('registration', views.registration_view, name='registration'),
    path('logout', views.logout_view, name='logout'),
    path('upload', views.upload_view, name='upload'),
    path('download', views.download_view, name='download'),
    path('models', views.models_view, name='models'),
    path('models/<int:id>', views.models_view_id, name='models_id'),
    path('model/create', views.create_model_view, name='create_model'),
    path('model/snod/<int:id>', views.SnodSearchView.as_view(), name='snod_search'),
    path('model/snod/result/<int:id>', views.snod_result, name='snod_result'),

    path('model/park/<int:id>', views.ParkSearchView.as_view(), name='park_search'),
    path('model/park/result/<int:pk>', ParkDetailView.as_view(), name='park_result'),
    path('model/park/<int:id>/settings', SettingsPACOMCreateView.as_view(), name='pacom_settings_create')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)