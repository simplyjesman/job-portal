"""REST-compliant profile views using context-aware endpoints (no /me)."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Q
from .models import CandidateProfile
from .serializers import CandidateProfileDetailSerializer, CandidateProfileEditSerializer
from jobs.invite_models import InterviewInvite


class CandidateProfileListCreateView(APIView):
    """
    Context-aware own profile endpoint (GET/POST/PATCH/DELETE all on same URL).
    GET /api/profiles - returns authenticated user's profile
    POST /api/profiles - creates profile for authenticated user
    PATCH /api/profiles - updates own profile (including status changes)
    DELETE /api/profiles - soft-deletes own profile
    """
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

    def post(self, request):
        """Create initial profile for authenticated user."""
        if hasattr(request.user, 'candidate_profile'):
            return Response(
                {'error': 'Profile already exists. Use PATCH to update.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CandidateProfileEditSerializer(data=request.data)
        if serializer.is_valid():
            profile = CandidateProfile.objects.create(
                user=request.user,
                **serializer.validated_data
            )
            return Response(
                CandidateProfileDetailSerializer(profile).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Update own profile (handles status, profile_status changes via PATCH)."""
        try:
            profile = request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Handle profile_status changes (publish/revert)
        if 'profile_status' in request.data:
            new_status = request.data.get('profile_status')
            if new_status == 'live' and profile.profile_status != 'live':
                validation_errors = self._validate_publish_requirements(profile)
                if validation_errors:
                    return Response(validation_errors, status=status.HTTP_400_BAD_REQUEST)
                profile.profile_status = 'live'
                profile.published_at = timezone.now()
            elif new_status == 'draft' and profile.profile_status == 'live':
                in_progress_invites = InterviewInvite.objects.filter(
                    candidate__user=request.user,
                    status__in=['sent', 'accepted']
                ).exists()
                if in_progress_invites:
                    return Response(
                        {'error': 'Cannot revert to draft while interview requests are in progress'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                profile.profile_status = 'draft'
                profile.published_at = None

        # Handle status changes (pause/unpause/archive)
        if 'status' in request.data:
            new_status = request.data.get('status')
            if new_status in ['active', 'paused', 'archived']:
                profile.status = new_status
                if new_status == 'archived':
                    profile.archived_at = timezone.now()

        # Update other fields (only if profile is draft)
        update_fields = {k: v for k, v in request.data.items()
                        if k not in ['profile_status', 'status', 'id', 'user', 'created_at', 'updated_at']}

        if update_fields:
            if profile.profile_status == 'live':
                return Response(
                    {'error': 'Cannot edit a live profile. Revert to draft first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = CandidateProfileEditSerializer(profile, data=update_fields, partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile.save()
        return Response(
            CandidateProfileDetailSerializer(profile).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        """Soft-delete own profile (archive)."""
        try:
            profile = request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        profile.status = 'archived'
        profile.archived_at = timezone.now()
        profile.save()

        return Response(
            {'message': 'Profile deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

    def _validate_publish_requirements(self, profile):
        """Validate that profile has required fields to publish."""
        errors = {}
        if not profile.headline:
            errors['headline'] = 'Headline is required before publishing'
        if not profile.location:
            errors['location'] = 'Location is required before publishing'
        if not profile.availability:
            errors['availability'] = 'Notice period is required before publishing'
        if not profile.work_history.exists():
            errors['work_history'] = 'At least one work experience entry is required'
        return errors if errors else None


class CandidateProfileDetailView(APIView):
    """Deprecated - all profile operations now on /api/profiles via CandidateProfileListCreateView."""
    pass


class CandidatePublicSearchView(APIView):
    """
    Public candidate search endpoint.
    GET /api/candidates - list public (live) profiles with filters
    No authentication required (open to all).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Search public candidate profiles."""
        queryset = CandidateProfile.objects.filter(
            profile_status='live',
            status='active'
        ).select_related('user').prefetch_related('skills', 'availability')

        location = request.query_params.get('location', '')
        if location:
            queryset = queryset.filter(location__icontains=location)

        skills = request.query_params.getlist('skills')
        if skills:
            try:
                skill_ids = [int(s) for s in skills]
                queryset = queryset.filter(skills__id__in=skill_ids).distinct()
            except (ValueError, TypeError):
                pass

        salary_min = request.query_params.get('salary_min')
        if salary_min:
            try:
                salary_min = int(salary_min)
                queryset = queryset.filter(salary_expectations__gte=salary_min)
            except (ValueError, TypeError):
                pass

        salary_max = request.query_params.get('salary_max')
        if salary_max:
            try:
                salary_max = int(salary_max)
                queryset = queryset.filter(salary_expectations__lte=salary_max)
            except (ValueError, TypeError):
                pass

        sort = request.query_params.get('sort', '-published_at')
        if sort in ['-published_at', 'published_at', '-created_at', 'created_at']:
            queryset = queryset.order_by(sort)

        page = request.query_params.get('page', 1)
        try:
            page = int(page)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

        page_size = 20
        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        profiles = queryset[start:end]

        results = [
            {
                'id': profile.id,
                'user_id': profile.user_id,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'headline': profile.headline,
                'location': profile.location,
                'phone': profile.phone,
                'salary_expectations': profile.salary_expectations,
                'availability': profile.availability,
                'profile_status': profile.profile_status,
                'published_at': profile.published_at,
            }
            for profile in profiles
        ]

        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': results
        }, status=status.HTTP_200_OK)


class CandidatePublicProfileView(APIView):
    """
    Public candidate profile detail view.
    GET /api/candidates/<id> - view public profile (live profiles only)
    No authentication required (open to all).
    """
    permission_classes = [AllowAny]

    def get(self, request, candidate_id):
        """Get a candidate's live public profile."""
        try:
            profile = CandidateProfile.objects.get(
                user_id=candidate_id,
                profile_status='live',
                status='active'
            )
        except CandidateProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found or not yet public'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CandidateProfileDetailSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
