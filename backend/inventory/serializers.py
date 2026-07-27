from rest_framework import serializers
from .models import DrugCategory, Drug
from accounts.serializers import UserSerializer
from .services import run_abc_ved_classification


class DrugCategorySerializer(serializers.ModelSerializer):
    updated_by_details = UserSerializer(source='updated_by', read_only=True)

    class Meta:
        model = DrugCategory
        fields = ('id', 'name', 'alert_lead_time_days', 'description', 'updated_by', 'updated_by_details', 'updated_at')
        read_only_fields = ('id', 'updated_at')


class DrugSerializer(serializers.ModelSerializer):
    category_details = DrugCategorySerializer(source='category', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model = Drug
        fields = (
            'id', 'name', 'generic_name', 'batch_number', 'manufacture_date',
            'expiry_date', 'quantity', 'unit_cost', 'total_value',
            'criticality', 'abc_tier', 'category', 'category_details',
            'barcode', 'created_by', 'created_by_details', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'total_value', 'abc_tier', 'created_at', 'updated_at')

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        drug = super().create(validated_data)
        run_abc_ved_classification()
        drug.refresh_from_db()
        return drug

    def update(self, instance, validated_data):
        drug = super().update(instance, validated_data)
        run_abc_ved_classification()
        drug.refresh_from_db()
        return drug
