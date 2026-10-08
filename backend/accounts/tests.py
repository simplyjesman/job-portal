import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import timedelta
from .models import EmailVerificationToken, PasswordResetToken, SessionToken

User = get_user_model()


@pytest.mark.django_db
class TestSignup:
    def setup_method(self):
        self.client = APIClient()
        self.signup_url = '/api/auth/signup'

    def test_signup_success(self):
        response = self.client.post(self.signup_url, {
            'email': 'candidate@example.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
        })
        assert response.status_code == 201
        assert response.data['message'] == 'Signup successful. Check your email to verify.'
        assert User.objects.filter(email='candidate@example.com').exists()
        user = User.objects.get(email='candidate@example.com')
        assert not user.is_active
        assert len(mail.outbox) == 1
        assert 'Verify your email' in mail.outbox[0].subject

    def test_signup_duplicate_email(self):
        User.objects.create_user(email='existing@example.com', password='password123')
        response = self.client.post(self.signup_url, {
            'email': 'existing@example.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
        })
        assert response.status_code == 400
        assert 'Email already registered' in str(response.data)

    def test_signup_password_mismatch(self):
        response = self.client.post(self.signup_url, {
            'email': 'candidate@example.com',
            'password': 'securepassword123',
            'password_confirm': 'differentpassword',
        })
        assert response.status_code == 400
        assert 'Passwords do not match' in str(response.data)

    def test_signup_weak_password(self):
        response = self.client.post(self.signup_url, {
            'email': 'candidate@example.com',
            'password': 'short',
            'password_confirm': 'short',
        })
        assert response.status_code == 400

    def test_signup_invalid_email(self):
        response = self.client.post(self.signup_url, {
            'email': 'not-an-email',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestVerifyEmail:
    def setup_method(self):
        self.client = APIClient()
        self.verify_url = '/api/auth/verify-email'
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = False
        self.user.save()

    def test_verify_email_success(self):
        token = 'test-token-123'
        expires_at = timezone.now() + timedelta(hours=24)
        EmailVerificationToken.objects.create(
            user=self.user,
            token=token,
            expires_at=expires_at
        )
        response = self.client.post(self.verify_url, {'token': token})
        assert response.status_code == 200
        assert response.data['message'] == 'Email verified successfully'
        user = User.objects.get(email='candidate@example.com')
        assert user.is_active
        assert not EmailVerificationToken.objects.filter(user=self.user).exists()

    def test_verify_email_invalid_token(self):
        response = self.client.post(self.verify_url, {'token': 'invalid-token'})
        assert response.status_code == 400
        assert 'Invalid token' in str(response.data)

    def test_verify_email_expired_token(self):
        token = 'test-token-expired'
        expires_at = timezone.now() - timedelta(hours=1)
        EmailVerificationToken.objects.create(
            user=self.user,
            token=token,
            expires_at=expires_at
        )
        response = self.client.post(self.verify_url, {'token': token})
        assert response.status_code == 400
        assert 'Token expired' in str(response.data)


@pytest.mark.django_db
class TestLogin:
    def setup_method(self):
        self.client = APIClient()
        self.login_url = '/api/auth/login'
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'email': 'candidate@example.com',
            'password': 'securepassword123',
            'remember_me': False,
        })
        assert response.status_code == 200
        assert 'token' in response.data
        assert response.data['user_id'] == self.user.id
        assert response.data['email'] == 'candidate@example.com'
        session = SessionToken.objects.get(user=self.user)
        assert session.token == response.data['token']
        assert not session.remember_me

    def test_login_with_remember_me(self):
        response = self.client.post(self.login_url, {
            'email': 'candidate@example.com',
            'password': 'securepassword123',
            'remember_me': True,
        })
        assert response.status_code == 200
        session = SessionToken.objects.get(user=self.user)
        assert session.remember_me

    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, {
            'email': 'candidate@example.com',
            'password': 'wrongpassword',
            'remember_me': False,
        })
        assert response.status_code == 400
        assert 'Invalid email or password' in str(response.data)

    def test_login_nonexistent_email(self):
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com',
            'password': 'securepassword123',
            'remember_me': False,
        })
        assert response.status_code == 400
        assert 'Invalid email or password' in str(response.data)

    def test_login_unverified_email(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, {
            'email': 'candidate@example.com',
            'password': 'securepassword123',
            'remember_me': False,
        })
        assert response.status_code == 400
        assert 'Email not verified' in str(response.data)


