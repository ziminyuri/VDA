from django.contrib import admin
from django.urls import include, path
import debug_toolbar

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
    path('', include('model.urls')),
    path('', include('pacom.urls')),
    path('', include('snod.urls')),

]
