from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet, AlertActionViewSet, NotificationLogViewSet

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'actions', AlertActionViewSet, basename='action')
router.register(r'logs', NotificationLogViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
]
