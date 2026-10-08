from django.db import models
from django.conf import settings
from django.utils import timezone


class CandidateProfile(models.Model):
    PROFILE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('live', 'Live'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255)
    headline = models.CharField(max_length=255, blank=True, null=True, help_text='e.g., Senior Backend Engineer, 8 years')
    photo = models.ImageField(upload_to='candidate_photos/', blank=True, null=True)
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
    profile_status = models.CharField(
        max_length=20,
        choices=PROFILE_STATUS_CHOICES,
        default='draft',
        help_text='Draft = editable, Live = locked for employers to view'
    )
    published_at = models.DateTimeField(null=True, blank=True, help_text='When profile was made live')
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

    @property
    def experience_level(self):
        """Calculate experience level from work history total years."""
        if not self.work_history.exists():
            return 'junior'

        from datetime import date
        total_days = 0
        for work in self.work_history.all():
            end = work.end_date or date.today()
            delta = (end - work.start_date).days
            total_days += delta

        years = total_days / 365.25
        if years < 2:
            return 'junior'
        elif years < 5:
            return 'mid'
        elif years < 10:
            return 'senior'
        else:
            return 'lead'


class ExternalLink(models.Model):
    PLATFORM_CHOICES = [
        ('github', 'GitHub'),
        ('linkedin', 'LinkedIn'),
        ('portfolio', 'Portfolio'),
    ]

    profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='external_links')
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    username = models.CharField(max_length=255, help_text='GitHub username, LinkedIn profile name, or portfolio URL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'external_links'
        unique_together = ('profile', 'platform')

    def __str__(self):
        return f"{self.profile.user.email} - {self.get_platform_display()}"

    @property
    def url(self):
        """Generate full URL from platform and username."""
        if self.platform == 'github':
            return f'https://github.com/{self.username}'
        elif self.platform == 'linkedin':
            return f'https://linkedin.com/in/{self.username}'
        else:  # portfolio
            return self.username
