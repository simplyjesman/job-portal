from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import SessionToken
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        try:
            user = User.objects.get(email=email or username)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None


class SessionTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
    model = SessionToken

    def get_model(self):
        return self.model

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.get(token=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        if not token.is_valid():
            raise AuthenticationFailed('Token expired.')

        if not token.user.is_active:
            raise AuthenticationFailed('User account is inactive.')

        return (token.user, token)
