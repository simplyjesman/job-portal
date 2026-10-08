from django.db import models
from django.conf import settings
from django.utils import timezone


class CandidateProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255)
    salary_expectations = models.IntegerField(help_text='Expected salary in GBP', null=True, blank=True)
    availability = models.CharField(
        max_length=50,
        choices=[
            ('immediate', 'Immediately available'),
            ('notice_1_week', '1 week notice'),
            ('notice_2_weeks', '2 weeks notice'),
            ('notice_1_month', '1 month notice'),
            ('notice_3_months', '3+ months notice'),
        ],
        default='immediate'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('paused', 'Paused'),
            ('archived', 'Archived'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True, help_text='Soft-delete timestamp for GDPR')
    deleted_at = models.DateTimeField(null=True, blank=True, help_text='Hard-delete after 90 days from archive')

    class Meta:
        db_table = 'candidate_profiles'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['archived_at']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"Profile for {self.user.email}"

    @property
    def email(self):
        return self.user.email

    def archive(self):
        """Soft-delete: archive profile for GDPR compliance."""
        self.archived_at = timezone.now()
        self.status = 'archived'
        self.save()
