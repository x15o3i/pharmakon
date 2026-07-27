from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from accounts.models import User
from inventory.models import DrugCategory, Drug
from inventory.services import run_abc_ved_classification


class InventoryEngineTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@test.com',
            full_name='Test Admin',
            role=User.Role.ADMIN,
            password='Password123!'
        )
        self.cat_critical = DrugCategory.objects.create(name='Critical/High-Value', alert_lead_time_days=90)
        self.cat_standard = DrugCategory.objects.create(name='Standard', alert_lead_time_days=60)
        self.cat_fast = DrugCategory.objects.create(name='Fast-Moving', alert_lead_time_days=30)

    def test_total_value_calculation(self):
        drug = Drug.objects.create(
            name='Test Drug 1',
            batch_number='B01',
            expiry_date=date.today() + timedelta(days=100),
            quantity=50,
            unit_cost=Decimal('12.50'),
            category=self.cat_standard,
            barcode='1000000000001',
            created_by=self.admin
        )
        self.assertEqual(drug.total_value, Decimal('625.00'))

    def test_abc_ved_classification(self):
        # Create high value drug
        drug_high = Drug.objects.create(
            name='High Value Drug',
            batch_number='B02',
            expiry_date=date.today() + timedelta(days=100),
            quantity=10,
            unit_cost=Decimal('1000.00'), # Total 10,000
            criticality=Drug.Criticality.VITAL,
            category=self.cat_fast,
            barcode='1000000000002',
            created_by=self.admin
        )

        # Create low value drug
        drug_low = Drug.objects.create(
            name='Low Value Drug',
            batch_number='B03',
            expiry_date=date.today() + timedelta(days=100),
            quantity=10,
            unit_cost=Decimal('1.00'), # Total 10
            criticality=Drug.Criticality.DESIRABLE,
            category=self.cat_standard,
            barcode='1000000000003',
            created_by=self.admin
        )

        res = run_abc_ved_classification()
        drug_high.refresh_from_db()
        drug_low.refresh_from_db()

        self.assertEqual(drug_high.abc_tier, Drug.ABCTier.A)
        self.assertEqual(drug_high.category, self.cat_critical) # Vital -> Critical
        self.assertEqual(drug_low.abc_tier, Drug.ABCTier.C)
        self.assertEqual(drug_low.category, self.cat_fast) # Desirable & C-tier -> Fast-Moving
