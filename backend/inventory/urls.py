from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DrugCategoryViewSet, DrugViewSet

router = DefaultRouter()
router.register(r'categories', DrugCategoryViewSet, basename='category')
router.register(r'drugs', DrugViewSet, basename='drug')

urlpatterns = [
    path('', include(router.urls)),
]
