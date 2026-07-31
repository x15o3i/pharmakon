import json
import re
from datetime import date
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Alert, AlertAction, NotificationLog
from .serializers import AlertSerializer, AlertActionSerializer, NotificationLogSerializer
from .tasks import check_expiring_drugs, escalate_unacknowledged_alerts
from inventory.models import Drug
from accounts.models import User
from accounts.permissions import IsPharmacistRole, IsSupervisorRole
from notifications.evolution_client import send_whatsapp_text, normalize_phone
from notifications.twilio_client import send_whatsapp_message
from django.conf import settings


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

    @action(detail=False, methods=['post'], permission_classes=[IsPharmacistRole])
    def send_whatsapp_summary(self, request):
        """
        On-demand action: Scans all expiring stock and dispatches a SINGLE
        consolidated WhatsApp summary report to active staff users.
        """
        # Run check first to make sure open alerts are fresh
        check_expiring_drugs()

        open_alerts = Alert.objects.filter(acknowledged=False).select_related('drug', 'drug__category').order_by('drug__expiry_date')
        today = date.today()

        if not open_alerts.exists():
            msg = "🏥 *[PHARMACY EXPIRY SUMMARY REPORT]*\n\n✅ Great news! All drug stock is currently SAFE and within valid expiration dates."
        else:
            items_list = []
            for idx, alert in enumerate(open_alerts[:15], start=1):
                drug = alert.drug
                days_left = (drug.expiry_date - today).days if drug.expiry_date else 0
                badge = "🔴" if alert.severity == 'red' else "🟡"
                items_list.append(
                    f"{idx}. {badge} *{drug.name}*\n"
                    f"   • Batch: {drug.batch_number} | Expiry: {drug.expiry_date} ({days_left}d left)\n"
                    f"   • Reply *ACK-{alert.id}* to acknowledge"
                )
            
            items_text = "\n\n".join(items_list)
            more_count = max(0, open_alerts.count() - 15)
            more_text = f"\n\n... and {more_count} more expiring items." if more_count > 0 else ""

            msg = (
                f"🏥 *[PHARMACY EXPIRY SUMMARY REPORT]*\n\n"
                f"Found *{open_alerts.count()} expiring stock items* needing attention:\n\n"
                f"{items_text}{more_text}\n\n"
                f"Log in to resolve or reply *ACK-code* to acknowledge any alert."
            )

        # Dispatch directly via Twilio WhatsApp Sandbox
        recipients = User.objects.filter(is_active=True, role__in=[User.Role.PHARMACIST, User.Role.ADMIN, User.Role.SUPERVISOR])

        dispatched_count = 0
        for recipient in recipients:
            phone = getattr(recipient, 'phone', None)
            if phone:
                send_whatsapp_message(phone, msg)
                dispatched_count += 1

        return Response({
            'status': 'success',
            'message': f'Consolidated WhatsApp Expiry Summary sent to {dispatched_count} staff user(s)!',
            'expiring_count': open_alerts.count(),
            'summary_text': msg
        }, status=status.HTTP_200_OK)


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


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def whatsapp_webhook_view(request):
    """
    Webhook handler for Evolution API incoming WhatsApp messages.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.data if hasattr(request, 'data') else {}

    msg_data = data.get('data', data)
    if isinstance(msg_data, list) and len(msg_data) > 0:
        msg_data = msg_data[0]

    message_text = ""
    sender_phone = ""

    if isinstance(msg_data, dict):
        key = msg_data.get('key', {})
        sender_phone = key.get('remoteJid', '') or msg_data.get('sender', '')
        
        message_obj = msg_data.get('message', {})
        if isinstance(message_obj, dict):
            message_text = (
                message_obj.get('conversation') or
                message_obj.get('extendedTextMessage', {}).get('text') or
                ''
            )
        elif isinstance(message_obj, str):
            message_text = message_obj

    match = re.search(r'ACK-([0-9a-zA-Z]+)', message_text, re.IGNORECASE)
    if not match:
        return JsonResponse({'status': 'ignored', 'reason': 'No ACK code found in message text'}, status=200)

    ack_token = match.group(1)
    
    notification_log = NotificationLog.objects.filter(ack_code__icontains=ack_token).first()
    alert = notification_log.alert if notification_log else None

    if not alert and ack_token.isdigit():
        alert = Alert.objects.filter(id=int(ack_token)).first()

    if not alert:
        return JsonResponse({'status': 'not_found', 'reason': f'No matching alert found for ACK-{ack_token}'}, status=200)

    if alert.acknowledged:
        return JsonResponse({'status': 'already_acknowledged', 'alert_id': alert.id}, status=200)

    normalized_sender = normalize_phone(sender_phone)
    staff_user = User.objects.filter(phone__icontains=normalized_sender[-10:]).first() if (normalized_sender and len(normalized_sender) >= 10) else None

    alert.acknowledged = True
    alert.acknowledged_by = staff_user
    alert.acknowledged_at = timezone.now()
    alert.save()

    if normalized_sender:
        reply_msg = f"✅ *[ALERT ACKNOWLEDGED]* Alert #{alert.id} for *{alert.drug.name}* has been marked as ACKNOWLEDGED."
        send_whatsapp_text(normalized_sender, reply_msg)

    return JsonResponse({
        'status': 'success',
        'message': f'Alert #{alert.id} marked as acknowledged via WhatsApp reply.',
        'alert_id': alert.id
    }, status=200)
