from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Q
from celery import shared_task
from inventory.models import Drug
from accounts.models import User
from .models import Alert
from notifications.service import dispatch_notification, dispatch_whatsapp_alert


@shared_task
def check_expiring_drugs():
    """
    Daily scheduled task.
    Checks drugs expiring within category lead times.
    Persists RED (<7 days or expired) and AMBER (within lead time) alerts.
    Dispatches WhatsApp notifications via Twilio Sandbox / Notification Service.
    """
    today = date.today()
    drugs = Drug.objects.select_related('category').filter(quantity__gt=0)
    alerts_created = 0

    for drug in drugs:
        days_remaining = (drug.expiry_date - today).days
        lead_time = drug.category.alert_lead_time_days if drug.category else 30

        # Check if alert condition is met (Red or Amber)
        if days_remaining <= lead_time:
            severity = Alert.Severity.RED if days_remaining <= 7 else Alert.Severity.AMBER

            # Prevent duplicate unacknowledged alerts for the same drug
            existing_open = Alert.objects.filter(drug=drug, acknowledged=False).first()
            if not existing_open:
                alert = Alert.objects.create(
                    drug=drug,
                    severity=severity,
                    channels_used=['email', 'sms', 'whatsapp']
                )

                # Dispatch initial notifications to Pharmacists and Admins
                recipients = User.objects.filter(is_active=True, role__in=[User.Role.PHARMACIST, User.Role.ADMIN])
                if recipients.exists():
                    dispatch_whatsapp_alert(alert, drug, recipients)
                    dispatch_notification(alert, drug, recipients, channel="email")
                    dispatch_notification(alert, drug, recipients, channel="sms")

                alerts_created += 1

    return f"Expiry check completed. {alerts_created} alerts generated."


@shared_task
def escalate_unacknowledged_alerts():
    """
    Periodic task.
    Escalates alerts that remain unacknowledged 48+ hours after creation or last escalation.
    Dispatches WhatsApp notifications to Supervisors.
    """
    cutoff_time = timezone.now() - timedelta(hours=48)

    unacknowledged = Alert.objects.filter(acknowledged=False).filter(
        Q(last_escalated_at__isnull=True, triggered_at__lte=cutoff_time) |
        Q(last_escalated_at__lte=cutoff_time)
    )
    escalated_count = 0

    supervisor = User.objects.filter(is_active=True, role=User.Role.SUPERVISOR).first()

    for alert in unacknowledged:
        alert.escalation_level += 1
        alert.last_escalated_at = timezone.now()

        # Assign to supervisor if escalation level reaches 2+
        if alert.escalation_level >= 2 and supervisor and not alert.escalated_to:
            alert.escalated_to = supervisor

        alert.save()

        drug = alert.drug
        target_users = [supervisor] if alert.escalated_to else list(User.objects.filter(is_active=True, role=User.Role.ADMIN))
        if target_users:
            dispatch_whatsapp_alert(alert, drug, target_users)
            dispatch_notification(alert, drug, target_users, channel="email")
            dispatch_notification(alert, drug, target_users, channel="sms")

        escalated_count += 1

    return f"Escalation check completed. {escalated_count} alerts escalated."
