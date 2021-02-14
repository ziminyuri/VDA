from spbpu import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('upload', views.upload_view, name='upload'),
    path('download', views.download_view, name='download'),
    path('models', views.models_view, name='models'),
    path('model/create', views.create_model_view, name='create_model'),

    path('api/v1/registration', views.registration),
    path('api/v1/model/demo/create', views.demo_create),
    path('api/v1/model/auto/create', views.auto_create),
    path('api/v1/question', views.question),
    path('api/v1/model/result/<int:id>', views.get_model),
    path('api/v1/models', views.get_models),
    path('api/v1/model/demo/park/create', views.demo_park_create),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)