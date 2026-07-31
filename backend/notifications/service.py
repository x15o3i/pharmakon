"""
Notification Service Module for Pharmacy Product Expiry Alert System.
Handles multi-channel notification dispatches across WhatsApp (via Twilio / Evolution API), SMS, and Email.
"""

from datetime import date
import logging
from django.conf import settings
from alerts.models import NotificationLog
from alerts.notifications import send_alert_email, send_alert_sms
from .twilio_client import send_whatsapp_message
from .evolution_client import send_whatsapp_text

logger = logging.getLogger(__name__)


def dispatch_whatsapp_alert(alert, drug, recipients):
    """
    Dispatches a WhatsApp expiry alert message to specified recipients using Twilio WhatsApp Sandbox (or Evolution API).

    :param alert: Alert model instance
    :param drug: Drug model instance
    :param recipients: User model instance, list/queryset of User objects, or phone string
    :return: List of created NotificationLog instances
    """
    if not isinstance(recipients, (list, tuple)):
        try:
            recipients = list(recipients)
        except TypeError:
            recipients = [recipients]

    logs = []
    today = date.today()
    days_remaining = (drug.expiry_date - today).days if (drug and drug.expiry_date) else 0
    severity_label = "URGENT" if (alert and (getattr(alert, 'severity', 'amber') == 'red' or days_remaining <= 7)) else "Approaching Expiry"
    alert_id_val = alert.id if (alert and hasattr(alert, 'id')) else 0
    ack_code = f"ACK-{alert_id_val}"

    message_text = (
        f"🚨 *[PHARMACY ALERT - {severity_label}]*\n\n"
        f"• *Drug Trade Name*: {drug.name if drug else 'N/A'}\n"
        f"• *Batch Number*: {drug.batch_number if drug else 'N/A'}\n"
        f"• *Expiry Date*: {drug.expiry_date if drug else 'N/A'} ({days_remaining} days remaining)\n"
        f"• *Lead Time*: {drug.category.alert_lead_time_days if (drug and drug.category) else 30} days\n\n"
        f"Please log in to resolve or reply *{ack_code}* to acknowledge this alert."
    )

    for recipient in recipients:
        target_phone = getattr(recipient, 'phone', None) or str(recipient)
        if not target_phone or target_phone == 'None':
            continue

        # Try Twilio WhatsApp first if configured; fallback to Evolution API
        twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        if twilio_sid:
            success, error = send_whatsapp_message(target_phone, message_text)
        else:
            success, error = send_whatsapp_text(target_phone, message_text)

        status = NotificationLog.Status.SENT if success else NotificationLog.Status.FAILED

        log_entry = NotificationLog.objects.create(
            alert=alert,
            channel=NotificationLog.Channel.WHATSAPP,
            recipient=target_phone,
            status=status,
            error=error,
            ack_code=ack_code
        )
        logs.append(log_entry)

    return logs


def dispatch_notification(alert, drug, recipients, channel="whatsapp"):
    """
    Unified multi-channel dispatcher supporting 'whatsapp', 'email', and 'sms'.
    """
    if channel == "whatsapp":
        return dispatch_whatsapp_alert(alert, drug, recipients)
    elif channel == "email":
        if not isinstance(recipients, (list, tuple)):
            try:
                recipients = list(recipients)
            except TypeError:
                recipients = [recipients]
        logs = []
        today = date.today()
        days_remaining = (drug.expiry_date - today).days if (drug and drug.expiry_date) else 0
        severity_label = "URGENT" if (alert and getattr(alert, 'severity', 'amber') == 'red') else "Approaching Expiry"
        alert_id_val = alert.id if (alert and hasattr(alert, 'id')) else 0
        ack_code = f"ACK-{alert_id_val}"

        subject = f"[{severity_label.upper()}] Expiry Alert: {drug.name if drug else 'Drug'}"
        email_body = (
            f"ATTENTION: {drug.name if drug else 'Drug'} (Batch: {drug.batch_number if drug else 'N/A'}) "
            f"expires on {drug.expiry_date if drug else 'N/A'} ({days_remaining} days remaining).\n"
            f"Please log in to take action or reply {ack_code}."
        )
        for recipient in recipients:
            target_email = getattr(recipient, 'email', None) or str(recipient)
            if target_email and target_email != 'None':
                log_entry = send_alert_email(target_email, subject, email_body, alert=alert)
                logs.append(log_entry)
        return logs

    elif channel == "sms":
        if not isinstance(recipients, (list, tuple)):
            try:
                recipients = list(recipients)
            except TypeError:
                recipients = [recipients]
        logs = []
        today = date.today()
        days_remaining = (drug.expiry_date - today).days if (drug and drug.expiry_date) else 0
        severity_label = "URGENT" if (alert and getattr(alert, 'severity', 'amber') == 'red') else "Approaching Expiry"
        alert_id_val = alert.id if (alert and hasattr(alert, 'id')) else 0
        ack_code = f"ACK-{alert_id_val}"

        sms_body = (
            f"[{severity_label}] {drug.name if drug else 'Drug'} (Batch: {drug.batch_number if drug else 'N/A'}) "
            f"expires in {days_remaining} days ({drug.expiry_date if drug else 'N/A'}). Reply {ack_code} to ACK."
        )
        for recipient in recipients:
            target_phone = getattr(recipient, 'phone', None) or str(recipient)
            if target_phone and target_phone != 'None':
                log_entry = send_alert_sms(target_phone, sms_body, alert=alert)
                logs.append(log_entry)
        return logs

    return []
