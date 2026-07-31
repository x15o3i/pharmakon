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
from alerts.notifications import send_alert_email, send_alert_sms, send_alert_whatsapp
from notifications.evolution_client import normalize_phone, send_whatsapp_text
from notifications.service import dispatch_notification


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

    def test_alert_generation(self):
        check_expiring_drugs()
        
        # Verify Red alert created
        red_alert = Alert.objects.filter(drug=self.drug_red).first()
        self.assertIsNotNone(red_alert)
        self.assertEqual(red_alert.severity, Alert.Severity.RED)

        # Verify Amber alert created
        amber_alert = Alert.objects.filter(drug=self.drug_amber).first()
        self.assertIsNotNone(amber_alert)
        self.assertEqual(amber_alert.severity, Alert.Severity.AMBER)

        # Verify Green drug has NO persisted alert record (prevents bloat)
        green_alert = Alert.objects.filter(drug=self.drug_green).first()
        self.assertIsNone(green_alert)

    def test_escalation_logic(self):
        alert = Alert.objects.create(
            drug=self.drug_red,
            severity=Alert.Severity.RED
        )
        # Force triggered_at into the past for test (> 48h unacknowledged)
        Alert.objects.filter(id=alert.id).update(triggered_at=timezone.now() - timedelta(hours=50))
        
        # Trigger first escalation
        escalate_unacknowledged_alerts()
        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 1)
        self.assertIsNotNone(alert.last_escalated_at)

        # Immediately call task a second time -> Assert it does NOT re-escalate (throttling check)
        escalate_unacknowledged_alerts()
        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 1)

        # Update last_escalated_at to 50 hours ago -> Trigger second escalation -> Assigns supervisor
        Alert.objects.filter(id=alert.id).update(last_escalated_at=timezone.now() - timedelta(hours=50))
        escalate_unacknowledged_alerts()
        alert.refresh_from_db()
        self.assertEqual(alert.escalation_level, 2)
        self.assertEqual(alert.escalated_to, self.supervisor)

    def test_action_tracking_validation(self):
        alert = Alert.objects.create(drug=self.drug_red, severity=Alert.Severity.RED)
        self.client.force_authenticate(user=self.pharmacist)

        # Attempt 'no_action_needed' without reason -> Should fail server-side
        response = self.client.post('/api/alerts/actions/', {
            'alert': alert.id,
            'action_type': 'no_action_needed',
            'reason': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt 'no_action_needed' WITH reason -> Should succeed and acknowledge alert
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

    @patch('notifications.evolution_client.requests.post')
    def test_send_whatsapp_text_success(self, mock_post):
        mock_res = MagicMock()
        mock_res.status_code = 201
        mock_post.return_value = mock_res

        with override_settings(
            EVOLUTION_API_URL='http://localhost:8080',
            EVOLUTION_API_KEY='secret-key',
            EVOLUTION_INSTANCE_NAME='pharmacy-alerts'
        ):
            success, error = send_whatsapp_text('+15551234567', 'Test Message')
            self.assertTrue(success)
            self.assertIsNone(error)

            mock_post.assert_called_once()
            url, kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
            self.assertEqual(url, 'http://localhost:8080/message/sendText/pharmacy-alerts')
            self.assertEqual(kwargs['headers']['apikey'], 'secret-key')
            self.assertEqual(kwargs['json'], {'number': '15551234567', 'text': 'Test Message'})

    @patch('notifications.evolution_client.requests.post')
    def test_send_whatsapp_text_failure(self, mock_post):
        mock_res = MagicMock()
        mock_res.status_code = 500
        mock_res.text = 'Internal Server Error'
        mock_post.return_value = mock_res

        with override_settings(
            EVOLUTION_API_URL='http://localhost:8080',
            EVOLUTION_API_KEY='secret-key'
        ):
            success, error = send_whatsapp_text('+15551234567', 'Test Message')
            self.assertFalse(success)
            self.assertIn('HTTP 500', error)

    @patch('notifications.evolution_client.requests.post')
    def test_dispatch_notification_service(self, mock_post):
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_post.return_value = mock_res

        alert = Alert.objects.create(drug=self.drug_red, severity=Alert.Severity.RED)

        with override_settings(EVOLUTION_API_KEY='secret-key'):
            logs = dispatch_notification(alert, self.drug_red, [self.pharmacist], channel='whatsapp')
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].status, NotificationLog.Status.SENT)
            self.assertEqual(logs[0].channel, NotificationLog.Channel.WHATSAPP)
            self.assertTrue(logs[0].ack_code.startswith('ACK-'))

    @patch('notifications.evolution_client.requests.post')
    def test_whatsapp_webhook_auto_ack(self, mock_post):
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_post.return_value = mock_res

        alert = Alert.objects.create(drug=self.drug_red, severity=Alert.Severity.RED)
        ack_code = f"ACK-{alert.id}"

        # Post incoming reply payload to webhook endpoint
        webhook_payload = {
            "data": {
                "key": {"remoteJid": "15551234567@s.whatsapp.net"},
                "message": {"conversation": f"I have checked the stock. {ack_code}"}
            }
        }

        res = self.client.post('/api/whatsapp/webhook/', webhook_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['status'], 'success')

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

    def test_role_hierarchy_access_to_pharmacist_endpoints(self):
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
