from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from inventory.models import DrugCategory, Drug
from alerts.models import Alert, AlertAction, NotificationLog
from alerts.tasks import check_expiring_drugs, escalate_unacknowledged_alerts
from alerts.notifications import send_alert_email, send_alert_sms
from notifications.evolution_client import normalize_phone, send_whatsapp_text
from notifications.twilio_client import send_whatsapp_message, normalize_phone as twilio_normalize_phone
from notifications.service import dispatch_notification, dispatch_whatsapp_alert


class AlertSystemTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='admin@test.com', full_name='Admin', role=User.Role.ADMIN, password='Password123!')
        self.pharmacist = User.objects.create_user(email='pharm@test.com', full_name='Pharmacist', role=User.Role.PHARMACIST, password='Password123!', phone='+15551234567')
        self.supervisor = User.objects.create_user(email='super@test.com', full_name='Supervisor', role=User.Role.SUPERVISOR, password='Password123!', phone='+15559876543')

        self.cat_critical = DrugCategory.objects.create(name='Critical/High-Value', alert_lead_time_days=90)
        self.cat_standard = DrugCategory.objects.create(name='Standard', alert_lead_time_days=60)

        today = date.today()
        # Red Drug (<7 days)
        self.drug_red = Drug.objects.create(
            name='Red Drug', batch_number='R1', expiry_date=today + timedelta(days=3),
            quantity=10, unit_cost=50, category=self.cat_standard, barcode='9000000000001'
        )
        # Amber Drug (<= 60 days)
        self.drug_amber = Drug.objects.create(
            name='Amber Drug', batch_number='A1', expiry_date=today + timedelta(days=25),
            quantity=10, unit_cost=50, category=self.cat_standard, barcode='9000000000002'
        )
        # Green Drug (Safe stock > 60 days)
        self.drug_green = Drug.objects.create(
            name='Green Drug', batch_number='G1', expiry_date=today + timedelta(days=120),
            quantity=10, unit_cost=50, category=self.cat_standard, barcode='9000000000003'
        )

        self.client = APIClient()

    @patch('notifications.twilio_client.send_whatsapp_message', return_value=(True, None))
    @patch('notifications.evolution_client.send_whatsapp_text', return_value=(True, None))
    def test_alert_generation(self, mock_evo, mock_twilio):
        check_expiring_drugs()
        
        # Verify Red alert created
        red_alert = Alert.objects.filter(drug=self.drug_red).first()
        self.assertIsNotNone(red_alert)
        self.assertEqual(red_alert.severity, Alert.Severity.RED)

        # Verify Amber alert created
        amber_alert = Alert.objects.filter(drug=self.drug_amber).first()
        self.assertIsNotNone(amber_alert)
        self.assertEqual(amber_alert.severity, Alert.Severity.AMBER)

        # Verify Green drug has NO persisted alert record
        green_alert = Alert.objects.filter(drug=self.drug_green).first()
        self.assertIsNone(green_alert)

    @patch('notifications.twilio_client.send_whatsapp_message', return_value=(True, None))
    @patch('notifications.evolution_client.send_whatsapp_text', return_value=(True, None))
    def test_escalation_logic(self, mock_evo, mock_twilio):
        alert = Alert.objects.create(
            drug=self.drug_red,
            severity=Alert.Severity.RED
        )
        Alert.objects.filter(id=alert.id).update(triggered_at=timezone.now() - timedelta(hours=50))
        
        escalate_unacknowledged_alerts()
        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 1)
        self.assertIsNotNone(alert.last_escalated_at)

        # Throttling check
        escalate_unacknowledged_alerts()
        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 1)

        Alert.objects.filter(id=alert.id).update(last_escalated_at=timezone.now() - timedelta(hours=50))
        escalate_unacknowledged_alerts()
        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 2)
        self.assertEqual(alert.escalated_to, self.supervisor)

    def test_action_tracking_validation(self):
        alert = Alert.objects.create(drug=self.drug_red, severity=Alert.Severity.RED)
        self.client.force_authenticate(user=self.pharmacist)

        response = self.client.post('/api/alerts/actions/', {
            'alert': alert.id,
            'action_type': 'no_action_needed',
            'reason': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_ok = self.client.post('/api/alerts/actions/', {
            'alert': alert.id,
            'action_type': 'no_action_needed',
            'reason': 'Verified remaining batch is reserved for emergency.'
        })
        self.assertEqual(response_ok.status_code, status.HTTP_201_CREATED)
        alert.refresh_from_db()
        self.assertTrue(alert.acknowledged)
        self.assertEqual(alert.acknowledged_by, self.pharmacist)

    def test_evolution_normalize_phone(self):
        self.assertEqual(normalize_phone('+1 (555) 123-4567'), '15551234567')
        self.assertEqual(normalize_phone('whatsapp:+447700900077'), '447700900077')
        self.assertEqual(normalize_phone(''), '')
        self.assertEqual(twilio_normalize_phone('+1 (555) 123-4567'), '+15551234567')

    @patch('notifications.twilio_client.TwilioClient')
    def test_twilio_send_whatsapp_success(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_msg = MagicMock()
        mock_msg.sid = 'SM123456789'
        mock_instance.messages.create.return_value = mock_msg
        mock_client_cls.return_value = mock_instance

        with override_settings(
            TWILIO_ACCOUNT_SID='AC123456789',
            TWILIO_AUTH_TOKEN='secret-token',
            TWILIO_WHATSAPP_FROM='+14155238886'
        ):
            success, error = send_whatsapp_message('+15551234567', 'Test Message')
            self.assertTrue(success)
            self.assertIsNone(error)

    @patch('notifications.twilio_client.send_whatsapp_message', return_value=(True, None))
    def test_twilio_webhook_auto_ack(self, mock_send):
        alert = Alert.objects.create(drug=self.drug_red, severity=Alert.Severity.RED)
        ack_code = f"ACK-{alert.id}"

        res = self.client.post('/api/twilio/whatsapp-webhook/', {
            'From': 'whatsapp:+15551234567',
            'Body': f'I checked the stock {ack_code}'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        alert.refresh_from_db()
        self.assertTrue(alert.acknowledged)
        self.assertEqual(alert.acknowledged_by, self.pharmacist)

    def test_category_lead_time_minimum(self):
        self.client.force_authenticate(user=self.admin)
        res_invalid = self.client.post('/api/inventory/categories/', {
            'name': 'Invalid Short Lead Time Category',
            'alert_lead_time_days': 5
        })
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

        res_valid = self.client.post('/api/inventory/categories/', {
            'name': 'Valid Lead Time Category',
            'alert_lead_time_days': 8
        })
        self.assertEqual(res_valid.status_code, status.HTTP_201_CREATED)

    def test_pharmacist_cannot_modify_categories(self):
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/inventory/categories/', {
            'name': 'Unauthorized Category',
            'alert_lead_time_days': 45
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.post('/api/inventory/categories/', {
            'name': 'Admin Approved Category',
            'alert_lead_time_days': 45
        })
        self.assertEqual(res_admin.status_code, status.HTTP_201_CREATED)

    @patch('notifications.twilio_client.send_whatsapp_message', return_value=(True, None))
    @patch('notifications.evolution_client.send_whatsapp_text', return_value=(True, None))
    def test_role_hierarchy_access_to_pharmacist_endpoints(self, mock_evo, mock_twilio):
        self.client.force_authenticate(user=self.admin)
        res_admin_drug = self.client.post('/api/inventory/drugs/', {
            'name': 'Admin Created Drug',
            'batch_number': 'ADM01',
            'expiry_date': (date.today() + timedelta(days=100)).strftime('%Y-%m-%d'),
            'quantity': 20,
            'unit_cost': '15.00',
            'category': self.cat_standard.id,
            'barcode': '8000000000001'
        })
        self.assertEqual(res_admin_drug.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.supervisor)
        res_super_drug = self.client.post('/api/inventory/drugs/', {
            'name': 'Supervisor Created Drug',
            'batch_number': 'SUP01',
            'expiry_date': (date.today() + timedelta(days=100)).strftime('%Y-%m-%d'),
            'quantity': 20,
            'unit_cost': '15.00',
            'category': self.cat_standard.id,
            'barcode': '8000000000002'
        })
        self.assertEqual(res_super_drug.status_code, status.HTTP_201_CREATED)
