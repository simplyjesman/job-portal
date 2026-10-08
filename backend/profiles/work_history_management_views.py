from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .work_history_models import WorkHistory
from .work_history_serializers import WorkHistorySerializer


class WorkHistoryListCreateView(APIView):
    """GET/POST /candidates/profile/work-history/ - List and create work experience."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all work history entries for own profile."""
        try:
            profile = request.user.candidate_profile
        except:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        work_history = profile.work_history.all()
        serializer = WorkHistorySerializer(work_history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Add a work history entry (only in draft mode)."""
        try:
            profile = request.user.candidate_profile
        except:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data['profile'] = profile.id
        serializer = WorkHistorySerializer(data=data)

        if serializer.is_valid():
            serializer.save(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkHistoryDetailView(APIView):
    """GET/PUT/DELETE /candidates/profile/work-history/{id}/ - Manage single entry."""
    permission_classes = [IsAuthenticated]

    def get(self, request, work_history_id):
        """Get a single work history entry."""
        try:
            profile = request.user.candidate_profile
            work = profile.work_history.get(id=work_history_id)
        except:
            return Response(
                {'error': 'Work history entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkHistorySerializer(work)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, work_history_id):
        """Update a work history entry (draft only)."""
        try:
            profile = request.user.candidate_profile
            work = profile.work_history.get(id=work_history_id)
        except:
            return Response(
                {'error': 'Work history entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = WorkHistorySerializer(work, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, work_history_id):
        """Delete a work history entry (draft only)."""
        try:
            profile = request.user.candidate_profile
            work = profile.work_history.get(id=work_history_id)
        except:
            return Response(
                {'error': 'Work history entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        work.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
