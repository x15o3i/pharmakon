from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet, AlertActionViewSet, NotificationLogViewSet, whatsapp_webhook_view
from webhooks.twilio_webhook import twilio_whatsapp_webhook

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'actions', AlertActionViewSet, basename='action')
router.register(r'logs', NotificationLogViewSet, basename='log')

urlpatterns = [
    path('whatsapp/webhook/', whatsapp_webhook_view, name='whatsapp-webhook'),
    path('twilio/whatsapp-webhook/', twilio_whatsapp_webhook, name='twilio-whatsapp-webhook'),
    path('', include(router.urls)),
]
