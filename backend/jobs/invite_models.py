from django.db import models
from django.utils import timezone
from profiles.models import CandidateProfile
from employers.models import Employer


class InterviewInvite(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='interview_invites')
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='interview_invites')
    
    # Job details included in invite
    job_title = models.CharField(max_length=255)
    job_description = models.TextField()
    salary_min = models.IntegerField(null=True, blank=True, help_text='Minimum salary in GBP (£)')
    salary_max = models.IntegerField(null=True, blank=True, help_text='Maximum salary in GBP (£)')
    location = models.CharField(max_length=255, null=True, blank=True)
    
    # Custom message from employer
    message = models.TextField(blank=True, null=True, max_length=1000)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    
    # For rejections/closures
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'interview_invites'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['employer', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Invite {self.job_title} to {self.candidate.user.email} - {self.status}"

    def accept(self):
        """Candidate accepts the invite."""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()

    def decline(self):
        """Candidate declines the invite."""
        self.status = 'declined'
        self.declined_at = timezone.now()
        self.save()

    def cancel(self):
        """Employer cancels the invite."""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()

    @property
    def is_active(self):
        """Check if invite is still open (not accepted/declined/cancelled)."""
        return self.status == 'sent'
