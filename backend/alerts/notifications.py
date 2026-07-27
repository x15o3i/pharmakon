import logging
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client
from .models import NotificationLog

logger = logging.getLogger(__name__)


def send_alert_email(recipient_email, subject, message_body, alert=None):
    """
    Dispatches email via Django's email backend. Safe fallback to console/log.
    """
    try:
        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        status = NotificationLog.Status.SENT
        logger.info(f"EMAIL SENT to {recipient_email}: {subject}")
    except Exception as e:
        status = NotificationLog.Status.FAILED
        logger.warning(f"EMAIL FALLBACK/FAILURE for {recipient_email}: {str(e)}")

    log_entry = NotificationLog.objects.create(
        alert=alert,
        channel=NotificationLog.Channel.EMAIL,
        recipient=recipient_email,
        status=status
    )
    return log_entry


def send_alert_sms(recipient_phone, message_body, alert=None):
    """
    Dispatches SMS via Twilio API if credentials exist; safely logs fallback otherwise.
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

    if account_sid and auth_token and from_number and recipient_phone:
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=message_body,
                from_=from_number,
                to=recipient_phone
            )
            status = NotificationLog.Status.SENT
            logger.info(f"TWILIO SMS SENT to {recipient_phone}: SID {message.sid}")
        except Exception as e:
            status = NotificationLog.Status.FAILED
            logger.warning(f"TWILIO SMS FAILED for {recipient_phone}: {str(e)}")
    else:
        status = NotificationLog.Status.SENT
        logger.info(f"[DEV FALLBACK SMS LOG] To: {recipient_phone} | Msg: {message_body}")

    log_entry = NotificationLog.objects.create(
        alert=alert,
        channel=NotificationLog.Channel.SMS,
        recipient=recipient_phone or 'Dev-Console',
        status=status
    )
    return log_entry


# NOTE ON WHATSAPP IMPLEMENTATION:
# 1. Twilio Sandbox Mode: Recipients must text "join <sandbox-keyword>" to the sandbox number and rejoin every 3 days.
# 2. Production Deployment: Requires a verified WhatsApp Business Account (WABA) and pre-approved Meta message templates.
def send_alert_whatsapp(recipient_phone, message_body, alert=None, template_name=None, template_vars=None):
    """
    Dispatches WhatsApp messages via Twilio API.
    In dev/sandbox mode, structures message according to sandbox template requirements.
    Falls back cleanly to console log if credentials or TWILIO_WHATSAPP_FROM are absent.
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', '')

    if from_number and not from_number.startswith('whatsapp:'):
        from_number = f"whatsapp:{from_number}"

    target_phone = recipient_phone
    if target_phone and not target_phone.startswith('whatsapp:'):
        target_phone = f"whatsapp:{recipient_phone}"

    # Sandbox / Template Formatting
    if template_vars and isinstance(template_vars, dict):
        formatted_msg = f"Your appointment is coming up on {template_vars.get('date')} at {template_vars.get('time')}"
    else:
        formatted_msg = f"📱 *[PHARMACY ALERT]*\n\n{message_body}"

    if account_sid and auth_token and from_number and recipient_phone:
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=formatted_msg,
                from_=from_number,
                to=target_phone
            )
            status = NotificationLog.Status.SENT
            logger.info(f"TWILIO WHATSAPP SENT to {target_phone}: SID {message.sid}")
        except Exception as e:
            status = NotificationLog.Status.FAILED
            logger.warning(f"TWILIO WHATSAPP FAILED for {target_phone}: {str(e)}")
    else:
        status = NotificationLog.Status.SENT
        logger.info(f"[DEV FALLBACK WHATSAPP LOG] To: {target_phone} | Msg: {formatted_msg}")

    log_entry = NotificationLog.objects.create(
        alert=alert,
        channel=NotificationLog.Channel.WHATSAPP,
        recipient=recipient_phone or 'Dev-Console',
        status=status
    )
    return log_entry
