import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .models import CandidateProfile

User = get_user_model()


@pytest.mark.django_db
class TestCandidateProfileCreation:
    def setup_method(self):
        self.client = APIClient()
        self.create_url = '/api/profiles'
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_create_profile_success(self):
        response = self.client.post(self.create_url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '0123456789',
            'location': 'Johannesburg',
        })
        assert response.status_code == 201
        assert response.data['first_name'] == 'John'
        assert response.data['last_name'] == 'Doe'
        assert response.data['phone'] == '0123456789'
        assert response.data['location'] == 'Johannesburg'
        assert response.data['email'] == 'candidate@example.com'
        assert response.data['status'] == 'pending'
        assert CandidateProfile.objects.filter(user=self.user).exists()

    def test_create_profile_without_phone(self):
        response = self.client.post(self.create_url, {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'location': 'Cape Town',
        })
        assert response.status_code == 201
        assert response.data['first_name'] == 'Jane'
        assert response.data['phone'] is None

    def test_create_profile_missing_required_field(self):
        response = self.client.post(self.create_url, {
            'first_name': 'John',
            'last_name': 'Doe',
        })
        assert response.status_code == 400
        assert 'location' in response.data

    def test_create_profile_empty_first_name(self):
        response = self.client.post(self.create_url, {
            'first_name': '   ',
            'last_name': 'Doe',
            'location': 'Johannesburg',
        })
        assert response.status_code == 400
        assert 'first_name' in response.data

    def test_create_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.create_url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'location': 'Johannesburg',
        })
        assert response.status_code == 401


@pytest.mark.django_db
class TestCandidateProfileRetrieval:
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
            phone='0123456789',
            location='Johannesburg'
        )
        self.detail_url = f'/api/profiles/{self.profile.id}'
        self.client.force_authenticate(user=self.user)

    def test_get_profile_success(self):
        response = self.client.get(self.detail_url)
        assert response.status_code == 200
        assert response.data['first_name'] == 'John'
        assert response.data['last_name'] == 'Doe'
        assert response.data['email'] == 'candidate@example.com'
        assert response.data['status'] == 'pending'

    def test_get_profile_not_found(self):
        response = self.client.get('/api/profiles/99999')
        assert response.status_code == 404
        assert 'Profile not found' in str(response.data)

    def test_get_profile_employer_viewing(self):
        other_user = User.objects.create_user(

            email='employer@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.get(self.detail_url)
        assert response.status_code == 200
        assert response.data['first_name'] == 'John'


@pytest.mark.django_db
class TestCandidateProfileUpdate:
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
            phone='0123456789',
            location='Johannesburg'
        )
        self.detail_url = f'/api/profiles/{self.profile.id}'
        self.client.force_authenticate(user=self.user)

    def test_update_profile_partial(self):
        response = self.client.patch(self.detail_url, {
            'location': 'Cape Town',
        })
        assert response.status_code == 200
        assert response.data['location'] == 'Cape Town'
        assert response.data['first_name'] == 'John'
        self.profile.refresh_from_db()
        assert self.profile.location == 'Cape Town'

    def test_update_profile_full(self):
        response = self.client.patch(self.detail_url, {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '9876543210',
            'location': 'Pretoria',
        })
        assert response.status_code == 200
        assert response.data['first_name'] == 'Jane'
        assert response.data['last_name'] == 'Smith'
        assert response.data['phone'] == '9876543210'
        assert response.data['location'] == 'Pretoria'

    def test_update_profile_email_readonly(self):
        response = self.client.patch(self.detail_url, {
            'email': 'newemail@example.com',
        })
        assert response.status_code == 200
        assert response.data['email'] == 'candidate@example.com'

    def test_update_profile_invalid_location(self):
        response = self.client.patch(self.detail_url, {
            'location': '   ',
        })
        assert response.status_code == 400
        assert 'location' in response.data

    def test_update_profile_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(self.detail_url, {
            'location': 'Durban',
        })
        assert response.status_code == 403
        assert 'You can only update your own profile' in str(response.data)

    def test_update_profile_not_found(self):
        response = self.client.patch('/api/profiles/99999', {
            'location': 'Durban',
        })
        assert response.status_code == 404
