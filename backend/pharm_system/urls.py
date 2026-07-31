from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from alerts.views import whatsapp_webhook_view
from webhooks.twilio_webhook import twilio_whatsapp_webhook

def root_health_check(request):
    return JsonResponse({
        'status': 'online',
        'system': 'Pharmacy Product Expiry Alert System API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'accounts': '/api/accounts/',
            'inventory': '/api/inventory/',
            'alerts': '/api/alerts/',
            'whatsapp_webhook': '/api/whatsapp/webhook/',
            'twilio_whatsapp_webhook': '/api/twilio/whatsapp-webhook/'
        }
    })

urlpatterns = [
    path('', root_health_check, name='root-health-check'),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/whatsapp/webhook/', whatsapp_webhook_view, name='whatsapp-webhook-direct'),
    path('api/twilio/whatsapp-webhook/', twilio_whatsapp_webhook, name='twilio-whatsapp-webhook-direct'),
]
