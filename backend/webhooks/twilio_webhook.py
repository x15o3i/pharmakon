"""
Twilio WhatsApp Webhook Module for Pharmacy Product Expiry Alert System.

Receives incoming WhatsApp message callbacks from Twilio Sandbox.
Parses ACK-{alert_id} messages and automatically marks matching alerts as acknowledged.
"""

import re
import logging
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model

from alerts.models import Alert
from notifications.twilio_client import send_whatsapp_message, normalize_phone

logger = logging.getLogger(__name__)
User = get_user_model()

try:
    from twilio.request_validator import RequestValidator
    TWILIO_VALIDATOR_AVAILABLE = True
except ImportError:
    TWILIO_VALIDATOR_AVAILABLE = False


@csrf_exempt
def twilio_whatsapp_webhook(request):
    """
    HTTP POST Webhook handler for incoming Twilio WhatsApp messages.
    URL: /api/twilio/whatsapp-webhook/
    """
    if request.method != 'POST':
        return HttpResponse("Method Not Allowed", status=405)

    # Optional Signature Validation
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    twilio_signature = request.headers.get('X-Twilio-Signature', '')
    if TWILIO_VALIDATOR_AVAILABLE and auth_token and twilio_signature and not settings.DEBUG:
        validator = RequestValidator(auth_token)
        url = request.build_absolute_uri()
        post_data = request.POST.dict()
        if not validator.validate(url, post_data, twilio_signature):
            logger.warning("[TWILIO WEBHOOK] Invalid X-Twilio-Signature header received.")
            return HttpResponse("Unauthorized Signature", status=403)

    from_number = request.POST.get('From', '').strip()
    body = request.POST.get('Body', '').strip()

    logger.info(f"[TWILIO WEBHOOK RECEIVED] From: {from_number} | Body: '{body}'")

    if not from_number or not body:
        return HttpResponse("<Response></Response>", content_type="text/xml")

    raw_phone = from_number.replace('whatsapp:', '')
    clean_phone = normalize_phone(raw_phone)

    # Check for ACK code pattern (e.g. "ACK-12" or "ACK-1234")
    match = re.search(r'ACK-?(\d+)', body, re.IGNORECASE)
    if match:
        alert_id = match.group(1)
        try:
            alert = Alert.objects.select_related('drug').get(pk=alert_id)
            
            # Identify acknowledging staff user by phone number match
            staff_user = None
            if clean_phone:
                digits_only = clean_phone.replace('+', '')
                staff_user = User.objects.filter(phone__icontains=digits_only).first()

            alert.acknowledged = True
            alert.acknowledged_at = timezone.now()
            if staff_user:
                alert.acknowledged_by = staff_user
            alert.save()

            drug_name = alert.drug.name if alert.drug else "Drug"
            ack_user_name = staff_user.get_full_name() or staff_user.email if staff_user else "Staff Member"

            reply_text = (
                f"✅ *[ALERT ACKNOWLEDGED]*\n\n"
                f"Alert #{alert.id} for *{drug_name}* has been marked as ACKNOWLEDGED by {ack_user_name}."
            )

            # Send WhatsApp confirmation reply back via Twilio
            send_whatsapp_message(raw_phone, reply_text)

            logger.info(f"[TWILIO WEBHOOK SUCCESS] Alert #{alert.id} acknowledged by {ack_user_name} ({clean_phone}).")

            twiml_response = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message>{reply_text}</Message></Response>"
            return HttpResponse(twiml_response, content_type="text/xml")

        except Alert.DoesNotExist:
            err_text = f"❌ Alert #{alert_id} not found in the pharmacy system."
            logger.warning(f"[TWILIO WEBHOOK] {err_text}")
            send_whatsapp_message(raw_phone, err_text)
            twiml_response = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message>{err_text}</Message></Response>"
            return HttpResponse(twiml_response, content_type="text/xml")

    twiml_default = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response><Message>Thank you for your message. Reply with ACK-{alert_id} to acknowledge an active pharmacy alert.</Message></Response>"
    )
    return HttpResponse(twiml_default, content_type="text/xml")
