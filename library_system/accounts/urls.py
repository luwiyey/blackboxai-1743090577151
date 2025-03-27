from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # User views
    path('dashboard/', views.UserDashboardView.as_view(), name='dashboard'),
    path('profile/', views.UserProfileUpdateView.as_view(), name='profile'),
    
    # Librarian views
    path('librarian/', views.LibrarianDashboardView.as_view(), name='librarian-dashboard'),
    path('loans/', views.loan_management, name='loan-management'),
    path('users/', views.user_management, name='user-management'),
    
    # API endpoints
    path('api/loans/', views.user_loans_api, name='user-loans-api'),
]

# HTMX endpoints
htmx_urlpatterns = [
    path('send-reminder/<int:loan_id>/', views.send_reminder, name='send-reminder'),
]

urlpatterns += htmx_urlpatterns