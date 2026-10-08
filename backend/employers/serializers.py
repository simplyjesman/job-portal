from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Employer, EmployerUser

User = get_user_model()


class EmployerRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    company_name = serializers.CharField(max_length=255)
    location = serializers.CharField(max_length=255)
    industry = serializers.CharField(max_length=255, required=False)
    company_size = serializers.CharField(max_length=50, required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_password(self, value):
        if value.isdigit():
            raise serializers.ValidationError("Password cannot be entirely numeric.")
        return value

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        company_name = validated_data.pop('company_name')
        location = validated_data.pop('location')
        industry = validated_data.pop('industry', '')
        company_size = validated_data.pop('company_size', '')

        user = User.objects.create_user(
            email=email,
            password=password
        )

        employer = Employer.objects.create(
            name=company_name,
            location=location,
            industry=industry,
            company_size=company_size
        )

        employer_user = EmployerUser.objects.create(
            user=user,
            employer=employer,
            role='admin'
        )

        return {
            'user': user,
            'employer': employer,
            'employer_user': employer_user
        }


class EmployerProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Employer
        fields = ['id', 'name', 'location', 'industry', 'company_size', 'email', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_email(self, obj):
        try:
            employer_user = EmployerUser.objects.get(employer=obj)
            return employer_user.user.email
        except EmployerUser.DoesNotExist:
            return None

    def get_role(self, obj):
        try:
            employer_user = EmployerUser.objects.get(employer=obj)
            return employer_user.role
        except EmployerUser.DoesNotExist:
            return None
