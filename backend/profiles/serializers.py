from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import CandidateProfile, ExternalLink
from .work_history_models import WorkHistory
from .work_history_serializers import WorkHistorySerializer
from .education_models import Education
from .education_serializers import EducationSerializer
from .skill_models import Skill

User = get_user_model()


class ExternalLinkSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField()

    class Meta:
        model = ExternalLink
        fields = ['id', 'platform', 'username', 'url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'url', 'created_at', 'updated_at']


class CandidateProfileSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = ['id', 'user_id', 'first_name', 'last_name', 'email', 'phone', 'location', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'email', 'status', 'created_at', 'updated_at']

    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required")
        return value.strip()

    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required")
        return value.strip()

    def validate_location(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Location is required")
        return value.strip()

    def create(self, validated_data):
        user = self.context['request'].user
        profile = CandidateProfile.objects.create(user=user, **validated_data)
        return profile

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class CandidateProfileDetailSerializer(serializers.ModelSerializer):
    """Full profile with nested work history, education, and links for viewing."""
    email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    experience_level = serializers.ReadOnlyField()
    work_history = WorkHistorySerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    external_links = ExternalLinkSerializer(many=True, read_only=True)
    first_name_display = serializers.CharField(source='first_name', read_only=True)
    last_name_display = serializers.CharField(source='last_name', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'user_id', 'first_name_display', 'last_name_display', 'email',
            'headline', 'location', 'availability', 'experience_level',
            'photo', 'work_history', 'education', 'external_links',
            'profile_status', 'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'email', 'experience_level', 'profile_status', 'published_at', 'created_at', 'updated_at']


class CandidateProfileEditSerializer(serializers.ModelSerializer):
    """Profile edit serializer for draft profiles."""
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = ['id', 'email', 'first_name', 'last_name', 'headline', 'location', 'availability', 'photo', 'updated_at']
        read_only_fields = ['id', 'email', 'updated_at']

    def validate_headline(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Headline cannot be blank")
        return value.strip() if value else value

    def update(self, instance, validated_data):
        # Check if profile is live and user is not trying to edit
        if instance.profile_status == 'live':
            raise serializers.ValidationError("Cannot edit a live profile. Revert to draft first.")

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
