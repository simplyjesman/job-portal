from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import CandidateProfile
from .serializers import CandidateProfileDetailSerializer, CandidateProfileEditSerializer
from jobs.invite_models import InterviewInvite


class CandidateOwnProfileView(APIView):
    """GET/PUT /candidates/profile/ - Own profile (authenticated user)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get own profile (full details for editing)."""
        try:
            profile = request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found. Complete signup first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CandidateProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """Update own profile (draft only)."""
        try:
            profile = request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile. Revert to draft first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CandidateProfileEditSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CandidateProfilePublicView(APIView):
    """GET /candidates/{id}/profile/ - Public profile view (any user can view live profiles)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, candidate_id):
        """Get a candidate's live profile (public view)."""
        try:
            profile = CandidateProfile.objects.get(user_id=candidate_id)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only show live profiles to employers
        if profile.profile_status != 'live':
            return Response(
                {'error': 'This profile is not yet public'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CandidateProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CandidateProfilePublishView(APIView):
    """POST /candidates/profile/publish/ - Make profile live."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Publish profile (go live)."""
        try:
            profile = request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check required fields
        if not profile.headline:
            return Response(
                {'error': 'Headline is required before publishing'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not profile.location:
            return Response(
                {'error': 'Location is required before publishing'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not profile.availability:
            return Response(
                {'error': 'Notice period is required before publishing'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not profile.work_history.exists():
            return Response(
                {'error': 'At least one work experience entry is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Already live?
        if profile.profile_status == 'live':
            return Response(
                {'error': 'Profile is already live'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Make it live
        profile.profile_status = 'live'
        profile.published_at = timezone.now()
        profile.save()

        serializer = CandidateProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CandidateProfileRevertView(APIView):
    """POST /candidates/profile/revert/ - Revert profile to draft."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Revert profile to draft (only if no in-progress interviews)."""
        try:
            profile = request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if profile is live
        if profile.profile_status != 'live':
            return Response(
                {'error': 'Profile is already in draft mode'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for in-progress interviews (pending or accepted invites)
        in_progress_invites = InterviewInvite.objects.filter(
            candidate__user=request.user,
            status__in=['sent', 'accepted']
        ).exists()

        if in_progress_invites:
            return Response(
                {'error': 'Cannot revert to draft while interview requests are in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Revert to draft
        profile.profile_status = 'draft'
        profile.published_at = None
        profile.save()

        serializer = CandidateProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
