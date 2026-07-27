from decimal import Decimal
from django.db import transaction
from .models import Drug, DrugCategory


def run_abc_ved_classification():
    """
    Ranks all inventory drugs using standard ABC Pareto value analysis (70%/20%/10%)
    combined with VED criticality tags to auto-classify ABC tiers and suggest/update categories.
    """
    drugs = list(Drug.objects.all())
    if not drugs:
        return {"processed": 0, "categories_updated": 0}

    # Ensure total_value is computed for all items first
    for d in drugs:
        d.total_value = d.unit_cost * d.quantity
        d.save(update_fields=['total_value'])

    # Sort descending by total_value
    drugs.sort(key=lambda d: d.total_value, reverse=True)

    total_inventory_value = sum((d.total_value for d in drugs), Decimal('0.00'))

    # Default category mapping cache
    category_map = {cat.name: cat for cat in DrugCategory.objects.all()}
    critical_cat = category_map.get('Critical/High-Value')
    standard_cat = category_map.get('Standard')
    fast_moving_cat = category_map.get('Fast-Moving')

    cumulative_value = Decimal('0.00')
    updated_count = 0

    with transaction.atomic():
        for idx, drug in enumerate(drugs):
            prev_cum_pct = (cumulative_value / total_inventory_value * Decimal('100.0')) if total_inventory_value > Decimal('0.00') else Decimal('0.00')
            cumulative_value += drug.total_value

            # ABC Assignment based on starting cumulative percentage bracket:
            # Top ~70% value -> Tier A (First item always included in Tier A)
            # Next ~20% value (70%-90%) -> Tier B
            # Remaining ~10% value (90%-100%) -> Tier C
            if idx == 0 or prev_cum_pct < Decimal('70.0'):
                assigned_abc = Drug.ABCTier.A
            elif prev_cum_pct < Decimal('90.0'):
                assigned_abc = Drug.ABCTier.B
            else:
                assigned_abc = Drug.ABCTier.C

            drug.abc_tier = assigned_abc

            # VED + ABC Matrix suggestion:
            # Vital OR A-Tier -> Critical/High-Value (90 days)
            # Essential OR B-Tier -> Standard (60 days)
            # Desirable AND C-Tier -> Fast-Moving (30 days)
            if drug.criticality == Drug.Criticality.VITAL or assigned_abc == Drug.ABCTier.A:
                suggested_cat = critical_cat
            elif drug.criticality == Drug.Criticality.ESSENTIAL or assigned_abc == Drug.ABCTier.B:
                suggested_cat = standard_cat
            else:
                suggested_cat = fast_moving_cat

            if suggested_cat and drug.category != suggested_cat:
                drug.category = suggested_cat

            drug.save()
            updated_count += 1

    return {
        "processed": len(drugs),
        "total_inventory_value": float(total_inventory_value),
        "updated": updated_count
    }
