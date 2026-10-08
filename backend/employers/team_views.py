from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Employer, EmployerUser
from .team_serializers import TeamMemberSerializer, AddTeamMemberSerializer

User = get_user_model()


class TeamMembersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            team_members = EmployerUser.objects.filter(employer=employer_user.employer)
            serializer = TeamMemberSerializer(team_members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            if employer_user.role != 'admin':
                return Response(
                    {'error': 'Only admins can add team members.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = AddTeamMemberSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                role = serializer.validated_data['role']
                user = User.objects.get(email=email)

                if EmployerUser.objects.filter(user=user, employer=employer_user.employer).exists():
                    return Response(
                        {'error': 'User is already a team member.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                team_member = EmployerUser.objects.create(
                    user=user,
                    employer=employer_user.employer,
                    role=role
                )

                result_serializer = TeamMemberSerializer(team_member)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )


class TeamMemberDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, member_id):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            if employer_user.role != 'admin':
                return Response(
                    {'error': 'Only admins can update team members.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            team_member = EmployerUser.objects.get(id=member_id, employer=employer_user.employer)

            if 'role' in request.data:
                team_member.role = request.data['role']
                team_member.save()

            serializer = TeamMemberSerializer(team_member)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Team member not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, member_id):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            if employer_user.role != 'admin':
                return Response(
                    {'error': 'Only admins can remove team members.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            team_member = EmployerUser.objects.get(id=member_id, employer=employer_user.employer)
            team_member.delete()

            return Response({'message': 'Team member removed.'}, status=status.HTTP_204_NO_CONTENT)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Team member not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
