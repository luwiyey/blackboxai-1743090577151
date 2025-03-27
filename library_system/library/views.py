from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator
import csv
from datetime import datetime
from io import StringIO

from .models import Book, Category
from .forms import BookForm

class BookListView(ListView):
    model = Book
    template_name = 'library/book_list.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().filter(available__gt=0)
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(isbn__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

class BookDetailView(DetailView):
    model = Book
    template_name = 'library/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        context['reviews'] = book.reviews.all().order_by('-created_at')[:5]
        if self.request.user.is_authenticated:
            context['current_loan'] = book.loans.filter(
                user=self.request.user,
                returned_date__isnull=True
            ).first()
            context['user_review'] = book.reviews.filter(
                user=self.request.user
            ).first()
        return context

class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'library/book_form.html'
    permission_required = 'library.add_book'
    success_url = reverse_lazy('book-list')

class BookUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'library/book_form.html'
    permission_required = 'library.change_book'

    def get_success_url(self):
        return reverse_lazy('book-detail', kwargs={'pk': self.object.pk})

@require_http_methods(["POST"])
def borrow_book(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    book = Book.objects.get(pk=pk)
    if book.available <= 0:
        return JsonResponse({'error': 'No available copies'}, status=400)
    
    # Create loan logic here
    return JsonResponse({
        'success': True,
        'message': f'You have successfully borrowed {book.title}',
        'available': book.available - 1
    })

@require_http_methods(["POST"])
def return_book(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    book = Book.objects.get(pk=pk)
    # Update loan logic here
    return JsonResponse({
        'success': True,
        'message': f'You have returned {book.title}',
        'available': book.available + 1
    })

def export_books(request):
    format = request.GET.get('format', 'csv')
    fields = request.GET.getlist('fields', ['title', 'author', 'isbn'])
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    queryset = Book.objects.all()
    
    if start_date and end_date:
        queryset = queryset.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="books_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(fields)
        
        for book in queryset:
            row = [getattr(book, field) for field in fields]
            writer.writerow(row)
        
        return response
    
    elif format == 'json':
        data = list(queryset.values(*fields))
        return JsonResponse(data, safe=False)
    
    # Add other formats as needed

def check_availability(request, pk):
    """API endpoint to check book availability"""
    from django.http import JsonResponse
    from .models import Book
    
    try:
        book = Book.objects.get(pk=pk)
        return JsonResponse({
            'available': book.available > 0,
            'quantity': book.available
        })
    except Book.DoesNotExist:
        return JsonResponse({
            'error': 'Book not found'
        }, status=404)

def book_search(request):
    """View for searching books"""
    from django.shortcuts import render
    from django.db.models import Q
    from .models import Book
    
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
    
    return render(request, 'library/book_search.html', {
        'query': query,
        'results': results
    })

def home_view(request):
    """Home page view showing featured books"""
    from django.shortcuts import render
    from .models import Book
    
    featured_books = Book.objects.filter(featured=True)[:4]
    new_releases = Book.objects.order_by('-created_at')[:4]
    
    return render(request, 'library/home.html', {
        'featured_books': featured_books,
        'new_releases': new_releases
    })

def book_review(request, pk):
    """View for submitting book reviews"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from django.contrib.auth.decorators import login_required
    from .models import Book, Review
    from .forms import ReviewForm
    
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been submitted!')
            return redirect('book-detail', pk=book.pk)
    else:
        form = ReviewForm()
    
    return render(request, 'library/book_review.html', {
        'book': book,
        'form': form
    })

def book_export(request):
    """View for exporting books to CSV"""
    from django.http import HttpResponse
    import csv
    from .models import Book
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['title', 'author', 'isbn', 'description', 'quantity', 'available'])
    
    books = Book.objects.all()
    for book in books:
        writer.writerow([
            book.title,
            book.author,
            book.isbn,
            book.description,
            book.quantity,
            book.available
        ])
    
    return response

def import_template(request):
    """View to download a CSV import template"""
    from django.http import HttpResponse
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="book_import_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['title', 'author', 'isbn', 'description', 'quantity', 'available'])
    writer.writerow(['Sample Book Title', 'Author Name', '1234567890', 'Book description', '5', '5'])
    
    return response

def book_import(request):
    """View for importing books from CSV"""
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from django.core.files.storage import FileSystemStorage
    import csv
    from io import TextIOWrapper
    from .models import Book, Category
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file')
            return redirect('book-import')
        
        try:
            fs = FileSystemStorage()
            filename = fs.save(csv_file.name, csv_file)
            file_path = fs.path(filename)
            
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    Book.objects.create(
                        title=row['title'],
                        author=row['author'],
                        isbn=row['isbn'],
                        description=row.get('description', ''),
                        quantity=int(row.get('quantity', 1)),
                        available=int(row.get('available', 1))
                    )
            
            messages.success(request, 'Books imported successfully!')
            return redirect('book-list')
        except Exception as e:
            messages.error(request, f'Error importing books: {str(e)}')
            return redirect('book-import')
    
    return render(request, 'library/book_import.html')

def renew_book(request, pk):
    """View for renewing a book loan"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from django.utils import timezone
    from .models import Loan
    from .forms import LoanForm
    
    loan = get_object_or_404(Loan, pk=pk)
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.due_date = timezone.now() + timezone.timedelta(weeks=2)  # Renew for 2 weeks
            loan.save()
            messages.success(request, f'Loan for {loan.book.title} renewed successfully!')
            return redirect('loan-management')
    else:
        form = LoanForm(instance=loan)
    
    return render(request, 'library/book_renew.html', {
        'form': form,
        'loan': loan
    })
