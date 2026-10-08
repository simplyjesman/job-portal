from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import ExternalLink
from .serializers import ExternalLinkSerializer


class ExternalLinksListCreateView(APIView):
    """GET/POST /candidates/profile/links/ - List and create external links."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all external links for own profile."""
        try:
            profile = request.user.candidate_profile
        except:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        links = profile.external_links.all()
        serializer = ExternalLinkSerializer(links, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Add an external link (only in draft mode)."""
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
        serializer = ExternalLinkSerializer(data=data)

        if serializer.is_valid():
            serializer.save(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExternalLinksDetailView(APIView):
    """GET/PUT/DELETE /candidates/profile/links/{id}/ - Manage single link."""
    permission_classes = [IsAuthenticated]

    def get(self, request, link_id):
        """Get a single external link."""
        try:
            profile = request.user.candidate_profile
            link = profile.external_links.get(id=link_id)
        except:
            return Response(
                {'error': 'Link not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ExternalLinkSerializer(link)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, link_id):
        """Update an external link (draft only)."""
        try:
            profile = request.user.candidate_profile
            link = profile.external_links.get(id=link_id)
        except:
            return Response(
                {'error': 'Link not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ExternalLinkSerializer(link, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, link_id):
        """Delete an external link (draft only)."""
        try:
            profile = request.user.candidate_profile
            link = profile.external_links.get(id=link_id)
        except:
            return Response(
                {'error': 'Link not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.profile_status == 'live':
            return Response(
                {'error': 'Cannot edit a live profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
