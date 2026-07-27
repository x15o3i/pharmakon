from django.contrib import admin
from .models import DrugCategory, Drug


@admin.register(DrugCategory)
class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'alert_lead_time_days', 'updated_by', 'updated_at')
    search_fields = ('name',)


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch_number', 'expiry_date', 'quantity', 'unit_cost', 'total_value', 'criticality', 'abc_tier', 'category', 'barcode')
    list_filter = ('criticality', 'abc_tier', 'category', 'expiry_date')
    search_fields = ('name', 'generic_name', 'batch_number', 'barcode')
    readonly_fields = ('total_value', 'abc_tier')
