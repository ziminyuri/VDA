from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('spbpu.urls')),
    path('', include('model.urls')),
    path('', include('pacom.urls')),
    path('', include('snod.urls')),
]
