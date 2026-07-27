from django.contrib import admin
from .models import Alert, AlertAction, NotificationLog


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('drug', 'severity', 'triggered_at', 'escalation_level', 'escalated_to', 'acknowledged', 'acknowledged_by')
    list_filter = ('severity', 'acknowledged', 'escalation_level')
    search_fields = ('drug__name', 'drug__batch_number')


@admin.register(AlertAction)
class AlertActionAdmin(admin.ModelAdmin):
    list_display = ('alert', 'action_type', 'performed_by', 'performed_at')
    list_filter = ('action_type',)
    search_fields = ('alert__drug__name', 'reason')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('channel', 'recipient', 'sent_at', 'status')
    list_filter = ('channel', 'status')
    search_fields = ('recipient',)
