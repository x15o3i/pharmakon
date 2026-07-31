from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DrugCategory, Drug
from .serializers import DrugCategorySerializer, DrugSerializer
from .services import run_abc_ved_classification
from accounts.permissions import IsAdminRole, IsPharmacistRole, IsSupervisorRole


class DrugCategoryViewSet(viewsets.ModelViewSet):
    queryset = DrugCategory.objects.all().order_by('name')
    serializer_class = DrugCategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsPharmacistRole()]
        return [IsAdminRole()]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class DrugViewSet(viewsets.ModelViewSet):
    queryset = Drug.objects.all().select_related('category', 'created_by').order_by('expiry_date')
    serializer_class = DrugSerializer
    permission_classes = [IsPharmacistRole]

    def get_queryset(self):
        qs = super().get_queryset()
        barcode = self.request.query_params.get('barcode')
        search = self.request.query_params.get('search')
        category_id = self.request.query_params.get('category')
        
        if barcode:
            qs = qs.filter(barcode=barcode)
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(generic_name__icontains=search) | qs.filter(batch_number__icontains=search)
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def perform_create(self, serializer):
        drug = serializer.save(created_by=self.request.user)
        # Automatically run expiry check so an alert & WhatsApp message is sent immediately if expiring soon
        from alerts.tasks import check_expiring_drugs
        try:
            check_expiring_drugs.delay()
        except Exception:
            check_expiring_drugs()

    @action(detail=False, methods=['get'], url_path='barcode/(?P<barcode_val>[^/.]+)')
    def find_by_barcode(self, request, barcode_val=None):
        try:
            drug = Drug.objects.get(barcode=barcode_val)
            serializer = self.get_serializer(drug)
            return Response(serializer.data)
        except Drug.DoesNotExist:
            return Response({'detail': 'Drug not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], permission_classes=[IsSupervisorRole])
    def reclassify(self, request):
        result = run_abc_ved_classification()
        return Response({
            'message': 'ABC/VED reclassification executed successfully',
            'details': result
        })
