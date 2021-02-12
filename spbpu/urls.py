from spbpu import views

urlpatterns = [
    path('api/v1/registration', views.registration),
    path('api/v1/login', views.login),
    path('api/v1/model/demo/create', views.demo_create),
    path('api/v1/model/auto/create', views.auto_create),
    path('api/v1/question', views.question),
    path('api/v1/model/result/<int:id>', views.get_model),
    path('api/v1/models', views.get_models),
    path('api/v1/model/demo/park/create', views.demo_park_create),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)