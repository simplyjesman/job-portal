import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Employer, EmployerUser
from accounts.models import SessionToken

User = get_user_model()


@pytest.mark.django_db
class TestEmployerRegistration:
    def setup_method(self):
        self.client = APIClient()

    def test_employer_registration_success(self):
        data = {
            'email': 'employer@example.com',
            'password': 'SecurePass123',
            'company_name': 'TechCorp',
            'location': 'Johannesburg',
            'industry': 'Technology',
            'company_size': '11-50'
        }
        response = self.client.post('/api/employer/register', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'employer@example.com'
        assert 'token' in response.data
        assert User.objects.filter(email='employer@example.com').exists()
        assert Employer.objects.filter(name='TechCorp').exists()
        employer_user = EmployerUser.objects.get(user__email='employer@example.com')
        assert employer_user.role == 'admin'

    def test_employer_registration_duplicate_email(self):
        User.objects.create_user(email='existing@example.com', password='Pass123')

        data = {
            'email': 'existing@example.com',
            'password': 'SecurePass123',
            'company_name': 'TechCorp',
            'location': 'Johannesburg'
        }
        response = self.client.post('/api/employer/register', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Email already registered' in str(response.data)

    def test_employer_registration_invalid_password(self):
        data = {
            'email': 'employer@example.com',
            'password': '123456789',
            'company_name': 'TechCorp',
            'location': 'Johannesburg'
        }
        response = self.client.post('/api/employer/register', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_employer_registration_short_password(self):
        data = {
            'email': 'employer@example.com',
            'password': 'Pass12',
            'company_name': 'TechCorp',
            'location': 'Johannesburg'
        }
        response = self.client.post('/api/employer/register', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_employer_registration_missing_required_fields(self):
        data = {
            'email': 'employer@example.com',
            'password': 'SecurePass123',
        }
        response = self.client.post('/api/employer/register', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestEmployerProfile:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='employer@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg',
            industry='Technology'
        )
        self.employer_user = EmployerUser.objects.create(
            user=self.user,
            employer=self.employer,
            role='admin'
        )
        self.token = SessionToken.objects.create(
            user=self.user,
            token='test-token-123',
            expires_at='2099-12-31T23:59:59Z'
        )

    def test_get_employer_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test-token-123')
        response = self.client.get('/api/employer/profile')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'TechCorp'
        assert response.data['location'] == 'Johannesburg'
        assert response.data['email'] == 'employer@example.com'
        assert response.data['role'] == 'admin'

    def test_get_employer_profile_unauthenticated(self):
        response = self.client.get('/api/employer/profile')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_employer_profile_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        response = self.client.get('/api/employer/profile')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestTeamMembers:
    def setup_method(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email='admin@example.com',

            password='SecurePass123'
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        self.new_user = User.objects.create_user(
            email='newuser@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        self.admin_employer_user = EmployerUser.objects.create(
            user=self.admin_user,
            employer=self.employer,
            role='admin'
        )
        self.recruiter_employer_user = EmployerUser.objects.create(
            user=self.recruiter_user,
            employer=self.employer,
            role='recruiter'
        )
        self.admin_token = SessionToken.objects.create(
            user=self.admin_user,
            token='admin-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )

    def test_list_team_members(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.get('/api/employer/team-members')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['email'] in ['admin@example.com', 'recruiter@example.com']

    def test_add_team_member_as_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        data = {
            'email': 'newuser@example.com',
            'role': 'recruiter'
        }
        response = self.client.post('/api/employer/team-members', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newuser@example.com'
        assert response.data['role'] == 'recruiter'
        assert EmployerUser.objects.filter(user=self.new_user, employer=self.employer).exists()

    def test_add_team_member_as_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'email': 'newuser@example.com',
            'role': 'recruiter'
        }
        response = self.client.post('/api/employer/team-members', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_duplicate_team_member(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        data = {
            'email': 'recruiter@example.com',
            'role': 'viewer'
        }
        response = self.client.post('/api/employer/team-members', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already a team member' in str(response.data)

    def test_add_nonexistent_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        data = {
            'email': 'nonexistent@example.com',
            'role': 'recruiter'
        }
        response = self.client.post('/api/employer/team-members', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_team_member_role(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        data = {
            'role': 'viewer'
        }
        response = self.client.patch(f'/api/employer/team-members/{self.recruiter_employer_user.id}', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == 'viewer'
        self.recruiter_employer_user.refresh_from_db()
        assert self.recruiter_employer_user.role == 'viewer'

    def test_update_team_member_as_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'role': 'viewer'
        }
        response = self.client.patch(f'/api/employer/team-members/{self.admin_employer_user.id}', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_remove_team_member(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.delete(f'/api/employer/team-members/{self.recruiter_employer_user.id}')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not EmployerUser.objects.filter(id=self.recruiter_employer_user.id).exists()

    def test_remove_team_member_as_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.delete(f'/api/employer/team-members/{self.admin_employer_user.id}')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestJobPosting:
    def setup_method(self):
        from profiles.skill_models import Skill
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email='admin@example.com',

            password='SecurePass123'
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.admin_user, employer=self.employer, role='admin')
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')
        EmployerUser.objects.create(user=self.viewer_user, employer=self.employer, role='viewer')

        self.admin_token = SessionToken.objects.create(
            user=self.admin_user,
            token='admin-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.viewer_token = SessionToken.objects.create(
            user=self.viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.python_skill = Skill.objects.create(name='Python')
        self.react_skill = Skill.objects.create(name='React')

    def test_create_job_as_recruiter(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for a senior Python developer',
            'location': 'Johannesburg',
            'salary_min': 150000,
            'salary_max': 250000,
            'experience_level': 'senior',
            'required_skill_ids': [self.python_skill.id]
        }
        response = self.client.post('/api/employer/jobs', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Senior Python Developer'
        assert response.data['status'] == 'draft'
        from .job_models import Job
        assert Job.objects.filter(title='Senior Python Developer').exists()

    def test_create_job_as_viewer_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        data = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for a senior Python developer',
            'location': 'Johannesburg',
            'salary_min': 150000,
            'salary_max': 250000,
            'experience_level': 'senior'
        }
        response = self.client.post('/api/employer/jobs', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_job_invalid_salary(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for a senior Python developer',
            'location': 'Johannesburg',
            'salary_min': 250000,
            'salary_max': 150000,
            'experience_level': 'senior'
        }
        response = self.client.post('/api/employer/jobs', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_employer_jobs(self):
        from .job_models import Job
        Job.objects.create(
            employer=self.employer,
            title='Python Developer',
            description='Looking for a Python dev',
            location='Johannesburg',
            salary_min=100000,
            salary_max=200000,
            experience_level='mid',
            status='draft'
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.get('/api/employer/jobs')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Python Developer'

    def test_get_job_detail(self):
        from .job_models import Job
        job = Job.objects.create(
            employer=self.employer,
            title='Python Developer',
            description='Looking for a Python dev',
            location='Johannesburg',
            salary_min=100000,
            salary_max=200000,
            experience_level='mid',
            status='draft'
        )
        response = self.client.get(f'/api/employer/jobs/{job.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Python Developer'

    def test_update_job_as_recruiter(self):
        from .job_models import Job
        job = Job.objects.create(
            employer=self.employer,
            title='Python Developer',
            description='Looking for a Python dev',
            location='Johannesburg',
            salary_min=100000,
            salary_max=200000,
            experience_level='mid',
            status='draft'
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'title': 'Senior Python Developer',
            'salary_min': 150000
        }
        response = self.client.patch(f'/api/employer/jobs/{job.id}', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Senior Python Developer'
        assert response.data['salary_min'] == 150000


@pytest.mark.django_db
class TestJobManagement:
    def setup_method(self):
        from .job_models import Job
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email='admin@example.com',

            password='SecurePass123'
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.admin_user, employer=self.employer, role='admin')
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')
        EmployerUser.objects.create(user=self.viewer_user, employer=self.employer, role='viewer')

        self.admin_token = SessionToken.objects.create(
            user=self.admin_user,
            token='admin-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.viewer_token = SessionToken.objects.create(
            user=self.viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title='Python Developer',
            description='Looking for a Python dev',
            location='Johannesburg',
            salary_min=100000,
            salary_max=200000,
            experience_level='mid',
            status='draft'
        )

    def test_publish_job(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.post(f'/api/employer/jobs/{self.job.id}/publish')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'published'
        self.job.refresh_from_db()
        assert self.job.status == 'published'

    def test_publish_job_as_viewer_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        response = self.client.post(f'/api/employer/jobs/{self.job.id}/publish')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_close_job(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.post(f'/api/employer/jobs/{self.job.id}/close')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'closed'
        self.job.refresh_from_db()
        assert self.job.status == 'closed'

    def test_unpublish_job(self):
        from .job_models import Job
        job = Job.objects.create(
            employer=self.employer,
            title='React Developer',
            description='Looking for React dev',
            location='Johannesburg',
            salary_min=100000,
            salary_max=200000,
            experience_level='mid',
            status='published'
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.post(f'/api/employer/jobs/{job.id}/unpublish')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'draft'
        job.refresh_from_db()
        assert job.status == 'draft'

    def test_get_job_metrics(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.get(f'/api/employer/jobs/{self.job.id}/metrics')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['job_id'] == self.job.id
        assert response.data['title'] == 'Python Developer'
        assert 'applications_count' in response.data
        assert 'views_count' in response.data

    def test_publish_nonexistent_job(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.post('/api/employer/jobs/9999/publish')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCandidateSearch:
    def setup_method(self):
        from profiles.models import CandidateProfile
        from profiles.availability_models import Availability
        self.client = APIClient()
        
        self.employer_user = User.objects.create_user(
            email='employer@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        self.employer_recruiter = EmployerUser.objects.create(
            user=self.employer_user,
            employer=self.employer,
            role='recruiter'
        )
        self.employer_token = SessionToken.objects.create(
            user=self.employer_user,
            token='employer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.python_skill = Skill.objects.create(name='Python')
        self.react_skill = Skill.objects.create(name='React')

        self.candidate1_user = User.objects.create_user(
            email='candidate1@example.com',

            password='SecurePass123'
        )
        self.candidate1 = CandidateProfile.objects.create(
            user=self.candidate1_user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            phone='0721234567',
            status='active'
        )
        self.candidate1.skills.add(self.python_skill)
        Availability.objects.create(
            profile=self.candidate1,
            available_from_month=1,
            available_from_year=2026,
            employment_type='full-time',
            salary_min=100000,
            salary_max=200000
        )

        self.candidate2_user = User.objects.create_user(
            email='candidate2@example.com',

            password='SecurePass123'
        )
        self.candidate2 = CandidateProfile.objects.create(
            user=self.candidate2_user,
            first_name='Jane',
            last_name='Smith',
            location='Cape Town',
            phone='0729876543',
            status='active'
        )
        self.candidate2.skills.add(self.react_skill)
        Availability.objects.create(
            profile=self.candidate2,
            available_from_month=2,
            available_from_year=2026,
            employment_type='contract',
            salary_min=80000,
            salary_max=150000
        )

        self.paused_candidate_user = User.objects.create_user(
            email='paused@example.com',

            password='SecurePass123'
        )
        self.paused_candidate = CandidateProfile.objects.create(
            user=self.paused_candidate_user,
            first_name='Bob',
            last_name='Johnson',
            location='Johannesburg',
            status='paused'
        )

    def test_search_all_active_candidates(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer employer-token')
        response = self.client.get('/api/employer/candidates/search')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_search_candidates_by_location(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer employer-token')
        response = self.client.get('/api/employer/candidates/search?location=Cape+Town')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['first_name'] == 'Jane'

    def test_search_candidates_by_skills(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer employer-token')
        response = self.client.get(f'/api/employer/candidates/search?skills={self.python_skill.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['first_name'] == 'John'

    def test_search_candidates_by_salary_range(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer employer-token')
        response = self.client.get('/api/employer/candidates/search?salary_min=90000&salary_max=180000')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['first_name'] == 'Jane'

    def test_search_candidates_by_employment_type(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer employer-token')
        response = self.client.get('/api/employer/candidates/search?employment_type=contract')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['first_name'] == 'Jane'

    def test_paused_candidates_not_visible(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer employer-token')
        response = self.client.get('/api/employer/candidates/search')
        
        assert response.status_code == status.HTTP_200_OK
        names = [c['first_name'] for c in response.data['results']]
        assert 'Bob' not in names

    def test_search_requires_authentication(self):
        response = self.client.get('/api/employer/candidates/search')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_pagination(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer employer-token')
        response = self.client.get('/api/employer/candidates/search?page=1')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['page'] == 1
        assert response.data['page_size'] == 20


@pytest.mark.django_db
class TestCandidateShortlist:
    def setup_method(self):
        from employers.shortlist_models import CandidateShortlist
        from profiles.models import CandidateProfile
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',

            password='SecurePass123'
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.admin_user, employer=self.employer, role='admin')
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')

        self.admin_token = SessionToken.objects.create(
            user=self.admin_user,
            token='admin-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.candidate1_user = User.objects.create_user(
            email='candidate1@example.com',

            password='SecurePass123'
        )
        self.candidate1 = CandidateProfile.objects.create(
            user=self.candidate1_user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='active'
        )

        self.candidate2_user = User.objects.create_user(
            email='candidate2@example.com',

            password='SecurePass123'
        )
        self.candidate2 = CandidateProfile.objects.create(
            user=self.candidate2_user,
            first_name='Jane',
            last_name='Smith',
            location='Cape Town',
            status='active'
        )

    def test_add_candidate_to_shortlist(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'candidate_id': self.candidate1.id
        }
        response = self.client.post('/api/employer/shortlist', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['first_name'] == 'John'
        from employers.shortlist_models import CandidateShortlist
        assert CandidateShortlist.objects.filter(
            employer=self.employer,
            candidate=self.candidate1
        ).exists()

    def test_add_duplicate_to_shortlist(self):
        from employers.shortlist_models import CandidateShortlist
        CandidateShortlist.objects.create(
            employer=self.employer,
            candidate=self.candidate1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'candidate_id': self.candidate1.id
        }
        response = self.client.post('/api/employer/shortlist', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already shortlisted' in str(response.data)

    def test_list_shortlist(self):
        from employers.shortlist_models import CandidateShortlist
        CandidateShortlist.objects.create(employer=self.employer, candidate=self.candidate1)
        CandidateShortlist.objects.create(employer=self.employer, candidate=self.candidate2)
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.get('/api/employer/shortlist')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['first_name'] in ['John', 'Jane']

    def test_remove_from_shortlist(self):
        from employers.shortlist_models import CandidateShortlist
        shortlist = CandidateShortlist.objects.create(
            employer=self.employer,
            candidate=self.candidate1
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.delete(f'/api/employer/shortlist/{shortlist.id}')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CandidateShortlist.objects.filter(id=shortlist.id).exists()

    def test_shortlist_requires_recruiter_role(self):
        from employers.shortlist_models import CandidateShortlist
        viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        EmployerUser.objects.create(user=viewer_user, employer=self.employer, role='viewer')
        viewer_token = SessionToken.objects.create(
            user=viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        data = {
            'candidate_id': self.candidate1.id
        }
        response = self.client.post('/api/employer/shortlist', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestApplicationReview:
    def setup_method(self):
        from jobs.application_models import JobApplication
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            email='admin@example.com',

            password='SecurePass123'
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.admin_user, employer=self.employer, role='admin')
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')
        EmployerUser.objects.create(user=self.viewer_user, employer=self.employer, role='viewer')

        self.admin_token = SessionToken.objects.create(
            user=self.admin_user,
            token='admin-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.viewer_token = SessionToken.objects.create(
            user=self.viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title='Senior Python Developer',
            description='We are looking for a senior Python developer',
            location='Johannesburg',
            salary_min=150000,
            salary_max=250000,
            experience_level='senior',
            status='published'
        )

        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',

            password='SecurePass123'
        )
        self.candidate = CandidateProfile.objects.create(
            user=self.candidate_user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='active'
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            cover_letter='I am interested in this position.'
        )

    def test_list_applications_as_recruiter(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/applications')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['candidate_first_name'] == 'John'
        assert response.data['results'][0]['job_title'] == 'Senior Python Developer'

    def test_list_applications_as_viewer_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        response = self.client.get('/api/employer/applications')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_applications_by_status(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/applications?status=applied')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'applied'

    def test_filter_applications_by_job_id(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get(f'/api/employer/applications?job_id={self.job.id}')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_get_application_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get(f'/api/employer/applications/{self.application.id}')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['candidate_first_name'] == 'John'
        assert response.data['candidate_last_name'] == 'Doe'
        assert response.data['job_title'] == 'Senior Python Developer'
        assert response.data['cover_letter'] == 'I am interested in this position.'

    def test_review_application(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'status': 'reviewed'
        }
        response = self.client.patch(f'/api/employer/applications/{self.application.id}', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'reviewed'
        self.application.refresh_from_db()
        assert self.application.status == 'reviewed'
        assert self.application.reviewed_at is not None

    def test_reject_application_with_reason(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'status': 'rejected',
            'rejection_reason': 'Does not meet experience requirements'
        }
        response = self.client.patch(f'/api/employer/applications/{self.application.id}', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'rejected'
        self.application.refresh_from_db()
        assert self.application.status == 'rejected'

    def test_reject_without_reason_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'status': 'rejected'
        }
        response = self.client.patch(f'/api/employer/applications/{self.application.id}', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_review_as_viewer_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        data = {
            'status': 'reviewed'
        }
        response = self.client.patch(f'/api/employer/applications/{self.application.id}', data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_review_other_employer_application(self):
        other_employer = Employer.objects.create(
            name='OtherCorp',
            location='Cape Town'
        )
        other_job = Job.objects.create(
            employer=other_employer,
            title='React Developer',
            description='Looking for React dev',
            location='Cape Town',
            salary_min=100000,
            salary_max=200000,
            experience_level='mid',
            status='published'
        )
        other_application = JobApplication.objects.create(
            candidate=self.candidate,
            job=other_job
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'status': 'reviewed'
        }
        response = self.client.patch(f'/api/employer/applications/{other_application.id}', data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pagination(self):
        from jobs.application_models import JobApplication
        for i in range(25):
            Job.objects.create(
                employer=self.employer,
                title=f'Job {i}',
                description='Test',
                location='Johannesburg',
                salary_min=100000,
                salary_max=200000,
                experience_level='mid',
                status='published'
            )
        for job in Job.objects.all()[1:26]:
            JobApplication.objects.create(candidate=self.candidate, job=job)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/applications?page=1')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['page'] == 1
        assert response.data['count'] >= 25


@pytest.mark.django_db
class TestApplicationShortlist:
    def setup_method(self):
        from jobs.application_models import JobApplication
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            email='admin@example.com',

            password='SecurePass123'
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.admin_user, employer=self.employer, role='admin')
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')
        EmployerUser.objects.create(user=self.viewer_user, employer=self.employer, role='viewer')

        self.admin_token = SessionToken.objects.create(
            user=self.admin_user,
            token='admin-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.viewer_token = SessionToken.objects.create(
            user=self.viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title='Senior Python Developer',
            description='We are looking for a senior Python developer',
            location='Johannesburg',
            salary_min=150000,
            salary_max=250000,
            experience_level='senior',
            status='published'
        )

        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',

            password='SecurePass123'
        )
        self.candidate = CandidateProfile.objects.create(
            user=self.candidate_user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='active'
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            cover_letter='I am interested in this position.'
        )

    def test_add_application_to_shortlist(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'application_id': self.application.id
        }
        response = self.client.post('/api/employer/application-shortlist', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['candidate_first_name'] == 'John'
        assert response.data['job_title'] == 'Senior Python Developer'
        from employers.application_shortlist_models import ApplicationShortlist
        assert ApplicationShortlist.objects.filter(
            employer=self.employer,
            application=self.application
        ).exists()

    def test_add_duplicate_to_application_shortlist(self):
        from employers.application_shortlist_models import ApplicationShortlist
        ApplicationShortlist.objects.create(
            employer=self.employer,
            application=self.application
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'application_id': self.application.id
        }
        response = self.client.post('/api/employer/application-shortlist', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already shortlisted' in str(response.data)

    def test_add_to_shortlist_as_viewer_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        data = {
            'application_id': self.application.id
        }
        response = self.client.post('/api/employer/application-shortlist', data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_application_shortlist(self):
        from employers.application_shortlist_models import ApplicationShortlist
        ApplicationShortlist.objects.create(employer=self.employer, application=self.application)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/application-shortlist')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['candidate_first_name'] == 'John'

    def test_remove_from_application_shortlist(self):
        from employers.application_shortlist_models import ApplicationShortlist
        shortlist = ApplicationShortlist.objects.create(
            employer=self.employer,
            application=self.application
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.delete(f'/api/employer/application-shortlist/{shortlist.id}')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ApplicationShortlist.objects.filter(id=shortlist.id).exists()

    def test_cannot_shortlist_other_employer_application(self):
        other_employer = Employer.objects.create(
            name='OtherCorp',
            location='Cape Town'
        )
        other_job = Job.objects.create(
            employer=other_employer,
            title='React Developer',
            description='Looking for React dev',
            location='Cape Town',
            salary_min=100000,
            salary_max=200000,
            experience_level='mid',
            status='published'
        )
        other_application = JobApplication.objects.create(
            candidate=self.candidate,
            job=other_job
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        data = {
            'application_id': other_application.id
        }
        response = self.client.post('/api/employer/application-shortlist', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'does not belong' in str(response.data)

    def test_application_shortlist_pagination(self):
        from employers.application_shortlist_models import ApplicationShortlist
        from jobs.application_models import JobApplication
        for i in range(25):
            job = Job.objects.create(
                employer=self.employer,
                title=f'Job {i}',
                description='Test',
                location='Johannesburg',
                salary_min=100000,
                salary_max=200000,
                experience_level='mid',
                status='published'
            )
            app = JobApplication.objects.create(candidate=self.candidate, job=job)
            ApplicationShortlist.objects.create(employer=self.employer, application=app)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/application-shortlist?page=1')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['page'] == 1
        assert response.data['count'] >= 25


@pytest.mark.django_db
class TestCommissionCalculation:
    def setup_method(self):
        from jobs.application_models import JobApplication
        from jobs.hire_confirmation_models import HireConfirmation
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            email='admin@example.com',

            password='SecurePass123'
        )
        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.admin_user, employer=self.employer, role='admin')
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')

        self.admin_token = SessionToken.objects.create(
            user=self.admin_user,
            token='admin-token',
            expires_at='2099-12-31T23:59:59Z'
        )
        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title='Senior Python Developer',
            description='Looking for senior Python dev',
            location='Johannesburg',
            salary_min=150000,
            salary_max=250000,
            experience_level='senior',
            status='published'
        )

        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',

            password='SecurePass123'
        )
        self.candidate = CandidateProfile.objects.create(
            user=self.candidate_user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='active'
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            cover_letter='Interested in this role'
        )

        self.hire_confirmation = HireConfirmation.objects.create(
            application=self.application,
            employer_confirmed=True,
            status='pending_candidate'
        )

    def test_commission_auto_created_on_hire(self):
        from employers.commission_models import Commission
        self.hire_confirmation.candidate_confirmed = True
        self.hire_confirmation.status = 'confirmed'
        self.hire_confirmation.save()

        commission = Commission.objects.filter(hire_confirmation=self.hire_confirmation).first()
        assert commission is not None
        assert commission.employer == self.employer
        assert commission.amount == 15000
        assert commission.rate == 10.00
        assert commission.status == 'pending'

    def test_commission_calculation_correct(self):
        from employers.commission_models import Commission
        self.hire_confirmation.candidate_confirmed = True
        self.hire_confirmation.status = 'confirmed'
        self.hire_confirmation.save()

        commission = Commission.objects.get(hire_confirmation=self.hire_confirmation)
        expected_amount = (150000 * 10.00) / 100
        assert float(commission.amount) == expected_amount

    def test_employer_views_commissions(self):
        from employers.commission_models import Commission
        self.hire_confirmation.candidate_confirmed = True
        self.hire_confirmation.status = 'confirmed'
        self.hire_confirmation.save()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/commissions')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['summary']['pending_amount'] == 15000
        assert response.data['results'][0]['candidate_first_name'] == 'John'
        assert response.data['results'][0]['job_title'] == 'Senior Python Developer'

    def test_admin_views_all_commissions(self):
        from employers.commission_models import Commission
        self.hire_confirmation.candidate_confirmed = True
        self.hire_confirmation.status = 'confirmed'
        self.hire_confirmation.save()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer admin-token')
        response = self.client.get('/api/admin/commissions')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['total_amount'] == 15000

    def test_filter_commissions_by_status(self):
        from employers.commission_models import Commission
        self.hire_confirmation.candidate_confirmed = True
        self.hire_confirmation.status = 'confirmed'
        self.hire_confirmation.save()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/commissions?status=pending')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'pending'

    def test_commission_summary_correct(self):
        from employers.commission_models import Commission
        self.hire_confirmation.candidate_confirmed = True
        self.hire_confirmation.status = 'confirmed'
        self.hire_confirmation.save()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/commissions')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['summary']['pending_amount'] == 15000
        assert response.data['summary']['invoiced_amount'] == 0
        assert response.data['summary']['paid_amount'] == 0
        assert response.data['summary']['total_amount'] == 15000

    def test_non_recruiter_cannot_view_commissions(self):
        viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        EmployerUser.objects.create(user=viewer_user, employer=self.employer, role='viewer')
        viewer_token = SessionToken.objects.create(
            user=viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        response = self.client.get('/api/employer/commissions')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_admin_cannot_view_admin_commissions(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/admin/commissions')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_pagination_commissions(self):
        from employers.commission_models import Commission
        for i in range(25):
            job = Job.objects.create(
                employer=self.employer,
                title=f'Job {i}',
                description='Test',
                location='Johannesburg',
                salary_min=100000 + (i * 10000),
                salary_max=200000,
                experience_level='mid',
                status='published'
            )
            app = JobApplication.objects.create(candidate=self.candidate, job=job)
            hire = HireConfirmation.objects.create(
                application=app,
                employer_confirmed=True,
                status='confirmed'
            )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/commissions?page=1')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20
        assert response.data['page'] == 1
        assert response.data['count'] >= 25

    def test_sort_commissions_by_amount(self):
        from employers.commission_models import Commission
        self.hire_confirmation.candidate_confirmed = True
        self.hire_confirmation.status = 'confirmed'
        self.hire_confirmation.save()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.get('/api/employer/commissions?sort=-amount')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1


@pytest.mark.django_db
class TestInvoiceGeneration:
    def setup_method(self):
        from jobs.application_models import JobApplication
        from jobs.hire_confirmation_models import HireConfirmation
        from employers.commission_models import Commission
        self.client = APIClient()

        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')

        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title='Senior Python Developer',
            description='Looking for senior Python dev',
            location='Johannesburg',
            salary_min=150000,
            salary_max=250000,
            experience_level='senior',
            status='published'
        )

        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',

            password='SecurePass123'
        )
        self.candidate = CandidateProfile.objects.create(
            user=self.candidate_user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='active'
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            cover_letter='Interested'
        )

        self.hire = HireConfirmation.objects.create(
            application=self.application,
            employer_confirmed=True,
            status='confirmed'
        )

    def test_generate_invoice_from_pending_commissions(self):
        from employers.invoice_models import Invoice
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.post('/api/employer/invoices')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['invoice_number'].startswith('INV-2026-')
        assert float(response.data['total_amount']) == 15000.00
        assert response.data['status'] == 'issued'
        assert len(response.data['line_items']) == 1
        assert Invoice.objects.filter(employer=self.employer).exists()

    def test_invoice_has_line_items(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.post('/api/employer/invoices')

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['line_items']) == 1
        line_item = response.data['line_items'][0]
        assert 'John Doe' in line_item['candidate_name']
        assert 'Senior Python Developer' in line_item['job_title']
        assert float(line_item['amount']) == 15000.00

    def test_commission_status_updated_on_invoice_generation(self):
        from employers.commission_models import Commission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        self.client.post('/api/employer/invoices')

        commission = Commission.objects.get(hire_confirmation=self.hire)
        assert commission.status == 'invoiced'
        assert commission.invoiced_at is not None

    def test_cannot_invoice_without_pending_commissions(self):
        from employers.commission_models import Commission
        commission = Commission.objects.get(hire_confirmation=self.hire)
        commission.status = 'invoiced'
        commission.save()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.post('/api/employer/invoices')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'No pending commissions' in str(response.data)

    def test_list_employer_invoices(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        self.client.post('/api/employer/invoices')

        response = self.client.get('/api/employer/invoices')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['total_amount'] == 15000.00
        assert response.data['results'][0]['status'] == 'issued'

    def test_get_invoice_detail(self):
        from employers.invoice_models import Invoice
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        self.client.post('/api/employer/invoices')

        invoice = Invoice.objects.get(employer=self.employer)
        response = self.client.get(f'/api/employer/invoices/{invoice.id}')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['invoice_number'] == invoice.invoice_number
        assert len(response.data['line_items']) == 1

    def test_invoice_number_sequential(self):
        from employers.invoice_models import Invoice
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        
        response1 = self.client.post('/api/employer/invoices')
        invoice1_number = response1.data['invoice_number']

        for i in range(2):
            job = Job.objects.create(
                employer=self.employer,
                title=f'Job {i}',
                description='Test',
                location='Johannesburg',
                salary_min=100000,
                salary_max=200000,
                experience_level='mid',
                status='published'
            )
            app = JobApplication.objects.create(candidate=self.candidate, job=job)
            hire = HireConfirmation.objects.create(
                application=app,
                employer_confirmed=True,
                status='confirmed'
            )

        response2 = self.client.post('/api/employer/invoices')
        invoice2_number = response2.data['invoice_number']

        assert invoice1_number != invoice2_number
        assert invoice2_number > invoice1_number

    def test_invoice_due_date_net_30(self):
        from datetime import timedelta
        from django.utils import timezone
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.post('/api/employer/invoices')

        due_date = response.data['due_date']
        issued_date = response.data['date_issued']
        
        assert due_date is not None
        assert issued_date is not None

    def test_filter_invoices_by_status(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        self.client.post('/api/employer/invoices')

        response = self.client.get('/api/employer/invoices?status=issued')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_pagination_invoices(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        for i in range(25):
            job = Job.objects.create(
                employer=self.employer,
                title=f'Job {i}',
                description='Test',
                location='Johannesburg',
                salary_min=100000 + (i * 10000),
                salary_max=200000,
                experience_level='mid',
                status='published'
            )
            app = JobApplication.objects.create(candidate=self.candidate, job=job)
            hire = HireConfirmation.objects.create(
                application=app,
                employer_confirmed=True,
                status='confirmed'
            )

        self.client.post('/api/employer/invoices')

        response = self.client.get('/api/employer/invoices?page=1')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert response.data['page'] == 1

    def test_non_recruiter_cannot_generate_invoice(self):
        viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        EmployerUser.objects.create(user=viewer_user, employer=self.employer, role='viewer')
        viewer_token = SessionToken.objects.create(
            user=viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        response = self.client.post('/api/employer/invoices')

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestPaymentProcessing:
    def setup_method(self):
        from jobs.application_models import JobApplication
        from jobs.hire_confirmation_models import HireConfirmation
        from employers.invoice_models import Invoice
        self.client = APIClient()

        self.recruiter_user = User.objects.create_user(
            email='recruiter@example.com',

            password='SecurePass123'
        )
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )
        EmployerUser.objects.create(user=self.recruiter_user, employer=self.employer, role='recruiter')

        self.recruiter_token = SessionToken.objects.create(
            user=self.recruiter_user,
            token='recruiter-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title='Senior Python Developer',
            description='Looking for senior Python dev',
            location='Johannesburg',
            salary_min=150000,
            salary_max=250000,
            experience_level='senior',
            status='published'
        )

        self.candidate_user = User.objects.create_user(
            email='candidate@example.com',

            password='SecurePass123'
        )
        self.candidate = CandidateProfile.objects.create(
            user=self.candidate_user,
            first_name='John',
            last_name='Doe',
            location='Johannesburg',
            status='active'
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            cover_letter='Interested'
        )

        self.hire = HireConfirmation.objects.create(
            application=self.application,
            employer_confirmed=True,
            status='confirmed'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer recruiter-token')
        response = self.client.post('/api/employer/invoices')
        self.invoice_id = response.data['id']

    def test_initiate_payment(self):
        from employers.payment_models import Payment
        data = {
            'payment_method': 'credit_card'
        }
        response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert response.data['amount'] == 15000.00
        assert response.data['payment_url'] is not None
        assert Payment.objects.filter(invoice_id=self.invoice_id).exists()

    def test_payment_has_reference(self):
        data = {
            'payment_method': 'credit_card'
        }
        response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['payment_reference'].startswith('PAY-')

    def test_payment_callback_success(self):
        from employers.payment_models import Payment
        from employers.invoice_models import Invoice
        
        data = {'payment_method': 'credit_card'}
        payment_response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')
        payment_reference = payment_response.data['payment_reference']

        callback_data = {
            'payment_reference': payment_reference,
            'status': 'completed'
        }
        callback_response = self.client.post('/api/webhooks/payment-callback', callback_data, format='json')

        assert callback_response.status_code == status.HTTP_200_OK
        
        payment = Payment.objects.get(payment_reference=payment_reference)
        assert payment.status == 'completed'
        assert payment.completed_at is not None

    def test_invoice_status_updated_on_payment(self):
        from employers.invoice_models import Invoice
        data = {'payment_method': 'credit_card'}
        payment_response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')
        payment_reference = payment_response.data['payment_reference']

        callback_data = {
            'payment_reference': payment_reference,
            'status': 'completed'
        }
        self.client.post('/api/webhooks/payment-callback', callback_data, format='json')

        invoice = Invoice.objects.get(id=self.invoice_id)
        assert invoice.status == 'paid'
        assert invoice.paid_at is not None

    def test_commission_status_updated_on_payment(self):
        from employers.commission_models import Commission
        data = {'payment_method': 'credit_card'}
        payment_response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')
        payment_reference = payment_response.data['payment_reference']

        callback_data = {
            'payment_reference': payment_reference,
            'status': 'completed'
        }
        self.client.post('/api/webhooks/payment-callback', callback_data, format='json')

        commission = Commission.objects.get(hire_confirmation=self.hire)
        assert commission.status == 'paid'
        assert commission.paid_at is not None

    def test_payment_callback_failure(self):
        from employers.payment_models import Payment
        data = {'payment_method': 'credit_card'}
        payment_response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')
        payment_reference = payment_response.data['payment_reference']

        callback_data = {
            'payment_reference': payment_reference,
            'status': 'failed'
        }
        callback_response = self.client.post('/api/webhooks/payment-callback', callback_data, format='json')

        assert callback_response.status_code == status.HTTP_200_OK
        
        payment = Payment.objects.get(payment_reference=payment_reference)
        assert payment.status == 'failed'

    def test_cannot_pay_paid_invoice(self):
        from employers.invoice_models import Invoice
        invoice = Invoice.objects.get(id=self.invoice_id)
        invoice.status = 'paid'
        invoice.save()

        data = {'payment_method': 'credit_card'}
        response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_employer_payments(self):
        data = {'payment_method': 'credit_card'}
        self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')

        response = self.client.get('/api/employer/payments')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['amount'] == 15000.00

    def test_filter_payments_by_status(self):
        data = {'payment_method': 'credit_card'}
        self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')

        response = self.client.get('/api/employer/payments?status=pending')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'pending'

    def test_non_recruiter_cannot_initiate_payment(self):
        viewer_user = User.objects.create_user(
            email='viewer@example.com',

            password='SecurePass123'
        )
        EmployerUser.objects.create(user=viewer_user, employer=self.employer, role='viewer')
        viewer_token = SessionToken.objects.create(
            user=viewer_user,
            token='viewer-token',
            expires_at='2099-12-31T23:59:59Z'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer viewer-token')
        data = {'payment_method': 'credit_card'}
        response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_webhook_callback_idempotent(self):
        from employers.payment_models import Payment
        data = {'payment_method': 'credit_card'}
        payment_response = self.client.post(f'/api/employer/invoices/{self.invoice_id}/pay', data, format='json')
        payment_reference = payment_response.data['payment_reference']

        callback_data = {
            'payment_reference': payment_reference,
            'status': 'completed'
        }
        response1 = self.client.post('/api/webhooks/payment-callback', callback_data, format='json')
        response2 = self.client.post('/api/webhooks/payment-callback', callback_data, format='json')

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        payment = Payment.objects.get(payment_reference=payment_reference)
        assert payment.status == 'completed'
