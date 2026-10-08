from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import models
import uuid
from .models import EmployerUser
from .invoice_models import Invoice
from .payment_models import Payment
from .payment_serializers import PaymentSerializer, PaymentInitiateSerializer


class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invoice_id):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            invoice = Invoice.objects.get(id=invoice_id, employer=employer_user.employer)

            if invoice.status in ['paid', 'cancelled']:
                return Response(
                    {'error': f'Cannot pay invoice with status: {invoice.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = PaymentInitiateSerializer(data=request.data)
            if serializer.is_valid():
                payment_method = serializer.validated_data['payment_method']
                payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
                payment_url = f"https://paycloud.mock/pay/{payment_reference}"

                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.total_amount,
                    status='pending',
                    payment_method=payment_method,
                    payment_reference=payment_reference,
                    payment_url=payment_url
                )

                result_serializer = PaymentSerializer(payment)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found or does not belong to your employer.'},
                status=status.HTTP_404_NOT_FOUND
            )


@method_decorator(csrf_exempt, name='dispatch')
class PaymentCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payment_reference = request.data.get('payment_reference')
        callback_status = request.data.get('status')

        if not payment_reference or not callback_status:
            return Response(
                {'error': 'Missing payment_reference or status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(payment_reference=payment_reference)

            if callback_status == 'completed':
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()

                invoice = payment.invoice
                total_paid = Payment.objects.filter(
                    invoice=invoice,
                    status='completed'
                ).aggregate(total=models.Sum('amount'))['total'] or 0

                if total_paid >= invoice.total_amount:
                    invoice.status = 'paid'
                    invoice.paid_at = timezone.now()
                else:
                    invoice.status = 'partially_paid'
                invoice.save()

                for commission in invoice.line_items.all():
                    commission.commission.status = 'paid'
                    commission.commission.paid_at = timezone.now()
                    commission.commission.save()

                return Response(
                    {'message': 'Payment processed successfully'},
                    status=status.HTTP_200_OK
                )
            elif callback_status == 'failed':
                payment.status = 'failed'
                payment.save()
                return Response(
                    {'message': 'Payment marked as failed'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class EmployerPaymentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            if employer_user.role not in ['admin', 'recruiter']:
                return Response(
                    {'error': 'Only admins and recruiters can view payments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            queryset = Payment.objects.filter(
                invoice__employer=employer_user.employer
            ).select_related('invoice')

            status_filter = request.query_params.get('status', '')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            sort = request.query_params.get('sort', '-created_at')
            if sort in ['-created_at', 'created_at', '-amount', 'amount']:
                queryset = queryset.order_by(sort)

            page = request.query_params.get('page', 1)
            try:
                page = int(page)
                if page < 1:
                    page = 1
            except (ValueError, TypeError):
                page = 1

            page_size = 20
            start = (page - 1) * page_size
            end = start + page_size

            total_count = queryset.count()
            payments = queryset[start:end]

            serializer = PaymentSerializer(payments, many=True)
            return Response({
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminPaymentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employer_user = EmployerUser.objects.filter(user=request.user).first()
        if not employer_user or employer_user.role != 'admin':
            return Response(
                {'error': 'Admin access required.'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = Payment.objects.select_related('invoice', 'invoice__employer')

        status_filter = request.query_params.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        sort = request.query_params.get('sort', '-created_at')
        if sort in ['-created_at', 'created_at', '-amount', 'amount']:
            queryset = queryset.order_by(sort)

        page = request.query_params.get('page', 1)
        try:
            page = int(page)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

        page_size = 20
        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        payments = queryset[start:end]

        serializer = PaymentSerializer(payments, many=True)
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class PaymentListCreateView(APIView):
    """REST-compliant: POST /invoices/<invoice_id>/payments - create payment for invoice."""
    permission_classes = [IsAuthenticated]

    def post(self, request, invoice_id):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            invoice = Invoice.objects.get(id=invoice_id, employer=employer_user.employer)

            if invoice.status in ['paid', 'cancelled']:
                return Response(
                    {'error': f'Cannot pay invoice with status: {invoice.status}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = PaymentInitiateSerializer(data=request.data)
            if serializer.is_valid():
                payment_method = serializer.validated_data['payment_method']
                payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
                payment_url = f"https://paycloud.mock/pay/{payment_reference}"

                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.total_amount,
                    status='pending',
                    payment_method=payment_method,
                    payment_reference=payment_reference,
                    payment_url=payment_url
                )

                result_serializer = PaymentSerializer(payment)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found or does not belong to your employer.'},
                status=status.HTTP_404_NOT_FOUND
            )


class EmployerPaymentDetailView(APIView):
    """REST-compliant: GET /payments/<payment_id> - view payment details."""
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            payment = Payment.objects.get(
                id=payment_id,
                invoice__employer=employer_user.employer
            )
            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found or does not belong to your employer.'},
                status=status.HTTP_404_NOT_FOUND
            )
