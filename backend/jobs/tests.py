import pytest
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from rest_framework import status
from employers.models import Employer, EmployerUser
from employers.job_models import Job
from profiles.skill_models import Skill
from accounts.models import SessionToken


@pytest.mark.django_db
class TestJobSearch:
    def setup_method(self):
        self.client = APIClient()
        self.employer = Employer.objects.create(
            name='TechCorp',
            location='Johannesburg'
        )

        self.python_skill = Skill.objects.create(name='Python')
        self.react_skill = Skill.objects.create(name='React')
        self.aws_skill = Skill.objects.create(name='AWS')

        self.published_job1 = Job.objects.create(
            employer=self.employer,
            title='Senior Python Developer',
            description='We are looking for a senior Python developer with AWS experience',
            location='Johannesburg',
            salary_min=150000,
            salary_max=250000,
            experience_level='senior',
            status='published'
        )
        self.published_job1.required_skills.create(skill=self.python_skill)
        self.published_job1.required_skills.create(skill=self.aws_skill)

        self.published_job2 = Job.objects.create(
            employer=self.employer,
            title='React Developer',
            description='We need a React developer for our frontend team',
            location='Cape Town',
            salary_min=100000,
            salary_max=180000,
            experience_level='mid',
            status='published'
        )
        self.published_job2.required_skills.create(skill=self.react_skill)

        self.draft_job = Job.objects.create(
            employer=self.employer,
            title='DevOps Engineer',
            description='We are hiring a DevOps engineer',
            location='Johannesburg',
            salary_min=120000,
            salary_max=200000,
            experience_level='mid',
            status='draft'
        )

    def test_search_all_published_jobs(self):
        response = self.client.get('/api/jobs/search')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_search_jobs_by_title(self):
        response = self.client.get('/api/jobs/search?search=Python')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Senior Python Developer'

    def test_search_jobs_by_location(self):
        response = self.client.get('/api/jobs/search?location=Cape+Town')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['location'] == 'Cape Town'

    def test_search_jobs_by_salary_range(self):
        response = self.client.get('/api/jobs/search?salary_min=140000&salary_max=200000')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Senior Python Developer'

    def test_search_jobs_by_skills(self):
        response = self.client.get(f'/api/jobs/search?skills={self.python_skill.id}&skills={self.aws_skill.id}')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Senior Python Developer'

    def test_draft_jobs_not_visible(self):
        response = self.client.get('/api/jobs/search')

        assert response.status_code == status.HTTP_200_OK
        titles = [job['title'] for job in response.data['results']]
        assert 'DevOps Engineer' not in titles

    def test_search_with_pagination(self):
        for i in range(25):
            Job.objects.create(
                employer=self.employer,
                title=f'Job {i}',
                description='Test job',
                location='Johannesburg',
                salary_min=100000,
                salary_max=200000,
                experience_level='mid',
                status='published'
            )

        response = self.client.get('/api/jobs/search?page=1')
        assert response.data['page'] == 1
        assert len(response.data['results']) == 20

        response = self.client.get('/api/jobs/search?page=2')
        assert response.data['page'] == 2
        assert len(response.data['results']) == 7

    def test_search_sort_by_newest(self):
        response = self.client.get('/api/jobs/search?sort=-created_at')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['title'] == 'React Developer'

    def test_search_sort_by_oldest(self):
        response = self.client.get('/api/jobs/search?sort=created_at')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['title'] == 'Senior Python Developer'

    def test_search_combined_filters(self):
        response = self.client.get('/api/jobs/search?search=Python&location=Johannesburg&salary_min=140000')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Senior Python Developer'
