from django.db import models
from django.utils import timezone
from jobs.hire_models import Hire


class Commission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Invoice'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    hire = models.OneToOneField(Hire, on_delete=models.CASCADE, related_name='commission')
    employer = models.ForeignKey('Employer', on_delete=models.CASCADE, related_name='commissions')
    
    # Amount (in GBP)
    amount_gbp = models.IntegerField(help_text='Commission amount in pence (GBP)')
    
    # Status & timeline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmed_at = models.DateTimeField(auto_now_add=True, help_text='When hire was confirmed')
    invoiced_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Invoice relation
    invoice = models.ForeignKey('CommissionInvoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='commissions')
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'commissions'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['invoiced_at']),
        ]

    def __str__(self):
        return f"Commission £{self.amount_gbp/100:.2f} - {self.employer.name} - {self.status}"

    @property
    def amount_pounds(self):
        """Convert pence to pounds for display."""
        return self.amount_gbp / 100


class CommissionInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]

    employer = models.ForeignKey('Employer', on_delete=models.CASCADE, related_name='commission_invoices')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Period
    invoice_date = models.DateField(auto_now_add=True)
    invoice_month = models.CharField(max_length=7, help_text='YYYY-MM format')
    
    # Amount
    total_amount_gbp = models.IntegerField(help_text='Total invoice amount in pence (GBP)')
    
    # Timeline
    sent_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Stripe/payment reference
    payment_method = models.CharField(
        max_length=20,
        choices=[('stripe', 'Stripe Card'), ('bank_transfer', 'Bank Transfer')],
        null=True,
        blank=True
    )
    payment_reference = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe Payment Intent ID or bank transaction ref')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'commission_invoices'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['employer', 'invoice_month']),
            models.Index(fields=['paid_at']),
        ]
        unique_together = ('employer', 'invoice_month')

    def __str__(self):
        return f"Invoice {self.invoice_month} - {self.employer.name} - £{self.total_amount_gbp/100:.2f}"

    @property
    def total_amount_pounds(self):
        """Convert pence to pounds for display."""
        return self.total_amount_gbp / 100


class CommissionRefund(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]

    commission = models.OneToOneField(Commission, on_delete=models.CASCADE, related_name='refund')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    
    # Reason for refund
    reason = models.CharField(
        max_length=20,
        choices=[
            ('candidate_left', 'Candidate Left'),
            ('candidate_terminated', 'Candidate Terminated'),
            ('other', 'Other'),
        ]
    )
    reason_detail = models.TextField(max_length=500, blank=True)
    
    # Timeline
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Evidence
    evidence = models.TextField(max_length=1000, help_text='Proof of hire termination (e.g., last day of work)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'commission_refunds'
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Refund request for Commission {self.commission.id} - {self.status}"

    def approve(self):
        """Approve refund and update commission status."""
        self.status = 'approved'
        self.save()
        # Actual refund processing will be handled by payment processor

    def process(self):
        """Mark refund as processed (payment returned)."""
        self.status = 'processed'
        self.processed_at = timezone.now()
        self.commission.status = 'refunded'
        self.commission.refunded_at = timezone.now()
        self.commission.save()
        self.save()
