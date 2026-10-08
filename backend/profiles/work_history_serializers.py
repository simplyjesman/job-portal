from rest_framework import serializers
from .work_history_models import WorkHistory
from .skill_models import Skill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']


class WorkHistorySerializer(serializers.ModelSerializer):
    is_current = serializers.ReadOnlyField()
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='skills'
    )

    class Meta:
        model = WorkHistory
        fields = ['id', 'company', 'role', 'start_date', 'end_date', 'description', 'skills', 'skill_ids', 'is_current', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_company(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Company is required")
        return value.strip()

    def validate_role(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Role is required")
        return value.strip()

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError("End date cannot be before start date")
        return data
