from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .education_models import Education
from .education_serializers import EducationSerializer


class EducationListCreateView(APIView):
    """GET/POST /candidates/profile/education/ - List and create education entries."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all education entries for own profile."""
        try:
            profile = request.user.candidate_profile
        except:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        education = profile.education.all()
        serializer = EducationSerializer(education, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Add an education entry (only in draft mode)."""
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
        serializer = EducationSerializer(data=data)

        if serializer.is_valid():
            serializer.save(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EducationDetailView(APIView):
    """GET/PUT/DELETE /candidates/profile/education/{id}/ - Manage single entry."""
    permission_classes = [IsAuthenticated]

    def get(self, request, education_id):
        """Get a single education entry."""
        try:
            profile = request.user.candidate_profile
            education = profile.education.get(id=education_id)
        except:
            return Response(
                {'error': 'Education entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EducationSerializer(education)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, education_id):
        """Update an education entry (draft only)."""
        try:
            profile = request.user.candidate_profile
            education = profile.education.get(id=education_id)
        except:
            return Response(
                {'error': 'Education entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = EducationSerializer(education, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, education_id):
        """Delete an education entry (draft only)."""
        try:
            profile = request.user.candidate_profile
            education = profile.education.get(id=education_id)
        except:
            return Response(
                {'error': 'Education entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        education.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
