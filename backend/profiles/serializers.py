from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CandidateProfile

User = get_user_model()


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
