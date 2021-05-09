from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from model.views import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login', LoginView.as_view(), name='login'),
    path('registration', RegistrationView.as_view(), name='registration'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('upload', UploadView.as_view(), name='upload'),
    path('download', DownloadCSVView.as_view(), name='download'),
    path('models', ModelListCreateView.as_view(), name='models'),
    path('models/<int:id>', ModelView.as_view(), name='models_id'),
    path('model/create', ModelCreateView.as_view(), name='create_model'),
    path('model/demo/create', DemoModelCreateView.as_view(), name='demo_create'),
    path('statistics', StatisticsView.as_view(), name='statistics')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)