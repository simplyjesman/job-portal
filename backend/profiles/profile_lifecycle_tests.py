import pytest
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from .models import CandidateProfile


@pytest.mark.django_db
class TestProfilePause:
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
            status='active'
        )
        self.pause_url = f'/api/profiles/{self.profile.id}/pause'
        self.client.force_authenticate(user=self.user)

    def test_pause_active_profile_success(self):
        response = self.client.post(self.pause_url)
        assert response.status_code == 200
        assert response.data['status'] == 'paused'
        self.profile.refresh_from_db()
        assert self.profile.status == 'paused'

    def test_pause_already_paused_profile(self):
        self.profile.status = 'paused'
        self.profile.save()
        response = self.client.post(self.pause_url)
        assert response.status_code == 400
        assert 'already paused' in str(response.data)

    def test_pause_archived_profile(self):
        self.profile.status = 'archived'
        self.profile.save()
        response = self.client.post(self.pause_url)
        assert response.status_code == 400
        assert 'Cannot pause an archived profile' in str(response.data)

    def test_pause_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.pause_url)
        assert response.status_code == 403

    def test_pause_profile_not_found(self):
        response = self.client.post('/api/profiles/99999/pause')
        assert response.status_code == 404


@pytest.mark.django_db
class TestProfileUnpause:
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
            status='paused'
        )
        self.unpause_url = f'/api/profiles/{self.profile.id}/unpause'
        self.client.force_authenticate(user=self.user)

    def test_unpause_paused_profile_success(self):
        response = self.client.post(self.unpause_url)
        assert response.status_code == 200
        assert response.data['status'] == 'active'
        self.profile.refresh_from_db()
        assert self.profile.status == 'active'

    def test_unpause_active_profile(self):
        self.profile.status = 'active'
        self.profile.save()
        response = self.client.post(self.unpause_url)
        assert response.status_code == 400
        assert 'not paused' in str(response.data)

    def test_unpause_archived_profile(self):
        self.profile.status = 'archived'
        self.profile.save()
        response = self.client.post(self.unpause_url)
        assert response.status_code == 400
        assert 'Cannot unpause an archived profile' in str(response.data)

    def test_unpause_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.unpause_url)
        assert response.status_code == 403

    def test_unpause_profile_not_found(self):
        response = self.client.post('/api/profiles/99999/unpause')
        assert response.status_code == 404


@pytest.mark.django_db
class TestProfileDelete:
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
            status='active'
        )
        self.delete_url = f'/api/profiles/{self.profile.id}/delete'
        self.client.force_authenticate(user=self.user)

    def test_delete_profile_success(self):
        response = self.client.post(self.delete_url)
        assert response.status_code == 200
        assert response.data['status'] == 'archived'
        assert '90 days' in str(response.data)
        self.profile.refresh_from_db()
        assert self.profile.status == 'archived'

    def test_delete_paused_profile(self):
        self.profile.status = 'paused'
        self.profile.save()
        response = self.client.post(self.delete_url)
        assert response.status_code == 200
        self.profile.refresh_from_db()
        assert self.profile.status == 'archived'

    def test_delete_already_archived_profile(self):
        self.profile.status = 'archived'
        self.profile.save()
        response = self.client.post(self.delete_url)
        assert response.status_code == 400
        assert 'already archived' in str(response.data)

    def test_delete_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.delete_url)
        assert response.status_code == 403

    def test_delete_profile_not_found(self):
        response = self.client.post('/api/profiles/99999/delete')
        assert response.status_code == 404

    def test_profile_data_preserved_after_delete(self):
        # Verify that profile data is preserved during soft-delete
        response = self.client.post(self.delete_url)
        assert response.status_code == 200
        self.profile.refresh_from_db()
        assert self.profile.first_name == 'John'
        assert self.profile.last_name == 'Doe'
        assert self.profile.location == 'Johannesburg'
