from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from profiles.models import CandidateProfile
from employers.models import Employer, EmployerUser
from .invite_models import InterviewInvite
from .hire_models import Hire
from .invite_serializers import InterviewInviteSerializer, SendInterviewInviteSerializer, CandidateResponseSerializer
from employers.commission_models import Commission


class EmployerInterviewInviteViewSet(viewsets.ModelViewSet):
    """Employer sending and managing interview invites."""
    serializer_class = InterviewInviteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only return invites sent by this employer."""
        try:
            employer_user = self.request.user.employer_user
            return InterviewInvite.objects.filter(employer=employer_user.employer)
        except:
            return InterviewInvite.objects.none()

    @action(detail=False, methods=['post'])
    def send_invite(self, request):
        """Employer sends interview invite to candidate."""
        serializer = SendInterviewInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            employer_user = request.user.employer_user
            candidate = CandidateProfile.objects.get(id=serializer.validated_data['candidate_id'])
        except (CandidateProfile.DoesNotExist, EmployerUser.DoesNotExist):
            return Response({'error': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create invite
        invite = InterviewInvite.objects.create(
            candidate=candidate,
            employer=employer_user.employer,
            job_title=serializer.validated_data['job_title'],
            job_description=serializer.validated_data['job_description'],
            salary_min=serializer.validated_data.get('salary_min'),
            salary_max=serializer.validated_data.get('salary_max'),
            location=serializer.validated_data.get('location', ''),
            message=serializer.validated_data.get('message', ''),
        )

        return Response(InterviewInviteSerializer(invite).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Employer cancels sent invite."""
        invite = self.get_object()
        if invite.status != 'sent':
            return Response({'error': 'Only sent invites can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        invite.cancel()
        return Response(InterviewInviteSerializer(invite).data)


class CandidateInterviewInviteViewSet(viewsets.ModelViewSet):
    """Candidate viewing and responding to interview invites."""
    serializer_class = InterviewInviteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only return invites sent to this candidate."""
        try:
            candidate = self.request.user.candidate_profile
            return candidate.interview_invites.all()
        except CandidateProfile.DoesNotExist:
            return InterviewInvite.objects.none()

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Candidate accepts or declines interview invite."""
        invite = self.get_object()
        serializer = CandidateResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if invite.status != 'sent':
            return Response({'error': 'This invite has already been responded to.'}, status=status.HTTP_400_BAD_REQUEST)

        action_type = serializer.validated_data['action']

        if action_type == 'accept':
            invite.accept()

            # Create hire record
            hire = Hire.objects.create(invite=invite, accepted_at=timezone.now())

            # Create commission record (auto-triggered on acceptance)
            commission = Commission.objects.create(
                hire=hire,
                employer=invite.employer,
                amount_gbp=0,  # Commission amount would be calculated based on salary or fixed rate
                status='pending'
            )

            return Response({
                'status': 'Invite accepted',
                'hire_id': hire.id,
                'commission_id': commission.id
            }, status=status.HTTP_200_OK)

        elif action_type == 'decline':
            invite.decline()
            return Response({'status': 'Invite declined'}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending invites for candidate."""
        invites = self.get_queryset().filter(status='sent')
        serializer = self.get_serializer(invites, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def accepted(self, request):
        """Get accepted invites for candidate."""
        invites = self.get_queryset().filter(status='accepted')
        serializer = self.get_serializer(invites, many=True)
        return Response(serializer.data)
