from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .commission_models import Commission, CommissionInvoice, CommissionRefund
from .commission_serializers import CommissionSerializer, CommissionInvoiceSerializer, CommissionRefundSerializer


class CommissionViewSet(viewsets.ModelViewSet):
    """Manage individual commissions for hires."""
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show commissions for employer's hires."""
        try:
            employer_user = self.request.user.employer_user
            return Commission.objects.filter(employer=employer_user.employer)
        except:
            return Commission.objects.none()


class CommissionInvoiceViewSet(viewsets.ModelViewSet):
    """Monthly invoices for commissions."""
    serializer_class = CommissionInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show invoices for the employer."""
        try:
            employer_user = self.request.user.employer_user
            return CommissionInvoice.objects.filter(employer=employer_user.employer)
        except:
            return CommissionInvoice.objects.none()

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send invoice to employer."""
        invoice = self.get_object()
        if invoice.status != 'draft':
            return Response({'error': 'Only draft invoices can be sent.'}, status=status.HTTP_400_BAD_REQUEST)
        
        invoice.status = 'sent'
        invoice.sent_at = timezone.now()
        invoice.due_date = invoice.sent_at.date() + timedelta(days=30)
        invoice.save()
        
        return Response(CommissionInvoiceSerializer(invoice).data)


class CommissionRefundViewSet(viewsets.ModelViewSet):
    """Handle commission refund requests."""
    serializer_class = CommissionRefundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show refunds for employer's commissions."""
        try:
            employer_user = self.request.user.employer_user
            return CommissionRefund.objects.filter(
                commission__employer=employer_user.employer
            )
        except:
            return CommissionRefund.objects.none()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a refund request."""
        refund = self.get_object()
        if refund.status != 'requested':
            return Response({'error': 'Only requested refunds can be approved.'}, status=status.HTTP_400_BAD_REQUEST)
        
        refund.approve()
        return Response(CommissionRefundSerializer(refund).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a refund request."""
        refund = self.get_object()
        if refund.status != 'requested':
            return Response({'error': 'Only requested refunds can be rejected.'}, status=status.HTTP_400_BAD_REQUEST)

        refund.status = 'rejected'
        refund.save()
        return Response(CommissionRefundSerializer(refund).data)


class EmployerCommissionsListView(generics.ListAPIView):
    """List commissions for the current employer."""
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            employer_user = self.request.user.employer_user
            return Commission.objects.filter(employer=employer_user.employer)
        except:
            return Commission.objects.none()


class CommissionDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /commissions/<id> - view/update commission details."""
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            employer_user = self.request.user.employer_user
            return Commission.objects.filter(employer=employer_user.employer)
        except:
            return Commission.objects.none()


class AdminCommissionsListView(generics.ListAPIView):
    """List all commissions (admin only)."""
    queryset = Commission.objects.all()
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]
