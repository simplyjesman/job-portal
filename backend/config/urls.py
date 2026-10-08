from django.contrib import admin
from django.urls import path, include
from profiles.skill_views import SkillListView, CandidateSkillView
from profiles.work_history_views import WorkHistoryListView, WorkHistoryDetailView
from profiles.availability_views import AvailabilityView
from profiles.profile_status_views import ProfileStatusView
from profiles.profile_lifecycle_views import ProfilePauseView, ProfileUnpauseView, ProfileDeleteView
from profiles.profile_views import (
    CandidateOwnProfileView, CandidateProfilePublicView,
    CandidateProfilePublishView, CandidateProfileRevertView
)
from profiles.work_history_management_views import (
    WorkHistoryListCreateView, WorkHistoryDetailView as WorkHistoryManagementDetailView
)
from profiles.education_management_views import (
    EducationListCreateView, EducationDetailView as EducationManagementDetailView
)
from profiles.external_links_management_views import (
    ExternalLinksListCreateView, ExternalLinksDetailView as ExternalLinksDetailManagementView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/employer/', include('employers.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/profiles', include('profiles.urls')),
    path('api/skills', SkillListView.as_view(), name='skill-list'),
    path('api/profiles/<int:pk>/skills', CandidateSkillView.as_view(), name='candidate-skills'),
    path('api/profiles/<int:pk>/work-history', WorkHistoryListView.as_view(), name='work-history-list'),
    path('api/profiles/<int:pk>/work-history/<int:work_history_id>', WorkHistoryDetailView.as_view(), name='work-history-detail'),
    path('api/profiles/<int:pk>/availability', AvailabilityView.as_view(), name='availability'),
    path('api/profiles/<int:pk>/status', ProfileStatusView.as_view(), name='profile-status'),
    path('api/profiles/<int:pk>/pause', ProfilePauseView.as_view(), name='profile-pause'),
    path('api/profiles/<int:pk>/unpause', ProfileUnpauseView.as_view(), name='profile-unpause'),
    path('api/profiles/<int:pk>/delete', ProfileDeleteView.as_view(), name='profile-delete'),

    # Candidate profile endpoints (new REST endpoints)
    path('api/candidates/profile/', CandidateOwnProfileView.as_view(), name='own-profile'),
    path('api/candidates/<int:candidate_id>/profile/', CandidateProfilePublicView.as_view(), name='candidate-profile'),
    path('api/candidates/profile/publish/', CandidateProfilePublishView.as_view(), name='profile-publish'),
    path('api/candidates/profile/revert/', CandidateProfileRevertView.as_view(), name='profile-revert'),

    # Work history management
    path('api/candidates/profile/work-history/', WorkHistoryListCreateView.as_view(), name='work-history-list-create'),
    path('api/candidates/profile/work-history/<int:work_history_id>/', WorkHistoryManagementDetailView.as_view(), name='work-history-detail'),

    # Education management
    path('api/candidates/profile/education/', EducationListCreateView.as_view(), name='education-list-create'),
    path('api/candidates/profile/education/<int:education_id>/', EducationManagementDetailView.as_view(), name='education-detail'),

    # External links management
    path('api/candidates/profile/links/', ExternalLinksListCreateView.as_view(), name='links-list-create'),
    path('api/candidates/profile/links/<int:link_id>/', ExternalLinksDetailManagementView.as_view(), name='links-detail'),
]
