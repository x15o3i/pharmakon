from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from inventory.models import DrugCategory, Drug
from alerts.models import Alert, AlertAction, NotificationLog
from alerts.tasks import check_expiring_drugs, escalate_unacknowledged_alerts
from alerts.notifications import send_alert_email, send_alert_sms, send_alert_whatsapp


class AlertSystemTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='admin@test.com', full_name='Admin', role=User.Role.ADMIN, password='Password123!')
        self.pharmacist = User.objects.create_user(email='pharm@test.com', full_name='Pharmacist', role=User.Role.PHARMACIST, password='Password123!')
        self.supervisor = User.objects.create_user(email='super@test.com', full_name='Supervisor', role=User.Role.SUPERVISOR, password='Password123!')

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
        self.assertIn('whatsapp', red_alert.channels_used)

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

    def test_notification_fallback_when_keys_missing(self):
        # Test SMS logging fallback when Twilio keys are blank
        log_sms = send_alert_sms('+15559990000', 'Test SMS Body', alert=None)
        self.assertEqual(log_sms.status, NotificationLog.Status.SENT)
        self.assertEqual(log_sms.channel, NotificationLog.Channel.SMS)

        # Test WhatsApp logging fallback when Twilio keys/from are blank
        log_wa = send_alert_whatsapp('+15559990000', 'Test WhatsApp Body', alert=None)
        self.assertEqual(log_wa.status, NotificationLog.Status.SENT)
        self.assertEqual(log_wa.channel, NotificationLog.Channel.WHATSAPP)

        # Test Email logging fallback when using console backend
        log_email = send_alert_email('test@pharmacy.com', 'Test Subject', 'Test Email Body', alert=None)
        self.assertEqual(log_email.status, NotificationLog.Status.SENT)
        self.assertEqual(log_email.channel, NotificationLog.Channel.EMAIL)

    def test_category_lead_time_minimum(self):
        self.client.force_authenticate(user=self.admin)
        # Attempt lead time <= 7 days -> Should return 400 Bad Request
        res_invalid = self.client.post('/api/inventory/categories/', {
            'name': 'Invalid Short Lead Time Category',
            'alert_lead_time_days': 5
        })
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt lead time >= 8 days -> Should return 201 Created
        res_valid = self.client.post('/api/inventory/categories/', {
            'name': 'Valid Lead Time Category',
            'alert_lead_time_days': 8
        })
        self.assertEqual(res_valid.status_code, status.HTTP_201_CREATED)

    def test_pharmacist_cannot_modify_categories(self):
        # Pharmacist attempting to modify drug categories -> Should be forbidden (403)
        self.client.force_authenticate(user=self.pharmacist)
        res = self.client.post('/api/inventory/categories/', {
            'name': 'Unauthorized Category',
            'alert_lead_time_days': 45
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Admin attempting to modify drug categories -> Should succeed (201)
        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.post('/api/inventory/categories/', {
            'name': 'Admin Approved Category',
            'alert_lead_time_days': 45
        })
        self.assertEqual(res_admin.status_code, status.HTTP_201_CREATED)

    def test_role_hierarchy_access_to_pharmacist_endpoints(self):
        # Test Admin POST to /api/inventory/drugs/ (Pharmacist endpoint)
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

        # Test Supervisor POST to /api/inventory/drugs/ (Pharmacist endpoint)
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

        # Test Admin POST to /api/alerts/actions/ (Pharmacist endpoint)
        alert1 = Alert.objects.create(drug=self.drug_red, severity=Alert.Severity.RED)
        self.client.force_authenticate(user=self.admin)
        res_admin_action = self.client.post('/api/alerts/actions/', {
            'alert': alert1.id,
            'action_type': 'removed_from_shelf',
            'reason': 'Admin action'
        })
        self.assertEqual(res_admin_action.status_code, status.HTTP_201_CREATED)

        # Test Supervisor POST to /api/alerts/actions/ (Pharmacist endpoint)
        alert2 = Alert.objects.create(drug=self.drug_amber, severity=Alert.Severity.AMBER)
        self.client.force_authenticate(user=self.supervisor)
        res_super_action = self.client.post('/api/alerts/actions/', {
            'alert': alert2.id,
            'action_type': 'discounted',
            'reason': 'Supervisor action'
        })
        self.assertEqual(res_super_action.status_code, status.HTTP_201_CREATED)
