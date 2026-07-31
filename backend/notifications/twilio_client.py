"""
Twilio WhatsApp Client Module for Pharmacy Product Expiry Alert System.

Supports Twilio WhatsApp Sandbox dispatches using twilio.rest.Client.
"""

import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception


def normalize_phone(phone: str) -> str:
    """
    Ensures phone number is in E.164 format (leading '+' followed by digits only).
    Example: '15551234567' or '+1 (555) 123-4567' -> '+15551234567'
    """
    if not phone:
        return ""
    cleaned = str(phone).replace('whatsapp:', '').strip()
    digits_only = re.sub(r'\D', '', cleaned)
    if not digits_only:
        return ""
    return f"+{digits_only}"


def send_whatsapp_message(to: str, text: str) -> tuple[bool, str | None]:
    """
    Sends a WhatsApp message via Twilio WhatsApp Sandbox / REST API.

    :param to: Target recipient phone number (e.g. "+15551234567")
    :param text: Message body content
    :return: Tuple of (success: bool, error: str | None)
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', '+14155238886')

    recipient_e164 = normalize_phone(to)
    if not recipient_e164:
        err_msg = "Invalid or empty phone number provided for WhatsApp dispatch."
        logger.warning(f"[TWILIO WHATSAPP] {err_msg}")
        return False, err_msg

    if not account_sid or not auth_token:
        err_msg = "TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN is not configured in settings."
        logger.warning(f"[TWILIO WHATSAPP FALLBACK] To: {recipient_e164} | Text: {text[:60]}... | Reason: {err_msg}")
        return False, err_msg

    if not TWILIO_AVAILABLE:
        err_msg = "Twilio Python package is not installed."
        logger.error(f"[TWILIO WHATSAPP] {err_msg}")
        return False, err_msg

    # Clean from number
    from_e164 = normalize_phone(whatsapp_from)
    from_whatsapp = f"whatsapp:{from_e164}"
    to_whatsapp = f"whatsapp:{recipient_e164}"

    try:
        client = TwilioClient(account_sid, auth_token)
        message = client.messages.create(
            from_=from_whatsapp,
            to=to_whatsapp,
            body=text
        )
        logger.info(f"[TWILIO WHATSAPP SENT] SID: {message.sid} | To: {recipient_e164}")
        return True, None
    except TwilioRestException as exc:
        err_msg = f"Twilio API Error {exc.code}: {exc.msg}"
        logger.error(f"[TWILIO WHATSAPP FAILED] To: {recipient_e164} | Error: {err_msg}")
        return False, err_msg
    except Exception as exc:
        err_msg = f"Unexpected exception during Twilio dispatch: {str(exc)}"
        logger.error(f"[TWILIO WHATSAPP EXCEPTION] To: {recipient_e164} | Error: {err_msg}")
        return False, err_msg
