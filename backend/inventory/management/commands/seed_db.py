from datetime import date, timedelta
from django.core.management.base import BaseCommand
from accounts.models import User
from inventory.models import DrugCategory, Drug
from inventory.services import run_abc_ved_classification
from alerts.tasks import check_expiring_drugs


class Command(BaseCommand):
    help = 'Seeds default categories, demo users (Admin, Pharmacist, Supervisor), and initial inventory.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding database with default categories, users, and inventory...'))

        # 1. Seed Categories
        cat_critical, _ = DrugCategory.objects.get_or_create(
            name='Critical/High-Value',
            defaults={'alert_lead_time_days': 90, 'description': 'Biologics, high-value specialty drugs, and vital emergency medicines.'}
        )
        cat_standard, _ = DrugCategory.objects.get_or_create(
            name='Standard',
            defaults={'alert_lead_time_days': 60, 'description': 'Essential prescription medications and standard formulations.'}
        )
        cat_fast, _ = DrugCategory.objects.get_or_create(
            name='Fast-Moving',
            defaults={'alert_lead_time_days': 30, 'description': 'Fast-moving generics and over-the-counter essentials.'}
        )

        # 2. Seed Users
        admin_user, _ = User.objects.get_or_create(
            email='admin@pharmacy.com',
            defaults={'full_name': 'Dr. Sarah Admin', 'role': User.Role.ADMIN, 'phone': '+15550199', 'is_staff': True, 'is_superuser': True}
        )
        if not admin_user.check_password('Password123!'):
            admin_user.set_password('Password123!')
            admin_user.save()

        pharmacist_user, _ = User.objects.get_or_create(
            email='pharmacist@pharmacy.com',
            defaults={'full_name': 'Alex Pharmacist', 'role': User.Role.PHARMACIST, 'phone': '+15550188'}
        )
        if not pharmacist_user.check_password('Password123!'):
            pharmacist_user.set_password('Password123!')
            pharmacist_user.save()

        supervisor_user, _ = User.objects.get_or_create(
            email='supervisor@pharmacy.com',
            defaults={'full_name': 'Chief Supervisor Jane', 'role': User.Role.SUPERVISOR, 'phone': '+15550177'}
        )
        if not supervisor_user.check_password('Password123!'):
            supervisor_user.set_password('Password123!')
            supervisor_user.save()

        # 3. Seed Sample Drugs
        today = date.today()

        sample_drugs = [
            {
                'name': 'Insulin Glargine SoloStar Pen',
                'generic_name': 'Insulin Glargine',
                'batch_number': 'INS-2026-X01',
                'manufacture_date': today - timedelta(days=200),
                'expiry_date': today + timedelta(days=4),  # RED Alert (<7 days)
                'quantity': 25,
                'unit_cost': 120.00,
                'criticality': Drug.Criticality.VITAL,
                'category': cat_critical,
                'barcode': '8901234567801',
            },
            {
                'name': 'Amoxicillin & Clavulanate 625mg',
                'generic_name': 'Amoxicillin',
                'batch_number': 'AMX-2026-B88',
                'manufacture_date': today - timedelta(days=150),
                'expiry_date': today + timedelta(days=20), # AMBER Alert (<= 30/60 days lead time)
                'quantity': 150,
                'unit_cost': 15.50,
                'criticality': Drug.Criticality.ESSENTIAL,
                'category': cat_fast,
                'barcode': '8901234567802',
            },
            {
                'name': 'Atorvastatin Calcium 20mg',
                'generic_name': 'Atorvastatin',
                'batch_number': 'ATV-2026-M44',
                'manufacture_date': today - timedelta(days=100),
                'expiry_date': today + timedelta(days=50), # AMBER Alert (<= 60 days lead time)
                'quantity': 300,
                'unit_cost': 8.75,
                'criticality': Drug.Criticality.ESSENTIAL,
                'category': cat_standard,
                'barcode': '8901234567803',
            },
            {
                'name': 'Metformin HCl 500mg XR',
                'generic_name': 'Metformin',
                'batch_number': 'MET-2026-Z12',
                'manufacture_date': today - timedelta(days=60),
                'expiry_date': today + timedelta(days=240), # GREEN (Safe stock)
                'quantity': 500,
                'unit_cost': 4.20,
                'criticality': Drug.Criticality.DESIRABLE,
                'category': cat_fast,
                'barcode': '8901234567804',
            },
            {
                'name': 'Pembrolizumab 100mg/4mL Vial',
                'generic_name': 'Pembrolizumab',
                'batch_number': 'PMB-2026-ONC',
                'manufacture_date': today - timedelta(days=80),
                'expiry_date': today + timedelta(days=75), # AMBER (<= 90 days lead time for Critical)
                'quantity': 10,
                'unit_cost': 4500.00,
                'criticality': Drug.Criticality.VITAL,
                'category': cat_critical,
                'barcode': '8901234567805',
            },
        ]

        for ddata in sample_drugs:
            Drug.objects.get_or_create(
                barcode=ddata['barcode'],
                defaults={**ddata, 'created_by': admin_user}
            )

        # 4. Run ABC/VED classification & Expiry Check
        run_abc_ved_classification()
        check_expiring_drugs()

        self.stdout.write(self.style.SUCCESS('Database successfully seeded with demo accounts & stock!'))
        self.stdout.write(self.style.WARNING('Demo Users created (Password: Password123!):'))
        self.stdout.write(' - Admin: admin@pharmacy.com')
        self.stdout.write(' - Pharmacist: pharmacist@pharmacy.com')
        self.stdout.write(' - Supervisor: supervisor@pharmacy.com')
