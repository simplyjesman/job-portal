import pytest
from datetime import date
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from .models import CandidateProfile
from .skill_models import Skill, CandidateSkill
from .work_history_models import WorkHistory
from .availability_models import Availability
from .profile_utils import is_profile_complete, update_profile_status


@pytest.mark.django_db
class TestProfileCompleteness:
    def setup_method(self):
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='pending'
        )
        self.skill = Skill.objects.create(name='Python')

    def test_profile_incomplete_no_skills(self):
        assert is_profile_complete(self.profile) == False

    def test_profile_incomplete_no_availability(self):
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill)
        assert is_profile_complete(self.profile) == False

    def test_profile_complete(self):
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill)
        Availability.objects.create(
            profile=self.profile,
            available_from_month=3,
            available_from_year=2024,
            employment_type='full-time'
        )
        assert is_profile_complete(self.profile) == True

    def test_profile_incomplete_empty_name(self):
        profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='',
            last_name='Doe',
            location='Johannesburg'
        )
        assert is_profile_complete(profile) == False

    def test_profile_incomplete_no_location(self):
        profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            location=''
        )
        CandidateSkill.objects.create(profile=profile, skill=self.skill)
        Availability.objects.create(
            profile=profile,
            available_from_month=3,
            available_from_year=2024,
            employment_type='full-time'
        )
        assert is_profile_complete(profile) == False


@pytest.mark.django_db
class TestProfileStatusTransition:
    def setup_method(self):
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='pending'
        )
        self.skill = Skill.objects.create(name='Python')

    def test_status_pending_to_active_on_completion(self):
        assert self.profile.status == 'pending'
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill)
        Availability.objects.create(
            profile=self.profile,
            available_from_month=3,
            available_from_year=2024,
            employment_type='full-time'
        )
        assert update_profile_status(self.profile) == True
        self.profile.refresh_from_db()
        assert self.profile.status == 'active'

    def test_status_active_to_pending_on_incomplete(self):
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill)
        Availability.objects.create(
            profile=self.profile,
            available_from_month=3,
            available_from_year=2024,
            employment_type='full-time'
        )
        self.profile.status = 'active'
        self.profile.save()

        # Delete skills
        CandidateSkill.objects.filter(profile=self.profile).delete()
        assert update_profile_status(self.profile) == True
        self.profile.refresh_from_db()
        assert self.profile.status == 'pending'

    def test_status_no_change_if_already_active(self):
        self.profile.status = 'active'
        self.profile.save()
        assert update_profile_status(self.profile) == False
        self.profile.refresh_from_db()
        assert self.profile.status == 'active'


@pytest.mark.django_db
class TestProfileStatusAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='pending'
        )
        self.url = f'/api/profiles/{self.profile.id}/status'
        self.client.force_authenticate(user=self.user)
        self.skill = Skill.objects.create(name='Python')

    def test_get_profile_status_pending(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['status'] == 'pending'
        assert response.data['is_complete'] == False
        assert 'not yet searchable' in response.data['message']

    def test_get_profile_status_active(self):
        self.profile.status = 'active'
        self.profile.save()
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['status'] == 'active'
        assert 'searchable by employers' in response.data['message']

    def test_get_profile_status_paused(self):
        self.profile.status = 'paused'
        self.profile.save()
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['status'] == 'paused'

    def test_get_profile_status_not_found(self):
        response = self.client.get('/api/profiles/99999/status')
        assert response.status_code == 404

    def test_profile_status_reflects_completeness(self):
        # Add skills and availability
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill)
        Availability.objects.create(
            profile=self.profile,
            available_from_month=3,
            available_from_year=2024,
            employment_type='full-time'
        )
        update_profile_status(self.profile)

        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['is_complete'] == True
        assert response.data['status'] == 'active'
