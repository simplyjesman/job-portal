import pytest
from datetime import date
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from .models import CandidateProfile
from .work_history_models import WorkHistory


@pytest.mark.django_db
class TestWorkHistoryCreate:
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
        self.url = f'/api/profiles/{self.profile.id}/work-history'
        self.client.force_authenticate(user=self.user)

    def test_create_work_history_success(self):
        response = self.client.post(self.url, {
            'company': 'Tech Company',
            'role': 'Software Engineer',
            'start_date': '2020-01-15',
            'end_date': '2022-06-30',
            'description': 'Built backend systems'
        })
        assert response.status_code == 201
        assert response.data['company'] == 'Tech Company'
        assert response.data['role'] == 'Software Engineer'
        assert response.data['is_current'] == False
        assert WorkHistory.objects.filter(profile=self.profile).count() == 1

    def test_create_work_history_current_role(self):
        response = self.client.post(self.url, {
            'company': 'Current Company',
            'role': 'Senior Engineer',
            'start_date': '2022-07-01',
            'end_date': None,
            'description': 'Leading team'
        })
        assert response.status_code == 201
        assert response.data['is_current'] == True
        assert response.data['end_date'] == None

    def test_create_work_history_no_description(self):
        response = self.client.post(self.url, {
            'company': 'Startup',
            'role': 'Developer',
            'start_date': '2023-01-01'
        })
        assert response.status_code == 201
        assert response.data['description'] == None

    def test_create_work_history_missing_company(self):
        response = self.client.post(self.url, {
            'role': 'Developer',
            'start_date': '2023-01-01'
        })
        assert response.status_code == 400
        assert 'company' in response.data

    def test_create_work_history_missing_role(self):
        response = self.client.post(self.url, {
            'company': 'Company',
            'start_date': '2023-01-01'
        })
        assert response.status_code == 400
        assert 'role' in response.data

    def test_create_work_history_missing_start_date(self):
        response = self.client.post(self.url, {
            'company': 'Company',
            'role': 'Developer'
        })
        assert response.status_code == 400
        assert 'start_date' in response.data

    def test_create_work_history_end_before_start(self):
        response = self.client.post(self.url, {
            'company': 'Company',
            'role': 'Developer',
            'start_date': '2023-01-01',
            'end_date': '2022-12-31'
        })
        assert response.status_code == 400
        assert 'End date cannot be before start date' in str(response.data)

    def test_create_work_history_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.url, {
            'company': 'Company',
            'role': 'Developer',
            'start_date': '2023-01-01'
        })
        assert response.status_code == 403

    def test_create_work_history_profile_not_found(self):
        response = self.client.post('/api/profiles/99999/work-history', {
            'company': 'Company',
            'role': 'Developer',
            'start_date': '2023-01-01'
        })
        assert response.status_code == 404


@pytest.mark.django_db
class TestWorkHistoryRetrieve:
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
        self.url = f'/api/profiles/{self.profile.id}/work-history'
        self.client.force_authenticate(user=self.user)
        self.work_history1 = WorkHistory.objects.create(
            profile=self.profile,
            company='Company 1',
            role='Engineer',
            start_date=date(2020, 1, 1),
            end_date=date(2022, 1, 1)
        )
        self.work_history2 = WorkHistory.objects.create(
            profile=self.profile,
            company='Company 2',
            role='Senior Engineer',
            start_date=date(2022, 6, 1)
        )

    def test_list_work_history(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['company'] == 'Company 2'
        assert response.data[1]['company'] == 'Company 1'

    def test_list_work_history_empty(self):
        profile = CandidateProfile.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            location='Cape Town'
        )
        url = f'/api/profiles/{profile.id}/work-history'
        response = self.client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_get_work_history_detail(self):
        url = f'/api/profiles/{self.profile.id}/work-history/{self.work_history1.id}'
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data['company'] == 'Company 1'
        assert response.data['role'] == 'Engineer'


@pytest.mark.django_db
class TestWorkHistoryUpdate:
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
        self.work_history = WorkHistory.objects.create(
            profile=self.profile,
            company='Old Company',
            role='Developer',
            start_date=date(2020, 1, 1),
            end_date=date(2022, 1, 1)
        )
        self.url = f'/api/profiles/{self.profile.id}/work-history/{self.work_history.id}'
        self.client.force_authenticate(user=self.user)

    def test_update_work_history_partial(self):
        response = self.client.patch(self.url, {
            'company': 'New Company'
        })
        assert response.status_code == 200
        assert response.data['company'] == 'New Company'
        assert response.data['role'] == 'Developer'

    def test_update_work_history_full(self):
        response = self.client.patch(self.url, {
            'company': 'Another Company',
            'role': 'Senior Developer',
            'start_date': '2021-01-01',
            'end_date': None,
            'description': 'New description'
        })
        assert response.status_code == 200
        assert response.data['is_current'] == True

    def test_delete_work_history(self):
        response = self.client.delete(self.url)
        assert response.status_code == 204
        assert WorkHistory.objects.filter(id=self.work_history.id).exists() == False

    def test_update_work_history_not_found(self):
        url = f'/api/profiles/{self.profile.id}/work-history/99999'
        response = self.client.patch(url, {'company': 'Company'})
        assert response.status_code == 404
