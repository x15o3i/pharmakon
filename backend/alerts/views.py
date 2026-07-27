from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Alert, AlertAction, NotificationLog
from .serializers import AlertSerializer, AlertActionSerializer, NotificationLogSerializer
from .tasks import check_expiring_drugs, escalate_unacknowledged_alerts
from inventory.models import Drug
from accounts.permissions import IsPharmacistRole, IsSupervisorRole


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.all().select_related('drug', 'acknowledged_by', 'escalated_to').prefetch_related('actions').order_by('-triggered_at')
    serializer_class = AlertSerializer
    permission_classes = [IsPharmacistRole]

    def get_queryset(self):
        qs = super().get_queryset()
        severity = self.request.query_params.get('severity')
        acknowledged = self.request.query_params.get('acknowledged')

        if severity:
            qs = qs.filter(severity=severity)
        if acknowledged is not None:
            is_ack = acknowledged.lower() in ['true', '1']
            qs = qs.filter(acknowledged=is_ack)
        return qs

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        open_alerts = Alert.objects.filter(acknowledged=False).select_related('drug', 'drug__category')
        red_count = open_alerts.filter(severity=Alert.Severity.RED).count()
        amber_count = open_alerts.filter(severity=Alert.Severity.AMBER).count()
        
        # Calculate dynamic Green count without bloating database table with Green alert rows
        total_active_drugs = Drug.objects.filter(quantity__gt=0).count()
        drugs_with_open_alerts = open_alerts.values_list('drug_id', flat=True).distinct().count()
        green_count = max(0, total_active_drugs - drugs_with_open_alerts)

        urgent_alerts = AlertSerializer(open_alerts.order_by('-triggered_at')[:50], many=True).data

        return Response({
            'red_count': red_count,
            'amber_count': amber_count,
            'green_count': green_count,
            'total_active_drugs': total_active_drugs,
            'urgent_alerts': urgent_alerts,
        })

    @action(detail=False, methods=['post'], permission_classes=[IsSupervisorRole])
    def trigger_check(self, request):
        result = check_expiring_drugs()
        return Response({'message': result})

    @action(detail=False, methods=['post'], permission_classes=[IsSupervisorRole])
    def trigger_escalation(self, request):
        result = escalate_unacknowledged_alerts()
        return Response({'message': result})


class AlertActionViewSet(viewsets.ModelViewSet):
    queryset = AlertAction.objects.all().select_related('alert', 'performed_by').order_by('-performed_at')
    serializer_class = AlertActionSerializer
    permission_classes = [IsPharmacistRole]

    def perform_create(self, serializer):
        action_instance = serializer.save(performed_by=self.request.user)
        alert = action_instance.alert
        alert.acknowledged = True
        alert.acknowledged_by = self.request.user
        alert.acknowledged_at = timezone.now()
        alert.save()


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificationLog.objects.all().order_by('-sent_at')
    serializer_class = NotificationLogSerializer
    permission_classes = [IsSupervisorRole]
