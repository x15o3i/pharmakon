from django.core.management.base import BaseCommand
from inventory.services import run_abc_ved_classification


class Command(BaseCommand):
    help = 'Executes ABC/VED inventory classification and auto-suggests category lead times.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting ABC/VED classification engine...'))
        res = run_abc_ved_classification()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully classified {res['processed']} drugs. "
                f"Total inventory value: ${res.get('total_inventory_value', 0):,.2f}"
            )
        )
