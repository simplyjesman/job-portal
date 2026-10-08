from django.contrib import admin
from django.urls import path, include
from profiles.skill_views import SkillListView, CandidateSkillView
from profiles.work_history_management_views import (
    WorkHistoryListCreateView, WorkHistoryDetailView as WorkHistoryManagementDetailView
)
from profiles.education_management_views import (
    EducationListCreateView, EducationDetailView as EducationManagementDetailView
)
from profiles.external_links_management_views import (
    ExternalLinksListCreateView, ExternalLinksDetailView as ExternalLinksDetailManagementView
)
from profiles.availability_views import AvailabilityView
from profiles.profile_rest_views import (
    CandidateProfileListCreateView, CandidateProfileDetailView,
    CandidatePublicSearchView, CandidatePublicProfileView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/employer/', include('employers.urls')),

    # ===== CANDIDATES (Public Search & View) =====
    path('api/candidates', CandidatePublicSearchView.as_view(), name='candidate-list-search'),
    path('api/candidates/<int:candidate_id>', CandidatePublicProfileView.as_view(), name='candidate-public-profile'),

    # ===== PROFILES (Own authenticated profile) =====
    # Context-aware: all methods (GET/POST/PATCH/DELETE) on same URL
    path('api/profiles', CandidateProfileListCreateView.as_view(), name='profile-detail'),  # GET own, POST create, PATCH/DELETE

    # Profile sub-resources
    path('api/profiles/skills', CandidateSkillView.as_view(), name='profile-skills'),          # GET/POST/PATCH own skills
    path('api/profiles/work-history', WorkHistoryListCreateView.as_view(), name='work-history-list-create'),  # GET/POST own work history
    path('api/profiles/work-history/<int:work_history_id>', WorkHistoryManagementDetailView.as_view(), name='work-history-detail'),  # GET/PATCH/DELETE
    path('api/profiles/education', EducationListCreateView.as_view(), name='education-list-create'),  # GET/POST own education
    path('api/profiles/education/<int:education_id>', EducationManagementDetailView.as_view(), name='education-detail'),  # GET/PATCH/DELETE
    path('api/profiles/links', ExternalLinksListCreateView.as_view(), name='links-list-create'),  # GET/POST own links
    path('api/profiles/links/<int:link_id>', ExternalLinksDetailManagementView.as_view(), name='links-detail'),  # GET/PATCH/DELETE
    path('api/profiles/availability', AvailabilityView.as_view(), name='availability'),        # GET/PATCH own availability

    # ===== SKILLS (Global) =====
    path('api/skills', SkillListView.as_view(), name='skill-list'),                           # GET all skills
]
