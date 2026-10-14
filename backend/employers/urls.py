from django.urls import path
from .views import EmployerRegisterView, EmployerProfileView
from .team_views import TeamMembersListView, TeamMemberDetailView
from .job_views import JobListCreateView, JobDetailView
from .job_management_views import JobMetricsView
from .candidate_search_views import CandidateSearchView
from .shortlist_views import ShortlistListView, ShortlistDetailView
from .application_review_views import EmployerApplicationsListView, EmployerApplicationDetailView
from .application_shortlist_views import ApplicationShortlistListView, ApplicationShortlistDetailView
from .commission_views import AdminCommissionsListView, EmployerCommissionsListView, CommissionDetailView
from .invoice_views import EmployerInvoicesListView, EmployerInvoiceDetailView, AdminInvoicesListView
from .payment_views import PaymentListCreateView, PaymentCallbackView, EmployerPaymentsListView, AdminPaymentsListView, EmployerPaymentDetailView
from .analytics_views import RevenueAnalyticsView, CommissionMetricsView, PaymentReconciliationView, DisputeManagementView

urlpatterns = [
    # ===== EMPLOYER PROFILE & TEAM =====
    path('register', EmployerRegisterView.as_view(), name='employer-register'),
    path('profile', EmployerProfileView.as_view(), name='employer-profile'),                    # GET/PATCH own profile
    path('team-members', TeamMembersListView.as_view(), name='team-members-list'),              # GET/POST
    path('team-members/<int:member_id>', TeamMemberDetailView.as_view(), name='team-member-detail'),  # GET/PATCH/DELETE

    # ===== JOBS (REST-compliant) =====
    path('jobs', JobListCreateView.as_view(), name='job-list-create'),                          # GET list, POST create
    path('jobs/<int:job_id>', JobDetailView.as_view(), name='job-detail'),                      # GET, PATCH (includes status changes), DELETE
    path('jobs/<int:job_id>/metrics', JobMetricsView.as_view(), name='job-metrics'),            # GET metrics

    # ===== CANDIDATES (Search & view) =====
    path('candidates', CandidateSearchView.as_view(), name='candidate-search'),                 # GET with ?location=...&skills=...

    # ===== SHORTLISTS (REST-compliant) =====
    path('shortlists', ShortlistListView.as_view(), name='shortlist-list'),                     # GET/POST
    path('shortlists/<int:shortlist_id>', ShortlistDetailView.as_view(), name='shortlist-detail'),  # GET/PATCH/DELETE

    # ===== APPLICATIONS (REST-compliant) =====
    path('applications', EmployerApplicationsListView.as_view(), name='applications-list'),    # GET list with filters
    path('applications/<int:application_id>', EmployerApplicationDetailView.as_view(), name='application-detail'),  # GET, PATCH (includes status)

    # ===== APPLICATION SHORTLISTS (REST-compliant) =====
    path('application-shortlists', ApplicationShortlistListView.as_view(), name='application-shortlist-list'),  # GET/POST
    path('application-shortlists/<int:shortlist_id>', ApplicationShortlistDetailView.as_view(), name='application-shortlist-detail'),  # GET/PATCH/DELETE

    # ===== COMMISSIONS (REST-compliant) =====
    path('commissions', EmployerCommissionsListView.as_view(), name='commissions-list'),       # GET list with filters
    path('commissions/<int:commission_id>', CommissionDetailView.as_view(), name='commission-detail'),  # GET, PATCH

    # ===== INVOICES (REST-compliant) =====
    path('invoices', EmployerInvoicesListView.as_view(), name='invoices-list'),                # GET list
    path('invoices/<int:invoice_id>', EmployerInvoiceDetailView.as_view(), name='invoice-detail'),  # GET, PATCH
    path('invoices/<int:invoice_id>/payments', PaymentListCreateView.as_view(), name='invoice-payments'),  # POST to create payment

    # ===== PAYMENTS (REST-compliant) =====
    path('payments', EmployerPaymentsListView.as_view(), name='payments-list'),                # GET list
    path('payments/<int:payment_id>', EmployerPaymentDetailView.as_view(), name='payment-detail'),  # GET
]

admin_urlpatterns = [
    path('admin/commissions', AdminCommissionsListView.as_view(), name='admin-commissions-list'),
    path('admin/invoices', AdminInvoicesListView.as_view(), name='admin-invoices-list'),
    path('admin/payments', AdminPaymentsListView.as_view(), name='admin-payments-list'),
    path('admin/analytics/revenue', RevenueAnalyticsView.as_view(), name='revenue-analytics'),
    path('admin/analytics/commissions', CommissionMetricsView.as_view(), name='commission-metrics'),
    path('admin/reconciliation', PaymentReconciliationView.as_view(), name='payment-reconciliation'),
    path('admin/disputes', DisputeManagementView.as_view(), name='disputes-list'),
    path('admin/commissions/<int:commission_id>/dispute', DisputeManagementView.as_view(), name='mark-disputed'),
]

webhook_urlpatterns = [
    path('webhooks/payment-callback', PaymentCallbackView.as_view(), name='payment-callback'),
]

urlpatterns += admin_urlpatterns + webhook_urlpatterns
