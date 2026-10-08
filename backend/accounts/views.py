from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import secrets
import jwt

User = get_user_model()

from .models import EmailVerificationToken, PasswordResetToken, SessionToken
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    VerifyEmailSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            self._send_verification_email(user)
            return Response(
                {'message': 'Signup successful. Check your email to verify.'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_verification_email(self, user):
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(seconds=settings.VERIFICATION_TOKEN_EXPIRY)
        EmailVerificationToken.objects.update_or_create(
            user=user,
            defaults={'token': token, 'expires_at': expires_at}
        )
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        send_mail(
            'Verify your email',
            f'Click the link to verify your email: {verification_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            token_obj = EmailVerificationToken.objects.get(token=serializer.validated_data['token'])
            user = token_obj.user
            user.is_active = True
            user.save()
            token_obj.delete()
            return Response(
                {'message': 'Email verified successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            session_token = self._create_session_token(user, serializer.validated_data.get('remember_me', False))
            return Response(
                {
                    'message': 'Login successful',
                    'token': session_token.token,
                    'user_id': user.id,
                    'email': user.email,
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _create_session_token(self, user, remember_me):
        token = secrets.token_urlsafe(32)
        if remember_me:
            expires_at = timezone.now() + timedelta(days=90)
        else:
            expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
        SessionToken.objects.filter(user=user).delete()
        return SessionToken.objects.create(
            user=user,
            token=token,
            remember_me=remember_me,
            expires_at=expires_at
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request, 'auth') and request.auth:
            request.auth.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.validated_data['email'])
            self._send_reset_email(user)
            return Response(
                {'message': 'Password reset email sent'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_reset_email(self, user):
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(seconds=settings.PASSWORD_RESET_TOKEN_EXPIRY)
        PasswordResetToken.objects.update_or_create(
            user=user,
            defaults={'token': token, 'expires_at': expires_at}
        )
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        send_mail(
            'Reset your password',
            f'Click the link to reset your password: {reset_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token_obj = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
            user = token_obj.user
            user.set_password(serializer.validated_data['password'])
            user.save()
            token_obj.delete()
            SessionToken.objects.filter(user=user).delete()
            return Response(
                {'message': 'Password reset successful'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
