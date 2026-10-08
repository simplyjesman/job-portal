from django.db import models
from .models import CandidateProfile
from .skill_models import Skill


class WorkHistory(models.Model):
    profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='work_history')
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True, max_length=500)
    skills = models.ManyToManyField(Skill, related_name='work_history', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'work_history'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.profile.user.email} - {self.role} at {self.company}"

    @property
    def is_current(self):
        return self.end_date is None
