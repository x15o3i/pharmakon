"""
Evolution API Client Module for Pharmacy Product Expiry Alert System.

Why Evolution API is used instead of Twilio WhatsApp:
1. No Meta Message Templates: Sends arbitrary formatted plain-text messages instantly.
2. No Business Verification: Operates without Meta Business Manager verification or approval.
3. Open-Source & Self-Hosted: Perfect for demo, local, and community pharmacy deployments.
"""

import re
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """
    Normalizes input phone number to country code + number digits only.
    Evolution API expects raw digits only (e.g. '15551234567').
    Strips leading +, spaces, hyphens, and 'whatsapp:' prefix.
    """
    if not phone:
        return ""
    cleaned = str(phone).replace('whatsapp:', '').strip()
    digits_only = re.sub(r'\D', '', cleaned)
    return digits_only


def ensure_instance_exists(api_url: str, api_key: str, instance_name: str) -> bool:
    """
    Checks if the Evolution API instance exists; if not, attempts auto-creation.
    """
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    try:
        state_res = requests.get(f"{api_url}/instance/connectionState/{instance_name}", headers=headers, timeout=3)
        if state_res.status_code == 200:
            return True

        create_payload = {
            "instanceName": instance_name,
            "token": api_key,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        create_res = requests.post(f"{api_url}/instance/create", json=create_payload, headers=headers, timeout=5)
        logger.info(f"[EVOLUTION API CREATE INSTANCE] Status: {create_res.status_code} | Body: {create_res.text}")
        return create_res.status_code in [200, 201]
    except Exception as e:
        logger.warning(f"[EVOLUTION API INSTANCE CHECK] Exception: {str(e)}")
        return False


def send_whatsapp_text(to: str, text: str) -> tuple[bool, str | None]:
    """
    Sends a plain-text WhatsApp message via self-hosted Evolution API gateway.

    :param to: Target phone number (e.g. "+15551234567" or "whatsapp:+15551234567")
    :param text: Message body content to transmit
    :return: Tuple of (success: bool, error: str | None)
    """
    api_url = getattr(settings, 'EVOLUTION_API_URL', 'http://localhost:8080').rstrip('/')
    api_key = getattr(settings, 'EVOLUTION_API_KEY', '')
    instance_name = getattr(settings, 'EVOLUTION_INSTANCE_NAME', 'pharmacy-alerts')

    recipient_clean = normalize_phone(to)
    if not recipient_clean:
        err_msg = "Invalid or empty phone number provided for WhatsApp dispatch."
        logger.warning(f"[EVOLUTION API] {err_msg}")
        return False, err_msg

    if not api_key:
        err_msg = "EVOLUTION_API_KEY is not configured in settings/environment."
        logger.warning(f"[EVOLUTION API FALLBACK] To: {recipient_clean} | Text: {text[:60]}... | Reason: {err_msg}")
        return False, err_msg

    # Ensure instance exists
    ensure_instance_exists(api_url, api_key, instance_name)

    endpoint = f"{api_url}/message/sendText/{instance_name}"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "number": recipient_clean,
        "text": text
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)

        if 200 <= response.status_code < 300:
            logger.info(f"[EVOLUTION API SENT] To: {recipient_clean} | Status: {response.status_code}")
            return True, None
        else:
            err_msg = f"HTTP {response.status_code}: {response.text}"
            if "onWhatsApp" in response.text or "not connected" in response.text.lower():
                err_msg = f"WhatsApp instance '{instance_name}' is created, but needs to be connected by scanning the QR code at {api_url}/instance/connect/{instance_name} using your phone (WhatsApp -> Linked Devices -> Link a Device)."
            logger.error(f"[EVOLUTION API FAILED] To: {recipient_clean} | Error: {err_msg}")
            return False, err_msg
    except requests.exceptions.Timeout:
        err_msg = "Connection to Evolution API server timed out (10s)."
        logger.error(f"[EVOLUTION API TIMEOUT] To: {recipient_clean} | Error: {err_msg}")
        return False, err_msg
    except Exception as exc:
        err_msg = f"Network or connection exception: {str(exc)}"
        logger.error(f"[EVOLUTION API EXCEPTION] To: {recipient_clean} | Error: {str(exc)}")
        return False, err_msg
