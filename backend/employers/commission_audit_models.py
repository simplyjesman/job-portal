from django.db import models
from django.conf import settings
from .commission_models import Commission


class CommissionAuditLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('disputed', 'Disputed'),
        ('approved', 'Approved'),
        ('adjusted', 'Adjusted'),
        ('refunded', 'Refunded'),
        ('status_changed', 'Status Changed'),
    ]

    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    previous_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reason = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action}: Commission {self.commission.id} by {self.admin_user}"


class CommissionDispute(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    commission = models.OneToOneField(Commission, on_delete=models.CASCADE, related_name='dispute')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    reason = models.TextField(max_length=500)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_disputes')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute: Commission {self.commission.id} ({self.status})"
