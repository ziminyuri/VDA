from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from modification.views import *

urlpatterns = [
    path('model/snod/<int:id>/incomparable', PairsIncomparableListView.as_view(),
         name='pairs_incomparable'),
    path('model/snod/<int:id>/modification/delete', ModificationModelDeleteView.as_view(),
         name='modification_model_delete'),
    path('model/snod/<int:id>/modification/create', ModificationCreateView.as_view(),
         name='pairs_incomparable_create'),
    path('model/snod/<int:id>/modification/modificate', ModificationCriterionCreateView.as_view(),
         name='modification_criterion'),
    path('model/snod/<int:id>/modification/update', ModificationCriterionUpdateView.as_view(),
         name='modification_update'),
    path('model/snod/<int:id>/modification/delete', ModificationCriterionDeleteView.as_view(),
         name='modification_delete'),
    path('model/snod/<int:id>/modification/value', ModificationValueCreateView.as_view(),
         name='values_create'),
    path('model/snod/<int:id>/modification/search_snod', ModificationSnodSearchView.as_view(),
         name='modification_snod_search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)