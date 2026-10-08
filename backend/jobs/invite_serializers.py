from rest_framework import serializers
from .invite_models import InterviewInvite


class InterviewInviteSerializer(serializers.ModelSerializer):
    candidate_email = serializers.CharField(source='candidate.user.email', read_only=True)
    candidate_name = serializers.SerializerMethodField()
    employer_name = serializers.CharField(source='employer.name', read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = InterviewInvite
        fields = [
            'id', 'candidate_email', 'candidate_name', 'employer_name',
            'job_title', 'job_description', 'salary_min', 'salary_max', 'location',
            'message', 'status', 'sent_at', 'accepted_at', 'declined_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'candidate_email', 'candidate_name', 'employer_name',
            'status', 'sent_at', 'accepted_at', 'declined_at', 'is_active'
        ]

    def get_candidate_name(self, obj):
        profile = obj.candidate
        return f"{profile.first_name} {profile.last_name}"

    def get_is_active(self, obj):
        return obj.is_active


class SendInterviewInviteSerializer(serializers.Serializer):
    """For employer sending invite to candidate."""
    candidate_id = serializers.IntegerField()
    job_title = serializers.CharField(max_length=255)
    job_description = serializers.CharField()
    salary_min = serializers.IntegerField(required=False, allow_null=True)
    salary_max = serializers.IntegerField(required=False, allow_null=True)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    message = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class CandidateResponseSerializer(serializers.Serializer):
    """For candidate accepting/declining invite."""
    action = serializers.ChoiceField(choices=['accept', 'decline'])
