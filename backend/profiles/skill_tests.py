import pytest
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from .models import CandidateProfile
from .skill_models import Skill, CandidateSkill


@pytest.mark.django_db
class TestSkillList:
    def setup_method(self):
        self.client = APIClient()
        self.skills_url = '/api/skills'
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        Skill.objects.create(name='Python')
        Skill.objects.create(name='React')
        Skill.objects.create(name='AWS')

    def test_get_skills_list(self):
        response = self.client.get(self.skills_url)
        assert response.status_code == 200
        assert len(response.data) == 3
        skill_names = [s['name'] for s in response.data]
        assert 'Python' in skill_names
        assert 'React' in skill_names
        assert 'AWS' in skill_names

    def test_get_skills_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.skills_url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestCandidateSkills:
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
        self.skills_url = f'/api/profiles/{self.profile.id}/skills'
        self.client.force_authenticate(user=self.user)
        self.skill1 = Skill.objects.create(name='Python')
        self.skill2 = Skill.objects.create(name='React')
        self.skill3 = Skill.objects.create(name='AWS')

    def test_add_skills_success(self):
        response = self.client.post(self.skills_url, {
            'skill_ids': [self.skill1.id, self.skill2.id]
        })
        assert response.status_code == 200
        assert len(response.data) == 2
        skill_names = [s['name'] for s in response.data]
        assert 'Python' in skill_names
        assert 'React' in skill_names
        assert CandidateSkill.objects.filter(profile=self.profile).count() == 2

    def test_add_skills_no_skills(self):
        response = self.client.post(self.skills_url, {
            'skill_ids': []
        })
        assert response.status_code == 400
        assert 'At least 1 skill is required' in str(response.data)

    def test_add_skills_max_10(self):
        skills = [Skill.objects.create(name=f'Skill{i}') for i in range(11)]
        response = self.client.post(self.skills_url, {
            'skill_ids': [s.id for s in skills]
        })
        assert response.status_code == 400
        assert 'Maximum 10 skills allowed' in str(response.data)

    def test_add_skills_exactly_10(self):
        skills = [Skill.objects.create(name=f'Skill{i}') for i in range(10)]
        response = self.client.post(self.skills_url, {
            'skill_ids': [s.id for s in skills]
        })
        assert response.status_code == 200
        assert len(response.data) == 10

    def test_get_candidate_skills(self):
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill1)
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill2)
        response = self.client.get(self.skills_url)
        assert response.status_code == 200
        assert len(response.data) == 2
        skill_names = [s['name'] for s in response.data]
        assert 'Python' in skill_names
        assert 'React' in skill_names

    def test_get_candidate_skills_empty(self):
        response = self.client.get(self.skills_url)
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_replace_skills(self):
        CandidateSkill.objects.create(profile=self.profile, skill=self.skill1)
        response = self.client.post(self.skills_url, {
            'skill_ids': [self.skill2.id, self.skill3.id]
        })
        assert response.status_code == 200
        assert len(response.data) == 2
        skill_names = [s['name'] for s in response.data]
        assert 'Python' not in skill_names
        assert 'React' in skill_names
        assert 'AWS' in skill_names

    def test_add_skills_not_own_profile(self):
        other_user = User.objects.create_user(

            email='other@example.com',
            password='password123'
        )
        other_user.is_active = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.skills_url, {
            'skill_ids': [self.skill1.id]
        })
        assert response.status_code == 403
        assert 'You can only update your own profile' in str(response.data)

    def test_add_skills_profile_not_found(self):
        response = self.client.post('/api/profiles/99999/skills', {
            'skill_ids': [self.skill1.id]
        })
        assert response.status_code == 404

    def test_add_skills_invalid_skill_id(self):
        response = self.client.post(self.skills_url, {
            'skill_ids': [99999]
        })
        assert response.status_code == 400
