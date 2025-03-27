from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    # Book views
    path('', views.BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('books/add/', views.BookCreateView.as_view(), name='book-create'),
    path('books/<int:pk>/edit/', views.BookUpdateView.as_view(), name='book-update'),
    
    # Book actions
    path('books/<int:pk>/borrow/', views.borrow_book, name='book-borrow'),
    path('books/<int:pk>/return/', views.return_book, name='book-return'),
    path('books/<int:pk>/renew/', views.renew_book, name='book-renew'),
    
    # Import/export
    path('import/', views.book_import, name='book-import'),
    path('import/template/', views.import_template, name='book-import-template'),
    path('export/', views.book_export, name='book-export'),
    
    # Reviews
    path('books/<int:pk>/review/', views.book_review, name='book-review'),
    
    # Home
    path('home/', views.home_view, name='home'),
]

# HTMX endpoints
htmx_urlpatterns = [
    path('search/', views.book_search, name='book-search'),
    path('check-availability/<int:pk>/', views.check_availability, name='check-availability'),
]

urlpatterns += htmx_urlpatterns