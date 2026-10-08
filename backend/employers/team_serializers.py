from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmployerUser

User = get_user_model()


class TeamMemberSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = EmployerUser
        fields = ['id', 'user_id', 'email', 'role', 'created_at']
        read_only_fields = ['id', 'user_id', 'email', 'created_at']


class AddTeamMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=['admin', 'recruiter', 'viewer'])

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def validate_role(self, value):
        if value not in ['admin', 'recruiter', 'viewer']:
            raise serializers.ValidationError("Invalid role.")
        return value
