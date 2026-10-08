from django.db import models
from django.utils import timezone
from .invite_models import InterviewInvite


class Hire(models.Model):
    """
    Represents a successful hire when candidate accepts an interview invite.
    Automatically created when InterviewInvite is accepted.
    """
    invite = models.OneToOneField(InterviewInvite, on_delete=models.CASCADE, related_name='hire')
    
    # Timeline
    accepted_at = models.DateTimeField(auto_now_add=True, help_text='When candidate accepted invite')
    finalized_at = models.DateTimeField(null=True, blank=True, help_text='When hire is finalized (30 days after acceptance)')

    class Meta:
        db_table = 'hires'
        ordering = ['-accepted_at']
        indexes = [
            models.Index(fields=['accepted_at']),
        ]

    def __str__(self):
        return f"Hire: {self.invite.candidate.user.email} - {self.invite.job_title}"

    def finalize(self):
        """Finalize hire after 30 days - closes dispute window."""
        self.finalized_at = timezone.now()
        self.save()

    def can_request_refund(self):
        """Check if refund can be requested (within 30 days of hire)."""
        days_since_hire = (timezone.now() - self.accepted_at).days
        return days_since_hire <= 30
