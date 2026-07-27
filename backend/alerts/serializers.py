from rest_framework import serializers
from .models import Alert, AlertAction, NotificationLog
from inventory.serializers import DrugSerializer
from accounts.serializers import UserSerializer


class AlertActionSerializer(serializers.ModelSerializer):
    performed_by_details = UserSerializer(source='performed_by', read_only=True)

    class Meta:
        model = AlertAction
        fields = ('id', 'alert', 'action_type', 'reason', 'performed_by', 'performed_by_details', 'performed_at')
        read_only_fields = ('id', 'performed_by', 'performed_at')

    def validate(self, attrs):
        action_type = attrs.get('action_type')
        reason = attrs.get('reason', '').strip()

        # Enforce server-side requirement that 'No Action Needed' MUST include a non-empty reason text
        if action_type == AlertAction.ActionType.NO_ACTION_NEEDED and not reason:
            raise serializers.ValidationError({
                "reason": "A mandatory explanation is required when selecting 'No Action Needed'."
            })
        return attrs


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = ('id', 'alert', 'channel', 'recipient', 'sent_at', 'status')


class AlertSerializer(serializers.ModelSerializer):
    drug_details = DrugSerializer(source='drug', read_only=True)
    acknowledged_by_details = UserSerializer(source='acknowledged_by', read_only=True)
    escalated_to_details = UserSerializer(source='escalated_to', read_only=True)
    actions = AlertActionSerializer(many=True, read_only=True)

    class Meta:
        model = Alert
        fields = (
            'id', 'drug', 'drug_details', 'severity', 'triggered_at', 'last_escalated_at',
            'channels_used', 'escalation_level', 'escalated_to', 'escalated_to_details',
            'acknowledged', 'acknowledged_by', 'acknowledged_by_details',
            'acknowledged_at', 'actions'
        )
        read_only_fields = ('id', 'triggered_at', 'last_escalated_at', 'acknowledged', 'acknowledged_by', 'acknowledged_at')
