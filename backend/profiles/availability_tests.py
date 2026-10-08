import pytest
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from .models import CandidateProfile
from .availability_models import Availability


@pytest.mark.django_db
class TestAvailabilityCreate:
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
            location='Johannesburg'
        )
        self.url = f'/api/profiles/{self.profile.id}/availability'
        self.client.force_authenticate(user=self.user)

    def test_create_availability_success(self):
        response = self.client.post(self.url, {
            'available_from_month': 3,
            'available_from_year': 2024,
            'employment_type': 'full-time',
            'salary_min': 60000,
            'salary_max': 80000
        })
        assert response.status_code == 201
        assert response.data['available_from_month'] == 3
        assert response.data['available_from_year'] == 2024
        assert response.data['employment_type'] == 'full-time'
        assert response.data['salary_min'] == 60000
        assert response.data['salary_max'] == 80000

    def test_create_availability_no_salary(self):
        response = self.client.post(self.url, {
            'available_from_month': 1,
            'available_from_year': 2024,
            'employment_type': 'part-time'
        })
        assert response.status_code == 201
        assert response.data['salary_min'] is None
        assert response.data['salary_max'] is None

    def test_create_availability_part_time(self):
        response = self.client.post(self.url, {
            'available_from_month': 12,
            'available_from_year': 2023,
            'employment_type': 'part-time'
        })
        assert response.status_code == 201
        assert response.data['employment_type'] == 'part-time'

    def test_create_availability_contract(self):
        response = self.client.post(self.url, {
            'available_from_month': 6,
            'available_from_year': 2024,
            'employment_type': 'contract'
        })
        assert response.status_code == 201
        assert response.data['employment_type'] == 'contract'

    def test_create_availability_invalid_month_low(self):
        response = self.client.post(self.url, {
            'available_from_month': 0,
            'available_from_year': 2024,
            'employment_type': 'full-time'
        })
        assert response.status_code == 400
        assert 'Month must be between 1 and 12' in str(response.data)

    def test_create_availability_invalid_month_high(self):
        response = self.client.post(self.url, {
            'available_from_month': 13,
            'available_from_year': 2024,
            'employment_type': 'full-time'
        })
        assert response.status_code == 400
        assert 'Month must be between 1 and 12' in str(response.data)

    def test_create_availability_salary_max_less_than_min(self):
        response = self.client.post(self.url, {
            'available_from_month': 3,
            'available_from_year': 2024,
            'employment_type': 'full-time',
            'salary_min': 80000,
            'salary_max': 60000
        })
        assert response.status_code == 400
        assert 'Salary max cannot be less than salary min' in str(response.data)

    def test_create_availability_negative_salary(self):
        response = self.client.post(self.url, {
            'available_from_month': 3,
            'available_from_year': 2024,
            'employment_type': 'full-time',
            'salary_min': -1000
        })
        assert response.status_code == 400
        assert 'Salary min cannot be negative' in str(response.data)

    def test_create_availability_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.url, {
            'available_from_month': 3,
            'available_from_year': 2024,
            'employment_type': 'full-time'
        })
        assert response.status_code == 403


@pytest.mark.django_db
class TestAvailabilityRetrieve:
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
            location='Johannesburg'
        )
        self.url = f'/api/profiles/{self.profile.id}/availability'
        self.client.force_authenticate(user=self.user)
        self.availability = Availability.objects.create(
            profile=self.profile,
            available_from_month=3,
            available_from_year=2024,
            employment_type='full-time',
            salary_min=60000,
            salary_max=80000
        )

    def test_get_availability_success(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['available_from_month'] == 3
        assert response.data['available_from_year'] == 2024

    def test_get_availability_not_set(self):
        profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            location='Cape Town'
        )
        url = f'/api/profiles/{profile.id}/availability'
        response = self.client.get(url)
        assert response.status_code == 404
        assert 'Availability not set' in str(response.data)


@pytest.mark.django_db
class TestAvailabilityUpdate:
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
            location='Johannesburg'
        )
        self.url = f'/api/profiles/{self.profile.id}/availability'
        self.client.force_authenticate(user=self.user)
        self.availability = Availability.objects.create(
            profile=self.profile,
            available_from_month=3,
            available_from_year=2024,
            employment_type='full-time',
            salary_min=60000,
            salary_max=80000
        )

    def test_update_availability_partial(self):
        response = self.client.patch(self.url, {
            'available_from_month': 6
        })
        assert response.status_code == 200
        assert response.data['available_from_month'] == 6
        assert response.data['available_from_year'] == 2024

    def test_update_availability_full(self):
        response = self.client.patch(self.url, {
            'available_from_month': 1,
            'available_from_year': 2025,
            'employment_type': 'part-time',
            'salary_min': 50000,
            'salary_max': 70000
        })
        assert response.status_code == 200
        assert response.data['employment_type'] == 'part-time'

    def test_update_availability_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(self.url, {
            'available_from_month': 12
        })
        assert response.status_code == 403

    def test_update_availability_not_set(self):
        profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            location='Cape Town'
        )
        url = f'/api/profiles/{profile.id}/availability'
        response = self.client.patch(url, {
            'available_from_month': 3
        })
        assert response.status_code == 404
