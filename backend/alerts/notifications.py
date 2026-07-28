import os
import logging
import requests
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


def send_alert_whatsapp(to, drug_name, batch_number, expiry_date, alert=None):
    """
    Dispatches WhatsApp template messages via Meta's WhatsApp Cloud API (Graph API).
    Falls back cleanly to stdout console log if credentials are missing.

    NOTE ON META WHATSAPP ACCESS TOKEN:
    In dev, WHATSAPP_ACCESS_TOKEN is a temporary token that expires after 24 hours and needs
    manual regeneration from the Meta App Dashboard; production should use a permanent token
    from a System User configured in Meta Business Manager.
    """
    access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '') or os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
    phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '') or os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
    api_version = getattr(settings, 'WHATSAPP_API_VERSION', '') or os.environ.get('WHATSAPP_API_VERSION', 'v21.0')
    template_name = getattr(settings, 'WHATSAPP_TEMPLATE_NAME', '') or os.environ.get('WHATSAPP_TEMPLATE_NAME', 'expiry_alert')
    template_lang = getattr(settings, 'WHATSAPP_TEMPLATE_LANGUAGE', '') or os.environ.get('WHATSAPP_TEMPLATE_LANGUAGE', 'en_US')

    # Format recipient phone in E.164 format without + or whatsapp: prefix
    recipient_clean = (to or '').replace('whatsapp:', '').lstrip('+').strip()

    if access_token and phone_number_id and recipient_clean:
        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_clean,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": template_lang},
                "components": [{
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(drug_name)},
                        {"type": "text", "text": str(batch_number)},
                        {"type": "text", "text": str(expiry_date)},
                    ]
                }]
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code >= 200 and response.status_code < 300:
                status = NotificationLog.Status.SENT
                logger.info(f"META WHATSAPP SENT to {recipient_clean}: Status {response.status_code}")
            else:
                status = NotificationLog.Status.FAILED
                logger.error(f"META WHATSAPP FAILED for {recipient_clean} [{response.status_code}]: {response.text}")
        except Exception as e:
            status = NotificationLog.Status.FAILED
            logger.error(f"META WHATSAPP EXCEPTION for {recipient_clean}: {str(e)}")
    else:
        status = NotificationLog.Status.SENT
        logger.info(f"[DEV FALLBACK WHATSAPP LOG] To: {to} | Drug: {drug_name} | Batch: {batch_number} | Exp: {expiry_date}")

    log_entry = NotificationLog.objects.create(
        alert=alert,
        channel=NotificationLog.Channel.WHATSAPP,
        recipient=to or 'Dev-Console',
        status=status
    )
    return log_entry
