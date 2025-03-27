from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import User
from .forms import UserProfileForm
from library.models import Loan

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Current active loans
        current_loans = Loan.objects.filter(
            user=user,
            returned_date__isnull=True
        ).select_related('book')
        
        # Loan history (last 6 months)
        loan_history = Loan.objects.filter(
            user=user,
            returned_date__isnull=False,
            checkout_date__gte=timezone.now() - timezone.timedelta(days=180)
        ).order_by('-checkout_date')
        
        context.update({
            'current_loans': current_loans,
            'loan_history': loan_history,
            'borrowing_limit': 10  # Default borrowing limit
        })
        return context

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('account_dashboard')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully')
        return super().form_valid(form)

@require_http_methods(["GET"])
def user_loans_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    loans = Loan.objects.filter(user=request.user).order_by('-checkout_date')
    data = {
        'current': [],
        'history': []
    }
    
    for loan in loans:
        loan_data = {
            'id': loan.id,
            'book_id': loan.book.id,
            'book_title': loan.book.title,
            'book_author': loan.book.author,
            'checkout_date': loan.checkout_date.strftime('%Y-%m-%d'),
            'due_date': loan.due_date.strftime('%Y-%m-%d'),
            'is_overdue': loan.is_overdue,
            'is_returned': loan.returned_date is not None
        }
        
        if loan.returned_date:
            data['history'].append(loan_data)
        else:
            data['current'].append(loan_data)
    
    return JsonResponse(data)

@login_required
def loan_management(request):
    """View for managing user loans"""
    user_loans = Loan.objects.filter(user=request.user).select_related('book')
    return render(request, 'accounts/loan_management.html', {
        'loans': user_loans
    })

@login_required
def send_reminder(request, loan_id):
    """Send reminder email for overdue loan"""
    from django.core.mail import send_mail
    from django.contrib import messages
    from django.core.exceptions import PermissionDenied
    from library.models import Loan
    
    if not request.user.is_librarian:
        raise PermissionDenied
    
    loan = get_object_or_404(Loan, pk=loan_id)
    
    if loan.is_overdue:
        send_mail(
            'Overdue Book Reminder',
            f'Please return "{loan.book.title}" by {loan.due_date}',
            'library@example.com',
            [loan.user.email],
            fail_silently=False,
        )
        messages.success(request, f'Reminder sent to {loan.user.email}')
    else:
        messages.warning(request, 'This loan is not yet overdue')
    
    return redirect('loan-management')

@login_required
def user_management(request):
    """View for managing users (librarian only)"""
    from django.contrib.auth import get_user_model
    from django.core.exceptions import PermissionDenied
    
    if not request.user.is_librarian:
        raise PermissionDenied
    
    User = get_user_model()
    users = User.objects.all().order_by('-date_joined')
    
    return render(request, 'accounts/user_management.html', {
        'users': users
    })

class LibrarianDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/librarian_dashboard.html'
    permission_required = 'library.manage_books'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Overdue books
        overdue_books = Loan.objects.filter(
            due_date__lt=today,
            returned_date__isnull=True
        ).select_related('book', 'user')
        
        # Today's stats
        stats = {
            'today_checkouts': Loan.objects.filter(
                checkout_date__date=today
            ).count(),
            'today_returns': Loan.objects.filter(
                returned_date__date=today
            ).count(),
            'overdue_books': overdue_books.count()
        }
        
        # Recent activity (last 10 actions)
        recent_activity = []  # Would come from ActivityLog model
        
        context.update({
            'overdue_books': overdue_books,
            'stats': stats,
            'recent_activity': recent_activity
        })
        return context
