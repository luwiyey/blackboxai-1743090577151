from django import forms
from .models import Book, Loan, Review

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'description', 'categories', 'quantity', 'publication_date', 'cover_image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
        }

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['book', 'user', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }