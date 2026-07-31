"""
Django Management Command: python manage.py test_evolution --phone="+15551234567"
Verifies Evolution API WhatsApp connection by sending a test alert message.
"""

from django.core.management.base import BaseCommand
from notifications.evolution_client import send_whatsapp_text, normalize_phone


class Command(BaseCommand):
    help = "Sends a test WhatsApp message via Evolution API to verify gateway connectivity."

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            default='+15551234567',
            help='Recipient phone number with country code (e.g. +15551234567 or 15551234567)'
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
        self.stdout.write(self.style.MIGRATE_HEADING("Testing Evolution API WhatsApp Gateway..."))
        self.stdout.write(f"Target Recipient: {phone} (Normalized: {normalized})")

        msg_body = custom_msg or (
            "[PHARMACY SYSTEM - TEST ALERT]\n\n"
            "• Drug: Amoxicillin 500mg\n"
            "• Batch: TEST-BATCH-99\n"
            "• Status: EVOLUTION API CONNECTION VERIFIED\n\n"
            "Reply ACK-TEST to test auto-acknowledgement."
        )

        success, error = send_whatsapp_text(phone, msg_body)

        if success:
            self.stdout.write(self.style.SUCCESS("[SUCCESS] Test WhatsApp message successfully sent via Evolution API!"))
        else:
            self.stdout.write(self.style.ERROR("[FAILURE] Failed to send WhatsApp message via Evolution API."))
            self.stdout.write(self.style.ERROR(f"Details: {error}"))