@pytest.mark.django_db
class TestForgotPassword:
    def setup_method(self):
        self.client = APIClient()
        self.forgot_url = '/api/auth/forgot-password'
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()

    def test_forgot_password_success(self):
        response = self.client.post(self.forgot_url, {
            'email': 'candidate@example.com'
        })
        assert response.status_code == 200
        assert response.data['message'] == 'Password reset email sent'
        assert len(mail.outbox) == 1
        assert 'Reset your password' in mail.outbox[0].subject
        assert PasswordResetToken.objects.filter(user=self.user).exists()

    def test_forgot_password_nonexistent_email(self):
        response = self.client.post(self.forgot_url, {
            'email': 'nonexistent@example.com'
        })
        assert response.status_code == 400
        assert 'Email not found' in str(response.data)


@pytest.mark.django_db
class TestResetPassword:
    def setup_method(self):
        self.client = APIClient()
        self.reset_url = '/api/auth/reset-password'
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='oldpassword123'
        )
        self.user.is_active = True
        self.user.save()

    def test_reset_password_success(self):
        token = 'reset-token-123'
        expires_at = timezone.now() + timedelta(hours=24)
        PasswordResetToken.objects.create(
            user=self.user,
            token=token,
            expires_at=expires_at
        )
        response = self.client.post(self.reset_url, {
            'token': token,
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
        })
        assert response.status_code == 200
        assert response.data['message'] == 'Password reset successful'
        self.user.refresh_from_db()
        assert self.user.check_password('newpassword123')
        assert not PasswordResetToken.objects.filter(user=self.user).exists()

    def test_reset_password_mismatch(self):
        token = 'reset-token-123'
        expires_at = timezone.now() + timedelta(hours=24)
        PasswordResetToken.objects.create(
            user=self.user,
            token=token,
            expires_at=expires_at
        )
        response = self.client.post(self.reset_url, {
            'token': token,
            'password': 'newpassword123',
            'password_confirm': 'differentpassword',
        })
        assert response.status_code == 400
        assert 'Passwords do not match' in str(response.data)

    def test_reset_password_invalid_token(self):
        response = self.client.post(self.reset_url, {
            'token': 'invalid-token',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
        })
        assert response.status_code == 400
        assert 'Invalid token' in str(response.data)

    def test_reset_password_expired_token(self):
        token = 'reset-token-expired'
        expires_at = timezone.now() - timedelta(hours=1)
        PasswordResetToken.objects.create(
            user=self.user,
            token=token,
            expires_at=expires_at
        )
        response = self.client.post(self.reset_url, {
            'token': token,
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
        })
        assert response.status_code == 400
        assert 'Token expired' in str(response.data)


@pytest.mark.django_db
class TestLogout:
    def setup_method(self):
        self.client = APIClient()
        self.logout_url = '/api/auth/logout'
        self.user = User.objects.create_user(

            email='candidate@example.com',
            password='securepassword123'
        )
        self.user.is_active = True
        self.user.save()
        self.session = SessionToken.objects.create(
            user=self.user,
            token='test-session-token',
            expires_at=timezone.now() + timedelta(hours=24)
        )

    def test_logout_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.session.token}')
        response = self.client.post(self.logout_url)
        assert response.status_code == 200
        assert response.data['message'] == 'Logout successful'
        assert not SessionToken.objects.filter(token='test-session-token').exists()
