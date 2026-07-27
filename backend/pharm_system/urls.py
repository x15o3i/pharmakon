from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def root_health_check(request):
    return JsonResponse({
        'status': 'online',
        'system': 'Pharmacy Product Expiry Alert System API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'accounts': '/api/accounts/',
            'inventory': '/api/inventory/',
            'alerts': '/api/alerts/'
        }
    })

urlpatterns = [
    path('', root_health_check, name='root-health-check'),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/alerts/', include('alerts.urls')),
]
