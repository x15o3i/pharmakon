from django.db import models
from django.conf import settings


class DrugCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    alert_lead_time_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True, default='')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_categories'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drug_categories'
        verbose_name_plural = 'Drug Categories'

    def __str__(self):
        return f"{self.name} ({self.alert_lead_time_days} days lead time)"


class Drug(models.Model):
    class Criticality(models.TextChoices):
        VITAL = 'vital', 'Vital'
        ESSENTIAL = 'essential', 'Essential'
        DESIRABLE = 'desirable', 'Desirable'

    class ABCTier(models.TextChoices):
        A = 'A', 'Tier A (High Value)'
        B = 'B', 'Tier B (Medium Value)'
        C = 'C', 'Tier C (Low Value)'

    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True, default='')
    batch_number = models.CharField(max_length=100)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(db_index=True)
    quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    criticality = models.CharField(
        max_length=20,
        choices=Criticality.choices,
        default=Criticality.ESSENTIAL
    )
    abc_tier = models.CharField(
        max_length=5,
        choices=ABCTier.choices,
        default=ABCTier.B
    )
    category = models.ForeignKey(
        DrugCategory,
        on_delete=models.PROTECT,
        related_name='drugs',
        db_index=True
    )
    barcode = models.CharField(max_length=100, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_drugs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drugs'
        ordering = ['expiry_date', 'name']

    def save(self, *args, **kwargs):
        # Calculate total_value cleanly in Python for DB compatibility
        self.total_value = self.unit_cost * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Batch: {self.batch_number}) - Exp: {self.expiry_date}"
