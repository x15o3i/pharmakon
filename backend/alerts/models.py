from django.db import models
from django.conf import settings
from inventory.models import Drug


class Alert(models.Model):
    class Severity(models.TextChoices):
        RED = 'red', 'Red (Urgent Expiry < 7 Days / Expired)'
        AMBER = 'amber', 'Amber (Within Lead Time Window)'

    drug = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    severity = models.CharField(max_length=10, choices=Severity.choices)
    triggered_at = models.DateTimeField(auto_now_add=True)
    last_escalated_at = models.DateTimeField(null=True, blank=True)
    channels_used = models.JSONField(default=list)
    escalation_level = models.PositiveIntegerField(default=0)
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_alerts'
    )
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'alerts'
        ordering = ['-triggered_at']

    def __str__(self):
        status = "ACKNOWLEDGED" if self.acknowledged else "OPEN"
        return f"[{self.get_severity_display()}] {self.drug.name} ({status})"


class AlertAction(models.Model):
    class ActionType(models.TextChoices):
        REMOVED_FROM_SHELF = 'removed_from_shelf', 'Removed from Shelf'
        DISCOUNTED = 'discounted', 'Discounted'
        RETURNED_TO_SUPPLIER = 'returned_to_supplier', 'Returned to Supplier'
        DISPOSED = 'disposed', 'Disposed'
        NO_ACTION_NEEDED = 'no_action_needed', 'No Action Needed'

    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    action_type = models.CharField(max_length=30, choices=ActionType.choices)
    reason = models.TextField(blank=True, default='')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='performed_actions'
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alert_actions'
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.get_action_type_display()} on {self.alert.drug.name} by {self.performed_by}"


class NotificationLog(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'
        WHATSAPP = 'whatsapp', 'WhatsApp'

    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        DELIVERED = 'delivered', 'Delivered'

    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    channel = models.CharField(max_length=15, choices=Channel.choices)
    recipient = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.SENT)

    class Meta:
        db_table = 'notification_log'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.channel.upper()} to {self.recipient} [{self.status}]"
