"""
Django Management Command: python manage.py test_twilio --phone="+15551234567"
Verifies Twilio WhatsApp Sandbox connection by sending a test alert message.
"""

from django.core.management.base import BaseCommand
from notifications.twilio_client import send_whatsapp_message, normalize_phone


class Command(BaseCommand):
    help = "Sends a test WhatsApp message via Twilio WhatsApp Sandbox."

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            default='+15551234567',
            help='Recipient phone number with country code (e.g. +2348146251103)'
        )
        parser.add_argument(
            '--message',
            type=str,
            default=None,
            help='Custom message string to transmit'
        )

    def handle(self, *args, **options):
        phone = options['phone']
        custom_msg = options['message']

        normalized = normalize_phone(phone)
        self.stdout.write(self.style.MIGRATE_HEADING("Testing Twilio WhatsApp Sandbox..."))
        self.stdout.write(f"Target Recipient: {phone} (Normalized: {normalized})")

        msg_body = custom_msg or (
            "🚨 [PHARMACY SYSTEM - TWILIO TEST ALERT]\n\n"
            "• Drug: Amoxicillin 500mg\n"
            "• Batch: TEST-BATCH-99\n"
            "• Status: TWILIO WHATSAPP SANDBOX VERIFIED\n\n"
            "Reply ACK-99 to test auto-acknowledgement."
        )

        success, error = send_whatsapp_message(phone, msg_body)

        if success:
            self.stdout.write(self.style.SUCCESS("[SUCCESS] Test WhatsApp message successfully sent via Twilio Sandbox!"))
        else:
            self.stdout.write(self.style.ERROR("[FAILURE] Failed to send WhatsApp message via Twilio Sandbox."))
            self.stdout.write(self.style.ERROR(f"Details: {error}"))
