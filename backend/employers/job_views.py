from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import EmployerUser, Employer
from .job_models import Job
from .job_serializers import JobSerializer


class JobListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            jobs = Job.objects.filter(employer=employer_user.employer)
            serializer = JobSerializer(jobs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            if employer_user.role not in ['admin', 'recruiter']:
                return Response(
                    {'error': 'Only admins and recruiters can post jobs.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            data = request.data.copy()
            data['employer'] = employer_user.employer.id
            serializer = JobSerializer(data=data)
            if serializer.is_valid():
                serializer.save(employer=employer_user.employer)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )


class JobDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
            serializer = JobSerializer(job)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request, job_id):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            job = Job.objects.get(id=job_id, employer=employer_user.employer)

            if employer_user.role not in ['admin', 'recruiter']:
                return Response(
                    {'error': 'Only admins and recruiters can edit jobs.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = JobSerializer(job, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found or does not belong to your employer.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, job_id):
        try:
            employer_user = EmployerUser.objects.get(user=request.user)
            job = Job.objects.get(id=job_id, employer=employer_user.employer)

            if employer_user.role not in ['admin', 'recruiter']:
                return Response(
                    {'error': 'Only admins and recruiters can delete jobs.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            job.delete()
            return Response(
                {'message': 'Job deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except EmployerUser.DoesNotExist:
            return Response(
                {'error': 'Employer not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Job.DoesNotExist:
            return Response(
                {'error': 'Job not found or does not belong to your employer.'},
                status=status.HTTP_404_NOT_FOUND
            )
